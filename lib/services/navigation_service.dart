import 'dart:convert';
import 'package:http/http.dart' as http;

class NavigationService {
  final String baseUrl = 'http://192.168.1.8:8000';
  
  Future<NavigationData> fetchNavigation(String slotNumber) async {
    // ✅ الـ URL الصح بتاع الـ Backend
    final url = Uri.parse('$baseUrl/api/navigation/$slotNumber/');

    print('Fetching navigation from: $url'); // للـ Debug

    final response = await http.get(
      url,
      headers: {'Content-Type': 'application/json'},
    );

    print('Response status: ${response.statusCode}'); // للـ Debug
    print('Response body: ${response.body}');          // للـ Debug

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return NavigationData.fromJson(data);
    } else {
      final error = json.decode(response.body);
      throw Exception(error['error'] ?? 'Failed: ${response.statusCode}');
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
      slotNumber:  json['slot_number'],
      entrance:    Position.fromJson(json['entrance']),
      roadStop:    Position.fromJson(json['road_stop']),
      destination: Position.fromJson(json['destination']),
      totalSteps:  json['total_steps'],
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
}