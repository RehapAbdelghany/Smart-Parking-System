class AppConfig {
  // ─────────────────────────────────────────────
  // Production Server (Cloud)
  // ─────────────────────────────────────────────
  static const String baseUrl = 'https://solven.aelanji.cloud';
  static const String apiBaseUrl = 'https://solven.aelanji.cloud/api';
  static const String authBaseUrl = 'https://solven.aelanji.cloud/api/auth';

  // ─────────────────────────────────────────────
  // Local Development (commented out for now)
  // ─────────────────────────────────────────────
  // static const String serverIp = '192.168.1.100';
  // static const String baseUrl = 'http://$serverIp:8000';
  // static const String apiBaseUrl = 'http://$serverIp:8000/api';
  // static const String authBaseUrl = 'http://$serverIp:8000/api/auth';

  // Helper to know if we're on production
  static const bool isProduction = true;
}
