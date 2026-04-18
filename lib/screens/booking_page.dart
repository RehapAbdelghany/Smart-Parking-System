import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/parking_provider.dart';
import '../widgets/info_card.dart';
import '../widgets/duration_slider.dart';
import 'navigation_page.dart';

class BookingPage extends StatefulWidget {
  final String slotId;
  final String floor;

  const BookingPage({
    super.key,
    required this.slotId,
    required this.floor,
  });

  @override
  _BookingPageState createState() => _BookingPageState();
}

class _BookingPageState extends State<BookingPage> {
  DateTime? _selectedDate;
  TimeOfDay? _selectedTime;
  int _durationHours = 1;
  final TextEditingController _licensePlateController = TextEditingController();
  bool _isBooking = false;

  Future<void> _pickDate(BuildContext context) async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: now,
      firstDate: now,
      lastDate: now.add(const Duration(days: 365)),
    );
    if (picked != null) setState(() => _selectedDate = picked);
  }

  Future<void> _pickTime(BuildContext context) async {
    final picked = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.now(),
    );
    if (picked != null) setState(() => _selectedTime = picked);
  }

  Map<String, dynamic> bookingSummary() {
    return {
      'floor': widget.floor,
      'number': widget.slotId,
      'date': _selectedDate != null
          ? DateFormat('yyyy-MM-dd').format(_selectedDate!)
          : null,
      'time': _selectedTime != null ? _formatTime(_selectedTime!) : null,
      'duration': _durationHours,
    };
  }

  String _formatTime(TimeOfDay time) {
    final now = DateTime.now();
    final dt = DateTime(now.year, now.month, now.day, time.hour, time.minute);
    return DateFormat('hh:mm a').format(dt);
  }

  bool canContinue() {
    return _selectedDate != null &&
        _selectedTime != null &&
        _durationHours > 0 &&
        _licensePlateController.text.trim().isNotEmpty;
  }

  // ✅ NEW: Send reservation to backend
  Future<void> _confirmBooking() async {
    if (!canContinue()) return;

    setState(() => _isBooking = true);

    // حساب الـ start_time و end_time
    final startDateTime = DateTime(
      _selectedDate!.year,
      _selectedDate!.month,
      _selectedDate!.day,
      _selectedTime!.hour,
      _selectedTime!.minute,
    );
    final endDateTime = startDateTime.add(Duration(hours: _durationHours));

    // جيب الـ slot ID (الرقمي) من الـ provider
    final provider = context.read<ParkingProvider>();
    final slot = provider.slots.firstWhere(
          (s) => s.slotNumber == widget.slotId,
    );

    final result = await provider.reserveSlot(
      slotId: int.parse(slot.slotId),
      licensePlate: _licensePlateController.text.trim().toUpperCase(),
      startTime: startDateTime,
      endTime: endDateTime,
    );

    setState(() => _isBooking = false);

    if (result != null && mounted) {
      // ✅ الحجز نجح → روح Navigation
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Booking confirmed! Code: ${result['code']}'),
          backgroundColor: Colors.green,
        ),
      );
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => NavigationPage(slotId: widget.slotId),
        ),
      );
    } else if (mounted) {
      // ❌ الحجز فشل
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(provider.reservationError ?? 'Booking failed!'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Widget _buildSummaryRow(
      {required IconData icon, required String label, required String value}) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: Colors.teal.shade100,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: Colors.teal.shade700, size: 20),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: TextStyle(
                  color: Colors.grey.shade600,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                value,
                style: TextStyle(
                  color: Colors.grey.shade800,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  @override
  void dispose() {
    _licensePlateController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final summary = bookingSummary();
    return Scaffold(
      appBar: AppBar(
        elevation: 0,
        backgroundColor: Colors.white,
        leading: const BackButton(color: Colors.black),
        title:
        const Text('Select Parking', style: TextStyle(color: Colors.black)),
        centerTitle: true,
      ),
      body: Column(children: [
        InfoCard(floor: widget.floor, no: widget.slotId),
        const SizedBox(height: 8),
        Expanded(
          child: SingleChildScrollView(
            child: Column(
              children: [
                // ✅ NEW: License Plate Field
                Padding(
                  padding:
                  const EdgeInsets.symmetric(horizontal: 18.0, vertical: 8),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text('License Plate Number',
                        style: TextStyle(
                            color: Colors.grey[800],
                            fontWeight: FontWeight.w600)),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 18.0),
                  child: TextField(
                    controller: _licensePlateController,
                    textCapitalization: TextCapitalization.characters,
                    decoration: InputDecoration(
                      hintText: 'e.g. ABC 1234',
                      prefixIcon: const Icon(Icons.directions_car),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                    onChanged: (_) => setState(() {}),
                  ),
                ),

                const SizedBox(height: 18),

                // Pick the date field
                Padding(
                  padding:
                  const EdgeInsets.symmetric(horizontal: 18.0, vertical: 8),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text('Pick the date',
                        style: TextStyle(
                            color: Colors.grey[800],
                            fontWeight: FontWeight.w600)),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 18.0),
                  child: GestureDetector(
                    onTap: () => _pickDate(context),
                    child: Container(
                      height: 54,
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.grey.shade300),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              summary['date'] == null
                                  ? 'dd / mm / yy'
                                  : summary['date'],
                              style: TextStyle(
                                  color: summary['date'] == null
                                      ? Colors.grey
                                      : Colors.black,
                                  fontSize: 16),
                            ),
                          ),
                          IconButton(
                            onPressed: () => _pickDate(context),
                            icon: const Icon(Icons.calendar_today_outlined),
                          )
                        ],
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 18),

                // Pick time field
                Padding(
                  padding:
                  const EdgeInsets.symmetric(horizontal: 18.0, vertical: 8),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text('Pick the time you would arrive',
                        style: TextStyle(
                            color: Colors.grey[800],
                            fontWeight: FontWeight.w600)),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 18.0),
                  child: GestureDetector(
                    onTap: () => _pickTime(context),
                    child: Container(
                      height: 54,
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.grey.shade300),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              summary['time'] == null
                                  ? '00 : 00 : 00 AM'
                                  : DateFormat('hh : mm : ss a').format(DateTime(
                                  0,
                                  0,
                                  0,
                                  _selectedTime!.hour,
                                  _selectedTime!.minute)),
                              style: TextStyle(
                                  color: summary['time'] == null
                                      ? Colors.grey
                                      : Colors.black,
                                  fontSize: 16),
                            ),
                          ),
                          IconButton(
                            onPressed: () => _pickTime(context),
                            icon: const Icon(Icons.access_time),
                          )
                        ],
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 18),

                // Duration slider
                DurationSlider(
                  initialValue: _durationHours,
                  onChanged: (val) {
                    setState(() {
                      _durationHours = val;
                    });
                  },
                ),

                const SizedBox(height: 80),
              ],
            ),
          ),
        ),

        // Continue button
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
          child: ElevatedButton(
            style: ElevatedButton.styleFrom(
              minimumSize: const Size.fromHeight(56),
              backgroundColor:
              canContinue() ? Colors.teal.shade600 : Colors.grey.shade400,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              elevation: 4,
              shadowColor: Colors.teal.shade200,
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
            onPressed: canContinue()
                ? () {
              final summary = bookingSummary();
              final formattedDate = summary['date'] ?? 'N/A';
              final formattedTime = summary['time'] ?? 'N/A';
              final duration = summary['duration'];

              showDialog(
                context: context,
                builder: (_) => AlertDialog(
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(20),
                  ),
                  elevation: 10,
                  backgroundColor: Colors.white,
                  titlePadding: EdgeInsets.zero,
                  title: Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          Colors.teal.shade700,
                          Colors.teal.shade400
                        ],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: const BorderRadius.only(
                        topLeft: Radius.circular(20),
                        topRight: Radius.circular(20),
                      ),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.check_circle,
                            color: Colors.white, size: 28),
                        SizedBox(width: 12),
                        Text(
                          'Booking Summary',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                  content: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildSummaryRow(
                        icon: Icons.meeting_room_outlined,
                        label: 'Slot Number:',
                        value: '${summary['number']}',
                      ),
                      const SizedBox(height: 16),
                      _buildSummaryRow(
                        icon: Icons.directions_car,
                        label: 'License Plate:',
                        value: _licensePlateController.text
                            .trim()
                            .toUpperCase(),
                      ),
                      const SizedBox(height: 16),
                      _buildSummaryRow(
                        icon: Icons.calendar_month_outlined,
                        label: 'Date:',
                        value: formattedDate,
                      ),
                      const SizedBox(height: 16),
                      _buildSummaryRow(
                        icon: Icons.access_time_outlined,
                        label: 'Time:',
                        value: formattedTime,
                      ),
                      const SizedBox(height: 16),
                      _buildSummaryRow(
                        icon: Icons.timer_outlined,
                        label: 'Duration:',
                        value: '$duration hours',
                      ),
                      const SizedBox(height: 20),
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.teal.shade50,
                          borderRadius: BorderRadius.circular(12),
                          border:
                          Border.all(color: Colors.teal.shade100),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.info_outline,
                                color: Colors.teal.shade700, size: 20),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                'Please review your booking details before confirming',
                                style: TextStyle(
                                  color: Colors.teal.shade800,
                                  fontWeight: FontWeight.w500,
                                  fontSize: 14,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  actions: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 8),
                      child: Row(
                        children: [
                          Expanded(
                            child: OutlinedButton(
                              onPressed: () => Navigator.pop(context),
                              style: OutlinedButton.styleFrom(
                                foregroundColor: Colors.grey.shade700,
                                backgroundColor: Colors.white,
                                side: BorderSide(
                                    color: Colors.grey.shade400,
                                    width: 1.5),
                                shape: RoundedRectangleBorder(
                                  borderRadius:
                                  BorderRadius.circular(14),
                                ),
                                padding: const EdgeInsets.symmetric(
                                    vertical: 16),
                              ),
                              child: const Row(
                                mainAxisAlignment:
                                MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.edit, size: 20),
                                  SizedBox(width: 8),
                                  Text(
                                    'Edit',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: ElevatedButton(
                              // ✅ الـ Confirm بيحجز في الـ Backend
                              onPressed: _isBooking
                                  ? null
                                  : () {
                                Navigator.pop(
                                    context); // اقفل الـ Dialog
                                _confirmBooking(); // ✅ ابعت الحجز
                              },
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.teal.shade600,
                                foregroundColor: Colors.white,
                                elevation: 3,
                                shape: RoundedRectangleBorder(
                                  borderRadius:
                                  BorderRadius.circular(14),
                                ),
                                padding: const EdgeInsets.symmetric(
                                    vertical: 16),
                              ),
                              child: _isBooking
                                  ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                                  : const Row(
                                mainAxisAlignment:
                                MainAxisAlignment.center,
                                children: [
                                  Icon(
                                      Icons
                                          .check_circle_outline,
                                      size: 20),
                                  SizedBox(width: 8),
                                  Text(
                                    'Confirm',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight:
                                      FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            }
                : null,
            child: canContinue()
                ? const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  'Continue',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                    color: Colors.white,
                    letterSpacing: 0.5,
                  ),
                ),
                SizedBox(width: 8),
                Icon(Icons.arrow_forward_rounded,
                    size: 22, color: Colors.white),
              ],
            )
                : const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  'Fill All Details',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                    color: Colors.white,
                  ),
                ),
                SizedBox(width: 8),
                Icon(Icons.lock_outline, size: 18, color: Colors.white),
              ],
            ),
          ),
        ),
      ]),
    );
  }
}