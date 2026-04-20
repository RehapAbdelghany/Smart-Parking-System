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
        self.input_queue = Queue(maxsize=batch_size * 2)
        self.results = {}  # cam_id -> latest_result
        self.lock = threading.Lock()
        self.running = True
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

    def run(self):
        while self.running:
            items = []
            # 1. تجميع الـ Batch
            try:
                # انتظر أول فريم
                items.append(self.input_queue.get(timeout=0.1))
                # اسحب الباقي المتاح فوراً حتى اكتمال الـ Batch size
                while len(items) < self.batch_size:
                    try:
                        items.append(self.input_queue.get_nowait())
                    except Empty:
                        break
            except Empty:
                continue

            if items:
                cam_ids, frames = zip(*items)
                
                # 2. الاستنتاج الجماعي (Batch Inference)
                # يولو بيدعم إرسال قائمة صور ومعالجتها بالتوازي
                results = self.model.track(list(frames),tracker="bytetrack.yaml", persist=True, verbose=False) 

                # 3. توزيع النتائج بالـ Lock لضمان سلامة البيانات
                with self.lock:
                    for i, res in enumerate(results):
                        self.results[cam_ids[i]] = res

