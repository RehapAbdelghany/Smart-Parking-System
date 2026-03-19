from django.urls import path
from .views import VehicleEntryAPIView, navigation_view
from .views import VehicleExitAPIView
from .views import BulkSlotUpdateAPIView
from .views import ParkingStatusAPIView
from .views import ParkingSlotListAPIView
from .views import CreateReservationAPIView
from .views import VehicleTrackingAPIView

urlpatterns = [

    path('api/entry/', VehicleEntryAPIView.as_view(), name='vehicle-entry'),
    path('api/exit/', VehicleExitAPIView.as_view(), name='vehicle-exit'),
    path('api/slots/update/', BulkSlotUpdateAPIView.as_view(), name='bulk-slot-update'),
    
    path('api/status/summary/', ParkingStatusAPIView.as_view(), name='parking-summary'),
    path('api/slots/', ParkingSlotListAPIView.as_view(), name='slot-list-mobile'),
    path('api/reserve/', CreateReservationAPIView.as_view(), name='create-reservation'),
    
    path('api/navigation/<str:slot_number>/', navigation_view),
    path('api/tracking/', VehicleTrackingAPIView.as_view(), name='vehicle-tracking'),

]