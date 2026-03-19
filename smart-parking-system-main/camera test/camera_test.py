import requests

# الكود السري اللي حطيناه في الـ .env
SECRET_KEY = "my_ultra_secure_camera_token_2026"
HEADERS = {'X-Camera-Key': SECRET_KEY}

URL_ENTRY = "http://127.0.0.1:8000/api/entry/"
URL_EXIT = "http://127.0.0.1:8000/api/exit/"
URL_SLOTS = "http://127.0.0.1:8000/api/slots/update/"


def simulate_camera_entry(image_path, plate_number):
    with open(image_path, 'rb') as img:
        # 1. تجهيز البيانات النصية والـ Embedding (بصمة تجريبية)
        data = {
            "license_plate": plate_number,
            "car_color": "Black",  # اختياري
            "car_embedding": [0.1, 0.2, 0.3, 0.4, 0.5] # بصمة وهمية للتجربة
        }
        
        # 2. إرسال الصورة كملف (files) والبيانات كـ (data)
        files = {"entry_image": img}
        
        # 3. إرسال الطلب مع الـ Headers
        response = requests.post(URL_ENTRY, data=data, files=files, headers=HEADERS)
        
        # طباعة النتيجة بشكل أوضح
        print(f"--- Testing Entry for {plate_number} ---")
        print("Status Code:", response.status_code)
        try:
            print("Response:", response.json())
        except:
            print("Raw Response:", response.text)

def simulate_camera_exit(image_path, plate_number):
    try:
        with open(image_path, 'rb') as img:
            # البيانات المطلوبة للـ Serializer
            data = {"license_plate": plate_number}
            files = {"exit_image": img}
            
            print(f"\n--- جاري تسجيل خروج السيارة: {plate_number} ---")
            
            # إرسال الطلب
            response = requests.post(URL_EXIT, data=data, files=files, headers=HEADERS)
            
            print("Exit Status:", response.status_code)
            
            if response.status_code == 200:
                res_data = response.json()
                summary = res_data.get('summary', {})
                print("✅ تم الخروج بنجاح!")
                print(f"⏱️ وقت الدخول: {summary.get('entry_time')}")
                print(f"🕒 وقت الخروج: {summary.get('exit_time')}")
                print(f"⏳ المدة المحسوبة: {summary.get('duration_hours')} ساعة")
                print(f"💰 إجمالي الرسوم: {summary.get('total_fee')} ج.م")
            else:
                # طباعة الخطأ لو العربية مش موجودة أو فيه مشكلة
                print("❌ فشل الخروج:", response.json())
                
    except FileNotFoundError:
        print(f"❌ خطأ: لم يتم العثور على ملف الصورة في المسار: {image_path}")

def simulate_slots_camera(camera_slots_data):
    # إضافة الـ Headers للأمان (لاحظ بنستخدم json= في الـ POST)
    response = requests.post(URL_SLOTS, json=camera_slots_data, headers=HEADERS)
    print("Slots Update Status:", response.status_code, response.json())

if __name__ == "__main__":
    # الآن الطلبات ستمر عبر الـ Permission بنجاح
    simulate_camera_entry(r"car.jpg", "ABG-123")
    # simulate_camera_exit(r"camera test\car_exit.jpg", "Cairo 123")
    # simulate_slots_camera([
    #     {"slot_id": "1", "is_occupied": True},
    #     {"slot_id": "3", "is_occupied": True},
    #     {"slot_id": "2", "is_occupied": False},
    # ])