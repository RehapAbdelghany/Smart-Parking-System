import 'package:flutter/foundation.dart';
import '../models/parking_slot.dart';
import '../models/parking_summary.dart';
import '../repositories/parking_repository.dart';

class ParkingProvider extends ChangeNotifier {
  ParkingProvider(this._parkingRepository) {
    loadSummary();
    loadSlots();
  }

  final ParkingRepository _parkingRepository;

  ParkingSummary? _summary;
  bool _isSummaryLoading = false;

  List<ParkingSlot> _slots = <ParkingSlot>[];
  bool _isSlotsLoading = false;

  String _selectedFloor = '1';
  String? _selectedSlotId;

  // Reservation state
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
    _selectedFloor = ((int.tryParse(floor) ?? 0) + 1).toString();
    _selectedSlotId = null;
    loadSlots();
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

  Future<void> loadSlots({String? status}) async {
    _isSlotsLoading = true;
    notifyListeners();
    try {
      _slots = await _parkingRepository.fetchSlots(status: status, floor: _selectedFloor);
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
      await loadSlots();
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
