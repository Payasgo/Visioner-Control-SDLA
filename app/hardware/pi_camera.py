# app/hardware/pi_camera.py

import cv2


class CameraError(RuntimeError):
    """Raised when the camera cannot be opened or a frame cannot be captured."""


class PiCameraHandler:
    """Thin wrapper around an OpenCV camera capture."""

    def __init__(self, cam_index: int = 0) -> None:
        self.cam = cv2.VideoCapture(cam_index)
        if not self.cam.isOpened():
            raise CameraError(f"Failed to open camera at index {cam_index}.")

    def capture_frame(self):
        """Returns the next frame as a numpy array, or raises CameraError."""
        ret, frame = self.cam.read()
        if not ret:
            raise CameraError("[PiCamera] Failed to capture frame.")
        return frame

    def release(self) -> None:
        self.cam.release()

    def __enter__(self):
        return self

    def __exit__(self, *_) -> None:
        self.release()
