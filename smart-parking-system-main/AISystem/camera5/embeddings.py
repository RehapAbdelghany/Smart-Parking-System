import cv2
import numpy as np

from AISystem.EntranceExitGates.Threads.CameraThread import CameraThread
from AISystem.EntranceExitGates.Threads.DetectionThread import DetectionThread
from AISystem.EntranceExitGates.gates.BaseGate import BaseGate
from AISystem.model_registry import ModelRegistry
import cv2
import torch
import numpy as np
from PIL import Image
from torchvision import transforms


class AfterEntrance (BaseGate):
    def __init__(self, source, car_model_path, plate_model_path, plate_recognition_path, backend_url):
        super().__init__(source, car_model_path, plate_model_path, plate_recognition_path, backend_url)
        ModelRegistry.initialize()
        self.device = ModelRegistry.device
        self.reid_model = ModelRegistry.reid_model
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((256, 128)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
        ])

        self.start_left =  (70, 336)
        self.end_left =  (486, 123)

        self.start_right = (345, 522)
        self.end_right = (662, 165)

        self.start_trigger = (339, 215)
        self.end_trigger = (546, 322)

    def get_embedding(self, img) -> np.ndarray:
        if isinstance(img, np.ndarray):
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # BGR → RGB
        elif isinstance(img, Image.Image):
            img = np.array(img.convert("RGB"))

        transform = transforms.Compose([
            transforms.ToPILImage(),  # expects HxWxC RGB uint8
            transforms.Resize((256, 128)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
        ])

        tensor = transform(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            # ✅ Extract intermediate features, NOT classifier logits
            features = self.reid_model.featuremaps(tensor)  # spatial feature map
            features = torch.nn.functional.adaptive_avg_pool2d(features, 1)
            features = features.view(features.size(0), -1)

        emb = features.cpu().numpy().flatten()
        return emb / (np.linalg.norm(emb) + 1e-6)



    def process_results(self, frame, results):

        if results[0].boxes.id is None:
            return

        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.cpu().numpy().astype(int)

        roi_polygon = self.get_roi_polygon()

        for box, track_id in zip(boxes, track_ids):

            x1, y1, x2, y2 = map(int, box)

            cx = (x1 + x2) // 2
            cy = y2

            if cv2.pointPolygonTest(roi_polygon, (cx, cy), False) < 0:
                continue

            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

            crop = frame[y1:y2, x1:x2]
            if track_id not in self.frame_buffers:
                self.frame_buffers[track_id] = []
            self.frame_buffers[track_id].append(crop.copy())
            if len(self.frame_buffers[track_id]) > 10:
                self.frame_buffers[track_id].pop(0)

            current_position = self.is_crossing_line(
                (cx, cy),
                self.start_trigger,
                self.end_trigger
            )
            previous_position = self.previous_side.get(track_id)

            if previous_position is not None:

                if previous_position * current_position < 0:
                    if track_id not in self.processed_ids:

                        best_frame = self.get_best_frame(track_id)

                        if best_frame is not None:
                            # cv2.imwrite(f"best_frame_id_{track_id}.jpg", best_frame)
                            embeddings = self.get_embedding(best_frame)
                            print("embeddings:", embeddings)
                            self.api.send_embeddings(embeddings)
                        self.processed_ids.add(track_id)
            self.previous_side[track_id] = current_position
    def get_roi_polygon(self):

        return np.array([
            self.start_left,
            self.end_left,
            self.end_right,
            self.start_right
        ], dtype=np.int32)

    def draw_lines(self, frame):

        cv2.line(frame, self.start_left, self.end_left, (0,255,0),2)
        cv2.line(frame, self.start_right, self.end_right, (0,255,0),2)

        cv2.line(frame, self.start_trigger, self.end_trigger, (0,0,255),3)

    def run(self):

        camera = CameraThread(self)
        detection = DetectionThread(self)

        camera.start()
        detection.start()

        while self.running:

            if self.output_frame is not None:

                frame = self.output_frame.copy()

                self.draw_lines(frame)

                cv2.imshow("Embeddings Gate", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):   # pause / resume
              paused = not paused

            if key == 27:  # ESC
              self.running = False
              break

        camera.join()
        detection.join()

        cv2.destroyAllWindows()