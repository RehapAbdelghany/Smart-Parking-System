from AISystem.tracknav.SingleCameraEngine import SingleCameraEngine


class MultiCameraEngine:
    def __init__(self, model_path, num_cams, cameraIds):
        self.engines = {}

        for cam_id in range(num_cams):
            engine = SingleCameraEngine(cameraIds[cam_id], model_path)
            engine.start()
            self.engines[cameraIds[cam_id]] = engine

    def submit_frame(self, cam_id, frame):
        self.engines[cam_id].submit_frame(frame)

    def get_result(self, cam_id):
        return self.engines[cam_id].get_result()