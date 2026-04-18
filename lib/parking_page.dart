import 'dart:math';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/parking_slot.dart' as model;
import '../providers/parking_provider.dart';
import '../screens/booking_page.dart';
import 'models/parking_slot.dart';
import 'widgets/parking_lane.dart';

class ParkingPage extends StatefulWidget {
  const ParkingPage({super.key});

  @override
  State<ParkingPage> createState() => _ParkingPageState();
}

class _ParkingPageState extends State<ParkingPage> with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  // ✅ لما الـ App يرجع من الـ background، حدّث الـ Slots
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      context.read<ParkingProvider>().loadSlots();
    }
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        backgroundColor: const Color(0xFFE5E5E5),
        appBar: AppBar(
          title: const Text(
            'Parking Garage',
            style: TextStyle(
              color: Colors.black,
              fontWeight: FontWeight.bold,
            ),
          ),
          centerTitle: true,
          backgroundColor: Colors.white,
          elevation: 0.5,
          bottom: TabBar(
            onTap: (index) {
              context.read<ParkingProvider>().setFloor(index.toString());
            },
            indicatorColor: Colors.blueAccent,
            labelColor: Colors.blueAccent,
            unselectedLabelColor: Colors.grey,
            tabs: const [
              Tab(text: 'Level 1'),
              Tab(text: 'Level 2'),
              Tab(text: 'Level 3'),
            ],
          ),
        ),
        body: Consumer<ParkingProvider>(
          builder: (context, provider, _) {
            if (provider.isSlotsLoading) {
              return const Center(child: CircularProgressIndicator());
            }

            final slots = provider.slots;

            final colB = slots.where((s) => s.slotNumber.startsWith('B')).toList()
              ..sort(_slotNumberComparator);
            final colC = slots.where((s) => s.slotNumber.startsWith('C')).toList()
              ..sort(_slotNumberComparator);
            final colD = slots.where((s) => s.slotNumber.startsWith('D')).toList()
              ..sort(_slotNumberComparator);
            final colA = slots.where((s) => s.slotNumber.startsWith('A')).toList()
              ..sort(_slotNumberComparator);

            final int globalMaxRows = [
              colA.length,
              colB.length,
              colC.length,
              colD.length,
            ].reduce((a, b) => a > b ? a : b);
            final int laneArrowCount = globalMaxRows > 0 ? globalMaxRows : 1;

            return Column(
              children: [
                const SizedBox(height: 8),
                _buildGateIndicator("ENTRANCE", Icons.login),
                const SizedBox(height: 8),
                Expanded(
                  child: Center(
                    child: Container(
                      width: 340,
                      margin: const EdgeInsets.symmetric(horizontal: 12),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 12, vertical: 16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(28),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.05),
                            blurRadius: 12,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: SingleChildScrollView(
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(
                                child: _buildSlotColumn(colB, provider,
                                    isLeftSkew: true)),
                            ParkingLane(arrowCount: laneArrowCount),
                            Expanded(
                                child: _buildSlotColumn(colC, provider,
                                    isLeftSkew: false)),
                            const SizedBox(width: 4),
                            Expanded(
                                child: _buildSlotColumn(colD, provider,
                                    isLeftSkew: true)),
                            ParkingLane(arrowCount: laneArrowCount),
                            Expanded(
                                child: _buildSlotColumn(colA, provider,
                                    isLeftSkew: false)),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
                _buildGateIndicator("EXIT", Icons.logout),
                _buildConfirmButton(context, provider),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildGateIndicator(String label, IconData icon) {
    return Column(
      children: [
        Text(label,
            style: const TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.grey,
                fontSize: 10)),
        Icon(icon, color: Colors.orange, size: 18),
      ],
    );
  }

  Widget _buildSlotColumn(
      List<ParkingSlot> columnSlots, ParkingProvider provider,
      {required bool isLeftSkew}) {
    return Column(
      children: columnSlots
          .map<Widget>((slot) => DiagonalParkingSlot(
        slot: slot,
        isLeftSkew: isLeftSkew,
        isSelected: provider.selectedSlotId == _slotKey(slot),
        onTap: () => provider.selectSlot(_slotKey(slot)),
      ))
          .toList(),
    );
  }

  Widget _buildConfirmButton(BuildContext context, ParkingProvider provider) {
    final bool hasSelection = provider.selectedSlotId != null;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
      child: ElevatedButton(
        onPressed: hasSelection
            ? () {
          final selectedSlot = provider.slots.firstWhere(
                (s) => _slotKey(s) == provider.selectedSlotId,
          );

          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => BookingPage(
                slotId: selectedSlot.slotNumber,
                floor: provider.selectedFloor == '0'
                    ? 'Ground'
                    : 'Floor ${provider.selectedFloor}',
              ),
            ),
          ).then((_) {
            // ✅ لما يرجع من الـ BookingPage، حدّث الـ Slots
            provider.loadSlots();
          });
        }
            : null,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.teal.shade700,
          minimumSize: const Size(double.infinity, 55),
          shape:
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        ),
        child: Text(
          hasSelection ? 'Confirm Booking' : 'Select a Slot',
          style: const TextStyle(
              color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }
}

String _slotKey(model.ParkingSlot slot) {
  // بعض السجلات قد لا يكون لها slotId في الـ API، فن fallback للـ slotNumber
  return slot.slotId.isNotEmpty ? slot.slotId : slot.slotNumber;
}

int _slotNumberComparator(model.ParkingSlot a, model.ParkingSlot b) {
  int extractNumber(model.ParkingSlot s) {
    final match = RegExp(r'\d+').firstMatch(s.slotNumber);
    return match != null ? int.parse(match.group(0)!) : 0;
  }

  final na = extractNumber(a);
  final nb = extractNumber(b);

  if (na != nb) return na.compareTo(nb);
  return a.slotNumber.compareTo(b.slotNumber);
}

class DiagonalParkingSlot extends StatelessWidget {
  final model.ParkingSlot slot;
  final bool isLeftSkew;
  final bool isSelected;
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

    // منطق الألوان المطلوب
    if (slot.status == 'occupied') {
      bgColor = Colors.red.shade400;
      canSelect = false;
    } else if (slot.status == 'reserved') {
      bgColor = Colors.yellow.shade600;
      canSelect = false;
    } else if (isSelected) {
      bgColor = Colors.green.shade500; // اللون الأخضر للمختار فقط
      canSelect = true;
    } else {
      bgColor = Colors.white; // أبيض للمتاح
      canSelect = true;
    }

    return GestureDetector(
      onTap: canSelect ? onTap : null,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Transform(
          alignment: Alignment.center,
          transform: Matrix4.skewY(isLeftSkew ? -0.3 : 0.3),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            height: 50,
            decoration: BoxDecoration(
              color: bgColor,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: isSelected ? Colors.green.shade900 : Colors.grey.shade300,
                width: isSelected ? 2 : 1,
              ),
            ),
            child: Transform(
              alignment: Alignment.center,
              transform: Matrix4.skewY(isLeftSkew ? 0.3 : -0.3),
              child: Center(
                child: slot.status == 'occupied'
                    ? const Icon(Icons.directions_car, color: Colors.white, size: 18)
                    : Text(
                        slot.slotNumber,
                        style: TextStyle(
                          color: (bgColor == Colors.white || bgColor == Colors.yellow.shade600)
                              ? Colors.black
                              : Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
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