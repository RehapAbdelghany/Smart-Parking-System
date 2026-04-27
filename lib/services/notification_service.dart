import 'dart:async';
import 'dart:io' show Platform;
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FlutterLocalNotificationsPlugin _plugin = FlutterLocalNotificationsPlugin();
  Timer? _reservationTimer;
  bool _sent5min = false;
  bool _sent2min = false;
  bool _sent1min = false;
  bool _sentExpired = false;

  Future<void> init() async {
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const initSettings = InitializationSettings(android: androidSettings);
    await _plugin.initialize(initSettings);

    // Request permission for Android 13+
    final androidPlugin = _plugin.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    if (androidPlugin != null) {
      await androidPlugin.requestNotificationsPermission();
    }
  }

  Future<void> showNotification({
    required int id,
    required String title,
    required String body,
  }) async {
    const androidDetails = AndroidNotificationDetails(
      'parking_channel',
      'Parking Notifications',
      channelDescription: 'Notifications for parking reservations',
      importance: Importance.max,
      priority: Priority.max,
      playSound: true,
      enableVibration: true,
      icon: '@mipmap/ic_launcher',
    );
    const details = NotificationDetails(android: androidDetails);
    await _plugin.show(id, title, body, details);
  }

  /// Show notification when user makes a reservation
  Future<void> showBookingConfirmed({
    required String slotNumber,
    required String endTime,
    String lang = 'en',
  }) async {
    await showNotification(
      id: 10,
      title: lang == 'ar' ? 'تم تأكيد الحجز ✅' : 'Booking Confirmed ✅',
      body: lang == 'ar'
          ? 'تم حجز المكان $slotNumber حتى $endTime'
          : 'Slot $slotNumber reserved until $endTime',
    );
  }

  /// Show notification when reservation is cancelled
  Future<void> showBookingCancelled({
    required String slotNumber,
    String lang = 'en',
  }) async {
    await showNotification(
      id: 11,
      title: lang == 'ar' ? 'تم إلغاء الحجز' : 'Booking Cancelled',
      body: lang == 'ar'
          ? 'تم إلغاء حجز المكان $slotNumber'
          : 'Reservation for slot $slotNumber has been cancelled',
    );
  }

  /// Show notification when reservation is extended
  Future<void> showBookingExtended({
    required String slotNumber,
    required int minutes,
    String lang = 'en',
  }) async {
    await showNotification(
      id: 12,
      title: lang == 'ar' ? 'تم تمديد الحجز ⏰' : 'Booking Extended ⏰',
      body: lang == 'ar'
          ? 'تم تمديد حجز المكان $slotNumber بمقدار $minutes دقيقة'
          : 'Slot $slotNumber extended by $minutes minutes',
    );
  }

  void startReservationMonitor(DateTime endTime, {String lang = 'en'}) {
    _reservationTimer?.cancel();
    _sent5min = false;
    _sent2min = false;
    _sent1min = false;
    _sentExpired = false;

    // Check every 10 seconds for more accurate timing
    _reservationTimer = Timer.periodic(const Duration(seconds: 10), (_) {
      final remaining = endTime.difference(DateTime.now());
      final mins = remaining.inMinutes;
      final secs = remaining.inSeconds;

      // 5 minutes warning (between 4:30 and 5:30)
      if (!_sent5min && mins >= 4 && mins <= 5 && secs <= 330) {
        _sent5min = true;
        showNotification(
          id: 1,
          title: lang == 'ar' ? '⚠️ تنبيه الموقف' : '⚠️ Parking Alert',
          body: lang == 'ar'
              ? 'حجزك ينتهي خلال 5 دقائق! قم بتمديد الحجز أو إخلاء المكان.'
              : 'Your reservation ends in 5 minutes! Extend or vacate.',
        );
      }

      // 2 minutes warning (between 1:30 and 2:30)
      if (!_sent2min && mins >= 1 && mins <= 2 && secs <= 150) {
        _sent2min = true;
        showNotification(
          id: 2,
          title: lang == 'ar' ? '🚨 تنبيه عاجل!' : '🚨 Urgent Alert!',
          body: lang == 'ar'
              ? 'حجزك ينتهي خلال دقيقتين!'
              : 'Your reservation ends in 2 minutes!',
        );
      }

      // 1 minute warning
      if (!_sent1min && secs > 0 && secs <= 70) {
        _sent1min = true;
        showNotification(
          id: 4,
          title: lang == 'ar' ? '⏰ دقيقة واحدة!' : '⏰ 1 Minute Left!',
          body: lang == 'ar'
              ? 'حجزك ينتهي خلال دقيقة واحدة!'
              : 'Your reservation ends in 1 minute!',
        );
      }

      // Expired
      if (!_sentExpired && remaining.isNegative) {
        _sentExpired = true;
        showNotification(
          id: 3,
          title: lang == 'ar' ? '🔴 انتهى الحجز' : '🔴 Reservation Expired',
          body: lang == 'ar'
              ? 'حجز الموقف انتهى. برجاء إخلاء المكان فوراً.'
              : 'Your parking reservation has expired. Please vacate immediately.',
        );
        _reservationTimer?.cancel();
      }
    });
  }

  void stopMonitor() {
    _reservationTimer?.cancel();
    _sent5min = false;
    _sent2min = false;
    _sent1min = false;
    _sentExpired = false;
  }
}
