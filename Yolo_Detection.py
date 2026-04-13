import cv2
import numpy as np
import pickle
import time
import requests
import threading
from multiprocessing import shared_memory
from ultralytics import YOLO
from config import FRAME_WIDTH, FRAME_HEIGHT

# --- Settings ---
DJANGO_API_URL = "http://127.0.0.1:8000/api/slots/update/"
HEADERS = {'X-Camera-Key': 'my_ultra_secure_camera_token_2026'}
STABILITY_THRESHOLD = 3 

# Configuration for Shared Memory
SHAPE = (FRAME_HEIGHT, FRAME_WIDTH, 3)
DTYPE = np.uint8

def send_to_django(data):
    """Utility to send occupancy updates to your backend."""
    try:
        requests.post(DJANGO_API_URL, json=data, headers=HEADERS, timeout=1)
    except Exception as e:
        # Silently fail or log to console if Django is down
        pass

def Yolo_Detection_Process(cam_ids, stop_event):
    print(f"[AI Process] Slot Detection Process started for Cams: {cam_ids}")
    
    # 1. Initialize YOLO inside the process (Mandatory for Multiprocessing)
    model = YOLO('best.pt').to("cuda")
    
    # 2. Load parking polygons
    try:
        with open('CarParkPos', 'rb') as f:
            polygons_raw = pickle.load(f)
    except Exception as e:
        print(f"[ERROR] Could not load CarParkPos: {e}")
        polygons_raw = []

    # 3. Attach to Shared Memory with Retry Logic
    shm_links = {}
    for cid in cam_ids:
        shm_name = f"parking_cam_{cid}"
        connected = False
        for attempt in range(5):  # Try 5 times to wait for Master Process
            try:
                shm = shared_memory.SharedMemory(name=shm_name)
                arr = np.ndarray(SHAPE, dtype=DTYPE, buffer=shm.buf)
                shm_links[cid] = (shm, arr)
                print(f"✅ Slot Process linked to {shm_name}")
                connected = True
                break
            except FileNotFoundError:
                time.sleep(0.5)
        
        if not connected:
            print(f"❌ Failed to link Cam {cid} - Buffer not found.")

    # Tracking states
    last_slots_state = {cid: {str(p['id']): False for p in polygons_raw} for cid in cam_ids}
    stability_counters = {cid: {str(p['id']): 0 for p in polygons_raw} for cid in cam_ids}

    # 4. Main Inference Loop
    try:
        while not stop_event.is_set():
            for cid, (shm, shared_arr) in shm_links.items():
                # Get a local copy so our drawings don't corrupt the raw feed
                frame = shared_arr.copy()
                
                # AI Inference (Classes 2/7 are car/truck in COCO)
                results = model.predict(frame, conf=0.4, classes=[2, 7], verbose=False)
                
                # Extract car centers
                car_centers = []
                for d in results[0].boxes.data.tolist():
                    cx = int((d[0] + d[2]) / 2)
                    cy = int((d[1] + d[3]) / 2)
                    car_centers.append((cx, cy))

                changes = []
                for p in polygons_raw:
                    p_id = str(p['id'])
                    poly_pts = np.array(p['points'], np.int32)

                    # Check if any car center is inside this polygon
                    is_occ = any(cv2.pointPolygonTest(poly_pts, c, False) >= 0 for c in car_centers)

                    # Stability check: Only trigger update if state persists
                    if is_occ != last_slots_state[cid][p_id]:
                        stability_counters[cid][p_id] += 1
                        if stability_counters[cid][p_id] >= STABILITY_THRESHOLD:
                            last_slots_state[cid][p_id] = is_occ
                            changes.append({
                                "camera_id": cid,
                                "slot_id": p_id,
                                "is_occupied": is_occ
                            })
                            stability_counters[cid][p_id] = 0
                    else:
                        stability_counters[cid][p_id] = 0

                    # --- DRAWING LOGIC ---
                    color = (0, 0, 255) if last_slots_state[cid][p_id] else (0, 255, 0)
                    # Draw polygon
                    cv2.polylines(frame, [poly_pts], True, color, 2)
                    # Draw Slot ID
                    cv2.putText(frame, p_id, (poly_pts[0][0], poly_pts[0][1]-5), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                # Show Resulting Frame
                cv2.imshow(f"Slot Detection: Cam {cid}", frame)

                # Send data to Django in a background thread
                if changes:
                    threading.Thread(target=send_to_django, args=(changes,), daemon=True).start()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
            # Throttle slightly to save GPU resources
            time.sleep(0.01)

    finally:
        # 5. Cleanup
        print("[AI Process] Closing Shared Memory links...")
        for shm, arr in shm_links.values():
            shm.close()
        cv2.destroyAllWindows()