import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config.dart';
import 'secure_storage_service.dart';

class NavigationService {
  final String baseUrl = AppConfig.baseUrl;
  final SecureStorageService _storage = SecureStorageService();

  /// Get auth headers with token
  Future<Map<String, String>> _getHeaders() async {
    final token = await _storage.readAccessToken();
    return {
      'Content-Type': 'application/json',
      if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
    };
  }

  Future<NavigationData> fetchNavigation(String slotNumber) async {
    final url = Uri.parse('$baseUrl/api/navigation/$slotNumber/');
    final headers = await _getHeaders();

    print('Fetching navigation from: $url');

    final response = await http.get(url, headers: headers);

    print('Response status: ${response.statusCode}');
    print('Response body: ${response.body}');

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return NavigationData.fromJson(data);
    } else {
      final error = json.decode(response.body);
      throw Exception(error['error'] ?? error['detail'] ?? 'Failed: ${response.statusCode}');
    }
  }

  /// Fetch car location from cameras
  Future<CarLocation?> fetchCarLocation(String licensePlate) async {
    try {
      final url = Uri.parse('$baseUrl/api/my-car-location/$licensePlate/');
      final headers = await _getHeaders();

      print('Fetching car location from: $url');

      final response = await http.get(url, headers: headers);

      print('Car location status: ${response.statusCode}');
      print('Car location body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return CarLocation.fromJson(data);
      }
      return null;
    } catch (e) {
      print('Error fetching car location: $e');
      return null;
    }
  }
}

class NavigationData {
  final String slotNumber;
  final Position entrance;
  final Position roadStop;
  final Position destination;
  final int totalSteps;
  final List<Position> path;

  NavigationData({
    required this.slotNumber,
    required this.entrance,
    required this.roadStop,
    required this.destination,
    required this.totalSteps,
    required this.path,
  });

  factory NavigationData.fromJson(Map<String, dynamic> json) {
    return NavigationData(
      slotNumber: json['slot_number'],
      entrance: Position.fromJson(json['entrance']),
      roadStop: Position.fromJson(json['road_stop']),
      destination: Position.fromJson(json['destination']),
      totalSteps: json['total_steps'],
      path: (json['path'] as List)
          .map((p) => Position.fromJson(p))
          .toList(),
    );
  }
}

class Position {
  final int row;
  final int col;

  Position({required this.row, required this.col});

  factory Position.fromJson(Map<String, dynamic> json) {
    return Position(
      row: json['row'],
      col: json['col'],
    );
  }

  @override
  bool operator ==(Object other) {
    if (other is Position) {
      return row == other.row && col == other.col;
    }
    return false;
  }

  @override
  int get hashCode => row.hashCode ^ col.hashCode;
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

  Position toPosition() => Position(row: row, col: col);
}
