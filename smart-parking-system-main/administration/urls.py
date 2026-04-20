from django.urls import path
from .views import (
    AdminGarageStatsAPIView,
    AdminPaymentAnalyticsAPIView,
    AdminVehicleLogListAPIView,
    AdminSlotListCreateAPIView,
    AdminSlotDetailAPIView,
    AdminUserListAPIView,
    CreateAdminUserAPIView,
    AdminReservationListAPIView,
    admin_dashboard_view,
)

urlpatterns = [
    path('', admin_dashboard_view,),
    path('stats/', AdminGarageStatsAPIView.as_view(), name='admin-stats'),
    path('analytics/', AdminPaymentAnalyticsAPIView.as_view(), name='admin-analytics'),
    path('logs/', AdminVehicleLogListAPIView.as_view(), name='admin-logs'),
    path('slots/', AdminSlotListCreateAPIView.as_view(), name='admin-slots'),
    path('slots/<int:pk>/', AdminSlotDetailAPIView.as_view(), name='admin-slot-detail'),
    path('users/', AdminUserListAPIView.as_view(), name='admin-users'),
    path('users/create-admin/', CreateAdminUserAPIView.as_view(), name='admin-create-admin'),
    path('reservations/', AdminReservationListAPIView.as_view(), name='admin-reservations'),
]