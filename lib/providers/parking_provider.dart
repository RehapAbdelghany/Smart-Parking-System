import 'package:flutter/foundation.dart';
import '../models/parking_slot.dart';
import '../models/parking_summary.dart';
import '../repositories/parking_repository.dart';

class ParkingProvider extends ChangeNotifier {
  ParkingProvider(this._parkingRepository) {
    loadSummary();
    loadSlots(floor: '0');
  }

  final ParkingRepository _parkingRepository;

  ParkingSummary? _summary;
  bool _isSummaryLoading = false;

  List<ParkingSlot> _slots = <ParkingSlot>[];
  bool _isSlotsLoading = false;

  String _selectedFloor = '0';
  String? _selectedSlotId;

  // ✅ NEW: Reservation state
  bool _isReserving = false;
  String? _reservationError;

  // Getters
  ParkingSummary? get summary => _summary;
  bool get isSummaryLoading => _isSummaryLoading;
  List<ParkingSlot> get slots => _slots;
  bool get isSlotsLoading => _isSlotsLoading;
  String get selectedFloor => _selectedFloor;
  String? get selectedSlotId => _selectedSlotId;
  bool get isReserving => _isReserving;
  String? get reservationError => _reservationError;

  void setFloor(String floor) {
    _selectedFloor = floor;
    _selectedSlotId = null;
    loadSlots(floor: floor);
    notifyListeners();
  }

  Future<void> loadSummary() async {
    _isSummaryLoading = true;
    notifyListeners();
    try {
      _summary = await _parkingRepository.fetchSummary();
    } catch (e) {
      if (kDebugMode) print('Summary Error: $e');
    } finally {
      _isSummaryLoading = false;
      notifyListeners();
    }
  }

  Future<void> loadSlots({String? floor}) async {
    _isSlotsLoading = true;
    notifyListeners();
    try {
      _slots = await _parkingRepository.fetchSlots(floor: floor ?? _selectedFloor);
    } catch (e) {
      if (kDebugMode) print('Slots Error: $e');
    } finally {
      _isSlotsLoading = false;
      notifyListeners();
    }
  }

  void selectSlot(String slotId) {
    if (_selectedSlotId == slotId) {
      _selectedSlotId = null;
    } else {
      _selectedSlotId = slotId;
    }
    notifyListeners();
  }

  // ✅ NEW: Reserve a slot
  Future<Map<String, dynamic>?> reserveSlot({
    required int slotId,
    required String licensePlate,
    required DateTime startTime,
    required DateTime endTime,
  }) async {
    _isReserving = true;
    _reservationError = null;
    notifyListeners();
    try {
      final result = await _parkingRepository.reserveSlot(
        slotId: slotId,
        licensePlate: licensePlate,
        startTime: startTime,
        endTime: endTime,
      );
      // ✅ بعد الحجز، حدّث الـ Slots
      await loadSlots(floor: _selectedFloor);
      return result;
    } catch (e) {
      _reservationError = e.toString();
      if (kDebugMode) print('Reserve Error: $e');
      return null;
    } finally {
      _isReserving = false;
      notifyListeners();
    }
  }
}