import 'dart:async';
import 'package:flutter/material.dart';
import '../services/secure_storage_service.dart';
import '../parking_page.dart';
import 'login_page.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  double carPosition = -150;
  final SecureStorageService _storage = SecureStorageService();

  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      setState(() {
        carPosition = 230;
      });
    });

    // بعد 3 ثواني شيك على الـ Token
    Timer(const Duration(seconds: 3), () {
      _checkAuthAndNavigate();
    });
  }

  Future<void> _checkAuthAndNavigate() async {
    final token = await _storage.readAccessToken();

    if (!mounted) return;

    if (token != null && token.isNotEmpty) {
      // ✅ في Token محفوظ → روح ParkingPage على طول
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const ParkingPage()),
      );
    } else {
      // ❌ مفيش Token → روح Login
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const LoginPage()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Stack(
        children: [
          Center(
            child: Image.asset('assets/logo.png', width: 300, height: 300),
          ),
          AnimatedPositioned(
            duration: const Duration(seconds: 2),
            curve: Curves.easeInOut,
            bottom: 20,
            left: carPosition,
            child: Image.asset('assets/car.png', width: 120, height: 120),
          ),
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Image.asset(
              'assets/road.jpg',
              width: MediaQuery.of(context).size.width,
              height: 50,
              fit: BoxFit.fill,
            ),
          ),
          Positioned(
            bottom: 40,
            right: 0,
            child: Image.asset('assets/halfhouse.png', width: 120, height: 120),
          ),
          Positioned(
            bottom: 45,
            right: 55,
            child: Image.asset('assets/p.png', width: 60, height: 60),
          ),
        ],
      ),
    );
  }
}