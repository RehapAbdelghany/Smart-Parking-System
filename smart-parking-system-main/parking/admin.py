from django.contrib import admin
from .models import ParkingSlot, VehicleLog, Reservation, Camera 

@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    # إظهار الأعمدة في القائمة
    list_display = ('slot_number', 'status', 'slot_type')
    # إضافة فلتر بالجنب
    list_filter = ('status', 'slot_type')
    # البحث برقم المكان
    search_fields = ('slot_number',)

@admin.register(VehicleLog)
class VehicleLogAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'entry_time', 'exit_time', 'is_paid')
    # ترتيب السجلات: الأحدث يظهر فوق
    ordering = ('-entry_time',)
    # البحث برقم اللوحة
    search_fields = ('license_plate',)

admin.site.register(Camera)
admin.site.register(Reservation)