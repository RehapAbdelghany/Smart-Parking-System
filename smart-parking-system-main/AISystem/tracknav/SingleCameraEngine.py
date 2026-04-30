import threading
from queue import Empty, Queue

from ultralytics import YOLO


class SingleCameraEngine(threading.Thread):
    def __init__(self, cam_id, model_path, device="cuda"):
        super().__init__(daemon=True)
        self.cam_id = cam_id
        self.model = YOLO(model_path)
        self.device = device

        self.queue = Queue(maxsize=5)
        self.result = None
        self.lock = threading.Lock()
        self.running = True

    def submit_frame(self, frame):
        if self.queue.full():
            try:
                self.queue.get_nowait()  # drop oldest
            except Empty:
                pass
        self.queue.put(frame)

    def get_result(self):
        with self.lock:
            return self.result

    def run(self):
        while self.running:
            try:
                frame = self.queue.get(timeout=0.01)
            except Empty:
                continue

            result = self.model.track(
                frame,
                persist=True,
                device=self.device,
                tracker="bytetrack.yaml",
                conf=0.25,
                iou=0.6,
                verbose=False
            )

            with self.lock:
                self.result = result