import threading
import cv2
import time
import numpy as np
import math

from AISystem.tracknav.MultiCameraEngine import MultiCameraEngine
import cv2
import time

from AISystem.tracknav.batch import BatchDetectionEngine
from AISystem.tracknav.camera_manager import get_camera_manager, get_shared_frame
from AISystem.tracknav.newTracking import VehicleTracker

def build_dynamic_grid(frames, cell_size=(500, 300)):
    if not frames:
        return None, 0, {}

    n = len(frames)
    cols = min(n, 3)
    rows = math.ceil(n / cols)

    w, h = cell_size
    grid_img = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)

    grid_positions = {}

    for idx, frame in enumerate(frames):
        r, c = divmod(idx, cols)

        x1, y1 = c * w, r * h
        x2, y2 = x1 + w, y1 + h

        resized = cv2.resize(frame, (w, h))
        grid_img[y1:y2, x1:x2] = resized

        grid_positions[idx] = (x1, y1, x2, y2)

    return grid_img, cols, grid_positions





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
    time.sleep(1)

    gate_ids = [0,1,2,3,4]

    # ✅ create multi-engine (engine per camera)
    # engine_manager = MultiCameraEngine(
    #     model_path="yolov8n.pt",
    #     num_cams=len(gate_ids),
    #     cameraIds = gate_ids
    # )
    engine = BatchDetectionEngine("yolov8n.pt", batch_size=6)
    engine.start()

    gates = [
        VehicleTracker(engine, c)
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

                local_x = x - x1
                local_y = y - y1


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
            for gate in gates:
                data = get_shared_frame(int(gate.camera_id))
                if data:
                    frame, _ = data

                    # optional resize لتحسين الأداء
                    frame = cv2.resize(frame, (640, 360))

                    current_frames[gate.camera_id] = frame.copy()



            display_list = []

            for gate in gates:
                raw_frame = current_frames.get(gate.camera_id)

                processed = gate.process_frame(raw_frame.copy())

                if processed is not None:
                    display_list.append(processed)


            if display_list:
                grid, cols, grid_positions = build_dynamic_grid(display_list)
                shared_context["grid_positions"] = grid_positions
                cv2.imshow(window_name, grid)


            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # for eng in engine_manager.engines.values():
        #     eng.running = False

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()