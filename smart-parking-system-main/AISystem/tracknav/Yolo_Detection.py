import cv2
import numpy as np
import pickle
import threading
import requests
import time
from ultralytics import YOLO
from queue import Queue

from frames_Inqueue import processed_results
from camera_manager import get_shared_frame 

# ================= SETTINGS =================
DJANGO_API_URL = "http://127.0.0.1:8000/api/slots/update/"
HEADERS = {'X-Camera-Key': 'my_ultra_secure_camera_token_2026'}
STABILITY_THRESHOLD = 3 

# قائمة الكاميرات المخصصة لرصد الركنات فقط
slot_camera_ids = [0,1,2,3,4] # عدل الأرقام حسب الكاميرات المتاحة لديك


# ================= LOAD POLYGONS =================
try:
    with open('CarParkPos', 'rb') as f:
        polygons_raw = pickle.load(f)
except Exception as e:
    print(f"[ERROR] Could not load CarParkPos: {e}")
    polygons_raw = []


# ================= GLOBAL STATE =================
last_slots_state = {}
stability_counters = {}

# Queue لإدارة طلبات الـ API بعيداً عن معالجة الفيديو
api_queue = Queue(maxsize=200)


# ================= API WORKER =================
def api_worker():
    """خادم مخصص لإرسال البيانات للسيرفر لضمان عدم تأخير المعالجة"""
    while True:
        data_list = api_queue.get()
        try:
            # نرسل التحديثات كقائمة واحدة لتقليل عدد الـ Requests
            response = requests.post(DJANGO_API_URL, json=data_list, headers=HEADERS, timeout=2)
            if response.status_code != 200:
                print(f"[API] Server returned error: {response.status_code}")
        except Exception as e:
            print(f"[API] Connection failed: {e}")
        finally:
            api_queue.task_done()


# ================= SINGLE CAMERA WORKER =================
def slot_worker(cam_id, engine):
    print(f"[AI] Slot worker started for Cam {cam_id} (Batch Mode)")

    # إعداد الحالة الابتدائية لهذه الكاميرا
    last_slots_state[cam_id] = {str(p['id']): False for p in polygons_raw}
    stability_counters[cam_id] = {str(p['id']): 0 for p in polygons_raw}

    while True:
        data = get_shared_frame(cam_id)

        if data is None:
            time.sleep(0.01)
            continue

        frame, ts = data

        # تجاهل الفريمات القديمة جداً (Lag Protection)
        if time.time() - ts > 1.0:
            continue

        frame_draw = frame.copy()

        try:
            # 1. إرسال الفريم للـ Batch Engine
            engine.submit_frame(cam_id, frame)
            
            # 2. سحب النتيجة مع محاولات إعادة (Retry Logic)
            results = None
            for _ in range(15): 
                results = engine.get_result(cam_id)
                if results is not None: 
                    break
                time.sleep(0.005)

            if results is None:
                continue

            # 3. استخراج مراكز السيارات المكتشفة
            car_centers = []
            # YOLOv8 Results object
            boxes = results[0].boxes
            if boxes is not None:
                for box in boxes:
                    # cls 2: car, 7: truck
                    cls = int(box.cls[0])
                    if cls in [2, 7]:
                        xyxy = box.xyxy[0].tolist()
                        cx = int((xyxy[0] + xyxy[2]) / 2)
                        cy = int((xyxy[1] + xyxy[3]) / 2)
                        car_centers.append((cx, cy))

            changes = []

            # 4. فحص كل ركنة (Polygon)
            for p in polygons_raw:
                p_id = str(p['id'])
                poly_pts = np.array(p['points'], np.int32)

                # هل يوجد مركز سيارة داخل هذا المضلع؟
                is_occ = any(cv2.pointPolygonTest(poly_pts, c, False) >= 0 for c in car_centers)

                # 5. منطق الاستقرار لتقليل الـ Flickering
                if is_occ != last_slots_state[cam_id][p_id]:
                    stability_counters[cam_id][p_id] += 1
                    if stability_counters[cam_id][p_id] >= STABILITY_THRESHOLD:
                        last_slots_state[cam_id][p_id] = is_occ
                        changes.append({
                            "camera_id": cam_id,
                            "slot_id": p_id,
                            "is_occupied": is_occ
                        })
                        stability_counters[cam_id][p_id] = 0
                else:
                    stability_counters[cam_id][p_id] = 0

                # 6. الرسم التوضيحي
                color = (0, 0, 255) if is_occ else (0, 255, 0)
                cv2.polylines(frame_draw, [poly_pts], True, color, 2)
                cv2.putText(frame_draw, p_id, (poly_pts[0][0], poly_pts[0][1]-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

            # تحديث النتيجة النهائية للعرض في الـ Grid
            processed_results[cam_id] = frame_draw

            # 7. إرسال التحديثات للـ Django عبر الـ Queue
            if changes:
                if not api_queue.full():
                    api_queue.put(changes)

        except Exception as e:
            print(f"[ERROR] AI Logic fail on Cam {cam_id}: {e}")

        # موازنة سرعة الـ Loop
        time.sleep(0.01)


# ================= START FUNCTION =================
def start_slot_workers(engine):
    """
    تشغيل عمال الركنات. 
    @param engine: كائن من BatchInferenceEngine (مُحمل بموديل best.pt)
    """
    # تشغيل خادم الـ API مرة واحدة
    t_api = threading.Thread(target=api_worker, daemon=True)
    t_api.start()

    # تشغيل Worker مستقل لكل كاميرا ركنات
    for cam_id in slot_camera_ids:
        t = threading.Thread(
            target=slot_worker,
            args=(cam_id, engine),
            daemon=True
        )
        t.start()
    
    print(f"[SYSTEM] {len(slot_camera_ids)} Slot workers are now running.")