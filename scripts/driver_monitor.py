# scripts/driver_monitor.py
#
# Requires: pip install opencv-python dlib numpy
# Also requires shape_predictor_68_face_landmarks.dat from dlib.
#
# Download the predictor:
#   wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
#   bunzip2 shape_predictor_68_face_landmarks.dat.bz2

import logging
import os

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_PREDICTOR_PATH = os.environ.get(
    "DLIB_PREDICTOR_PATH", "shape_predictor_68_face_landmarks.dat"
)
_EAR_THRESHOLD = 0.22

# Lazy globals – initialised on first call to get_driver_state()
_detector = None
_predictor = None


def _load_models():
    """Load dlib models once; raise a clear error if files are missing."""
    global _detector, _predictor
    if _detector is not None:
        return

    try:
        import dlib  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "dlib is required for driver monitoring. "
            "Install it with: pip install dlib"
        ) from exc

    if not os.path.exists(_PREDICTOR_PATH):
        raise FileNotFoundError(
            f"dlib predictor file not found at '{_PREDICTOR_PATH}'. "
            "Set the DLIB_PREDICTOR_PATH environment variable or download the file."
        )

    _detector = dlib.get_frontal_face_detector()
    _predictor = dlib.shape_predictor(_PREDICTOR_PATH)


def _eye_aspect_ratio(eye: np.ndarray) -> float:
    a = np.linalg.norm(eye[1] - eye[5])
    b = np.linalg.norm(eye[2] - eye[4])
    c = np.linalg.norm(eye[0] - eye[3])
    return float((a + b) / (2.0 * c)) if c > 0 else 1.0


def get_driver_state(frame: np.ndarray) -> str:
    """
    Analyse *frame* and return 'Drowsy' or 'Attentive'.

    Models are loaded on the first call.
    """
    _load_models()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = _detector(gray)  # type: ignore[call-arg]

    for face in faces:
        landmarks = _predictor(gray, face)  # type: ignore[call-arg]
        points = np.array([[p.x, p.y] for p in landmarks.parts()])

        left_eye = points[36:42]
        right_eye = points[42:48]
        ear = (_eye_aspect_ratio(left_eye) + _eye_aspect_ratio(right_eye)) / 2.0

        if ear < _EAR_THRESHOLD:
            return "Drowsy"

    return "Attentive"
