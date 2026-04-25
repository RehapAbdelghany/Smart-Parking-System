import cv2
import torch
import numpy as np
import requests
from PIL import Image
from torchvision import transforms
import torchvision.models as models
from transformers import CLIPProcessor, CLIPModel
import json

# ==============================================================
# 1. Car Analyzer Class
# ==============================================================
class CarAnalyzer:
    def __init__(self, device='cuda' if torch.cuda.is_available() else 'cpu'):
        self.device = device
        self.reid_model = models.resnet50(weights='DEFAULT')
        self.reid_model.fc = torch.nn.Identity()
        self.reid_model.to(device).eval()
        
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        
        self.reid_transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        self.car_colors = ["a red car", "a blue car", "a black car", "a white car", "a silver car", "a gray car"]
        self.color_names = [c.replace("a ", "").replace(" car", "").title() for c in self.car_colors]

    def get_analysis(self, car_crop):
        img_rgb = cv2.cvtColor(car_crop, cv2.COLOR_BGR2RGB)
        inputs = self.clip_processor(text=self.car_colors, images=Image.fromarray(img_rgb), return_tensors="pt", padding=True).to(self.device)
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
# 2. Interactive Gate System Class
# ==============================================================
class InteractiveGateSystem:
    def __init__(self, camera_id, engine, analyzer, config_path="cameras_config.json"):
        self.config_path = config_path
        with open(config_path, 'r') as f:
            full_config = json.load(f)
        
        self.camera_id = str(camera_id)
        config = full_config[self.camera_id]
        
        self.source = config['source']
        self.roi_points = config['roi']
        self.trigger_line = config['trigger']
        
        self.analyzer = analyzer
        self.engine = engine
        
        self.window_name = f"Camera {self.camera_id} - {config.get('zone', 'Gate')}"
        self.tracked_ids = set()
        self.selected_point = None 

    def save_config(self):
        with open(self.config_path, 'r') as f:
            full_config = json.load(f)
        full_config[self.camera_id]['roi'] = self.roi_points
        full_config[self.camera_id]['trigger'] = self.trigger_line
        with open(self.config_path, 'w') as f:
            json.dump(full_config, f, indent=4)
        print(f"[SYSTEM] Config updated for camera {self.camera_id}")

    def send_to_backend(self, color, embedding):
        url = "http://127.0.0.1:8000/api/tracking/"
        payload = {"car_embedding": embedding, "camera_id": int(self.camera_id) + 1, "car_color": color.lower()}
        try:
            requests.post(url, json=payload, timeout=2)
        except Exception as e:
            print(f"❌ Error: {e}")

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            for i, p in enumerate(self.roi_points):
                if np.linalg.norm(np.array(p) - np.array([x, y])) < 25:
                    self.selected_point = ('roi', i)
                    return
            for i, p in enumerate(self.trigger_line):
                if np.linalg.norm(np.array(p) - np.array([x, y])) < 25:
                    self.selected_point = ('trigger', i)
                    return

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.selected_point:
                pt_type, idx = self.selected_point
                if pt_type == 'roi': self.roi_points[idx] = [x, y]
                elif pt_type == 'trigger': self.trigger_line[idx] = [x, y]

        elif event == cv2.EVENT_LBUTTONUP:
            if self.selected_point:
                self.save_config()
            self.selected_point = None

    def get_ui_frame(self):
        from camera_manager import get_shared_frame
        data = get_shared_frame(int(self.camera_id))
        if data is None: return None
        frame, _ = data
        frame_draw = frame.copy()
        roi_np = np.array(self.roi_points, dtype=np.int32)

        self.engine.submit_frame(int(self.camera_id), frame)
        results = self.engine.get_result(int(self.camera_id))

        if results and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.int().cpu().tolist()
            ids = results[0].boxes.id.int().cpu().tolist()
            for box, track_id in zip(boxes, ids):
                x1, y1, x2, y2 = box
                cx, cy = (x1 + x2) // 2, y2 
                if cv2.pointPolygonTest(roi_np, (cx, cy), False) >= 0:
                    p1, p2 = np.array(self.trigger_line[0]), np.array(self.trigger_line[1])
                    p3 = np.array([cx, cy])
                    dist = np.abs(np.cross(p2-p1, p1-p3)) / np.linalg.norm(p2-p1)
                    if dist < 12 and track_id not in self.tracked_ids:
                        car_crop = frame[max(0, y1):y2, max(0, x1):x2]
                        if car_crop.size > 0:
                            color, emb = self.analyzer.get_analysis(car_crop)
                            self.send_to_backend(color, emb)
                            self.tracked_ids.add(track_id)

        cv2.polylines(frame_draw, [roi_np], True, (0, 255, 0), 2)
        for p in self.roi_points:
            cv2.circle(frame_draw, (int(p[0]), int(p[1])), 8, (255, 255, 255), -1)
        cv2.line(frame_draw, tuple(self.trigger_line[0]), tuple(self.trigger_line[1]), (0, 0, 255), 3)
        for p in self.trigger_line:
            cv2.circle(frame_draw, (int(p[0]), int(p[1])), 8, (255, 255, 255), -1)
        return frame_draw