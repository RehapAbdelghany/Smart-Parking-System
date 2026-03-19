import requests
import json

URL_TRACKING = "http://127.0.0.1:8000/api/tracking/" # تأكد من المسار في urls.py
HEADERS = {'X-Camera-Key': 'my_ultra_secure_camera_token_2026'}

def test_tracking(description, embedding, cam_id, color):
    print(f"\n--- Testing: {description} ---")
    data = {
        "car_embedding": embedding,
        "camera_id": cam_id,
        "car_color": color
    }
    
    response = requests.post(URL_TRACKING, json=data, headers=HEADERS)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    # ملاحظة: القيم هنا افتراضية، يفضل استخدام أرقام قريبة من التي خزنها الـ Entry
    
    # الحالة 1: تطابق تام (نفس الأرقام اللي بعتناها في الدخول)
    perfect_match = [0.1, 0.2, 0.3, 0.4, 0.5]
    test_tracking("Perfect Match (Identical Embedding)", perfect_match, "CAM-02", "Black")

    # الحالة 2: تطابق قريب (تغيير بسيط في الأرقام - محاكاة للواقع)
    close_match = [0.12, 0.18, 0.31, 0.39, 0.52]
    test_tracking("Close Match (Simulated Real Camera)", close_match, "CAM-03", "Black")

    # الحالة 3: لون مختلف (حتى لو البصمة قريبة، الفلتر هيمنعه)
    test_tracking("Wrong Color Filter", perfect_match, "CAM-04", "Red")

    # الحالة 4: بصمة غريبة تماماً (سيارة لم تدخل)
    stranger_car = [0.9, 0.8, 0.7, 0.1, 0.2]
    test_tracking("Stranger Car (No Match)", stranger_car, "CAM-04 ", "White")