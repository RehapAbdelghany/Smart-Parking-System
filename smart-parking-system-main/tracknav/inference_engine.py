import threading
import time
from queue import Queue, Empty
import numpy as np
from ultralytics import YOLO

class BatchInferenceEngine(threading.Thread):
    def __init__(self, model_path, batch_size=6, device="cuda"):
        super().__init__(daemon=True)
        self.model = YOLO(model_path).to(device)
        self.batch_size = batch_size
        self.device = device
        self.input_queue = Queue(maxsize=batch_size * 2)
        self.results = {}
        self.lock = threading.Lock()
        self.running = True

        # ✅ FPS control
        self.last_infer_time = 0
        self.infer_interval = 0.2  # = 5 FPS
        
        print(f"[ENGINE] Batch Engine started for {model_path} (Batch Size: {batch_size})")

    def submit_frame(self, cam_id, frame):
        """تستخدمها الكاميرا لإرسال الفريم للمحرك"""
        try:
            # لو الطابور مليان، بنشيل القديم عشان نضمن Real-time
            if self.input_queue.full():
                self.input_queue.get_nowait()
            self.input_queue.put_nowait((cam_id, frame))
        except:
            pass

    def get_result(self, cam_id):
        """تستخدمها الكاميرا لسحب النتيجة الخاصة بها"""
        with self.lock:
            return self.results.get(cam_id, None)
    
    # inference_engine.py
    def run(self):
     while self.running:
        if time.time() - self.last_infer_time < self.infer_interval:
            time.sleep(0.005)
            continue

        items = []
        # سحب الفريمات الموجودة في الـ Queue حالياً
        try:
            while len(items) < self.batch_size:
                items.append(self.input_queue.get_nowait())
        except Empty:
            if not items:
                time.sleep(0.01)
                continue

        cam_ids, frames = zip(*items)
        
        # ✅ عمل Detection فقط (بدون track) لسرعة الـ Batch
        # في ملف inference_engine.py
        results = self.model.track(frames, persist=True, device=self.device, verbose=False)

        with self.lock:
            for i, res in enumerate(results):
                # نضع النتيجة الخام في الـ dictionary ليراها الـ Tracker الخاص بكل كاميرا
                self.results[cam_ids[i]] = res
        
        self.last_infer_time = time.time()