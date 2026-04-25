import 'package:flutter/material.dart';

class ParkingLane extends StatelessWidget {
  final int arrowCount;

  const ParkingLane({super.key, required this.arrowCount});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    const double rowHeight = 62;

    return Container(
      width: 40,
      margin: const EdgeInsets.symmetric(horizontal: 4),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF141829) : const Color(0xFFF2F2F2),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        children: List.generate(
          arrowCount,
          (index) => SizedBox(
            height: rowHeight,
            child: Center(
              child: Icon(
                Icons.arrow_downward,
                color: isDark ? const Color(0xFFFFA726).withOpacity(0.7) : const Color(0xFFFFB74D),
                size: 18,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
