import cv2
import pickle
import numpy as np
import time
import requests
import threading
import psutil
import os
from ultralytics import YOLO

# --- إعدادات ---
DJANGO_API_URL = "http://127.0.0.1:8000/api/slots/update/"
HEADERS = {'X-Camera-Key': 'my_ultra_secure_camera_token_2026'}
model = YOLO('yolov8n.pt') 
process = psutil.Process(os.getpid())

# الحجم اللي هنشتغل عليه طول الوقت (عشان السرعة)
TARGET_WIDTH = 1280
TARGET_HEIGHT = 720

STABILITY_THRESHOLD = 5 

try:
    with open('CarParkPos', 'rb') as f:
        polygons_raw = pickle.load(f)
except FileNotFoundError:
    print("Error: 'CarParkPos' file not found.")
    polygons_raw = []

cap = cv2.VideoCapture('../videos/back.mp4')

# تعديل إحداثيات المضلعات لتناسب الحجم الجديد مرة واحدة فقط (بدل ما نعدلها كل فريم)
original_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
original_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

polygons = []
for p in polygons_raw:
    scaled_points = []
    for pt in p['points']:
        scaled_points.append([int(pt[0] * TARGET_WIDTH / original_w), 
                             int(pt[1] * TARGET_HEIGHT / original_h)])
    polygons.append({'id': str(p['id']), 'points': np.array(scaled_points, np.int32)})

last_slots_state = {p['id']: False for p in polygons}
stability_counters = {p['id']: 0 for p in polygons}
current_small_frame = None
running = True

def send_to_django(data):
    try:
        requests.post(DJANGO_API_URL, json=data, headers=HEADERS, timeout=1)
    except: pass

def ai_worker():
    global last_slots_state, stability_counters, running
    frame_counter = 0
    while running:
        if current_small_frame is not None:
            frame_counter += 1
            if frame_counter % 12 == 0: # معالجة كل 12 فريم
                # الموديل هيشتغل على 640x360 (السرعة القصوى لـ YOLO)
                img_ai = cv2.resize(current_small_frame, (640, 360))
                results = model.predict(img_ai, conf=0.4, classes=[2, 7], verbose=False)
                
                # تعديل مراكز السيارات لتناسب الـ TARGET_WIDTH
                car_centers = []
                for d in results[0].boxes.data.tolist():
                    cx = int(((d[0] + d[2]) / 2) * (TARGET_WIDTH / 640))
                    cy = int(((d[1] + d[3]) / 2) * (TARGET_HEIGHT / 360))
                    car_centers.append((cx, cy))

                changes = []
                for p in polygons:
                    is_occ = any(cv2.pointPolygonTest(p['points'], c, False) >= 0 for c in car_centers)
                    
                    if is_occ != last_slots_state[p['id']]:
                        stability_counters[p['id']] += 1
                        if stability_counters[p['id']] >= STABILITY_THRESHOLD:
                            last_slots_state[p['id']] = is_occ
                            changes.append({"slot_id": p['id'], "is_occupied": is_occ})
                            stability_counters[p['id']] = 0
                    else:
                        stability_counters[p['id']] = 0
                
                if changes:
                    threading.Thread(target=send_to_django, args=(changes,)).start()
        time.sleep(0.01)

def run_ai_service():
    global current_small_frame, running
    threading.Thread(target=ai_worker, daemon=True).start()

    while True:
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        # السر هنا: نصغر الفريم فوراً
        current_small_frame = cv2.resize(frame, (TARGET_WIDTH, TARGET_HEIGHT))

        # الرسم على الفريم الصغير (أسرع بكتير)
        for p in polygons:
            state = last_slots_state[p['id']]
            color = (0, 0, 255) if state else (0, 255, 0)
            cv2.polylines(current_small_frame, [p['points']], True, color, 2)
            
            count = stability_counters[p['id']]
            label = f"ID:{p['id']}" + (f"({count})" if count > 0 else "")
            cv2.putText(current_small_frame, label, tuple(p['points'][0]), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # عرض الفريم الجاهز
        cv2.imshow("Smart Parking System - Ultra Fast", current_small_frame)
        
        # تحكم في سرعة العرض (1 مللي ثانية)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_ai_service()
