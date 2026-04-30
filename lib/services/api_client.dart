import 'dart:async';
import 'package:dio/dio.dart';
import '../models/auth_tokens.dart';
import 'secure_storage_service.dart';

class ApiClient {
  final Dio _dio;
  final SecureStorageService _storage;

  ApiClient({
    Dio? dio,
    SecureStorageService? secureStorageService,
  })  : _dio = dio ??
      Dio(
        BaseOptions(
          baseUrl: 'http://127.0.0.1:8000/api', // تأكدي إن ده IP السيرفر لو بتجربي من موبايل حقيقي
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 20),
          contentType: 'application/json',
          headers: {
            'Accept': 'application/json',
          },
        ),
      ),
        _storage = secureStorageService ?? SecureStorageService() {

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // جلب التوكين من التخزين الآمن
          final token = await _storage.readAccessToken();

          if (token != null && token.isNotEmpty) {
            // إضافة التوكين في الهيدر
            // ملاحظة: لو بتستخدمي JWT خليها Bearer، لو Token Authentication خليها Token
            // عدلي السطر ده جوه الـ Interceptor (في ملف api_client.dart)
            options.headers['Authorization'] = 'Bearer $token';
            print('--- [API Request] Token Added: Bearer ${token.substring(0, 10)}...');
          } else {
            print('--- [API Request] No Token Found in Storage!');
          }

          return handler.next(options);
        },
        onError: (DioException error, handler) async {
          // لو السيرفر رد بـ 401 (التوكين انتهى) نحاول نجدده
          if (_shouldAttemptRefresh(error)) {
            print('--- [API Error] 401 Unauthorized, Attempting Refresh...');
            try {
              final newTokens = await _refreshToken();
              if (newTokens != null) {
                final requestOptions = error.requestOptions;
                requestOptions.headers['Authorization'] = 'Bearer ${newTokens.access}';

                // إعادة محاولة الطلب القديم بالتوكين الجديد
                final clonedResponse = await _dio.fetch(requestOptions);
                return handler.resolve(clonedResponse);
              }
            } catch (e) {
              print('--- [API Refresh] Refresh failed: $e');
            }
          }
          return handler.next(error);
        },
      ),
    );
  }

  Dio get dio => _dio;

  // GET Request
  Future<Response<T>> get<T>(
      String path, {
        Map<String, dynamic>? queryParameters,
        CancelToken? cancelToken,
      }) {
    return _dio.get<T>(
      path,
      queryParameters: queryParameters,
      cancelToken: cancelToken,
    );
  }

  // POST Request
  Future<Response<T>> post<T>(
      String path, {
        Object? data,
        Map<String, dynamic>? queryParameters,
        CancelToken? cancelToken,
      }) {
    return _dio.post<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      cancelToken: cancelToken,
    );
  }

  bool _shouldAttemptRefresh(DioException error) {
    return error.response?.statusCode == 401;
  }

  Future<AuthTokens?> _refreshToken() async {
    final refresh = await _storage.readRefreshToken();
    if (refresh == null || refresh.isEmpty) return null;

    final refreshDio = Dio(BaseOptions(baseUrl: 'http://127.0.0.1:8000/api/auth'));

    try {
      final response = await refreshDio.post('/token/refresh/', data: {'refresh': refresh});
      if (response.statusCode == 200) {
        final tokens = AuthTokens.fromJson(response.data as Map<String, dynamic>);
        await _storage.saveTokens(accessToken: tokens.access, refreshToken: tokens.refresh);
        return tokens;
      }
    } catch (e) {
      print('Refresh API Error: $e');
    }
    return null;
  }
}