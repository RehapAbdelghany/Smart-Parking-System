import multiprocessing
import cv2
import time
from camera_manager import get_camera_manager
from Yolo_Detection import Yolo_Detection_Process
from finalNavemb import InteractiveGateSystem, CarAnalyzer
from ultralytics import YOLO

def main():
    print("=== Smart Parking Master Process Booting ===")
    
    # 1. Start Camera Manager (Creates Shared Memory Blocks)
    cm = get_camera_manager()

    # 2. Setup Multiprocessing
    stop_event = multiprocessing.Event()
    slot_camera_ids = [0, 1, 2, 3, 4, 5] # Define cameras for slots
    
    # Launch Slot AI in a separate system process
    p_slot = multiprocessing.Process(
        target=Yolo_Detection_Process, 
        args=(slot_camera_ids, stop_event)
    )
    p_slot.start()

    # 3. Main Thread: Gate Systems (GUIs must run in the main thread)
    shared_yolo = YOLO("yolov8n.pt")
    shared_analyzer = CarAnalyzer()
    
    gate_ids = [0, 1, 2, 3, 4] # Example gate cams
    gates = [InteractiveGateSystem(i, shared_yolo, shared_analyzer) for i in gate_ids]

    for i in gate_ids:
        cv2.namedWindow(f"Gate System - Cam {i}", cv2.WINDOW_NORMAL)

    try:
        while True:
            for gate in gates:
                frame = gate.update()
                if frame is not None:
                    cv2.imshow(f"Gate System - Cam {gate.camera_id}", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            time.sleep(0.01)

    finally:
        print("Shutting down...")
        stop_event.set()
        p_slot.join()
        cm.cleanup()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # MANDATORY FOR WINDOWS MULTIPROCESSING
    multiprocessing.freeze_support()
    main()