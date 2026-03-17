import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../models/parking_slot.dart' as model;

class DiagonalParkingSlot extends StatelessWidget {
  final model.ParkingSlot slot;
  final bool isLeftSkew;
  final bool isSelected; // دي بتيجي من provider.selectedSlotId == slot.slotId
  final VoidCallback onTap;

  const DiagonalParkingSlot({
    super.key,
    required this.slot,
    required this.isLeftSkew,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    Color bgColor;
    bool canSelect = false;

    // 1. تحديد اللون والحالة
    if (slot.status == 'occupied') {
      bgColor = Colors.red; // أحمر: مشغول - لا يمكن اختياره
      canSelect = false;
    } else if (slot.status == 'reserved') {
      bgColor = Colors.yellow; // أصفر: محجوز - لا يمكن اختياره
      canSelect = false;
    } else if (isSelected) {
      bgColor = Colors.green; // أخضر: هو ده المكان الوحيد اللي تم اختياره حالياً
      canSelect = true;
    } else {
      bgColor = Colors.white; // أبيض: متاح للاختيار
      canSelect = true;
    }

    return GestureDetector(
      onTap: canSelect ? onTap : null, // لو أحمر أو أصفر الزرار مبيشتغلش
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 10),
        child: Transform(
          transform: Matrix4.skewY(isLeftSkew ? -0.3 : 0.3),
          child: AnimatedContainer( // استخدام AnimatedContainer بيخلي نقل اللون الأخضر ناعم
            duration: const Duration(milliseconds: 250),
            height: 65,
            decoration: BoxDecoration(
              color: bgColor,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: isSelected ? Colors.green[900]! : Colors.black12,
                width: isSelected ? 2.5 : 1,
              ),
              boxShadow: isSelected
                  ? [BoxShadow(color: Colors.green.withOpacity(0.4), blurRadius: 10, spreadRadius: 2)]
                  : null,
            ),
            child: Transform(
              transform: Matrix4.skewY(isLeftSkew ? 0.3 : -0.3),
              child: Center(
                child: slot.status == 'occupied'
                    ? const Icon(Icons.directions_car, size: 22, color: Colors.white)
                    : Text(
                  slot.slotNumber,
                  style: TextStyle(
                    color: (bgColor == Colors.red || bgColor == Colors.green) ? Colors.white : Colors.black87,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}