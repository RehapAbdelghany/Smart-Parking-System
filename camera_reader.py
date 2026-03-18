import cv2
import time
from frames_Inqueue import queues # Now importing the dictionary of queues
from config import FRAME_WIDTH, FRAME_HEIGHT

def camera_reader(rtsp_url, cam_id):
    # Initial connection
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    # Grab THIS camera's specific queue from the dictionary
    my_queue = queues[cam_id]
    
    print(f"[INFO] Camera {cam_id} Reader Thread Started")

    while True:
        ret, frame = cap.read()
        
        if not ret:
            print(f"[WARNING] Camera {cam_id} lost connection. Retrying in 2s...")
            cap.release()
            time.sleep(2)  # Critical: prevents CPU spike during disconnect
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            continue

        # Resize for consistent AI processing
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Check if THIS specific queue is full
        if my_queue.full():
            try: 
                my_queue.get_nowait() # Drop the oldest frame to keep it real-time
            except: 
                pass

        try:
            # Push to the camera-specific queue
            my_queue.put_nowait((cam_id, frame, time.time()))
        except Exception as e:
            # This handles cases where the queue might be locked or closed
            pass