import 'package:dio/dio.dart';
import '../models/auth_tokens.dart';
import '../models/user.dart';
import '../services/api_client.dart';
import '../services/secure_storage_service.dart';

class AuthRepository {
  AuthRepository({
    ApiClient? apiClient,
    SecureStorageService? secureStorageService,
  })  : _apiClient = apiClient ?? ApiClient(),
        _storage = secureStorageService ?? SecureStorageService();

  final ApiClient _apiClient;
  final SecureStorageService _storage;

  Future<(User, AuthTokens)> register({
    required String username,
    required String email,
    required String password,
    required String passwordConfirm,
    required String firstName,
    required String lastName,
  }) async {
    try {
      final Response<dynamic> response =
          await _apiClient.post<dynamic>('/auth/register/', data: {
        'username': username,
        'password': password,
        'password_confirm': passwordConfirm,
        'email': email,
        'first_name': firstName,
        'last_name': lastName,
      });

      if (response.statusCode == 201 || response.statusCode == 200) {
        final data = (response.data is Map<String, dynamic>)
            ? (response.data as Map<String, dynamic>)
            : <String, dynamic>{};
        final user = data['user'] is Map<String, dynamic>
            ? User.fromJson(data['user'] as Map<String, dynamic>)
            : User.fromJson(data);
        final loginResult = await login(username: username, password: password);
        final loggedInUser = loginResult.$1 ?? user;
        final tokens = loginResult.$2;
        return (loggedInUser, tokens);
      }
      throw Exception('Registration failed (${response.statusCode})');
    } on DioException catch (e) {
      throw Exception(_extractErrorMessage(e, fallback: 'Registration failed'));
    }
  }

  Future<(User?, AuthTokens)> login({
    required String username,
    required String password,
  }) async {
    try {
      final Response<dynamic> response =
          await _apiClient.post<dynamic>('/auth/login/', data: {
        'username': username,
        'password': password,
      });

      if (response.statusCode == 200) {
        final data = response.data as Map<String, dynamic>;
        final tokens = AuthTokens.fromJson(data);
        User? user;
        if (data['user'] != null) {
          user = User.fromJson(data['user'] as Map<String, dynamic>);
        }
        await _storage.saveTokens(
          accessToken: tokens.access,
          refreshToken: tokens.refresh,
        );
        return (user, tokens);
      }
      throw Exception('Login failed (${response.statusCode})');
    } on DioException catch (e) {
      throw Exception(_extractErrorMessage(e, fallback: 'Login failed'));
    }
  }

  Future<User?> fetchProfile() async {
    try {
      final Response<dynamic> response =
          await _apiClient.get<dynamic>('/auth/profile/');
      if (response.statusCode == 200 && response.data is Map<String, dynamic>) {
        return User.fromJson(response.data as Map<String, dynamic>);
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  Future<void> logout() async {
    await _storage.clearTokens();
  }

  Future<bool> hasValidSession() async {
    final access = await _storage.readAccessToken();
    return access != null && access.isNotEmpty;
  }

  String _extractErrorMessage(DioException exception, {required String fallback}) {
    final response = exception.response;
    if (response?.data is Map<String, dynamic>) {
      final data = response!.data as Map<String, dynamic>;
      if (data['detail'] != null) return data['detail'].toString();
      if (data['error'] != null) return data['error'].toString();
      final formatted = _formatValidationErrors(data);
      if (formatted != null && formatted.isNotEmpty) return formatted;
    }
    return fallback;
  }

  String? _formatValidationErrors(Map<String, dynamic> data) {
    final lines = <String>[];
    for (final entry in data.entries) {
      final key = entry.key.toString();
      final value = entry.value;
      if (value == null) continue;
      if (value is List) {
        final msgs = value.map((e) => e.toString()).where((s) => s.isNotEmpty);
        final joined = msgs.join('\n- ');
        if (joined.isNotEmpty) {
          lines.add('${key == 'non_field_errors' ? 'Error' : key}: - $joined');
        }
      } else {
        final msg = value.toString();
        if (msg.isNotEmpty) lines.add('$key: $msg');
      }
    }
    return lines.isEmpty ? null : lines.join('\n');
  }
}
