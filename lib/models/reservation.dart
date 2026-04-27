class Reservation {
  final int id;
  final String reservationCode;
  final String slotNumber;
  final int floor;
  final String licensePlate;
  final DateTime startTime;
  final DateTime endTime;
  final bool isActive;
  final DateTime createdAt;

  Reservation({
    required this.id,
    required this.reservationCode,
    required this.slotNumber,
    required this.floor,
    required this.licensePlate,
    required this.startTime,
    required this.endTime,
    required this.isActive,
    required this.createdAt,
  });

  factory Reservation.fromJson(Map<String, dynamic> json) {
    return Reservation(
      id: json['id'] ?? 0,
      reservationCode: json['reservation_code'] ?? '',
      slotNumber: json['slot_number'] ?? '',
      floor: json['floor'] ?? 1,
      licensePlate: json['license_plate'] ?? '',
      startTime: DateTime.parse(json['start_time']).toLocal(),
      endTime: DateTime.parse(json['end_time']).toLocal(),
      isActive: json['is_active'] ?? false,
      createdAt: DateTime.parse(json['created_at']).toLocal(),
    );
  }

  bool get isExpired => DateTime.now().isAfter(endTime);

  Duration get remainingTime {
    final diff = endTime.difference(DateTime.now());
    return diff.isNegative ? Duration.zero : diff;
  }

  String get statusLabel {
    if (isActive && !isExpired) return 'Active';
    if (isActive && isExpired) return 'Expired';
    return 'Cancelled';
  }
}
