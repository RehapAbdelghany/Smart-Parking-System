
import cv2

from Threads.CameraThread import CameraThread
from Threads.DetectionThread import DetectionThread
from gates.BaseGate import BaseGate

import numpy as np
class EntranceGate(BaseGate):

    def __init__(self, source, car_model_path,plate_model_path,plate_recognition_path , backend_url=None):

        super().__init__(source, car_model_path,plate_model_path,plate_recognition_path, backend_url)


        self.start_left = (3, 334)
        self.end_left = (605, 137)

        self.start_right = (847, 497)
        self.end_right = (873, 137)

        self.start_trigger = (117, 321)
        self.end_trigger = (837, 416)

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

            #     cv2.imshow("Entrance Gate", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):   # pause / resume
              paused = not paused

            if key == 27:  # ESC
              self.running = False
              break

        camera.join()
        detection.join()

        cv2.destroyAllWindows()