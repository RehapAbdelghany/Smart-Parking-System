import threading
import cv2
import time
import numpy as np
import math

from AISystem.tracknav.MultiCameraEngine import MultiCameraEngine
from AISystem.tracknav.camera_manager import get_camera_manager, get_shared_frame
from AISystem.tracknav.newTracking import VehicleTracker
from AISystem.tracknav.track import CarAnalyzer, InteractiveGateSystem
from Yolo_Detection import start_slot_workers
from frames_Inqueue import processed_results
from inference_engine import BatchInferenceEngine
from config import FRAME_HEIGHT, FRAME_WIDTH



# ============================================================
# GRID HELPER (Dynamic)
# ============================================================
# def build_dynamic_grid(frames, cell_size=(500, 300)):
#     if not frames: return None, 0
#     n = len(frames)
#     cols = min(n, 3)  # بحد أقصى 3 أعمدة
#     rows = math.ceil(n / cols)
#
#     w, h = cell_size
#     # إنشاء لوحة سوداء بالأبعاد المناسبة تماماً لعدد الكاميرات
#     grid_img = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
#
#     for idx, frame in enumerate(frames):
#         r, c = divmod(idx, cols)
#         resized = cv2.resize(frame, (w, h))
#         grid_img[r * h:(r + 1) * h, c * w:(c + 1) * w] = resized
#
#     return grid_img, cols

def build_dynamic_grid(frames, cell_size=(500, 300)):
    if not frames:
        return None, 0, {}

    n = len(frames)
    cols = min(n, 3)
    rows = math.ceil(n / cols)

    w, h = cell_size
    grid_img = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)

    grid_positions = {}  # 👈 مهم جدًا

    for idx, frame in enumerate(frames):
        r, c = divmod(idx, cols)

        x1, y1 = c * w, r * h
        x2, y2 = x1 + w, y1 + h

        resized = cv2.resize(frame, (w, h))
        grid_img[y1:y2, x1:x2] = resized

        grid_positions[idx] = (x1, y1, x2, y2)  # 👈 حفظ مكان الكاميرا

    return grid_img, cols, grid_positions

# import cv2
# import time
# from AISystem.tracknav.camera_manager import get_camera_manager, get_shared_frame
# from AISystem.tracknav.newTracking import VehicleTracker
# from inference_engine import BatchInferenceEngine
#
# def main():
#     get_camera_manager()
#     time.sleep(3)
#
#     gate_engine = BatchInferenceEngine(model_path="yolov8n.pt", batch_size=5)
#     gate_engine.start()
#
#     gate_ids = [0, 1, 2, 3, 4]
#     gates = [VehicleTracker(gate_engine, c) for c in gate_ids]
#
#     window_name = "Smart Parking - Multi-Cam Async"
#     cv2.namedWindow(window_name)
#
#     try:
#         while True:
#             # STAGE 1: Submit ALL frames first to fill the Batch Engine
#             current_frames = {}
#             for gate in gates:
#                 data = get_shared_frame(int(gate.camera_id))
#                 if data:
#                     frame, _ = data
#                     current_frames[gate.camera_id] = frame.copy()
#                     gate_engine.submit_frame(gate.camera_id, frame)
#
#             # STAGE 2: Process results and build UI grid[cite: 3]
#             display_list = []
#             for gate in gates:
#                 raw_frame = current_frames.get(gate.camera_id)
#                 # Tracker now uses the results from the background thread
#                 processed = gate.process_frame(raw_frame)
#                 if processed is not None:
#                     display_list.append(processed)
#
#             # (Grid building logic from source 3)
#             if display_list:
#                 # Assuming build_dynamic_grid is defined as in source 3
#                 grid, _ = build_dynamic_grid(display_list)
#                 cv2.imshow(window_name, grid)
#
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break
#     finally:
#         gate_engine.running = False
#         cv2.destroyAllWindows()
#
# if __name__ == "__main__":
#     main()


import cv2
import time
from AISystem.tracknav.camera_manager import get_camera_manager, get_shared_frame
from AISystem.tracknav.newTracking import VehicleTracker


def create_global_mouse_callback(gates, grid_positions, cell_size):
    def global_mouse(event, x, y, flags, param):
        w, h = cell_size

        for idx, (x1, y1, x2, y2) in grid_positions.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                gate = gates[idx]

                # 👇 نحول لإحداثيات داخل الكاميرا
                local_x = int((x - x1))
                local_y = int((y - y1))

                # ⚠️ مهم: لو الفريم الأصلي مش بنفس الحجم
                scale_x = gate.original_width / w
                scale_y = gate.original_height / h

                local_x = int(local_x * scale_x)
                local_y = int(local_y * scale_y)

                gate.mouse_callback(event, local_x, local_y, flags, None)
                break

    return global_mouse

def main():
    get_camera_manager()

    gate_ids = [0,1,2]

    # ✅ create multi-engine (engine per camera)
    engine_manager = MultiCameraEngine(
        model_path="yolov8n.pt",
        num_cams=len(gate_ids),
        cameraIds = gate_ids
    )

    gates = [
        VehicleTracker(engine_manager.engines[c], c)
        for c in gate_ids
    ]


    window_name = "Smart Parking - Multi-Cam Async"
    cv2.namedWindow(window_name)
    cell_size = (500, 300)
    shared_context = {"grid_positions": {}}

    def on_mouse(event, x, y, flags, param):
        w, h = cell_size
        # نبحث في أي خلية (Camera) وقعت الضغطة
        for idx, (x1, y1, x2, y2) in shared_context["grid_positions"].items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                gate = gates[idx]

                # 1. تحويل الإحداثيات من الـ Grid إلى الـ Cell (0-500, 0-300)
                local_x = x - x1
                local_y = y - y1

                # 2. تحويل الإحداثيات من حجم الـ Cell إلى حجم الفريم اللي Tracker شغال عليه (640, 360)
                # بما إنك بتعمل resize للفريم لـ 640x360 قبل ما تبعته للـ process_frame
                scale_x = 640 / w
                scale_y = 360 / h

                final_x = int(local_x * scale_x)
                final_y = int(local_y * scale_y)

                # إرسال الإحداثيات المصلحة للـ Tracker
                gate.mouse_callback(event, final_x, final_y, flags, None)
                break

    cv2.setMouseCallback(window_name, on_mouse)

    try:
        while True:
            current_frames = {}

            # =====================================================
            # STAGE 1: read + submit لكل كاميرا (independent)
            # =====================================================
            for gate in gates:
                data = get_shared_frame(int(gate.camera_id))
                if data:
                    frame, _ = data

                    # optional resize لتحسين الأداء
                    frame = cv2.resize(frame, (640, 360))

                    current_frames[gate.camera_id] = frame.copy()

                    # 👇 submit للـ engine الخاص بالكاميرا
                    gate.engine.submit_frame(frame)

            # =====================================================
            # STAGE 2: process tracking results
            # =====================================================
            display_list = []

            for gate in gates:
                raw_frame = current_frames.get(gate.camera_id)

                processed = gate.process_frame(raw_frame.copy())

                if processed is not None:
                    display_list.append(processed)

            # =====================================================
            # STAGE 3: display
            # =====================================================
            if display_list:
                grid, cols, grid_positions = build_dynamic_grid(display_list)
                shared_context["grid_positions"] = grid_positions
                cv2.imshow(window_name, grid)

                # cv2.setMouseCallback(
                #     window_name,
                #     create_global_mouse_callback(
                #         gates,
                #         grid_positions,
                #         cell_size=(500, 300)
                #     )
                # )

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # ✅ اقفل كل engines
        for eng in engine_manager.engines.values():
            eng.running = False

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()