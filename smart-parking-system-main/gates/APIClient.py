import cv2
import requests

class APIClient:

    def __init__(self, base_url):
        self.base_url = base_url
        self.HEADERS = {'X-Camera-Key': 'my_ultra_secure_camera_token_2026'}

    def send_to_backend(self, image, plate_text):

        # convert frame to jpeg
        if image is None:
            print("No image to send")
            return
        _, img_encoded = cv2.imencode('.jpg', image)
        if self.base_url.endswith("/entry/"):
          files = {
            "entry_image": ("image.jpg", img_encoded.tobytes(), "image/jpeg")
          }
        elif self.base_url.endswith("/exit/"):
          files = {
            "exit_image": ("image.jpg", img_encoded.tobytes(), "image/jpeg")
          }
        data = {
            "license_plate": plate_text,
            "camera_id": 1
        }

        response = requests.post(
            self.base_url,
            files=files,
            data=data,
            headers=self.HEADERS
        )

        if response.status_code == 201 or response.status_code == 200:
            print("✅ Sent to backend successfully")
        else:
            print("❌ Backend error:", response.text)