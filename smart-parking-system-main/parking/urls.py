from django.urls import path
from .views import (
    VehicleEntryAPIView, navigation_view,
    VehicleExitAPIView, BulkSlotUpdateAPIView,
    ParkingStatusAPIView, ParkingSlotListAPIView,
    CreateReservationAPIView, VehicleTrackingAPIView,
    UserCurrentLocationAPIView, UserReservationsAPIView,
    CancelReservationAPIView, ExtendReservationAPIView,
    CleanupExpiredAPIView,
)

urlpatterns = [
    path('api/entry/', VehicleEntryAPIView.as_view(), name='vehicle-entry'),
    path('api/exit/', VehicleExitAPIView.as_view(), name='vehicle-exit'),
    path('api/slots/update/', BulkSlotUpdateAPIView.as_view(), name='bulk-slot-update'),
    path('api/status/summary/', ParkingStatusAPIView.as_view(), name='parking-summary'),
    path('api/slots/', ParkingSlotListAPIView.as_view(), name='slot-list-mobile'),
    path('api/reserve/', CreateReservationAPIView.as_view(), name='create-reservation'),
    path('api/navigation/<str:slot_number>/', navigation_view),
    path('api/tracking/', VehicleTrackingAPIView.as_view(), name='vehicle-tracking'),
    path('api/my-car-location/<str:plate_number>/', UserCurrentLocationAPIView.as_view()),
    path('api/my-reservations/', UserReservationsAPIView.as_view(), name='user-reservations'),
    path('api/reservations/<int:reservation_id>/cancel/', CancelReservationAPIView.as_view(), name='cancel-reservation'),
    path('api/reservations/<int:reservation_id>/extend/', ExtendReservationAPIView.as_view(), name='extend-reservation'),
    path('api/cleanup-expired/', CleanupExpiredAPIView.as_view(), name='cleanup-expired'),
]
