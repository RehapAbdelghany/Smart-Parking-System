import threading
import cv2
import time
from config import CAMERA_URLS, FRAME_WIDTH, FRAME_HEIGHT


class CameraManager:
    def __init__(self):
        # cam_id -> (frame, timestamp)
        self.frames = {}
        self.locks = {i: threading.Lock() for i in range(len(CAMERA_URLS))}
        self.running = True

    def start_all(self):
        for cam_id, source in enumerate(CAMERA_URLS):
            t = threading.Thread(
                target=self._reader,
                args=(cam_id, source),
                daemon=True
            )
            t.start()

        print(f"[SYSTEM] Camera Manager Active ({len(CAMERA_URLS)} cameras)")

    def _reader(self, cam_id, source):
        cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)

        if not cap.isOpened():
            print(f"[ERROR] Cannot open camera {cam_id}")

        while self.running:
            ret, frame = cap.read()   # ✅ FIX: use read()

            if not ret or frame is None:
                print(f"[RECONNECT] Cam {cam_id} lost... reconnecting")
                cap.release()
                time.sleep(1)

                cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                continue

            # Resize (optional but recommended)
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

            # ❗ Filter gray / corrupted frames
            if frame.mean() < 5:
                print(f"[WARNING] Cam {cam_id} gray frame skipped")
                continue

            # Save latest frame with timestamp
            with self.locks[cam_id]:
                self.frames[cam_id] = (frame, time.time())

            # Control FPS (IMPORTANT)
            time.sleep(0.03)  # ~30 FPS

    def get_frame(self, cam_id):
        lock = self.locks.get(cam_id)
        if lock:
            with lock:
                return self.frames.get(cam_id, None)
        return None


# ==============================================================
# GLOBAL SINGLETON
# ==============================================================

_cm_instance = None


def get_camera_manager():
    global _cm_instance
    if _cm_instance is None:
        _cm_instance = CameraManager()
        _cm_instance.start_all()
    return _cm_instance


def get_shared_frame(cam_id):
    global _cm_instance
    if _cm_instance is not None:
        return _cm_instance.get_frame(cam_id)
    return None