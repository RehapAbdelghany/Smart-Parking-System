import cv2
import pickle
import numpy as np
import time
import requests
import threading
from ultralytics import YOLO

# --- إعدادات ---
DJANGO_API_URL = "http://127.0.0.1:8000/api/slots/update/"
HEADERS = {'X-Camera-Key': 'my_ultra_secure_camera_token_2026'}
model = YOLO('yolov8n.pt') 

# تحميل الإحداثيات
try:
    with open('CarParkPos', 'rb') as f:
        polygons = pickle.load(f)
except FileNotFoundError:
    print("Error: 'CarParkPos' file not found.")
    polygons = []

cap = cv2.VideoCapture('../videos/back.mp4')

# متغيرات للتحكم في الأداء
last_api_update = 0
update_interval = 5  # إرسال للـ API كل 5 ثوانٍ
payload_lock = threading.Lock()
current_payload = []

def send_to_django(data):
    """وظيفة تُشغل في الخلفية لإرسال البيانات دون تعطيل الفيديو"""
    try:
        response = requests.post(DJANGO_API_URL, json=data, headers=HEADERS, timeout=3)
        if response.status_code == 200:
            print(f"[API] Updated {len(data)} slots successfully.")
    except Exception as e:
        print(f"[API Error] {e}")

def run_ai_service():
    global last_api_update
    print("AI Parking Monitoring Started (Press 'q' to quit)...")

    while True:
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        # 1. معالجة YOLO (تقليل حجم الصورة قليلاً يسرع المعالجة جداً)
        # نقوم بالمعالجة فقط كل X فريم أو بناءً على الوقت لتقليل استهلاك المعالج
        results = model.predict(frame, conf=0.4, classes=[2, 7], verbose=False, device='cpu') # 'cuda' if GPU
        detections = results[0].boxes.data.tolist()
        car_centers = [(int((d[0] + d[2]) / 2), int((d[1] + d[3]) / 2)) for d in detections]

        django_payload = []
        
        # 2. التحقق من السلوتس والرسم
        for entry in polygons:
            slot_id = str(entry['id'])
            poly_points = np.array(entry['points'], np.int32)
            
            is_occupied = False
            for center in car_centers:
                if cv2.pointPolygonTest(poly_points, center, False) >= 0:
                    is_occupied = True
                    break
            
            # تحديد اللون: أحمر للمشغول، أخضر للفارغ
            color = (0, 0, 255) if is_occupied else (0, 255, 0)
            thickness = 2 if is_occupied else 1
            
            # رسم المضلع على الفريم للعرض البصري
            cv2.polylines(frame, [poly_points], True, color, thickness)
            cv2.putText(frame, f"ID:{slot_id}", tuple(poly_points[0]), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            django_payload.append({"slot_id": slot_id, "is_occupied": is_occupied})

        # 3. إرسال للـ API في Thread منفصل كل X ثانية
        current_time = time.time()
        if current_time - last_api_update > update_interval:
            # تشغيل خيط جديد للإرسال حتى لا يتوقف الفيديو
            thread = threading.Thread(target=send_to_django, args=(django_payload,))
            thread.start()
            last_api_update = current_time

        # 4. عرض الفيديو
        cv2.imshow("Parking Management System - Visual Monitor", frame)
        
        # الخروج عند الضغط على q
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_ai_service()