import 'package:flutter/foundation.dart';
import '../models/user.dart';
import '../repositories/auth_repository.dart';

class AuthProvider extends ChangeNotifier {
  AuthProvider(this._authRepository);

  final AuthRepository _authRepository;

  bool _isLoading = false;
  String? _errorMessage;
  User? _user;

  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  User? get user => _user;
  bool get isLoggedIn => _user != null;

  Future<bool> login(String username, String password) async {
    _setLoading(true);
    try {
      final result = await _authRepository.login(
        username: username.trim(),
        password: password,
      );
      _user = result.$1;
      _errorMessage = null;
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = 'Login failed: ${e.toString()}';
      if (kDebugMode) print('Login error: $e');
      notifyListeners();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  Future<bool> signup({
    required String username,
    required String email,
    required String password,
    required String passwordConfirm,
    required String firstName,
    required String lastName,
  }) async {
    _setLoading(true);
    try {
      final result = await _authRepository.register(
        username: username.trim(),
        email: email.trim(),
        password: password,
        passwordConfirm: passwordConfirm,
        firstName: firstName.trim(),
        lastName: lastName.trim(),
      );
      _user = result.$1;
      _errorMessage = null;
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = 'Signup failed: ${e.toString()}';
      if (kDebugMode) print('Signup error: $e');
      notifyListeners();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  Future<void> fetchProfile() async {
    _setLoading(true);
    try {
      final user = await _authRepository.fetchProfile();
      if (user != null) {
        _user = user;
      }
    } catch (e) {
      if (kDebugMode) print('Profile fetch error: $e');
    } finally {
      _setLoading(false);
    }
  }

  Future<void> logout() async {
    await _authRepository.logout();
    _user = null;
    notifyListeners();
  }

  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  void _setLoading(bool value) {
    _isLoading = value;
    notifyListeners();
  }
}
