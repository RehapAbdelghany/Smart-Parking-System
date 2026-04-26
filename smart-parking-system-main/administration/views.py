from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDay, TruncMonth, TruncHour
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from parking.models import ParkingSlot, VehicleLog, Reservation
from .serializers import (
    AdminVehicleLogSerializer,
    AdminSlotSerializer,
    AdminUserSerializer,
    CreateAdminSerializer,
    AdminReservationSerializer,
)
from .permissions import IsAdminUser, IsSuperAdmin


# ─────────────────────────────────────────────
# 1. GARAGE LIVE STATS
# GET /api/admin/stats/
# ─────────────────────────────────────────────
class AdminGarageStatsAPIView(APIView):
    """
    Returns a full live snapshot of the garage:
    - Slot capacity breakdown
    - Cars currently inside
    - Today's revenue and car count
    - Occupancy rate
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = timezone.now().date()

        # Slot counts
        total      = ParkingSlot.objects.count()
        available  = ParkingSlot.objects.filter(status='available').count()
        occupied   = ParkingSlot.objects.filter(status='occupied').count()
        reserved   = ParkingSlot.objects.filter(status='reserved').count()
        occupancy  = round((occupied / total) * 100, 1) if total else 0

        # Cars currently inside (entered but not exited)
        inside_now = VehicleLog.objects.filter(exit_time__isnull=True).count()

        # Today stats
        today_logs    = VehicleLog.objects.filter(entry_time__date=today)
        cars_today    = today_logs.count()
        today_revenue = today_logs.filter(is_paid=True).aggregate(
            total=Sum('total_fee')
        )['total'] or Decimal('0.00')

        # All time revenue
        total_revenue = VehicleLog.objects.filter(is_paid=True).aggregate(
            total=Sum('total_fee')
        )['total'] or Decimal('0.00')

        return Response({
            "capacity": {
                "total_slots": total,
                "available":   available,
                "occupied":    occupied,
                "reserved":    reserved,
                "occupancy_rate": f"{occupancy}%",
            },
            "live": {
                "cars_inside_now": inside_now,
            },
            "today": {
                "date":           str(today),
                "cars_entered":   cars_today,
                "revenue":        float(today_revenue),
            },
            "all_time": {
                "total_revenue": float(total_revenue),
            }
        })


# ─────────────────────────────────────────────
# 2. PAYMENT ANALYTICS
# GET /api/admin/analytics/
# Query params:
#   ?range=7     → last 7 days (default)
#   ?range=30    → last 30 days
#   ?range=365   → last year
# ─────────────────────────────────────────────
class AdminPaymentAnalyticsAPIView(APIView):
    """
    Returns revenue analytics designed for a SAME-DAY garage.
    Cars always enter and exit within the same day — no overnight stays.

    Default view → daily stats for last N days + today's hourly breakdown + peak hours.
    Optional ?view=monthly → monthly totals (for future multi-day garage upgrade).

    Query params:
        ?range=7        → last 7 days (default)
        ?range=30       → last 30 days
        ?view=monthly   → switch to monthly breakdown (future upgrade mode)
    """
    permission_classes = [IsAdminUser]

    # ── business rule: flag any session longer than this as abnormal ──
    MAX_NORMAL_SESSION_HOURS = 24

    def get(self, request):
        try:
            days = int(request.query_params.get('range', 7))
        except ValueError:
            days = 7

        view_mode = request.query_params.get('view', 'daily')  # 'daily' or 'monthly'
        since     = timezone.now() - timedelta(days=days)
        today     = timezone.now().date()
        paid_logs = VehicleLog.objects.filter(is_paid=True)

        # ── Today's hourly revenue breakdown ──────────────────────────
        # Most useful for a same-day garage — shows revenue hour by hour today
        today_hourly = (
            paid_logs
            .filter(exit_time__date=today)
            .annotate(hour=TruncHour('exit_time'))
            .values('hour')
            .annotate(
                revenue=Sum('total_fee'),
                cars=Count('id'),
            )
            .order_by('hour')
        )

        # ── Daily revenue breakdown for last N days ───────────────────
        daily = (
            paid_logs
            .filter(exit_time__date__gte=since.date())
            .annotate(day=TruncDay('exit_time'))
            .values('day')
            .annotate(
                revenue=Sum('total_fee'),
                cars=Count('id'),
            )
            .order_by('day')
        )

        # ── Peak entry hours (busiest hours in the garage) ────────────
        peak_hours = (
            VehicleLog.objects
            .filter(entry_time__gte=since)
            .annotate(hour=TruncHour('entry_time'))
            .values('hour')
            .annotate(cars=Count('id'))
            .order_by('-cars')[:5]
        )

        # ── Average session fee ───────────────────────────────────────
        avg_fee = paid_logs.aggregate(avg=Avg('total_fee'))['avg'] or 0

        # ── Unpaid completed sessions ─────────────────────────────────
        unpaid_count = VehicleLog.objects.filter(
            is_paid=False,
            exit_time__isnull=False
        ).count()

        # ── Abnormal sessions: stayed longer than MAX_NORMAL_SESSION_HOURS
        # These are data issues or edge cases in a same-day garage
        abnormal_sessions = VehicleLog.objects.filter(
            exit_time__isnull=False
        ).extra(
            where=["EXTRACT(EPOCH FROM (exit_time - entry_time))/3600 > %s"],
            params=[self.MAX_NORMAL_SESSION_HOURS]
        ).values('id', 'license_plate', 'entry_time', 'exit_time', 'total_fee')

        # ── Build response ────────────────────────────────────────────
        response_data = {
            "garage_type":   "same_day",   # flag so frontend knows the mode
            "range_days":    days,
            "average_fee_per_session":      round(float(avg_fee), 2),
            "unpaid_completed_sessions":    unpaid_count,
            "abnormal_sessions_count":      abnormal_sessions.count(),
            "abnormal_sessions":            list(abnormal_sessions),
            "today_hourly_breakdown":       list(today_hourly),
            "daily_breakdown":              list(daily),
            "peak_entry_hours":             list(peak_hours),
        }

        # ── Monthly view: only shown when explicitly requested ────────
        # Kept here for future upgrade to multi-day/monthly garage
        if view_mode == 'monthly':
            monthly = (
                paid_logs
                .annotate(month=TruncMonth('exit_time'))
                .values('month')
                .annotate(
                    revenue=Sum('total_fee'),
                    cars=Count('id'),
                )
                .order_by('-month')[:6]
            )
            response_data['monthly_breakdown'] = list(monthly)
            response_data['note'] = (
                "Monthly view is available for future multi-day garage upgrade. "
                "This garage currently operates on a same-day basis."
            )

        return Response(response_data)


# ─────────────────────────────────────────────
# 3. VEHICLE LOG LIST (with entry/exit photos)
# GET /api/admin/logs/
# Query params:
#   ?date=2026-03-08
#   ?plate=ABC123
#   ?status=inside   → still in garage
#   ?status=exited   → already left
# ─────────────────────────────────────────────
class AdminVehicleLogListAPIView(ListAPIView):
    """
    Full paginated list of all vehicle logs for admin review.
    Shows entry photos, exit photos, fees, and duration.
    """
    permission_classes = [IsAdminUser]
    serializer_class = AdminVehicleLogSerializer

    def get_queryset(self):
        qs = VehicleLog.objects.select_related('slot').order_by('-entry_time')

        # Filter by date
        date = self.request.query_params.get('date')
        if date:
            qs = qs.filter(entry_time__date=date)

        # Filter by license plate
        plate = self.request.query_params.get('plate')
        if plate:
            qs = qs.filter(license_plate__icontains=plate)

        # Filter by inside/exited status
        log_status = self.request.query_params.get('status')
        if log_status == 'inside':
            qs = qs.filter(exit_time__isnull=True)
        elif log_status == 'exited':
            qs = qs.filter(exit_time__isnull=False)

        return qs

    def get_serializer_context(self):
        # Pass request to serializer so image URLs are absolute
        return {'request': self.request}


# ─────────────────────────────────────────────
# 4. SLOT MANAGEMENT
# GET  /api/admin/slots/          → list all slots
# POST /api/admin/slots/          → create a new slot
# ─────────────────────────────────────────────
class AdminSlotListCreateAPIView(APIView):
    """
    Admin can view all slots or add new ones manually.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        slots = ParkingSlot.objects.all().order_by('slot_number')
        
        # Optional filter
        status_param = request.query_params.get('status')
        if status_param:
            slots = slots.filter(status=status_param)

        serializer = AdminSlotSerializer(slots, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AdminSlotSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────
# 5. SLOT DETAIL (edit/delete a single slot)
# GET    /api/admin/slots/<id>/
# PATCH  /api/admin/slots/<id>/
# DELETE /api/admin/slots/<id>/
# ─────────────────────────────────────────────
class AdminSlotDetailAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get_object(self, pk):
        try:
            return ParkingSlot.objects.get(pk=pk)
        except ParkingSlot.DoesNotExist:
            return None

    def get(self, request, pk):
        slot = self.get_object(pk)
        if not slot:
            return Response({"error": "Slot not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminSlotSerializer(slot).data)

    def patch(self, request, pk):
        slot = self.get_object(pk)
        if not slot:
            return Response({"error": "Slot not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminSlotSerializer(slot, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        slot = self.get_object(pk)
        if not slot:
            return Response({"error": "Slot not found."}, status=status.HTTP_404_NOT_FOUND)
        slot.delete()
        return Response({"message": "Slot deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────
# 6. USER MANAGEMENT
# GET /api/admin/users/   → list all users
# ─────────────────────────────────────────────
class AdminUserListAPIView(ListAPIView):
    """
    Admin can view all registered users.
    """
    permission_classes = [IsAdminUser]
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        qs = User.objects.all().order_by('-date_joined')

        # Filter by admin status
        is_staff = self.request.query_params.get('is_staff')
        if is_staff == 'true':
            qs = qs.filter(is_staff=True)
        elif is_staff == 'false':
            qs = qs.filter(is_staff=False)

        return qs


# ─────────────────────────────────────────────
# 7. CREATE ADMIN USER
# POST /api/admin/users/create-admin/
# Only superusers can create other admins
# ─────────────────────────────────────────────
class CreateAdminUserAPIView(APIView):
    """
    Only a superuser can create another admin account.
    """
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        serializer = CreateAdminSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Admin account created successfully.",
                "user": AdminUserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────
# 8. RESERVATIONS LIST
# GET /api/admin/reservations/
# ─────────────────────────────────────────────
class AdminReservationListAPIView(ListAPIView):
    """
    Admin view of all reservations with user and slot info.
    """
    permission_classes = [IsAdminUser]
    serializer_class = AdminReservationSerializer

    def get_queryset(self):
        qs = Reservation.objects.select_related('user', 'slot').order_by('-created_at')

        is_active = self.request.query_params.get('is_active')
        if is_active == 'true':
            qs = qs.filter(is_active=True)
        elif is_active == 'false':
            qs = qs.filter(is_active=False)

        return qs


@login_required
@ensure_csrf_cookie  
def admin_dashboard_view(request):
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Admins only.")
    return render(request, 'administration/dashboard.html')