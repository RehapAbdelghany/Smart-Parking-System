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

slot_camera_ids = [0, 1, 2, 3, 4, 5]


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

api_queue = Queue(maxsize=100)


# ================= API WORKER =================
def api_worker():
    while True:
        data = api_queue.get()
        try:
            # إرسال التحديثات للـ Django
            requests.post(DJANGO_API_URL, json=data, headers=HEADERS, timeout=1)
        except:
            pass
        api_queue.task_done()


# ================= SINGLE CAMERA WORKER =================
def slot_worker(cam_id, engine):
    print(f"[AI] Slot worker started for Cam {cam_id} (Batch Mode)")

    # إعداد الحالة الابتدائية
    last_slots_state[cam_id] = {str(p['id']): False for p in polygons_raw}
    stability_counters[cam_id] = {str(p['id']): 0 for p in polygons_raw}

    while True:
        data = get_shared_frame(cam_id)

        if data is None:
            time.sleep(0.01)
            continue

        frame, ts = data

        # Skip old frames
        if time.time() - ts > 0.5:
            continue

        frame_draw = frame.copy()

        try:
            # ✅ إرسال الفريم للمحرك المركزي (Batch Engine)
            engine.submit_frame(cam_id, frame)
            
            # ✅ سحب النتيجة (Best.pt)
            results = None
            for _ in range(10): # محاولة السحب
                results = engine.get_result(cam_id)
                if results: break
                time.sleep(0.01)

            if results is None:
                continue

            car_centers = []
            # الحصول على الداتا من الصناديق (xyxy, conf, cls)
            for d in results.boxes.data.tolist():
                # classes=[2, 7] (Car and Truck)
                if int(d[5]) in [2, 7]:
                    cx = int((d[0] + d[2]) / 2)
                    cy = int((d[1] + d[3]) / 2)
                    car_centers.append((cx, cy))

            changes = []

            for p in polygons_raw:
                p_id = str(p['id'])
                poly_pts = np.array(p['points'], np.int32)

                # هل توجد سيارة داخل المضلع؟
                is_occ = any(
                    cv2.pointPolygonTest(poly_pts, c, False) >= 0
                    for c in car_centers
                )

                # منطق الاستقرار (Stability Logic)
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

                # الرسم على الفريم
                color = (0, 0, 255) if is_occ else (0, 255, 0)
                cv2.polylines(frame_draw, [poly_pts], True, color, 2)

            # حفظ النتيجة للعرض في الواجهة الرئيسية
            processed_results[cam_id] = frame_draw

            # إرسال التحديثات للـ Queue الخاص بالـ API
            if changes:
                if not api_queue.full():
                    api_queue.put(changes)

        except Exception as e:
            print(f"[ERROR] Slot AI fail on Cam {cam_id}: {e}")

        time.sleep(0.02)


# ================= START FUNCTION =================
def start_slot_workers(engine):
    """
    يجب تمرير الـ slot_engine من الـ main.py هنا
    """
    # API thread
    threading.Thread(target=api_worker, daemon=True).start()

    # One worker per camera using the same engine
    for cam_id in slot_camera_ids:
        threading.Thread(
            target=slot_worker,
            args=(cam_id, engine),
            daemon=True
        ).start()