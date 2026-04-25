import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/parking_provider.dart';
import '../providers/locale_provider.dart';
import '../utils/app_strings.dart';
import '../widgets/info_card.dart';
import '../widgets/duration_slider.dart';
import '../services/notification_service.dart';
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
  State<BookingPage> createState() => _BookingPageState();
}

class _BookingPageState extends State<BookingPage> {
  DateTime? _selectedDate;
  TimeOfDay? _selectedTime;
  int _durationValue = 1;
  final TextEditingController _licensePlateController = TextEditingController();
  bool _isBooking = false;

  bool get _isMinutesMode => _durationValue < 0;
  int get _displayDuration => _durationValue.abs();
  String get _durationLabel =>
      _isMinutesMode ? '$_displayDuration min' : '$_displayDuration h';

  Duration get _bookingDuration {
    if (_isMinutesMode) {
      return Duration(minutes: _displayDuration);
    } else {
      return Duration(hours: _displayDuration);
    }
  }

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
      'duration': _durationLabel,
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
        _displayDuration > 0 &&
        _licensePlateController.text.trim().isNotEmpty;
  }

  Future<void> _confirmBooking() async {
    if (!canContinue()) return;

    setState(() => _isBooking = true);

    final startDateTime = DateTime(
      _selectedDate!.year, _selectedDate!.month, _selectedDate!.day,
      _selectedTime!.hour, _selectedTime!.minute,
    );
    final endDateTime = startDateTime.add(_bookingDuration);
    final startUtc = startDateTime.toUtc();
    final endUtc = endDateTime.toUtc();

    final provider = context.read<ParkingProvider>();
    final lang = context.read<LocaleProvider>().locale.languageCode;
    final slot = provider.slots.firstWhere((s) => s.slotNumber == widget.slotId);

    final result = await provider.reserveSlot(
      slotId: int.parse(slot.slotId),
      licensePlate: _licensePlateController.text.trim().toUpperCase(),
      startTime: startUtc,
      endTime: endUtc,
    );

    setState(() => _isBooking = false);

    if (result != null && mounted) {
      // Send booking confirmed notification
      NotificationService().showBookingConfirmed(
        slotNumber: widget.slotId,
        endTime: DateFormat('hh:mm a').format(endDateTime),
        lang: lang,
      );

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Booking confirmed for $_durationLabel!'),
          backgroundColor: Colors.green,
        ),
      );
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => NavigationPage(
            slotId: widget.slotId,
            licensePlate: _licensePlateController.text.trim().toUpperCase(),
          ),
        ),
      );
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(provider.reservationError ?? 'Booking failed!'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  void dispose() {
    _licensePlateController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final lang = context.watch<LocaleProvider>().locale.languageCode;
    final summary = bookingSummary();

    return Scaffold(
      appBar: AppBar(
        leading: const BackButton(),
        title: Text(AppStrings.get('selectParking', lang)),
      ),
      body: Column(children: [
        InfoCard(floor: widget.floor, no: widget.slotId),
        const SizedBox(height: 8),
        Expanded(
          child: SingleChildScrollView(
            child: Column(
              children: [
                _buildFieldLabel(AppStrings.get('licensePlateNumber', lang), theme),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 18.0),
                  child: TextFormField(
                    controller: _licensePlateController,
                    textCapitalization: TextCapitalization.characters,
                    style: TextStyle(color: theme.textTheme.bodyLarge?.color),
                    decoration: InputDecoration(
                      hintText: 'e.g. ABC 1234',
                      prefixIcon: Icon(Icons.directions_car, color: theme.colorScheme.primary),
                    ),
                    onChanged: (_) => setState(() {}),
                  ),
                ),
                const SizedBox(height: 18),
                _buildFieldLabel(AppStrings.get('pickDate', lang), theme),
                _buildPickerField(
                  context: context, theme: theme,
                  value: summary['date'],
                  placeholder: 'dd / mm / yy',
                  icon: Icons.calendar_today_outlined,
                  onTap: () => _pickDate(context),
                ),
                const SizedBox(height: 18),
                _buildFieldLabel(AppStrings.get('pickTime', lang), theme),
                _buildPickerField(
                  context: context, theme: theme,
                  value: summary['time'],
                  placeholder: '00 : 00 AM',
                  icon: Icons.access_time,
                  onTap: () => _pickTime(context),
                ),
                const SizedBox(height: 18),
                DurationSlider(
                  initialValue: 1,
                  onChanged: (val) => setState(() => _durationValue = val),
                ),
                const SizedBox(height: 80),
              ],
            ),
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
          child: SizedBox(
            width: double.infinity, height: 56,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: canContinue()
                    ? theme.colorScheme.primary
                    : theme.dividerColor,
              ),
              onPressed: canContinue()
                  ? () => _showConfirmDialog(context, theme, lang)
                  : null,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    canContinue()
                        ? AppStrings.get('continueBtn', lang)
                        : AppStrings.get('fillAllDetails', lang),
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: Colors.white),
                  ),
                  const SizedBox(width: 8),
                  Icon(canContinue() ? Icons.arrow_forward_rounded : Icons.lock_outline,
                      size: 20, color: Colors.white),
                ],
              ),
            ),
          ),
        ),
      ]),
    );
  }

  Widget _buildFieldLabel(String label, ThemeData theme) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 18.0, vertical: 8),
      child: Align(
        alignment: Alignment.centerLeft,
        child: Text(label, style: theme.textTheme.titleMedium),
      ),
    );
  }

  Widget _buildPickerField({
    required BuildContext context,
    required ThemeData theme,
    required String? value,
    required String placeholder,
    required IconData icon,
    required VoidCallback onTap,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 18.0),
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          height: 54,
          padding: const EdgeInsets.symmetric(horizontal: 12),
          decoration: BoxDecoration(
            color: theme.inputDecorationTheme.fillColor,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: theme.dividerColor),
          ),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  value ?? placeholder,
                  style: TextStyle(
                    color: value == null
                        ? theme.textTheme.bodySmall?.color
                        : theme.textTheme.bodyLarge?.color,
                    fontSize: 16,
                  ),
                ),
              ),
              Icon(icon, color: theme.colorScheme.primary),
            ],
          ),
        ),
      ),
    );
  }

  void _showConfirmDialog(BuildContext context, ThemeData theme, String lang) {
    final summary = bookingSummary();
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: theme.cardColor,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        titlePadding: EdgeInsets.zero,
        title: Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [theme.colorScheme.primary, theme.colorScheme.secondary],
            ),
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(20), topRight: Radius.circular(20),
            ),
          ),
          child: Row(
            children: [
              const Icon(Icons.check_circle, color: Colors.white, size: 28),
              const SizedBox(width: 12),
              Text(AppStrings.get('bookingSummary', lang),
                  style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
            ],
          ),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSummaryRow(Icons.meeting_room_outlined,
                AppStrings.get('slotNumber', lang), '${summary['number']}', theme),
            const SizedBox(height: 16),
            _buildSummaryRow(Icons.directions_car,
                AppStrings.get('licensePlate', lang),
                _licensePlateController.text.trim().toUpperCase(), theme),
            const SizedBox(height: 16),
            _buildSummaryRow(Icons.calendar_month_outlined,
                AppStrings.get('date', lang), summary['date'] ?? 'N/A', theme),
            const SizedBox(height: 16),
            _buildSummaryRow(Icons.access_time_outlined,
                AppStrings.get('time', lang), summary['time'] ?? 'N/A', theme),
            const SizedBox(height: 16),
            _buildSummaryRow(Icons.timer_outlined,
                AppStrings.get('duration', lang), '${summary['duration']}', theme),
            const SizedBox(height: 20),
            if (_isMinutesMode)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.orange.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.orange.withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.science, color: Colors.orange, size: 20),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text('Test mode: $_displayDuration minutes',
                          style: const TextStyle(color: Colors.orange, fontWeight: FontWeight.w500, fontSize: 13)),
                    ),
                  ],
                ),
              ),
          ],
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
            child: Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => Navigator.pop(context),
                    child: Text(AppStrings.get('edit', lang)),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    onPressed: _isBooking ? null : () {
                      Navigator.pop(context);
                      _confirmBooking();
                    },
                    child: _isBooking
                        ? const SizedBox(width: 20, height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : Text(AppStrings.get('confirm', lang)),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryRow(IconData icon, String label, String value, ThemeData theme) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 36, height: 36,
          decoration: BoxDecoration(
            color: theme.colorScheme.primary.withOpacity(0.1),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: theme.colorScheme.primary, size: 20),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: theme.textTheme.bodySmall),
              const SizedBox(height: 4),
              Text(value, style: theme.textTheme.titleMedium),
            ],
          ),
        ),
      ],
    );
  }
}
