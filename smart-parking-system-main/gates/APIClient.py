import cv2
import numpy as np
import requests
import torchvision.models as models
from torchvision import transforms
import torch

from gates.CarDetails import CarDetails


class APIClient:

    def __init__(self, base_url):
        self.base_url = base_url
        self.HEADERS = {'X-Camera-Key': 'my_ultra_secure_camera_token_2026'}
    def send_to_entrance(self,image, plate_text):
        success, img_encoded = cv2.imencode(".jpg", image)
        if not success:
            print("❌ Failed to encode image")
            return
        car_details = CarDetails(image)
        color, embeddings = car_details.get_car_details()

        files = {}

        data = {
            "license_plate": plate_text,
            "car_embedding": embeddings,
            "car_color": color,
            "camera_id": 1
        }
        files["entry_image"] = (
            "image.jpg",
            img_encoded.tobytes(),
            "image/jpeg"
        )
        try:
            print(data)
            response = requests.post(
                self.base_url,
                files=files,
                data=data,
                headers=self.HEADERS
            )

            if response.status_code in (200, 201):
                print("✅ Sent to backend successfully")
            else:
                print("❌ Backend error:", response.text)


        except requests.exceptions.RequestException as e:
            print("❌ Request failed:", str(e))
    def end_to_exit(self,image, plate_text):
        success, img_encoded = cv2.imencode(".jpg", image)
        if not success:
            print("❌ Failed to encode image")
            return
        data = {
            "license_plate": plate_text,
            "camera_id": 2
        }
        files = {"exit_image": (
            "image.jpg",
            img_encoded.tobytes(),
            "image/jpeg"
        )}
        try:
            print(data)
            response = requests.post(
                self.base_url,
                files=files,
                data=data,
                headers=self.HEADERS
            )

            if response.status_code in (200, 201):
                print("✅ Sent to backend successfully")
            else:
                print("❌ Backend error:", response.text)


        except requests.exceptions.RequestException as e:
            print("❌ Request failed:", str(e))

    def send_to_backend(self, image, plate_text):
        if image is None:
            print("No image to send")
            return

        if self.base_url.endswith("/entry/"):
            self.send_to_entrance(image,plate_text)

        # Handle exit camera
        elif self.base_url.endswith("/exit/"):
            self.end_to_exit(image,plate_text)




