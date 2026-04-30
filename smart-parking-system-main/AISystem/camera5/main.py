import threading

from AISystem.camera5.embeddings import AfterEntrance


def main():

    camera = AfterEntrance(
        source="D05.mp4",
        car_model_path="../Models/car_detection/yolov8m.pt",
        plate_model_path="../Models/plate_detection/best.pt",
        plate_recognition_path="../Models/plate_recognition/best.pt",
        backend_url="http://127.0.0.1:8000/api/update-perspective/",
    )
    # AISystem = AfterEntrance(
    #     source="rtsp://admin:M.H.M&F.Y.M&9620@192.168.1.100:554/Streaming/Channels/401",
    #     car_model_path="../Models/car_detection/yolov8m.pt",
    #     plate_model_path="../Models/plate_detection/best.pt",
    #     plate_recognition_path="../Models/plate_recognition/best.pt",
    #     backend_url="http://127.0.0.1:8000/api/update-perspective/"
    # )
    entrance_thread = threading.Thread(target=camera.run)
    entrance_thread.start()
    entrance_thread.join()
if __name__ == "__main__":
    main()