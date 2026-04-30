import threading
import time
from queue import Queue, Empty
import numpy as np
from ultralytics import YOLO

class BatchInferenceEngine(threading.Thread):
    def __init__(self, model_path, batch_size=4, device="cuda"):
        super().__init__(daemon=True)
        self.model = YOLO(model_path)
        self.batch_size = batch_size
        self.device = device
        self.input_queues = {}   # per camera
        self.queue_lock = threading.Lock()
        self.results = {}
        self.lock = threading.Lock()
        self.running = True

    def _get_queue(self, cam_id):
        with self.queue_lock:
            if cam_id not in self.input_queues:
                self.input_queues[cam_id] = Queue(maxsize=self.batch_size * 2)
            return self.input_queues[cam_id]

    def submit_frame(self, cam_id, frame):
        q = self._get_queue(cam_id)
        if q.full():
            try: q.get_nowait()
            except Empty: pass
        q.put((cam_id, frame))

    def get_result(self, cam_id):
        with self.lock:
            return self.results.get(cam_id)

    def run(self):
        while self.running:
            items = []
            # Collect one frame from each camera
            with self.queue_lock:
                queues = list(self.input_queues.items())
            for cam_id, q in queues:
                try:
                    items.append(q.get_nowait())
                except Empty:
                    pass
            if not items:
                time.sleep(0.001)
                continue

            cam_ids, frames = zip(*items)
            results = self.model.track(
                list(frames),
                persist=True,
                device=self.device,
                tracker="bytetrack.yaml",
                verbose=False,
                conf=0.20,  # Lowered from 0.35 to catch cars earlier
                iou=0.5,  # Increased slightly to handle overlapping cars better
            )
            with self.lock:
                for i, res in enumerate(results):
                    self.results[cam_ids[i]] = res