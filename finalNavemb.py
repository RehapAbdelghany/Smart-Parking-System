import cv2
import torch
import numpy as np
import requests
from PIL import Image
from torchvision import transforms
import torchvision.models as models
from ultralytics import YOLO
import json
import threading
from multiprocessing import shared_memory
from config import FRAME_WIDTH, FRAME_HEIGHT

# ==============================================================
# 1. Car Analyzer (ResNet + CLIP)
# ==============================================================
class CarAnalyzer:
    def __init__(self, device='cuda' if torch.cuda.is_available() else 'cpu'):
        self.device = device
        
        # ResNet ReID Model
        self.reid_model = models.resnet50(weights=None)
        try:
            self.reid_model.load_state_dict(
                torch.load("models/resnet50.pth", map_location=device)
            )
        except Exception as e:
            print(f"⚠️ ReID model load failed: {e}. Using identity features.")
            
        self.reid_model.fc = torch.nn.Identity()
        self.reid_model.to(device).eval()

        self.reid_transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        self.clip_model = None
        self.clip_processor = None
        self.clip_loaded = False

        self.car_colors = ["a red car", "a blue car", "a black car", "a white car", "a silver car", "a gray car"]
        self.color_names = [c.replace("a ", "").replace(" car", "").title() for c in self.car_colors]

    def load_clip(self):
        if self.clip_loaded: return
        try:
            print("🚀 Loading CLIP Model...")
            from transformers import CLIPProcessor, CLIPModel
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_loaded = True
            print("✅ CLIP Ready!")
        except Exception as e:
            print(f"❌ CLIP failed: {e}")

    def get_analysis(self, car_crop):
        img_rgb = cv2.cvtColor(car_crop, cv2.COLOR_BGR2RGB)
        self.load_clip()

        color = "Unknown"
        if self.clip_loaded:
            try:
                inputs = self.clip_processor(text=self.car_colors, images=Image.fromarray(img_rgb), return_tensors="pt", padding=True).to(self.device)
                with torch.no_grad():
                    outputs = self.clip_model(**inputs)
                probs = outputs.logits_per_image.softmax(dim=1)[0]
                color = self.color_names[probs.argmax().item()]
            except:
                color = "Error"

        tensor = self.reid_transform(car_crop).unsqueeze(0).to(self.device)
        with torch.no_grad():
            feat = self.reid_model(tensor).cpu().numpy()[0]
        embedding = (feat / np.linalg.norm(feat)).tolist()

        return color, embedding

# ==============================================================
# 2. Gate System (Multiprocessing Shared Memory Consumer)
# ==============================================================
class InteractiveGateSystem:
    def __init__(self, camera_id, yolo_model, analyzer, config_path="cameras_config.json"):
        with open(config_path, 'r') as f:
            full_config = json.load(f)

        self.camera_id = int(camera_id)
        config = full_config[str(self.camera_id)]

        self.roi_points = config['roi']
        self.trigger_line = config['trigger']
        self.zone_name = config['zone']

        self.analyzer = analyzer
        self.yolo = yolo_model 

        self.tracked_ids = set()
        self.selected_point = None

        # --- ATTACH TO SHARED MEMORY ---
        # The main process must have created 'parking_cam_X' already
        shm_name = f"parking_cam_{self.camera_id}"
        try:
            self.shm = shared_memory.SharedMemory(name=shm_name)
            expected_shape = (FRAME_HEIGHT, FRAME_WIDTH, 3)
            self.shared_frame = np.ndarray(expected_shape, dtype=np.uint8, buffer=self.shm.buf)
            print(f"✅ Gate {self.camera_id} attached to Shared Memory.")
        except FileNotFoundError:
            print(f"❌ Error: Shared memory '{shm_name}' not found. Run the main process first!")
            self.shared_frame = None

    def process_trigger(self, car_crop, track_id):
        try:
            color, embedding = self.analyzer.get_analysis(car_crop)
            print(f"📍 [CAM {self.camera_id}] Trigger! ID: {track_id} | Color: {color}")
            
            url = "http://127.0.0.1:8000/api/tracking/"
            payload = {
                "car_embedding": embedding,
                "camera_id": self.camera_id,
                "car_color": color.lower()
            }
            requests.post(url, json=payload, timeout=2)
        except Exception as e:
            print(f"❌ Analysis Thread Error: {e}")

    def update(self):
        if self.shared_frame is None: return None

        # 1. Access latest pixels directly from RAM
        # Use .copy() so our drawings don't affect other processes reading the same RAM
        frame = self.shared_frame.copy()
        roi_np = np.array(self.roi_points, dtype=np.int32)

        # 2. Shared Tracking
        results = self.yolo.track(frame, persist=True, verbose=False)

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.int().cpu().tolist()
            ids = results[0].boxes.id.int().cpu().tolist()

            for box, track_id in zip(boxes, ids):
                x1, y1, x2, y2 = box
                cx, cy = (x1 + x2) // 2, y2

                if cv2.pointPolygonTest(roi_np, (cx, cy), False) >= 0:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

                    # Trigger Line Detection
                    p1, p2 = np.array(self.trigger_line[0]), np.array(self.trigger_line[1])
                    p3 = np.array([cx, cy])
                    dist = np.abs(np.cross(p2 - p1, p1 - p3)) / np.linalg.norm(p2 - p1)

                    if dist < 15 and track_id not in self.tracked_ids:
                        car_crop = frame[max(0, y1):y2, max(0, x1):x2]
                        if car_crop.size > 0:
                            self.tracked_ids.add(track_id)
                            threading.Thread(
                                target=self.process_trigger, 
                                args=(car_crop.copy(), track_id), 
                                daemon=True
                            ).start()

        # UI Overlays
        cv2.polylines(frame, [roi_np], True, (0, 255, 0), 2)
        cv2.line(frame, tuple(self.trigger_line[0]), tuple(self.trigger_line[1]), (0, 0, 255), 3)
        cv2.putText(frame, f"Zone: {self.zone_name}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        return frame

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            for i, p in enumerate(self.roi_points):
                if np.linalg.norm(np.array(p) - np.array([x, y])) < 15:
                    self.selected_point = ('roi', i); return
            for i, p in enumerate(self.trigger_line):
                if np.linalg.norm(np.array(p) - np.array([x, y])) < 15:
                    self.selected_point = ('trigger', i); return
        elif event == cv2.EVENT_MOUSEMOVE and self.selected_point:
            t, idx = self.selected_point
            if t == 'roi': self.roi_points[idx] = [x, y]
            else: self.trigger_line[idx] = [x, y]
        elif event == cv2.EVENT_LBUTTONUP:
            self.selected_point = None

    def __del__(self):
        # Cleanup connection to shared memory
        if hasattr(self, 'shm'):
            self.shm.close()