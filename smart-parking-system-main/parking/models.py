from django.db import models
from pgvector.django import VectorField
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User

class ParkingSlot(models.Model):
    SLOT_TYPES = (
        ('regular', 'Regular'),
        ('disabled', 'Disabled'),
        ('electric', 'Electric'),
    )
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
    )

    slot_number = models.CharField(max_length=10, unique=True) # رقم المكان (مثلاً A1, A2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    slot_type = models.CharField(max_length=20, choices=SLOT_TYPES, default='regular')

    # الإحداثيات لو حابب ترسمها على خريطة في الموبايل مستقبلاً
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    floor = models.IntegerField(default=1)  # إضافة حقل الطابق



    # **إحداثيات الـ grid**
    row = models.PositiveIntegerField(help_text="Grid row index for navigation")
    col = models.PositiveIntegerField(help_text="Grid column index for navigation")

    class Meta:
        ordering = ['floor', 'row', 'col']  # ترتيب احترافي عند الاستعلام

    def __str__(self):
        return f"Slot {self.slot_number} - {self.status} (Row {self.row}, Col {self.col})"
    

class Camera(models.Model):
    camera_id = models.CharField(max_length=50, unique=True)
    zone_name = models.CharField(max_length=100)
    # إحداثيات الكاميرا في الـ Grid لتحديث نقطة بداية الـ A*
    row = models.PositiveIntegerField()
    col = models.PositiveIntegerField()

    def __str__(self):
            return f"Camera {self.camera_id} - Zone {self.zone_name}"
class VehicleLog(models.Model):
    license_plate = models.CharField(max_length=20) # رقم اللوحة اللي هيطلع من الـ ML
    
    # صور الدخول والخروج (هتتحفظ في مجلد media اللي عملناه)
    entry_image = models.ImageField(upload_to='entry_pics/%Y/%m/%d/')
    exit_image = models.ImageField(upload_to='exit_pics/%Y/%m/%d/', null=True, blank=True)
    
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    
    # الربط مع المكان اللي ركنت فيه
    slot = models.ForeignKey(ParkingSlot, on_delete=models.SET_NULL, null=True)
    
    total_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    is_paid = models.BooleanField(default=False)

    # حقل الـ Embedding الاحترافي (128 أو 512 هو الطول الشائع لنماذج الـ Re-ID)
    # نستخدم VectorField من pgvector للبحث السريع
    # car_embedding = VectorField(dimensions=128, null=True, blank=True)
    car_embedding = models.JSONField(null=True, blank=True)
    # تخزين لون السيارة كفلتر إضافي (Metadata)
    car_color = models.CharField(max_length=30, null=True, blank=True)
    # ربط السيارة بآخر كاميرا رصدتها (التتبع اللحظي)
    last_camera = models.ForeignKey(Camera, on_delete=models.SET_NULL, null=True, blank=True)
    # هل السيارة حالياً داخل الموقف؟ (لتحسين سرعة البحث)
    is_inside = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            # إنشاء فحص (Index) لنوع البحث عن المتجهات (HNSW أو IVFFLAT) لتحقيق سرعة خارقة
            models.Index(fields=['is_inside', 'last_seen']),
        ]
    def __str__(self):
        return f"{self.license_plate} - {self.entry_time.strftime('%Y-%m-%d %H:%M')}"

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    license_plate = models.CharField(max_length=20, verbose_name="رقم اللوحة")
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE)
    reservation_code = models.CharField(max_length=10, unique=True) # كود يكتبه عند الدخول
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Res {self.reservation_code} for {self.user.username}"
