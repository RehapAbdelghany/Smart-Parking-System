import cv2
import torch
import numpy as np
import requests
from PIL import Image
from torchvision import transforms
import torchvision.models as models
from transformers import CLIPProcessor, CLIPModel
from ultralytics import YOLO

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
# 2. Interactive System
# ==============================================================
class InteractiveGateSystem:
    def __init__(self, camera_id, config_path="cameras_config.json"):
        # 1. تحميل الإعدادات من الملف
        with open(config_path, 'r') as f:
            full_config = json.load(f)
        
        self.camera_id = str(camera_id)
        config = full_config[self.camera_id]
        
        # 2. تعيين الإعدادات الخاصة بهذه الكاميرا فقط
        self.source = config['source']
        self.roi_points = config['roi']
        self.trigger_line = config['trigger']
        
        # باقي التعريفات (YOLO, Analyzer, etc.)
        self.analyzer = CarAnalyzer()
        self.yolo = YOLO("yolov8n.pt")
        self.window_name = f"Camera {self.camera_id} - {config['zone']}"
        self.tracked_ids = set()

    def send_to_backend(self, color, embedding):
    # تأكد أن الرابط هو api/tracking/ كما هو مسجل في الـ urls.py عندك
        url = "http://127.0.0.1:8000/api/tracking/"
    
        payload = {
        "car_embedding": embedding, # المصفوفة اللي جاية من ReID
        "camera_id": 1,             # تأكد أن رقم 1 موجود في جدول Camera في الداتابيز
        "car_color": color.lower()  # تحويل اللون لـ lowercase ليطابق الفلتر
        }
    
        try:
           response = requests.post(url, json=payload, timeout=2)
           if response.status_code == 200:
              data = response.json()
              print(f"✅ تم التعرف على السيارة: {data['identified_plate']}")
              print(f"📍 الموقع الحالي: {data['current_zone']}")
           elif response.status_code == 404:
              print("❌ لم يتم العثور على سيارة مطابقة في الجراج")
           else:
            print(f"⚠️ خطأ من السيرفر: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ فشل الاتصال: {e}")

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
                if type == 'roi': self.roi_points[idx] = [x, y]
                else: self.trigger_line[idx] = [x, y]
        elif event == cv2.EVENT_LBUTTONUP:
            if self.selected_point:
                print(f"\n--- Coordinates Updated: ROI={self.roi_points}, Trigger={self.trigger_line}")
            self.selected_point = None

    def run(self):
        cap = cv2.VideoCapture(self.source)
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            roi_np = np.array(self.roi_points, dtype=np.int32)
            results = self.yolo.track(frame, persist=True, verbose=False)
            
            if results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.int().cpu().tolist()
                ids = results[0].boxes.id.int().cpu().tolist()
                
                for box, track_id in zip(boxes, ids):
                    x1, y1, x2, y2 = box
                    cx, cy = (x1 + x2) // 2, y2

                    if cv2.pointPolygonTest(roi_np, (cx, cy), False) >= 0:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                        
                        # حساب المسافة من الخط (تعديل لتجنب NumPy Warning)
                        p1 = np.array(self.trigger_line[0])
                        p2 = np.array(self.trigger_line[1])
                        p3 = np.array([cx, cy])
                        
                        # معادلة المسافة بين نقطة وخط (2D)
                        dist = np.abs(np.cross(p2-p1, p1-p3)) / np.linalg.norm(p2-p1)
                        
                        if dist < 12 and track_id not in self.tracked_ids:
                            car_crop = frame[max(0,y1):y2, max(0,x1):x2]
                            if car_crop.size > 0:
                                color, emb = self.analyzer.get_analysis(car_crop)
                                print(f"📍 Trigger Hit! Analyzing Car ID: {track_id}")
                                # تفعيل الإرسال هنا
                                self.send_to_backend(color, emb)
                                self.tracked_ids.add(track_id)

            # الرسم
            cv2.polylines(frame, [roi_np], True, (0, 255, 0), 2)
            cv2.line(frame, tuple(self.trigger_line[0]), tuple(self.trigger_line[1]), (0, 0, 255), 3)
            
            cv2.imshow(self.window_name, frame)
            if cv2.waitKey(1) & 0xFF == 27: break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # تأكد أن السيرفر يعمل على هذا الرابط
    system = InteractiveGateSystem(source="D02.mp4") 
    system.run()