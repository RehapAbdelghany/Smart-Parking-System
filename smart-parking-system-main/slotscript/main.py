import threading
import cv2
import time
import numpy as np
from ultralytics import YOLO

from camera_manager import get_camera_manager
from Yolo_Detection import start_slot_workers
from frames_Inqueue import processed_results
from finalemb import InteractiveGateSystem, CarAnalyzer
from inference_engine import BatchInferenceEngine  # استيراد المحرك الجديد

# ============================================================
# ANALYZER SINGLETON
# ============================================================
class AnalyzerSingleton:
    _instance = None

    @staticmethod
    def get():
        if AnalyzerSingleton._instance is None:
            AnalyzerSingleton._instance = CarAnalyzer()
        return AnalyzerSingleton._instance


def main():
    print("\n" + "="*50)
    print("      SMART PARKING SYSTEM - BATCH MODE 2026")
    print("="*50 + "\n")

    # 1. CAMERA MANAGER (بدء سحب الفريمات من الـ RTSP)
    get_camera_manager()

    # 2. LOAD SHARED ANALYZER (CLIP & ReID)
    print("[SYSTEM] Loading shared Re-ID & Color models...")
    shared_analyzer = AnalyzerSingleton.get()

    # ============================================================
    # 3. INITIALIZE BATCH ENGINES (المحركات المركزية)
    # ============================================================
    print("[SYSTEM] Initializing AI Engines...")
    
    # محرك البوابات (Gate Engine) - يتعامل مع 5 كاميرات
    gate_engine = BatchInferenceEngine(
        model_path="yolov8n.pt", 
        batch_size=5, 
        device="cuda"
    )
    gate_engine.start()

    # محرك السلوتات (Slot Engine) - يتعامل مع 6 كاميرات
    slot_engine = BatchInferenceEngine(
        model_path="best.pt", 
        batch_size=6, 
        device="cuda"
    )
    slot_engine.start()

    print("[SYSTEM] AI Engines are Warming up and Ready.")

    # ============================================================
    # 4. START SLOT DETECTION WORKERS
    # ============================================================
    print("[SYSTEM] Starting Slot Detection workers...")
    # قمنا بتمرير المحرك للعمال بدلاً من فتح موديل لكل واحد
    start_slot_workers(engine=slot_engine)

    # ============================================================
    # 5. GATE SYSTEMS INITIALIZATION
    # ============================================================
    gate_ids = [0, 1, 2, 3, 4]
    gates = []

    for cam_id in gate_ids:
        print(f"[SYSTEM] Initializing Gate System for Camera {cam_id}...")

        # لاحظ: لم نعد ننشئ YOLO هنا، نمرر الـ gate_engine فقط
        instance = InteractiveGateSystem(
            camera_id=cam_id,
            engine=gate_engine, # المحرك المشترك
            analyzer=shared_analyzer
        )

        win_name = f"Gate System - Cam {cam_id}"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(win_name, instance.mouse_callback)

        gates.append(instance)

    print(f"\n[SYSTEM] All {len(gates)} Gate modules and 6 Slot workers active.")
    print("[SYSTEM] UI Loop Started. Press 'q' to quit.")

    # ============================================================
    # 6. MAIN UI LOOP (Visualizer)
    # ============================================================
    try:
        while True:
            # ---------- عرض نتائج ركن السيارات (Slots) ----------
            # نستخدم list لتجنب RuntimeError في حالة تغير حجم الـ dict أثناء اللوب
            for cam_id, img in list(processed_results.items()):
                if img is not None:
                    cv2.imshow(f"Slot Detection: Cam {cam_id}", img)

            # ---------- عرض نتائج البوابات (Gates) ----------
            for gate in gates:
                frame = gate.get_ui_frame()
                if frame is not None:
                    cv2.imshow(
                        f"Gate System - Cam {gate.camera_id}",
                        frame
                    )

            # ---------- الخروج ----------
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break

            # تقليل استهلاك البروسيسور في اللوب الأساسي
            time.sleep(0.01)

    except Exception as e:
        print(f"[SYSTEM ERROR] {e}")

    finally:
        print("\n[SYSTEM] Shutting down...")
        
        # إيقاف المحركات
        gate_engine.running = False
        slot_engine.running = False
        
        # إيقاف ثريدز البوابات
        for gate in gates:
            gate.running = False

        cv2.destroyAllWindows()
        print("[SYSTEM] Goodbye.")


if __name__ == "__main__":
    main()