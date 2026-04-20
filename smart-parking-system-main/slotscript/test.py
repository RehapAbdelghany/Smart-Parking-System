# import cv2
# import torch
# import numpy as np
# import requests
# from PIL import Image
# from torchvision import transforms
# import torchvision.models as models
# from transformers import CLIPProcessor, CLIPModel
# from ultralytics import YOLO
# import json
# import time
# import threading
# from queue import Queue   # ✅ NEW
# from camera_manager import get_shared_frame


# # ==============================================================
# # 1. Car Analyzer Class
# # ==============================================================
# class CarAnalyzer:
#     def __init__(self, device='cuda' if torch.cuda.is_available() else 'cpu'):
#         self.device = device
#         self.reid_model = models.resnet50(weights=None)  # no pretrained download

#         state_dict = torch.load("models/resnet50.pth", map_location=self.device)
#         self.reid_model.load_state_dict(state_dict)
#         self.reid_model.fc = torch.nn.Identity()
#         self.reid_model.to(device).eval()
        
#         self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
#         self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        
#         self.reid_transform = transforms.Compose([
#             transforms.ToPILImage(),
#             transforms.Resize((224, 224)),
#             transforms.ToTensor(),
#             transforms.Normalize(mean=[0.485, 0.456, 0.406],
#                                  std=[0.229, 0.224, 0.225])
#         ])
        
#         self.car_colors = [
#             "a red car", "a blue car", "a black car",
#             "a white car", "a silver car", "a gray car"
#         ]
#         self.color_names = [c.replace("a ", "").replace(" car", "").title()
#                             for c in self.car_colors]

#     def get_analysis(self, car_crop):
#         img_rgb = cv2.cvtColor(car_crop, cv2.COLOR_BGR2RGB)

#         inputs = self.clip_processor(
#             text=self.car_colors,
#             images=Image.fromarray(img_rgb),
#             return_tensors="pt",
#             padding=True
#         ).to(self.device)

#         with torch.no_grad():
#             outputs = self.clip_model(**inputs)

#         probs = outputs.logits_per_image.softmax(dim=1)[0]
#         color = self.color_names[probs.argmax().item()]

#         tensor = self.reid_transform(car_crop).unsqueeze(0).to(self.device)
#         with torch.no_grad():
#             feat = self.reid_model(tensor).cpu().numpy()[0]

#         embedding = (feat / np.linalg.norm(feat)).tolist()
#         return color, embedding


# # ==============================================================
# # 2. Interactive System
# # ==============================================================
# class InteractiveGateSystem:
#     def __init__(self, camera_id, engine, analyzer , config_path="cameras_config.json"):
#         # Load config
#         with open(config_path, 'r') as f:
#             full_config = json.load(f)
        
        
#         self.camera_id = str(camera_id)
#         config = full_config[self.camera_id]

#         self.source = config['source']
#         self.roi_points = config['roi']
#         self.trigger_line = config['trigger']

#         self.analyzer = analyzer
#         self.engine = engine  # المحرك المشترك

#         self.window_name = f"Camera {self.camera_id} - {config['zone']}"
#         self.tracked_ids = set()
#         self.selected_point = None

#         # Thread-safe frame
#         self.latest_annotated_frame = None
#         self.lock = threading.Lock()
#         self.running = True

#         # ✅ Queue for multithreading
#         self.trigger_queue = Queue(maxsize=20)

#         # ✅ Start worker thread
#         threading.Thread(target=self._trigger_worker, daemon=True).start()
#         threading.Thread(target=self._inference_loop, daemon=True).start()

#     # ==========================================================
#     # Worker Thread
#     # ==========================================================
#     def _trigger_worker(self):
#         while True:
#             car_crop, track_id = self.trigger_queue.get()

#             try:
#                 color, embedding = self.analyzer.get_analysis(car_crop)

#                 print(f"🚀 Worker Processing ID: {track_id} | {color}")

#                 response = requests.post(
#                     "http://127.0.0.1:8000/api/tracking/",
#                     json={
#                         "car_embedding": embedding,
#                         "camera_id": int(self.camera_id),
#                         "car_color": color.lower()
#                     },
#                     timeout=2
#                 )

#                 if response.status_code == 200:
#                     data = response.json()
#                     print(f"✅ {data['identified_plate']} | {data['current_zone']}")
#                 elif response.status_code == 404:
#                     print("❌ No match found")
#                 else:
#                     print(f"⚠️ Server error: {response.status_code}")

#             except Exception as e:
#                 print(f"❌ Worker error: {e}")

#             self.trigger_queue.task_done()
            
            
#     def get_ui_frame(self):
#        with self.lock:
#           return self.latest_annotated_frame
        
#     def _inference_loop(self):
#       print(f"[GATE {self.camera_id}] Started")

#       roi_np = np.array(self.roi_points, dtype=np.int32)

#       while self.running:
#         data = get_shared_frame(int(self.camera_id))

#         if data is None:
#             time.sleep(0.01)
#             continue

#         frame, ts = data

#         if time.time() - ts > 0.5:
#             continue

#         processed = frame.copy()

#         results = self.yolo.track(
#             processed,
#             persist=True,
#             verbose=False,
#             half=False
#         )

#         if results[0].boxes.id is not None:
#             boxes = results[0].boxes.xyxy.int().cpu().tolist()
#             ids = results[0].boxes.id.int().cpu().tolist()

#             for box, track_id in zip(boxes, ids):
#                 x1, y1, x2, y2 = box
#                 cx, cy = (x1 + x2)//2, y2

#                 if cv2.pointPolygonTest(roi_np, (cx, cy), False) >= 0:
#                     cv2.rectangle(processed, (x1, y1), (x2, y2),
#                                   (255, 0, 0), 2)

#                     p1, p2 = np.array(self.trigger_line)
#                     dist = abs(np.cross(p2 - p1, p1 - [cx, cy])) / np.linalg.norm(p2 - p1)

#                     if dist < 12 and track_id not in self.tracked_ids:
#                         crop = frame[y1:y2, x1:x2]

#                         if crop.size > 0:
#                             self.tracked_ids.add(track_id)

#                             if not self.trigger_queue.full():
#                                 self.trigger_queue.put((crop.copy(), track_id))

#         # ✅ IMPORTANT: update UI frame
#         with self.lock:
#             self.latest_annotated_frame = processed

#         time.sleep(0.03)
        
#     # ==========================================================
#     # Mouse Interaction
#     # ==========================================================
#     def mouse_callback(self, event, x, y, flags, param):
#         if event == cv2.EVENT_LBUTTONDOWN:
#             for i, p in enumerate(self.roi_points):
#                 if np.linalg.norm(np.array(p) - np.array([x, y])) < 15:
#                     self.selected_point = ('roi', i)
#                     return
#             for i, p in enumerate(self.trigger_line):
#                 if np.linalg.norm(np.array(p) - np.array([x, y])) < 15:
#                     self.selected_point = ('trigger', i)
#                     return

#         elif event == cv2.EVENT_MOUSEMOVE:
#             if self.selected_point:
#                 type, idx = self.selected_point
#                 if type == 'roi':
#                     self.roi_points[idx] = [x, y]
#                 else:
#                     self.trigger_line[idx] = [x, y]

#         elif event == cv2.EVENT_LBUTTONUP:
#             if self.selected_point:
#                 print(f"\n--- Coordinates Updated: ROI={self.roi_points}, Trigger={self.trigger_line}")
#             self.selected_point = None

#     # ==========================================================
#     # Main Loop (NON-BLOCKING NOW)
#     # ==========================================================
#     def run(self):
#         cap = cv2.VideoCapture(self.source)
#         cv2.namedWindow(self.window_name)
#         cv2.setMouseCallback(self.window_name, self.mouse_callback)

#         while cap.isOpened():
#             ret, frame = cap.read()
#             if not ret:
#                 break

#             roi_np = np.array(self.roi_points, dtype=np.int32)
#             results = self.yolo.track(frame, persist=True, verbose=False , half=False)

#             if results[0].boxes.id is not None:
#                 boxes = results[0].boxes.xyxy.int().cpu().tolist()
#                 ids = results[0].boxes.id.int().cpu().tolist()

#                 for box, track_id in zip(boxes, ids):
#                     x1, y1, x2, y2 = box
#                     cx, cy = (x1 + x2) // 2, y2

#                     if cv2.pointPolygonTest(roi_np, (cx, cy), False) >= 0:
#                         cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

#                         p1 = np.array(self.trigger_line[0])
#                         p2 = np.array(self.trigger_line[1])
#                         p3 = np.array([cx, cy])

#                         dist = np.abs(np.cross(p2 - p1, p1 - p3)) / np.linalg.norm(p2 - p1)

#                         if dist < 12 and track_id not in self.tracked_ids:
#                             car_crop = frame[max(0, y1):y2, max(0, x1):x2]

#                             if car_crop.size > 0:
#                                 print(f"📍 Trigger Hit! Queued ID: {track_id}")
#                                 self.tracked_ids.add(track_id)

#                                 if not self.trigger_queue.full():
#                                     self.trigger_queue.put((car_crop.copy(), track_id))

#             # Draw UI
#             cv2.polylines(frame, [roi_np], True, (0, 255, 0), 2)
#             cv2.line(frame,
#                      tuple(self.trigger_line[0]),
#                      tuple(self.trigger_line[1]),
#                      (0, 0, 255), 3)

#             cv2.imshow(self.window_name, frame)
#             if cv2.waitKey(1) & 0xFF == 27:
#                 break

#         cap.release()
#         cv2.destroyAllWindows()


# # ==============================================================
# # Main
# # ==============================================================
# if __name__ == "__main__":
#     system = InteractiveGateSystem(camera_id=0)
#     system.run()

