import threading
import cv2
import time
from config import CAMERA_URLS
from camera_reader import camera_reader
from Yolo_Detection import Yolo_Detection
from frames_Inqueue import processed_results

def main():
    print("--- Smart Parking System Booting ---")

    # 1. Start all camera threads
    # These push raw frames into the 'frame_queue'
    for i, source in enumerate(CAMERA_URLS):
        t = threading.Thread(target=camera_reader, args=(source, i), daemon=True)
        t.start()
        print(f"[SYSTEM] Camera {i} Reader Thread Started")

    # 2. Start the AI worker in a background thread
    # This thread pulls from 'frame_queue' and puts results in 'processed_results'
    ai_thread = threading.Thread(target=Yolo_Detection, daemon=True)
    ai_thread.start()

    print("[SYSTEM] AI Worker Thread Started")
    print("[SYSTEM] UI Loop Active. Press 'q' on any video window to exit.")

    # 3. The Main UI Loop
    # This thread is responsible for showing the boxes on the screen
    try:
        while True:
            # Create a list of current keys to avoid 'dict changed during iteration' error
            cam_ids = list(processed_results.keys())
            
            for cam_id in cam_ids:
                # Get the frame that the AI has finished drawing on
                img = processed_results.get(cam_id)
                
                if img is not None:
                    cv2.imshow(f"Camera {cam_id}", img)

            # Check for the quit key (must be in the main thread)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[SYSTEM] Quit signal received.")
                break
                
            # Small sleep to keep the CPU from maxing out while waiting for new frames
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n[SYSTEM] Keyboard Interrupt detected.")
    finally:
        print("[SYSTEM] Shutting down and cleaning up...")
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()