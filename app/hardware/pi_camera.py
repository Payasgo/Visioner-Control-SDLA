# app/hardware/pi_camera.py

import cv2

class PiCameraHandler:
    def __init__(self, cam_index=0):
        self.cam = cv2.VideoCapture(cam_index)

    def capture_frame(self):
        ret, frame = self.cam.read()
        if not ret:
            print("[PiCamera] Failed to capture frame.")
            return None
        return frame

    def release(self):
        self.cam.release()
