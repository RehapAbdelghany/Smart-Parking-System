import threading
import cv2


class DetectionThread(threading.Thread):

    def __init__(self, gate):
        super().__init__()
        self.gate = gate

    def run(self):

        while self.gate.running:

            frame = self.gate.frame

            if frame is None:
                continue

            frame = frame.copy()

            results = self.gate.car_model.track(
                frame,
                persist=True,
                classes=[2],
                conf=0.5,
                verbose=False
            )

            self.gate.process_results(frame, results)

            self.gate.output_frame = frame