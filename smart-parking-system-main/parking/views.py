from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework import status

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Count
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from .serializers import VehicleEntrySerializer, VehicleExitSerializer, SlotDisplaySerializer, ReservationSerializer, VehicleTrackSerializer, SlotStatusUpdateSerializer
from .models import ParkingSlot, VehicleLog, Reservation,Camera
from .pathfinding import astar, get_road_cell_next_to_slot
from .permissions import IsCameraNode, IsOwnerOrAdmin
from .grid import GARAGE_GRID, SLOT_COORDINATES

import uuid
import numpy as np
ENTRANCE = (0, 1)   # ENTER cell

class VehicleEntryAPIView(APIView):
    permission_classes = [IsCameraNode]
    
    def post(self, request, *args, **kwargs):
        serializer = VehicleEntrySerializer(data=request.data)
        
        if serializer.is_valid():
            v_data = serializer.validated_data
            plate = v_data['license_plate']
            
            # --- 1. التحقق من الدخول المزدوج (Double Entry Check) ---
            # إذا كانت السيارة مسجلة أنها بالداخل بالفعل، نحدث بياناتها ولا ننشئ سجلاً جديداً
            existing_log = VehicleLog.objects.filter(license_plate=plate, is_inside=True).first()
            if existing_log:
                return Response({
                    "status": "warning",
                    "message": "السيارة مسجلة بالداخل بالفعل (دخول مزدوج)",
                    "log_id": existing_log.id
                }, status=200)

            # --- 2. البحث عن حجز نشط (Reservation Check) ---
            now = timezone.now()
            reservation = Reservation.objects.filter(
                license_plate=plate,
                is_active=True,
                start_time__lte=now,
                end_time__gte=now
            ).select_related('slot').first()

            target_slot = None
            
            # استخدام Atomic Transaction لضمان سلامة البيانات عند تغيير حالة الـ Slot
            with transaction.atomic():
                if reservation:
                    target_slot = reservation.slot
                    identified_user = reservation.user.username
                else:
                    # --- 3. التعامل مع الزوار (Guest Allocation) ---
                    # اختيار أول مكان متاح (Available) وتخصيصه فوراً
                    target_slot = ParkingSlot.objects.filter(status='available').first()
                    identified_user = "Guest"

                # 4. تحديث حالة المكان المحجوز/المخصص
                if target_slot:
                    target_slot.status = 'occupied' # أو reserved مؤقتاً
                    target_slot.save()

                # 5. حفظ سجل الدخول
                vehicle_log = VehicleLog.objects.create(
                    license_plate=plate,
                    entry_image=v_data.get('entry_image'),
                    car_embedding=v_data['car_embedding'],
                    car_color=v_data.get('car_color', 'unknown'),
                    is_inside=True,
                    slot=target_slot,
                    last_camera_id=1
                )

            return Response({
                "status": "success",
                "log_id": vehicle_log.id,
                "identified_user": identified_user,
                "target_slot": target_slot.slot_number if target_slot else "No Slots Available",
                "message": "تم تسجيل الدخول وتخصيص مكان"
            }, status=201)
            
        return Response(serializer.errors, status=400)

class VehicleExitAPIView(APIView):
    """
    إغلاق سجل السيارة وحساب التكلفة عند بوابة الخروج.
    ملاحظة: الماشين هي المسؤولة عن تحديث حالة الـ Slot إلى available 
    عبر BulkSlotUpdateAPIView، لذا لن نقوم بتغيير حالة السلوت هنا يدوياً.
    """
    permission_classes = [IsCameraNode]

    def post(self, request):
        serializer = VehicleExitSerializer(data=request.data)
        if serializer.is_valid():
            plate = serializer.validated_data['license_plate']
            image = serializer.validated_data.get('exit_image')

            # البحث عن آخر سجل دخول للسيارة لم يغلق بعد
            # الفلتر بـ is_inside=True يضمن أننا نتعامل مع سيارة موجودة فعلياً
            log = VehicleLog.objects.filter(
                license_plate=plate, 
                is_inside=True
            ).select_related('slot').last()

            if not log:
                return Response({
                    "error": "Vehicle not found in garage or already exited"
                }, status=status.HTTP_404_NOT_FOUND)

            with transaction.atomic():
                now = timezone.now()
                log.exit_time = now
                log.exit_image = image
                log.is_inside = False  # إخراج السيارة من نظام التتبع فوراً
                
                # حساب الساعات بطريقة احترافية (أي جزء من الساعة = ساعة كاملة)
                duration = now - log.entry_time
                hours = math.ceil(duration.total_seconds() / 3600)
                if hours < 1: hours = 1
                
                # حساب التكلفة (25 جنيهاً للساعة)
                log.total_fee = Decimal(hours) * Decimal(25.00)
                log.is_paid = True 
                log.save()

                # --- خطوة إضافية احترافية ---
                # إنهاء أي حجز نشط لهذه اللوحة لضمان نظافة البيانات
                Reservation.objects.filter(
                    license_plate=plate, 
                    is_active=True
                ).update(is_active=False)

            return Response({
                "status": "success",
                "message": "Vehicle exit recorded successfully",
                "summary": {
                    "plate": plate,
                    "entry_time": log.entry_time.strftime('%Y-%m-%d %H:%M'),
                    "exit_time": log.exit_time.strftime('%Y-%m-%d %H:%M'),
                    "duration_hours": hours,
                    "total_fee": float(log.total_fee)
                }
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# --- 2. تحديث الحالات من كاميرات الـ Slots ---

class BulkSlotUpdateAPIView(APIView):
    permission_classes = [IsCameraNode]
    def post(self, request):
        data = request.data
        if not isinstance(data, list):
            return Response({"error": "Expected a list of slots"}, status=400)
        updated_slots = []
        for item in data:
            slot_no = item.get('slot_id')
            occupied = item.get('is_occupied')
            new_status = 'occupied' if occupied else 'available'
            # لا نحدث الحالة لو كانت محجوزة يدوياً إلا لو ركنت فعلاً
            count = ParkingSlot.objects.filter(slot_number=slot_no).exclude(status='reserved').update(status=new_status)
            if count > 0:
                updated_slots.append(slot_no)
        return Response({"status": "success", "updated_slots": updated_slots})

# --- 3. الـ APIs الخاصة بتطبيق الموبايل (التعديل هنا) ---

class ParkingStatusAPIView(APIView):
    """
    تم تغيير الصلاحية من IsAdminUser لـ IsAuthenticated
    ليتمكن المستخدم العادي من رؤية ملخص الجراج في التطبيق.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = ParkingSlot.objects.values('status').annotate(total=Count('status'))
        summary = {
            "total_slots": ParkingSlot.objects.count(),
            "available": 0, "occupied": 0, "reserved": 0
        }
        for item in stats:
            if item['status'] in summary:
                summary[item['status']] = item['total']
        return Response(summary)

class ParkingSlotListAPIView(ListAPIView):
    """
    عرض قائمة الركنات للمستخدمين المسجلين.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SlotDisplaySerializer

    def get_queryset(self):
        queryset = ParkingSlot.objects.all().order_by('slot_number')
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

class CreateReservationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = ReservationSerializer(data=request.data)
        if serializer.is_valid():
            slot = serializer.validated_data['slot']
            if slot.status != 'available':
                return Response({"error": "Slot is not available"}, status=400)

            reservation = serializer.save(
                user=request.user,
                reservation_code=str(uuid.uuid4())[:8].upper()
            )
            slot.status = 'reserved'
            slot.save()
            return Response({
                "message": "Reservation successful",
                "code": reservation.reservation_code,
                "slot": slot.slot_number
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def navigation_view(request, slot_number: str):

    slot_number = slot_number.upper().strip()

    # ── 1. Validate slot exists ───────────────────────────────
    if slot_number not in SLOT_COORDINATES:
        return JsonResponse(
            {"error": f"Slot '{slot_number}' not found."},
            status=404
        )

    slot_row, slot_col = SLOT_COORDINATES[slot_number]

    # ── 2. Find the road cell next to this slot ───────────────
    road_stop = get_road_cell_next_to_slot(slot_row, slot_col)

    if road_stop is None:
        return JsonResponse(
            {"error": f"No accessible road cell next to '{slot_number}'."},
            status=500
        )

    # ── 3. Run A* on road cells only ─────────────────────────
    path = astar(ENTRANCE, road_stop)

    if not path:
        return JsonResponse(
            {"error": f"No path found to '{slot_number}'."},
            status=400
        )

    # ── 4. Return response ────────────────────────────────────
    return JsonResponse({
        "slot_number"  : slot_number,
        "entrance"     : {"row": ENTRANCE[0],   "col": ENTRANCE[1]},
        "road_stop"    : {"row": road_stop[0],  "col": road_stop[1]},
        "destination"  : {"row": slot_row,      "col": slot_col},
        "total_steps"  : len(path),
        "path"         : [
            {"row": r, "col": c} for r, c in path
        ],
    })


class VehicleTrackingAPIView(APIView):
    """
    تتبع السيارة عبر الكاميرات الداخلية باستخدام مقارنة البصمات (Embeddings) في الذاكرة.
    بدون استخدام pgvector.
    """
    permission_classes = [IsCameraNode]

    def post(self, request, *args, **kwargs):
        serializer = VehicleTrackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        v_data = serializer.validated_data
        incoming_embedding = np.array(v_data['car_embedding'])
        camera_id = v_data['camera_id']
        color_hint = v_data.get('car_color')

        # 1. فلترة ذكية لتقليل حجم البيانات المسحوبة (Optimization)
        # نسحب فقط السيارات اللي "بالداخل" حالياً
        queryset = VehicleLog.objects.filter(is_inside=True)
        
        # إذا كان اللون معروفاً، نستخدمه لتقليص دائرة البحث (Heuristic filtering)
        if color_hint and color_hint != 'unknown':
            queryset = queryset.filter(car_color=color_hint)

        # نسحب فقط الحقول الضرورية لتوفير الذاكرة
        logs = queryset.only('id', 'license_plate', 'car_embedding')

        if not logs.exists():
            return Response({"status": "unknown", "message": "No active vehicles match the criteria"}, status=404)

        # 2. عملية البحث عن أقرب تطابق (Similarity Search in Memory)
        best_match = None
        min_distance = float('inf')
        SIMILARITY_THRESHOLD = 0.6  # المسافة الإقليدية: كلما قل الرقم زاد التشابه

        for log in logs:
            # تحويل البصمة المخزنة في الداتابيز لمصفوفة Numpy
            existing_embedding = np.array(log.car_embedding)
            
            # حساب المسافة الإقليدية (Euclidean Distance)
            distance = np.linalg.norm(incoming_embedding - existing_embedding)

            if distance < min_distance:
                min_distance = distance
                best_match = log

        # 3. التحقق من عتبة الثقة (Thresholding)
        if best_match and min_distance <= SIMILARITY_THRESHOLD:
            # تحديث موقع السيارة في الداتابيز
            camera = get_object_or_404(Camera, camera_id=camera_id)
            best_match.last_camera = camera
            best_match.save(update_fields=['last_camera']) # تحديث حقل واحد فقط للسرعة

            return Response({
                "status": "success",
                "identified_plate": best_match.license_plate,
                "confidence_score": round(float(min_distance), 3),
                "current_zone": camera.zone_name,
                "message": f"Vehicle {best_match.license_plate} tracked at {camera.zone_name}"
            }, status=200)

        # 4. حالة الفشل في التعرف (Unknown Vehicle)
        return Response({
            "status": "unknown",
            "message": "Vehicle detected but could not be identified with high confidence"
        }, status=404)
    
