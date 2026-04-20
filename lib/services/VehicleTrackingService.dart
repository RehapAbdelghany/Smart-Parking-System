// lib/services/vehicle_tracking_service.dart
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

class VehicleTrackingService {
  final String baseUrl;

  VehicleTrackingService({required this.baseUrl});

  /// GET /api/my-car-location/{license_plate}/
  Future<CarLocation?> getCarLocation(String licensePlate) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/my-car-location/$licensePlate/'),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return CarLocation.fromJson(data);
      }
      return null;
    } catch (e) {
      print('Error getting car location: $e');
      return null;
    }
  }

  /// Poll car location every [intervalSeconds]
  Stream<CarLocation?> trackCarStream({
    required String licensePlate,
    int intervalSeconds = 3,
  }) {
    late StreamController<CarLocation?> controller;
    Timer? timer;

    controller = StreamController<CarLocation?>.broadcast(
      onListen: () {
        // Fetch immediately
        getCarLocation(licensePlate).then((loc) {
          if (!controller.isClosed) controller.add(loc);
        });

        // Then poll every interval
        timer = Timer.periodic(
          Duration(seconds: intervalSeconds),
              (_) {
            getCarLocation(licensePlate).then((loc) {
              if (!controller.isClosed) controller.add(loc);
            });
          },
        );
      },
      onCancel: () {
        timer?.cancel();
        controller.close();
      },
    );

    return controller.stream;
  }
}

class CarLocation {
  final String licensePlate;
  final int row;
  final int col;
  final String zone;
  final String lastSeen;

  CarLocation({
    required this.licensePlate,
    required this.row,
    required this.col,
    required this.zone,
    required this.lastSeen,
  });

  factory CarLocation.fromJson(Map<String, dynamic> json) {
    final pos = json['current_position'] ?? {};
    return CarLocation(
      licensePlate: json['license_plate'] ?? '',
      row: pos['row'] ?? 0,
      col: pos['col'] ?? 0,
      zone: pos['zone'] ?? '',
      lastSeen: json['last_seen'] ?? '',
    );
  }

  String get positionText => 'Zone $zone (Row $row, Col $col)';
}