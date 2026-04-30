import json

import cv2
import torch
import numpy as np
from PIL import Image
from torchvision import transforms
from collections import defaultdict
import threading

from AISystem.APIClient import APIClient
from AISystem.model_registry import ModelRegistry
from AISystem.tracknav.camera_manager import get_shared_frame
from AISystem.tracknav.inference_engine import BatchInferenceEngine


class VehicleTracker:
    MOVE_THRESHOLD = 5
    MIN_HISTORY = 2
    STATIONARY_FRAMES_REQUIRED = 90
    STATIONARY_THRESHOLD = 5
    MAX_EMBEDDINGS_PER_TRACK = 10
    MAX_DISAPPEARED = 50

    def __init__(self,  engine, camera_id, config_path="cameras_config.json"):
        self.config_path = config_path
        self.camera_id = str(camera_id)
        with open(config_path, 'r') as f:
            full_config = json.load(f)
        config = full_config[self.camera_id]
        # self.camera_id = int(camera_id)
        self.roi_points = np.array(config['roi'], dtype=np.int32)
        self.original_height = 0
        self.original_width =0
        self.MAX_DISAPPEARED = 30
        self.disappeared_count = defaultdict(int)

        # self.video_path = config['source']
        # self.cap = cv2.VideoCapture(self.video_path)
        self.engine = engine

        self.window_name = f"Tracking - {self.camera_id}"

        # Models provided by ModelRegistry
        ModelRegistry.initialize()
        self.device = ModelRegistry.device
        self.reid_model = ModelRegistry.reid_model
        self.clip_model = ModelRegistry.clip_model
        self.clip_processor = ModelRegistry.clip_processor

        # Vehicle classes from YOLO (2: car, 3: motorcycle, 5: bus, 7: truck)
        self.vehicle_classes = [2, 3, 5, 7]

        self.car_colors = [
            "a black car", "a white car", "a silver car", "a gray car",
            "a red car", "a blue car", "a green car", "a beige car",
            "a gold car", "a bronze car", "a brown car", "a sand colored car",
            "a cream colored car", "an orange car", "a yellow car",
            "a purple car", "a pink car", "a turquoise car"
        ]

        self.color_names = [c.replace("a ", "").replace("an ", "").replace(" car", "").title()
                            for c in self.car_colors]



        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((256, 128)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])

        # State Tracking
        self.track_history = defaultdict(list)
        self.track_embeddings = defaultdict(list)
        self.track_colors = {}
        self.stationary_counter = defaultdict(int)
        self.finalized_ids = set()
        self.prev_active_ids = set()
        self.frame_count = 0

        self.api = APIClient("http://127.0.0.1:8000/api/tracking/")

        # UI State
        self._selected_point = None

        # ── Interactive ROI ───────────────────────────────────────────────

    def _mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            for i, p in enumerate(self.roi_points):
                if np.linalg.norm(np.array(p, dtype=float) - np.array([x, y], dtype=float)) < 25:
                    self._selected_point = i
                    return
        elif event == cv2.EVENT_MOUSEMOVE:
            if self._selected_point is not None:
                self.roi_points[self._selected_point] = [x, y]
        elif event == cv2.EVENT_LBUTTONUP:
            if self._selected_point is not None:
                self._selected_point = None
                self._save_roi()

    def _save_roi(self):
        import json
        config_path = "cameras_config.json"
        try:
            with open(config_path, 'r') as f:
                full_config = json.load(f)
            full_config[self.camera_id]['roi'] = self.roi_points.tolist()
            with open(config_path, 'w') as f:
                json.dump(full_config, f, indent=4)
            print(f"[Tracker {self.camera_id}] ROI saved.")
        except Exception as e:
            print(f"[Tracker {self.camera_id}] Could not save ROI: {e}")

    # ── Logic Helpers ──────────────────────────────────────────────────

    def create_roi_mask(self, frame):
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [self.roi_points], 255)
        return mask

    def is_good_crop(self, x1, y1, x2, y2) -> bool:
        return (x2 - x1) * (y2 - y1) > 5000

    def has_moved_since_entry(self, track_id: int) -> bool:
        points = self.track_history[track_id]
        if len(points) < self.MIN_HISTORY:
            return False
        dist = np.linalg.norm(np.array(points[-1]) - np.array(points[0]))
        return dist > self.MOVE_THRESHOLD

    def is_currently_stationary(self, track_id: int) -> bool:
        points = self.track_history[track_id]
        if len(points) < 3:
            return False
        dist = np.linalg.norm(np.array(points[-1]) - np.array(points[-3]))
        return dist < self.STATIONARY_THRESHOLD

    def getColor(self, car_crop) -> str:
        img_rgb = cv2.cvtColor(car_crop, cv2.COLOR_BGR2RGB)
        inputs = self.clip_processor(
            text=self.car_colors,
            images=Image.fromarray(img_rgb),
            return_tensors="pt",
            padding=True,
        ).to(self.device)
        with torch.no_grad():
            outputs = self.clip_model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)[0]
        return self.color_names[probs.argmax().item()]

    def get_embedding(self, img) -> np.ndarray:
        if isinstance(img, np.ndarray):
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        tensor = self.transform(img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            features = self.reid_model.featuremaps(tensor)
            features = torch.nn.functional.adaptive_avg_pool2d(features, 1)
            features = features.view(features.size(0), -1)
        emb = features.cpu().numpy().flatten()
        return emb / (np.linalg.norm(emb) + 1e-6)

    def _finalize_track(self, track_id: int):
        if track_id in self.finalized_ids:
            return
        embs = self.track_embeddings.get(track_id)
        if not embs:
            return
        self.finalized_ids.add(track_id)
        print(len(embs))
        avg_emb = np.array(embs).mean(axis=0)
        avg_emb /= (np.linalg.norm(avg_emb) + 1e-6)
        color = self.track_colors.get(track_id, "unknown")
        print(f"[Tracker {self.camera_id}] Finalized ID {track_id} | Color: {color}")
        self.api.send_tracking_embeddings(color, avg_emb.tolist(), self.camera_id)

    def is_good_crop(self, x1, y1, x2, y2) -> bool:
        return (x2 - x1) * (y2 - y1) > 2000

    # def is_inside_roi(self, x1, y1, x2, y2):
    #     cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    #     bottom_center = ((x1 + x2) // 2, y2)
    #     return any(cv2.pointPolygonTest(self.roi_points, (float(px), float(py)), False) >= 0
    #                for px, py in [(cx, cy), bottom_center])
    def is_inside_roi(self, x1, y1, x2, y2):
        # نفحص الأركان الأربعة + المركز
        points_to_check = [
            ((x1 + x2) // 2, y2),  # منتصف القاعدة (الأهم)
            (x1, y1), (x2, y1), (x1, y2), (x2, y2),  # الأركان
            ((x1 + x2) // 2, (y1 + y2) // 2)  # المركز
        ]
        for p in points_to_check:
            if cv2.pointPolygonTest(self.roi_points, (float(p[0]), float(p[1])), False) >= 0:
                return True
        return False


    # def process_frame(self,frame):
    #     # data = get_shared_frame(int(self.camera_id))
    #     if frame is None:
    #         # Return a placeholder instead of None so grid still shows
    #         placeholder = np.zeros((300, 500, 3), dtype=np.uint8)
    #         cv2.putText(placeholder, f"Camera {self.camera_id} - Waiting...",
    #                     (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
    #         return placeholder
    #     # frame, timestamp = data
    #     # frame = frame.copy()
    #
    #     self.frame_count += 1
    #
    #     # تقليل الحمل
    #
    #
    #     # 1. Send frame to inference engine
    #     self.original_height, self.original_width = frame.shape[:2]
    #     self.engine.submit_frame(frame)
    #
    #     # 2. Get detection results
    #     # if self.frame_count % 2 != 0:
    #     #     return frame
    #     results = self.engine.get_result()
    #
    #     current_active_ids = set()
    #
    #     if results is not None:
    #         results = results[0]
    #         if results.boxes is not None:
    #             for box in results.boxes:
    #                 cls = int(box.cls[0])
    #                 if cls not in self.vehicle_classes:
    #                     continue
    #
    #                 track_id = int(box.id[0]) if box.id is not None else -1
    #                 if track_id == -1 or track_id in self.finalized_ids:
    #                     continue
    #
    #                 x1, y1, x2, y2 = map(int, box.xyxy[0])
    #                 cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    #
    #                 # ROI check
    #                 if not self.is_inside_roi(x1, y1, x2, y2):
    #                     continue
    #
    #                 current_active_ids.add(track_id)
    #                 self.track_history[track_id].append((cx, cy))
    #
    #                 # ================= LOGIC =================
    #                 enough_history = len(self.track_history[track_id]) >= self.MIN_HISTORY
    #                 under_cap = len(self.track_embeddings[track_id]) < self.MAX_EMBEDDINGS_PER_TRACK
    #                 moved = self.has_moved_since_entry(track_id)
    #                 currently_stat = self.is_currently_stationary(track_id)
    #
    #                 pad = 10
    #                 x1p, y1p = max(0, x1 - pad), max(0, y1 - pad)
    #                 x2p, y2p = min(frame.shape[1], x2 + pad), min(frame.shape[0], y2 + pad)
    #                 good_crop = self.is_good_crop(x1p, y1p, x2p, y2p)
    #
    #                 # Collect embeddings
    #                 if (enough_history and not currently_stat and moved
    #                         and under_cap and good_crop and self.frame_count % 2 == 0):
    #
    #                     crop = frame[y1p:y2p, x1p:x2p]
    #                     self.track_embeddings[track_id].append(self.get_embedding(crop))
    #
    #                     if track_id not in self.track_colors:
    #                         self.track_colors[track_id] = self.getColor(crop)
    #
    #                 # Stationary logic
    #                 if moved and currently_stat:
    #                     self.stationary_counter[track_id] += 1
    #                 else:
    #                     self.stationary_counter[track_id] = 0
    #
    #                 if (self.stationary_counter[track_id] >= self.STATIONARY_FRAMES_REQUIRED
    #                         and self.track_embeddings[track_id]):
    #                     self._finalize_track(track_id)
    #                     current_active_ids.discard(track_id)
    #
    #                 # ================= DRAW =================
    #                 status = "STOPPED" if self.stationary_counter[track_id] >= self.STATIONARY_FRAMES_REQUIRED \
    #                     else f"emb:{len(self.track_embeddings[track_id])}"
    #
    #                 cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    #                 cv2.putText(frame, f"ID:{track_id} {status}",
    #                             (x1, y1 - 10),
    #                             cv2.FONT_HERSHEY_SIMPLEX, 0.7,
    #                             (0, 255, 0), 2)
    #
    #
    #
    #     # ================= FALLBACK =================
    #     disappeared = self.prev_active_ids - current_active_ids
    #     for tid in disappeared:
    #         self.disappeared_count[tid] += 1
    #         if self.disappeared_count[tid] >= self.MAX_DISAPPEARED:
    #             if tid not in self.finalized_ids and self.track_embeddings.get(tid):
    #                 self._finalize_track(tid)
    #                 # متبعتش الـ ID ده تاني خلاص
    #                 self.finalized_ids.add(tid)
    #     for tid in current_active_ids:
    #         self.disappeared_count[tid] = 0
    #
    #     self.prev_active_ids = current_active_ids
    #
    #     # ================= ROI DRAW =================
    #     cv2.polylines(frame, [self.roi_points], True, (255, 0, 0), 3)
    #     for p in self.roi_points:
    #         cv2.circle(frame, (int(p[0]), int(p[1])), 8, (255, 255, 255), -1)
    #         cv2.circle(frame, (int(p[0]), int(p[1])), 8, (255, 0, 0), 2)
    #
    #     return frame
    def process_frame(self, frame):
        if frame is None:
            return None

        self.frame_count += 1
        self.engine.submit_frame(frame)
        results = self.engine.get_result()

        current_active_ids = set()

        if results is not None and len(results) > 0:
            boxes = results[0].boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0])
                    if cls not in self.vehicle_classes:
                        continue

                    track_id = int(box.id[0]) if box.id is not None else -1
                    if track_id == -1 or track_id in self.finalized_ids:
                        continue

                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    if not self.is_inside_roi(x1, y1, x2, y2):
                        continue

                    # السيارة موجودة ونشطة
                    current_active_ids.add(track_id)
                    self.disappeared_count[track_id] = 0  # صفر عداد الاختفاء

                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    self.track_history[track_id].append((cx, cy))

                    # --- منطق جمع الـ Embeddings ---
                    under_cap = len(self.track_embeddings[track_id]) < self.MAX_EMBEDDINGS_PER_TRACK

                    if under_cap and self.frame_count % 2 == 0:
                        pad = 5
                        x1p, y1p = max(0, x1 - pad), max(0, y1 - pad)
                        x2p, y2p = min(frame.shape[1], x2 + pad), min(frame.shape[0], y2 + pad)

                        if (x2p - x1p) * (y2p - y1p) > 2000:
                            crop = frame[y1p:y2p, x1p:x2p]
                            self.track_embeddings[track_id].append(self.get_embedding(crop))
                            if track_id not in self.track_colors:
                                self.track_colors[track_id] = self.getColor(crop)

                    # --- تحديث حالة الثبات ---
                    if self.is_currently_stationary(track_id):
                        self.stationary_counter[track_id] += 1
                    else:
                        self.stationary_counter[track_id] = 0

                    # رسم توضيحي
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"ID:{track_id} Embs:{len(self.track_embeddings[track_id])}",
                                (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # --- منطق الـ Finalization (الأهم لمنع التكرار) ---
        # الـ IDs اللي كانت موجودة واختفت في الفريم ده
        lost_ids = self.prev_active_ids - current_active_ids
        for tid in lost_ids:
            self.disappeared_count[tid] += 1
            # لا ننهي التتبع إلا إذا اختفت السيارة لفترة طويلة (مثلاً ثانية ونصف)
            if self.disappeared_count[tid] >= self.MAX_DISAPPEARED:
                if tid not in self.finalized_ids:
                    self._finalize_track(tid)

        self.prev_active_ids = current_active_ids

        cv2.polylines(frame, [self.roi_points], True, (255, 0, 0), 3)

        for i, p in enumerate(self.roi_points):
            # لون مختلف لو النقطة هي اللي متحدة حالياً (اختياري)
            color = (0, 0, 255) if i == self._selected_point else (255, 0, 0)

            cv2.circle(frame, (int(p[0]), int(p[1])), 8, (255, 255, 255), -1)  # خلفية بيضاء
            cv2.circle(frame, (int(p[0]), int(p[1])), 8, color, 2)  # إطار ملون
        return frame



    def mouse_callback(self, event, x, y, flags, param):
        self._mouse_callback(event, x, y, flags, param)

    def post_process(self):
        print(f"\n=== Summary for {self.camera_id} ===")
        for track_id, embs in self.track_embeddings.items():
            if embs:
                print(f"  Track {track_id}: {len(embs)} embeddings | finalized={track_id in self.finalized_ids}")

