import cv2
import numpy as np
import pickle
import threading
import requests
import time
import queue
from ultralytics import YOLO
from frames_Inqueue import queues, processed_results  # Imported 'queues' (dict) instead of 'frame_queue'

# --- Settings ---
DJANGO_API_URL = "http://127.0.0.1:8000/api/slots/update/"
HEADERS = {'X-Camera-Key': 'my_ultra_secure_camera_token_2026'}
STABILITY_THRESHOLD = 5 
TARGET_WIDTH, TARGET_HEIGHT = 640 , 360

model = YOLO('best.pt')
model.to("cuda")

try:
    with open('CarParkPos', 'rb') as f:
        polygons_raw = pickle.load(f)
except Exception as e:
    print(f"[ERROR] Could not load CarParkPos: {e}")
    polygons_raw = []

# Global Tracking
last_slots_state = {} 
stability_counters = {}

def send_to_django(data):
    try:
        requests.post(DJANGO_API_URL, json=data, headers=HEADERS, timeout=1)
    except:
        pass

def Yolo_Detection():
    global last_slots_state, stability_counters
    print("[AI] Worker started - Equal Time (Multi-Queue) Mode")

    while True:
        processed_at_least_one = False
        
        # Check every camera queue one by one
        for cam_id, q in queues.items():
            try:
                # Use get_nowait() so we don't get stuck if one camera is slow
                cam_id, frame, ts = q.get_nowait()
                processed_at_least_one = True

                # --- Initialization ---
                if cam_id not in last_slots_state:
                    last_slots_state[cam_id] = {str(p['id']): False for p in polygons_raw}
                    stability_counters[cam_id] = {str(p['id']): 0 for p in polygons_raw}

                # --- AI Inference ---
                img_ai = frame
                results = model.predict(img_ai, conf=0.4, classes=[2, 7], verbose=False)

                # --- Scaling & Processing ---
                car_centers = []
                for d in results[0].boxes.data.tolist():
                    cx = int(((d[0] + d[2]) / 2) * (TARGET_WIDTH / 640))
                    cy = int(((d[1] + d[3]) / 2) * (TARGET_HEIGHT / 480))
                    car_centers.append((cx, cy))

                changes = []
                for p in polygons_raw:
                    p_id = str(p['id'])
                    poly_pts = np.array(p['points'], np.int32)
                    is_occ = any(cv2.pointPolygonTest(poly_pts, c, False) >= 0 for c in car_centers)

                    # Stability logic
                    if is_occ != last_slots_state[cam_id][p_id]:
                        stability_counters[cam_id][p_id] += 1
                        if stability_counters[cam_id][p_id] >= STABILITY_THRESHOLD:
                            last_slots_state[cam_id][p_id] = is_occ
                            changes.append({"camera_id": cam_id, "slot_id": p_id, "is_occupied": is_occ})
                            stability_counters[cam_id][p_id] = 0
                    else:
                        stability_counters[cam_id][p_id] = 0

                    # Drawing
                    color = (0, 0, 255) if last_slots_state[cam_id][p_id] else (0, 255, 0)
                    cv2.polylines(frame, [poly_pts], True, color, 2)
                    cv2.putText(frame, f"ID:{p_id}", tuple(poly_pts[0]), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

                # Push result to UI
                processed_results[cam_id] = frame
                
                if changes:
                    threading.Thread(target=send_to_django, args=(changes,), daemon=True).start()

                # Optional: Print only if you want to track the round-robin flow
                print(f"[AI] Equal Time: Processed Cam {cam_id}")

            except queue.Empty:
                # This specific camera queue is empty, just move to the next cam_id
                continue
            except Exception as e:
                print(f"[ERROR] AI Cam {cam_id} fail: {e}")
                continue

        # If ALL queues were empty, sleep 10ms to save CPU
        if not processed_at_least_one:
            time.sleep(0.01)