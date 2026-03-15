import requests

# الكود السري اللي حطيناه في الـ .env
SECRET_KEY = "my_ultra_secure_camera_token_2026"
HEADERS = {'X-Camera-Key': SECRET_KEY}

URL_ENTRY = "http://127.0.0.1:8000/api/entry/"
URL_EXIT = "http://127.0.0.1:8000/api/exit/"
URL_SLOTS = "http://127.0.0.1:8000/api/slots/update/"



def simulate_camera_entry(image_path, plate_number):
    with open(image_path, 'rb') as img:
        data = {"license_plate": plate_number}
        files = {"entry_image": img}
        # إضافة الـ Headers للأمان
        response = requests.post(URL_ENTRY, data=data, files=files, headers=HEADERS)
        print("Entry Status:", response.status_code, response.json())

def simulate_camera_exit(image_path, plate_number):
    with open(image_path, 'rb') as img:
        data = {"license_plate": plate_number}
        files = {"exit_image": img}
        # إضافة الـ Headers للأمان
        response = requests.post(URL_EXIT, data=data, files=files, headers=HEADERS)
        print("Exit Status:", response.status_code, response.json())

def simulate_slots_camera(camera_slots_data):
    # إضافة الـ Headers للأمان (لاحظ بنستخدم json= في الـ POST)
    response = requests.post(URL_SLOTS, json=camera_slots_data, headers=HEADERS)
    print("Slots Update Status:", response.status_code, response.json())

if __name__ == "__main__":
    # الآن الطلبات ستمر عبر الـ Permission بنجاح
    simulate_camera_entry(r"camera test\car.jpg", "Cairo 123")
    simulate_camera_exit(r"camera test\car_exit.jpg", "Cairo 123")
    # simulate_slots_camera([
    #     {"slot_id": "1", "is_occupied": True},
    #     {"slot_id": "3", "is_occupied": True},
    #     {"slot_id": "2", "is_occupied": False},
    # ])