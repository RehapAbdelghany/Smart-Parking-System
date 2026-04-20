class AppConfig {
  // ✅ غيّر الـ IP هنا بس - كل الـ App هيتغير
  static const String serverIp = '192.168.1.8';
  static const String baseUrl = 'http://$serverIp:8000';
  static const String apiBaseUrl = 'http://$serverIp:8000/api';
  static const String authBaseUrl = 'http://$serverIp:8000/api/auth';
}
