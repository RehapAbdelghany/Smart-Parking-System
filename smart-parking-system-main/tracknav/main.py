import threading
import cv2
import time
import numpy as np
import math

from camera_manager import get_camera_manager
from Yolo_Detection import start_slot_workers
from frames_Inqueue import processed_results
from finalemb import InteractiveGateSystem, CarAnalyzer
from inference_engine import BatchInferenceEngine
from config import FRAME_HEIGHT , FRAME_WIDTH

# ============================================================
# ANALYZER SINGLETON
# ============================================================
class AnalyzerSingleton:
    """
    يضمن تحميل موديلات Re-ID و CLIP مرة واحدة فقط لتوفير الذاكرة
    """
    _instance = None
    @staticmethod
    def get():
        if AnalyzerSingleton._instance is None:
            print("[SYSTEM] Loading shared Re-ID & Color models (Analyzer)...")
            AnalyzerSingleton._instance = CarAnalyzer()
        return AnalyzerSingleton._instance

# ============================================================
# GRID HELPER (Dynamic)
# ============================================================
def build_dynamic_grid(frames, cell_size=(500, 300)):
    if not frames: return None, 0
    n = len(frames)
    cols = min(n, 3) # بحد أقصى 3 أعمدة
    rows = math.ceil(n / cols)
    
    w, h = cell_size
    # إنشاء لوحة سوداء بالأبعاد المناسبة تماماً لعدد الكاميرات
    grid_img = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
    
    for idx, frame in enumerate(frames):
        r, c = divmod(idx, cols)
        resized = cv2.resize(frame, (w, h))
        grid_img[r*h:(r+1)*h, c*w:(c+1)*w] = resized
        
    return grid_img, cols

 
# ============================================================
# MAIN
# ============================================================
def main():
    print("\n" + "="*50)
    print("      SMART PARKING SYSTEM - BATCH MODE 2026")
    print("="*50 + "\n")

    get_camera_manager()
    shared_analyzer = AnalyzerSingleton.get()

    # محركات الذكاء الاصطناعي
    print("[SYSTEM] Initializing AI Engines...")
    gate_engine = BatchInferenceEngine(model_path="yolov8n.pt", batch_size=5, device="cuda")
    gate_engine.start()
    
    # slot_engine = BatchInferenceEngine(model_path="best.pt", batch_size=6, device="cuda")
    # slot_engine.start()
    # start_slot_workers(engine=slot_engine)

    # تجهيز البوابات
    gate_ids = [0,1,2,3,4,5]
    gates = [InteractiveGateSystem(c, gate_engine, shared_analyzer) for c in gate_ids]

    # إنشاء النافذة وربط الماوس
    window_name = "Smart Parking System - Central Monitor"
    cv2.namedWindow(window_name)

    # ✅ STATE ثابت يحل المشكلة
    state = {
        "frame_sources": [],
        "cols": 1
    }
    
    # دالة تحويل الإحداثيات للماوس (Mapping) لضمان دقة السحب
    def mouse_wrapper(event, x, y, flags, param):
      cell_w, cell_h = 500, 300

      col = x // cell_w
      row = y // cell_h
      idx = row * state["cols"] + col

      if idx < len(state["frame_sources"]):
        src_type, obj = state["frame_sources"][idx]

        # ✅ تحويل الإحداثيات صح (640x480)
        rel_x = int((x % cell_w) * (FRAME_WIDTH / cell_w))
        rel_y = int((y % cell_h) * (FRAME_HEIGHT / cell_h))

        if src_type == "gate":
            obj.mouse_callback(event, rel_x, rel_y, flags, param)


    cv2.setMouseCallback(window_name, mouse_wrapper)

    print("[SYSTEM] UI Grid Started. Press 'q' to quit.")

    try:
        while True:
            frames_to_display = []
            state["frame_sources"] = []  # ✅ بدل reset العادي

            # 1. Slot Frames
            # for cam_id, img in list(processed_results.items()):
            #  if img is not None:
            #   frame_copy = img.copy()
            #   cv2.putText(frame_copy, f"Slot Cam {cam_id}", (15, 30),
            #         cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            #   frames_to_display.append(frame_copy)
            #   state["frame_sources"].append(("slot", cam_id))

            # 2. Gate Frames (مع التفاعل)
            for gate in gates:
               frame = gate.get_ui_frame()
               if frame is not None:
                frame_copy = frame.copy()
                cv2.putText(frame_copy, f"Gate Cam {gate.camera_id}", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                frames_to_display.append(frame_copy)
                state["frame_sources"].append(("gate", gate)) 

            # بناء الشبكة ديناميكياً لتجنب الفراغات السوداء
            grid, cols = build_dynamic_grid(frames_to_display)
            state["cols"] = cols  # ✅ FIX الحقيقي هنا

            if grid is not None:
                cv2.imshow(window_name, grid)

            if cv2.waitKey(1) & 0xFF in [ord('q'), 27]:
                break
            time.sleep(0.01)

    finally:
        gate_engine.running = False
        #slot_engine.running = False
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
