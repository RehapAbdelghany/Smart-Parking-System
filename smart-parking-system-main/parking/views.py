from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework import status

from django.http import JsonResponse
from .serializers import VehicleEntrySerializer, VehicleExitSerializer, SlotDisplaySerializer, ReservationSerializer
from .permissions import IsCameraNode, IsOwnerOrAdmin
from .models import ParkingSlot, VehicleLog, Reservation
from .pathfinding import astar, get_road_cell_next_to_slot
from .grid import GARAGE_GRID, SLOT_COORDINATES

ENTRANCE = (0, 1)   # ENTER cell
from django.db.models import Count
from django.utils import timezone
from decimal import Decimal
import uuid

# --- 1. كاميرات المداخل والمخارج (تحتاج صلاحية الكاميرا) ---

class VehicleEntryAPIView(APIView):
    permission_classes = [IsCameraNode]
    def post(self, request, *args, **kwargs):
        serializer = VehicleEntrySerializer(data=request.data)
        if serializer.is_valid():
            vehicle_log = serializer.save()
            return Response({
                "status": "success",
                "message": "Vehicle entry recorded",
                "log_id": vehicle_log.id,
                "entry_time": vehicle_log.entry_time
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VehicleExitAPIView(APIView):
    permission_classes = [IsCameraNode]
    def post(self, request):
        serializer = VehicleExitSerializer(data=request.data)
        if serializer.is_valid():
            plate = serializer.validated_data['license_plate']
            image = serializer.validated_data['exit_image']
            log = VehicleLog.objects.filter(license_plate=plate, exit_time__isnull=True).last()
            if not log:
                return Response({"error": "Vehicle not found in garage"}, status=status.HTTP_404_NOT_FOUND)

            log.exit_time = timezone.now()
            log.exit_image = image
            duration = log.exit_time - log.entry_time
            hours = Decimal(duration.total_seconds() / 3600).quantize(Decimal('1.00'))
            if hours < 1: hours = 1
            log.total_fee = hours * Decimal(25.00)
            log.is_paid = True
            log.save()
            return Response({
                "status": "success",
                "total_fee": log.total_fee
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