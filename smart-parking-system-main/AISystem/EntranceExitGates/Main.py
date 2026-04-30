import sys

from AISystem.EntranceExitGates.gates.EntranceGate import EntranceGate

sys.path.append(r'D:\python_packages')



import threading

def main():

    entrance = EntranceGate(
        source="D://garage/Entrance_v1.mp4",
        car_model_path="../Models/car_detection/yolov8m.pt",
        plate_model_path="../Models/plate_detection/best.pt",
        plate_recognition_path="../Models/plate_recognition/best.pt",
        backend_url="http://127.0.0.1:8000/api/entry/"
    )

    # exit_gate = ExitGate(
    #     source="./car_clips/Exit/car_19.mp4",
    #     car_model_path="Models/car_detection/yolov8m.pt",
    #     plate_model_path="Models/plate_detection/best.pt",
    #     plate_recognition_path="Models/plate_recognition/best.pt",
    #     backend_url="http://127.0.0.1:8000/api/exit/"
    # )


    # entrance = EntranceGate(
    #     source="rtsp://admin:M.H.M&F.Y.M&9620@192.168.1.100:554/Streaming/Channels/201",
    #     car_model_path="../Models/car_detection/yolov8m.pt",
    #     plate_model_path="../Models/plate_detection/best.pt",
    #     plate_recognition_path="../Models/plate_recognition/best.pt",
    #     backend_url="http://127.0.0.1:8000/api/entry/"
    # )

    # exit_gate = ExitGate(
    #     source="rtsp://admin:M.H.M&F.Y.M&9620@192.168.1.100:554/Streaming/Channels/101",
    #     car_model_path="Models/car_detection/yolov8m.pt",
    #     plate_model_path="Models/plate_detection/best.pt",
    #     plate_recognition_path="Models/plate_recognition/best.pt",
    #       backend_url = "http://127.0.0.1:8000/api/exit/"
    # )

    entrance_thread = threading.Thread(target=entrance.run)
    # exit_thread = threading.Thread(target=exit_gate.run)

    entrance_thread.start()
    # exit_thread.start()

    entrance_thread.join()
    # exit_thread.join()


if __name__ == "__main__":
    main()