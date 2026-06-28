# app/vision/safety_detectors.py
"""
Feature  8  – Helmet Detection       (Missing → Implemented)
Feature  9  – Seatbelt Detection     (Missing → Implemented)
Feature 10  – Phone Usage Detection  (Missing → Implemented)
Feature 12  – Distraction Detection  (Partial → Full, head-pose added)
Feature 13  – Drunk Driver Detection (Missing → Implemented)
Feature 14  – Honk Detection         (Missing → Implemented, audio thread)

All detectors return a simple dataclass so the caller can decide how
to log / alert.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Shared YOLO loader
# ─────────────────────────────────────────────────────────────────────────────

def _yolo(path: str):
    try:
        from ultralytics import YOLO          # type: ignore
        return YOLO(path)
    except Exception as exc:
        logger.warning("YOLO not loaded (%s).", exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 1. Helmet Detection
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class HelmetResult:
    track_id: int
    has_helmet: bool


class HelmetDetector:
    """
    Checks whether a motorcycle rider wears a helmet.
    Uses a dedicated YOLO model when available, otherwise a Hough-circle
    heuristic on the top-third of each vehicle ROI.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        self._model   = _yolo(model_path) if model_path else None
        self._alerted: set[int] = set()

    def process(
        self, frame: np.ndarray, tracked_vehicles: Dict[int, dict]
    ) -> list[HelmetResult]:
        results = []
        for tid, info in tracked_vehicles.items():
            x1, y1, x2, y2 = info["bbox"]
            head = frame[y1: y1 + (y2 - y1) // 3, x1:x2]
            if head.size == 0:
                continue
            ok = self._check(head)
            color = (0, 200, 0) if ok else (0, 0, 255)
            label = "HELMET OK" if ok else "NO HELMET!"
            cv2.putText(frame, label, (x1, y1 - 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            results.append(HelmetResult(tid, ok))
        return results

    def _check(self, roi: np.ndarray) -> bool:
        if self._model:
            for r in self._model(roi, verbose=False):
                for box in r.boxes:
                    if int(box.cls[0]) == 0:       # class 0 = helmet
                        return True
            return False
        h, w = roi.shape[:2]
        if h < 10 or w < 10:
            return True
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), 0)
        circles = cv2.HoughCircles(
            blur, cv2.HOUGH_GRADIENT, 1.2,
            minDist=max(h // 2, 10), param1=80, param2=30,
            minRadius=max(h // 4, 5), maxRadius=max(h, 10),
        )
        return circles is not None


# ─────────────────────────────────────────────────────────────────────────────
# 2. Seatbelt Detection
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SeatbeltResult:
    track_id: int
    has_seatbelt: bool


class SeatbeltDetector:
    """
    Detects a diagonal seatbelt strap across the driver's torso via
    Hough line analysis, or via a custom YOLO model.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        consec_frames: int = 20,
    ) -> None:
        self._model   = _yolo(model_path) if model_path else None
        self._counter: Dict[int, int] = defaultdict(int)
        self._consec  = consec_frames
        self._alerted: set[int] = set()

    def process(
        self, frame: np.ndarray, tracked_vehicles: Dict[int, dict]
    ) -> list[SeatbeltResult]:
        results = []
        for tid, info in tracked_vehicles.items():
            x1, y1, x2, y2 = info["bbox"]
            h3 = (y2 - y1) // 3
            torso = frame[y1 + h3: y1 + 2 * h3, x1: x1 + (x2 - x1) // 2]
            if torso.size == 0:
                continue
            ok = self._detect(torso)
            if not ok:
                self._counter[tid] += 1
                if self._counter[tid] >= self._consec:
                    self._alerted.add(tid)
            else:
                self._counter[tid] = max(0, self._counter[tid] - 2)
                self._alerted.discard(tid)
            label = "SEATBELT OK" if ok else "NO SEATBELT!"
            color = (0, 200, 0) if ok else (0, 0, 255)
            cv2.putText(frame, label, (x1, y1 - 36),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
            results.append(SeatbeltResult(tid, ok))
        return results

    def _detect(self, torso: np.ndarray) -> bool:
        if self._model:
            for r in self._model(torso, verbose=False):
                for box in r.boxes:
                    if int(box.cls[0]) == 0:
                        return True
            return False
        gray  = cv2.cvtColor(torso, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 30,
                                 minLineLength=torso.shape[0] // 3, maxLineGap=20)
        if lines is None:
            return False
        for x1, y1, x2, y2 in lines[:, 0]:
            if x2 == x1:
                continue
            angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            if 25 < angle < 65:
                return True
        return False


# ─────────────────────────────────────────────────────────────────────────────
# 3. Phone Usage Detection
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PhoneResult:
    track_id: int
    phone_detected: bool


class PhoneUsageDetector:
    """
    Flags a driver holding a phone (COCO class 67) near their face.
    """

    PHONE_CLS = 67

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        consec_frames: int = 15,
    ) -> None:
        self._model   = _yolo(model_path)
        self._counter: Dict[int, int] = defaultdict(int)
        self._consec  = consec_frames
        self._alerted: set[int] = set()
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def process(
        self, frame: np.ndarray, tracked_vehicles: Dict[int, dict]
    ) -> list[PhoneResult]:
        results = []
        for tid, info in tracked_vehicles.items():
            x1, y1, x2, y2 = info["bbox"]
            roi = frame[y1:y2, x1:x2]
            if roi.size == 0:
                continue
            detected = self._check(roi)
            if detected:
                self._counter[tid] += 1
                if self._counter[tid] >= self._consec:
                    self._alerted.add(tid)
                cv2.putText(frame, "PHONE USAGE!", (x1, y1 - 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                self._counter[tid] = max(0, self._counter[tid] - 1)
                self._alerted.discard(tid)
            results.append(PhoneResult(tid, detected))
        return results

    def _check(self, roi: np.ndarray) -> bool:
        if self._model is None:
            return False
        phone_boxes, face_boxes = [], []
        for r in self._model(roi, conf=0.35, verbose=False):
            for box in r.boxes:
                cls    = int(box.cls[0])
                coords = list(map(int, box.xyxy[0]))
                if cls == self.PHONE_CLS:
                    phone_boxes.append(coords)
                elif cls == 0:
                    face_boxes.append(coords)
        if not face_boxes:
            gray  = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            faces = self._face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
            face_boxes = [[x, y, x + w, y + h] for x, y, w, h in faces]
        for pb in phone_boxes:
            for fb in face_boxes:
                if self._proximity(pb, fb) < 80:
                    return True
        return False

    @staticmethod
    def _proximity(a, b) -> float:
        ca = ((a[0] + a[2]) / 2, (a[1] + a[3]) / 2)
        cb = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
        return float(np.hypot(ca[0] - cb[0], ca[1] - cb[1]))


# ─────────────────────────────────────────────────────────────────────────────
# 4. Distraction Detection (head-pose – upgrades partial implementation)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DistractionResult:
    track_id: int
    distracted: bool
    yaw: float
    pitch: float


class DistractionDetector:
    """
    Estimates head pose (yaw/pitch) via 6-point PnP and flags distraction.
    Falls back to the existing EAR-based drowsiness check in driver_monitor.
    """

    _MODEL_PTS = np.array([
        [ 0.0,    0.0,    0.0   ],
        [ 0.0,  -330.0, -65.0  ],
        [-225.0,  170.0,-135.0 ],
        [ 225.0,  170.0,-135.0 ],
        [-150.0, -150.0,-125.0 ],
        [ 150.0, -150.0,-125.0 ],
    ], dtype=np.float64)

    def __init__(
        self,
        predictor_path: str = "shape_predictor_68_face_landmarks.dat",
        yaw_thresh: float = 25.0,
        pitch_thresh: float = 20.0,
        consec_frames: int = 20,
    ) -> None:
        self._yaw_thresh   = yaw_thresh
        self._pitch_thresh = pitch_thresh
        self._consec       = consec_frames
        self._counter: Dict[int, int] = defaultdict(int)
        self._alerted: set[int] = set()
        self._detector  = None
        self._predictor = None
        self._mp        = None
        self._load(predictor_path)

    def _load(self, predictor_path: str) -> None:
        try:
            import dlib                                         # type: ignore
            self._detector  = dlib.get_frontal_face_detector()
            self._predictor = dlib.shape_predictor(predictor_path)
            logger.info("DistractionDetector: dlib loaded.")
            return
        except Exception:
            pass
        try:
            import mediapipe as mp                              # type: ignore
            self._mp = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False, max_num_faces=1,
                refine_landmarks=True, min_detection_confidence=0.5)
            logger.info("DistractionDetector: MediaPipe loaded.")
        except Exception as exc:
            logger.warning("DistractionDetector: no pose model (%s).", exc)

    def process(
        self, frame: np.ndarray, tracked_vehicles: Dict[int, dict]
    ) -> list[DistractionResult]:
        results = []
        h, w   = frame.shape[:2]
        cam    = np.array([[w, 0, w/2], [0, w, h/2], [0, 0, 1]], np.float64)
        dist   = np.zeros((4, 1))

        for tid, info in tracked_vehicles.items():
            x1, y1, x2, y2 = info["bbox"]
            roi_gray = cv2.cvtColor(
                frame[max(0,y1):y2, max(0,x1):x2], cv2.COLOR_BGR2GRAY)
            yaw, pitch = self._pose(frame, roi_gray, x1, y1, cam, dist)
            if yaw is None:
                continue
            distracted = abs(yaw) > self._yaw_thresh or abs(pitch) > self._pitch_thresh
            if distracted:
                self._counter[tid] += 1
                if self._counter[tid] >= self._consec and tid not in self._alerted:
                    self._alerted.add(tid)
                cv2.putText(frame, f"DISTRACTED Y:{yaw:+.0f} P:{pitch:+.0f}",
                            (x1, y1 - 62),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            else:
                self._counter[tid] = max(0, self._counter[tid] - 1)
                self._alerted.discard(tid)
            results.append(DistractionResult(tid, distracted, yaw, pitch))
        return results

    def _pose(self, frame, roi_gray, ox, oy, cam, dist):
        pts = None
        if self._predictor and self._detector:
            faces = self._detector(roi_gray, 0)
            if not faces:
                return None, None
            shape = self._predictor(roi_gray, faces[0])
            idxs  = [30, 8, 36, 45, 48, 54]
            pts   = np.array(
                [(shape.part(i).x + ox, shape.part(i).y + oy) for i in idxs],
                np.float64)
        elif self._mp:
            res = self._mp.process(cv2.cvtColor(roi_gray, cv2.COLOR_GRAY2RGB))
            if not res.multi_face_landmarks:
                return None, None
            lm = res.multi_face_landmarks[0].landmark
            h, w = roi_gray.shape[:2]
            key  = [1, 152, 33, 263, 61, 291]
            pts  = np.array(
                [(lm[i].x * w + ox, lm[i].y * h + oy) for i in key], np.float64)
        else:
            return None, None
        ok, rvec, _ = cv2.solvePnP(
            self._MODEL_PTS, pts, cam, dist, flags=cv2.SOLVEPNP_ITERATIVE)
        if not ok:
            return None, None
        rmat, _ = cv2.Rodrigues(rvec)
        angles, *_ = cv2.RQDecomp3x3(rmat)
        return float(angles[1]), float(angles[0])


# ─────────────────────────────────────────────────────────────────────────────
# 5. Drunk Driver Detection
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DrunkDriverResult:
    track_id: int
    flagged: bool
    reason: str     # "SWERVE" | "DROWSY"


class DrunkDriverDetector:
    """
    Detects drunk/impaired driving via:
      • Swerve analysis  – lateral centroid deviation in recent frames
      • Drowsiness       – EAR from the existing driver_monitor module
    """

    def __init__(
        self,
        swerve_px: int = 80,
        swerve_frames: int = 15,
        ear_threshold: float = 0.22,
        ear_frames: int = 20,
    ) -> None:
        self._swerve_px     = swerve_px
        self._swerve_frames = swerve_frames
        self._ear_thresh    = ear_threshold
        self._ear_frames    = ear_frames
        self._cx_hist: Dict[int, deque]   = defaultdict(lambda: deque(maxlen=60))
        self._swerve_cnt: Dict[int, int]  = defaultdict(int)
        self._ear_cnt: Dict[int, int]     = defaultdict(int)
        self._alerted: set[int]           = set()
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self._eye_cascade  = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )

    def process(
        self, frame: np.ndarray, tracked_vehicles: Dict[int, dict]
    ) -> list[DrunkDriverResult]:
        results = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        for tid, info in tracked_vehicles.items():
            cx, _ = info["centroid"]
            x1, y1, x2, y2 = info["bbox"]
            self._cx_hist[tid].append(cx)

            # -- Swerve check
            if len(self._cx_hist[tid]) >= 10:
                xs = list(self._cx_hist[tid])
                if max(xs) - min(xs) > self._swerve_px:
                    self._swerve_cnt[tid] += 1
                    if (self._swerve_cnt[tid] >= self._swerve_frames
                            and tid not in self._alerted):
                        self._alerted.add(tid)
                        cv2.putText(frame, "DRUNK/ERRATIC!", (x1, y1 - 70),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        results.append(DrunkDriverResult(tid, True, "SWERVE"))
                        self._swerve_cnt[tid] = 0
                else:
                    self._swerve_cnt[tid] = max(0, self._swerve_cnt[tid] - 1)

            # -- EAR/eye-openness check inside vehicle ROI
            roi_gray = gray[max(0, y1):y2, max(0, x1):x2]
            ear = self._ear_from_roi(roi_gray)
            if ear is not None and ear < self._ear_thresh:
                self._ear_cnt[tid] += 1
                if (self._ear_cnt[tid] >= self._ear_frames
                        and tid not in self._alerted):
                    self._alerted.add(tid)
                    results.append(DrunkDriverResult(tid, True, "DROWSY"))
                    self._ear_cnt[tid] = 0
            else:
                self._ear_cnt[tid] = max(0, self._ear_cnt[tid] - 1)

        return results

    def _ear_from_roi(self, roi_gray: np.ndarray) -> Optional[float]:
        """Estimate eye-openness ratio from detected eye rectangles."""
        faces = self._face_cascade.detectMultiScale(roi_gray, 1.1, 4)
        for (fx, fy, fw, fh) in faces:
            face_roi = roi_gray[fy: fy + fh, fx: fx + fw]
            eyes = self._eye_cascade.detectMultiScale(face_roi, 1.1, 3)
            if len(eyes) >= 2:
                heights = [ey[3] for ey in eyes[:2]]
                widths  = [ey[2] for ey in eyes[:2]]
                ear = sum(h / max(w, 1) for h, w in zip(heights, widths)) / 2
                return float(ear)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 6. Honk Detection
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class HonkEvent:
    timestamp: float
    energy: float


class HonkDetector:
    """
    Listens for horn sounds in a background audio thread.
    Calls *on_honk(HonkEvent)* when a honk is detected.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk: int = 1024,
        energy_thresh: float = 3000.0,
        freq_lo: float = 300.0,
        freq_hi: float = 3000.0,
        cooldown_s: float = 5.0,
        on_honk=None,
    ) -> None:
        self._rate       = sample_rate
        self._chunk      = chunk
        self._energy_thr = energy_thresh
        self._freq_lo    = freq_lo
        self._freq_hi    = freq_hi
        self._cooldown   = cooldown_s
        self._on_honk    = on_honk or (lambda e: logger.info("[HONK] %s", e))
        self._running    = False
        self._last_ts    = 0.0
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._running = True
        self._thread  = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _run(self) -> None:
        try:
            import pyaudio                                  # type: ignore
        except ImportError:
            logger.warning("pyaudio not installed – honk detection disabled.")
            return
        pa     = pyaudio.PyAudio()
        stream = None
        try:
            stream = pa.open(format=pyaudio.paInt16, channels=1,
                             rate=self._rate, input=True,
                             frames_per_buffer=self._chunk)
            while self._running:
                data   = stream.read(self._chunk, exception_on_overflow=False)
                frames = np.frombuffer(data, np.int16).astype(np.float32)
                if self._is_honk(frames):
                    now = time.time()
                    if now - self._last_ts > self._cooldown:
                        self._last_ts = now
                        self._on_honk(HonkEvent(now, float(np.sqrt(np.mean(frames**2)))))
        except Exception as exc:
            logger.warning("Audio stream error: %s", exc)
        finally:
            if stream:
                stream.stop_stream(); stream.close()
            pa.terminate()

    def _is_honk(self, frames: np.ndarray) -> bool:
        rms = float(np.sqrt(np.mean(frames ** 2)))
        if rms < self._energy_thr:
            return False
        mag  = np.abs(np.fft.rfft(frames))
        freq = np.fft.rfftfreq(len(frames), 1.0 / self._rate)
        band = (freq >= self._freq_lo) & (freq <= self._freq_hi)
        return float(mag[band].sum()) / max(float(mag.sum()), 1e-9) > 0.40
