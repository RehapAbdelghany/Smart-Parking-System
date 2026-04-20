import cv2
import torch
import numpy as np
import requests
from PIL import Image
from torchvision import transforms
import torchvision.models as models
from transformers import CLIPProcessor, CLIPModel
from ultralytics import YOLO
import json
import time
import threading
from queue import Queue
from camera_manager import get_shared_frame


# ==============================================================
# 1. Car Analyzer Class (بقي كما هو تماماً)
# ==============================================================
class CarAnalyzer:
    def __init__(self, device='cuda' if torch.cuda.is_available() else 'cpu'):
        self.device = device
        self.reid_model = models.resnet50(weights=None)

        state_dict = torch.load("models/resnet50.pth", map_location=self.device)
        self.reid_model.load_state_dict(state_dict)
        self.reid_model.fc = torch.nn.Identity()
        self.reid_model.to(device).eval()
        
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        
        self.reid_transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])
        
        self.car_colors = [
            "a red car", "a blue car", "a black car",
            "a white car", "a silver car", "a gray car"
        ]
        self.color_names = [c.replace("a ", "").replace(" car", "").title()
                            for c in self.car_colors]

    def get_analysis(self, car_crop):
        img_rgb = cv2.cvtColor(car_crop, cv2.COLOR_BGR2RGB)

        inputs = self.clip_processor(
            text=self.car_colors,
            images=Image.fromarray(img_rgb),
            return_tensors="pt",
            padding=True
        ).to(self.device)

        with torch.no_grad():
            outputs = self.clip_model(**inputs)

        probs = outputs.logits_per_image.softmax(dim=1)[0]
        color = self.color_names[probs.argmax().item()]

        tensor = self.reid_transform(car_crop).unsqueeze(0).to(self.device)
        with torch.no_grad():
            feat = self.reid_model(tensor).cpu().numpy()[0]

        embedding = (feat / np.linalg.norm(feat)).tolist()
        return color, embedding


# ==============================================================
# 2. Interactive System (تحديث لاستخدام الـ Engine)
# ==============================================================
class InteractiveGateSystem:
    def __init__(self, camera_id, engine, analyzer, config_path="cameras_config.json"):
        # Load config
        with open(config_path, 'r') as f:
            full_config = json.load(f)
        
        self.camera_id = str(camera_id)
        config = full_config[self.camera_id]

        self.source = config['source']
        self.roi_points = config['roi']
        self.trigger_line = config['trigger']
        

        self.analyzer = analyzer
        self.engine = engine

        self.window_name = f"Camera {self.camera_id} - {config['zone']}"
        self.tracked_ids = set()
        self.selected_point = None

        self.latest_annotated_frame = None
        self.lock = threading.Lock()
        self.running = True

        self.trigger_queue = Queue(maxsize=20)
        self.initialized = False

        threading.Thread(target=self._trigger_worker, daemon=True).start()
        threading.Thread(target=self._inference_loop, daemon=True).start()

    def _trigger_worker(self):
        while self.running:
            try:
                car_crop, track_id = self.trigger_queue.get(timeout=1)
                color, embedding = self.analyzer.get_analysis(car_crop)
                
                print(f"🚀 Worker Processing ID: {track_id} | {color}")

                response = requests.post(
                    "http://127.0.0.1:8000/api/tracking/",
                    json={
                        "car_embedding": embedding,
                        "camera_id": int(self.camera_id),
                        "car_color": color.lower()
                    },
                    timeout=2
                )

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {data['identified_plate']} | {data['current_zone']}")
                else:
                    print(f"⚠️ Server error: {response.status_code}")

                self.trigger_queue.task_done()
            except:
                continue
            
    def get_ui_frame(self):
        with self.lock:
            if self.latest_annotated_frame is None:
                return None
            
            display_frame = self.latest_annotated_frame.copy()
            
            roi_np = np.array(self.roi_points, dtype=np.int32)
            cv2.polylines(display_frame, [roi_np], True, (0, 255, 0), 2)
            
            for p in self.roi_points:
                cv2.circle(display_frame, tuple(p), 6, (222, 222, 0), -1)

            # (مفيش تغيير هنا)
            return display_frame
        
    def _inference_loop(self):
        print(f"[GATE {self.camera_id}] Inference Loop Started")

        while self.running:
            # ✅ تحديث الـ ROI كل فريم
            roi_np = np.array(self.roi_points, dtype=np.int32)

            data = get_shared_frame(int(self.camera_id))

            if data is None:
                time.sleep(0.01)
                continue

            frame, ts = data
            
            # ✅ أول frame بس نعمل clamp
            if not self.initialized:
             h, w = frame.shape[:2]
             
             MARGIN = 20

             def clamp_point(p):
              return [
              max(MARGIN, min(p[0], w - 1 - MARGIN)),
              max(MARGIN, min(p[1], h - 1 - MARGIN))
             ]
             print("Trigger after clamp:", self.trigger_line)
             self.roi_points = [clamp_point(p) for p in self.roi_points]
             

             if len(self.trigger_line) >= 2:
              self.trigger_line = [
              clamp_point(self.trigger_line[0]),
              clamp_point(self.trigger_line[1])
            ]

             print("✅ ROI after clamp:", self.roi_points)
             print("✅ Trigger after clamp:", self.trigger_line)

            self.initialized = True

            if time.time() - ts > 0.5:
                continue

            processed = frame.copy()

            self.engine.submit_frame(self.camera_id, processed)
            
            res = None
            for _ in range(5):
                res = self.engine.get_result(self.camera_id)
                if res:
                    break
                time.sleep(0.01)

            if res is None:
                continue
            
            #هنا
            print("DEBUG -> Result received")

            if res.boxes is not None:
              print("DEBUG -> IDs:", res.boxes.id)
              print(f"DEBUG -> {len(res.boxes)} boxes")
              # ✅ ADD THIS BLOCK HERE (TEMP TEST)
              boxes = res.boxes.xyxy.int().cpu().tolist()
              
              for box in boxes[:1]:  # test first detection only
                x1, y1, x2, y2 = box
                crop = frame[max(0,y1):y2, max(0,x1):x2]

                if crop.size > 0:
                  color, embedding = self.analyzer.get_analysis(crop)
                  print("✅ EMBEDDING WORKS:", color, len(embedding))
            else:
              print("DEBUG -> No boxes detected")

            if res.boxes.id is not None:
                boxes = res.boxes.xyxy.int().cpu().tolist()
                ids = res.boxes.id.int().cpu().tolist()

                for box, track_id in zip(boxes, ids):
                    x1, y1, x2, y2 = box
                    cx, cy = (x1 + x2)//2, y2

                    if cv2.pointPolygonTest(roi_np, (cx, cy), False) >= 0:
                        cv2.rectangle(processed, (x1, y1), (x2, y2), (255, 0, 0), 2)

                        # ✅ trigger line dynamic
                        p1 = np.array(self.trigger_line[0])
                        p2 = np.array(self.trigger_line[1])

                        # ✅ حماية
                        if np.linalg.norm(p2 - p1) == 0:
                            continue

                        dist = abs(np.cross(p2 - p1, p1 - [cx, cy])) / np.linalg.norm(p2 - p1)

                        if dist < 12 and track_id not in self.tracked_ids:
                            crop = frame[max(0,y1):y2, max(0,x1):x2]

                            if crop.size > 0:
                                self.tracked_ids.add(track_id)
                                if not self.trigger_queue.full():
                                    self.trigger_queue.put((crop.copy(), track_id))

            cv2.polylines(processed, [roi_np], True, (0, 255, 0), 2)
            cv2.line(processed, tuple(self.trigger_line[0]), tuple(self.trigger_line[1]), (0, 0, 255), 3)

            with self.lock:
                self.latest_annotated_frame = processed

            time.sleep(0.01)
    
    def save_config(self):
        try:
            with open("cameras_config.json", 'r') as f:
                config_data = json.load(f)
            
            config_data[self.camera_id]['roi'] = self.roi_points
            config_data[self.camera_id]['trigger'] = self.trigger_line
            
            with open("cameras_config.json", 'w') as f:
                json.dump(config_data, f, indent=4)
            print(f"✅ [CONFIG] Camera {self.camera_id} settings saved to JSON.")
        except Exception as e:
            print(f"❌ [ERROR] Could not save config: {e}")
        
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            for i, p in enumerate(self.roi_points):
                if np.linalg.norm(np.array(p) - np.array([x, y])) < 15:
                    self.selected_point = ('roi', i)
                    return
            for i, p in enumerate(self.trigger_line):
                if np.linalg.norm(np.array(p) - np.array([x, y])) < 15:
                    self.selected_point = ('trigger', i)
                    return

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.selected_point:
                type, idx = self.selected_point
                if type == 'roi':
                    h, w = self.latest_annotated_frame.shape[:2] if self.latest_annotated_frame is not None else (720, 1280)
                    x = max(0, min(x, w - 1))
                    y = max(0, min(y, h - 1))
                    self.roi_points[idx] = [x, y]
                else:
                    h, w = self.latest_annotated_frame.shape[:2] if self.latest_annotated_frame is not None else (720, 1280)
                    x = max(0, min(x, w - 1))
                    y = max(0, min(y, h - 1))
                    self.trigger_line[idx] = [x, y]

        elif event == cv2.EVENT_LBUTTONUP:
            if self.selected_point:
                print(f"Updated: ROI={self.roi_points}, Trigger={self.trigger_line}")
            self.selected_point = None
            self.save_config()