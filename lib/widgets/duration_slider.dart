import 'package:flutter/material.dart';

class DurationSlider extends StatefulWidget {
  final int initialValue;
  final ValueChanged<int> onChanged;

  const DurationSlider({
    super.key,
    required this.initialValue,
    required this.onChanged,
  });

  @override
  State<DurationSlider> createState() => _DurationSliderState();
}

class _DurationSliderState extends State<DurationSlider> {
  late double _currentValue;
  bool _useMinutes = false; // ✅ Toggle for testing

  @override
  void initState() {
    super.initState();
    _currentValue = widget.initialValue.toDouble();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 18.0, vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Duration',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              Row(
                children: [
                  Text(
                    _useMinutes
                        ? '${_currentValue.round()} min'
                        : '${_currentValue.round()} h',
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(width: 8),
                  // ✅ Toggle button for testing
                  GestureDetector(
                    onTap: () {
                      setState(() {
                        _useMinutes = !_useMinutes;
                        _currentValue = _useMinutes ? 2 : 1;
                      });
                      widget.onChanged(_useMinutes
                          ? -_currentValue.round() // negative = minutes
                          : _currentValue.round());
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: _useMinutes
                            ? Colors.orange.shade100
                            : Colors.grey.shade200,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(
                          color: _useMinutes
                              ? Colors.orange
                              : Colors.grey.shade400,
                        ),
                      ),
                      child: Text(
                        _useMinutes ? '🧪 MIN' : 'HR',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color:
                              _useMinutes ? Colors.orange : Colors.grey.shade600,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 8),
          Slider(
            value: _currentValue,
            min: _useMinutes ? 1 : 1,
            max: _useMinutes ? 30 : 12,
            divisions: _useMinutes ? 29 : 11,
            label: _useMinutes
                ? '${_currentValue.round()} min'
                : '${_currentValue.round()} h',
            activeColor: _useMinutes ? Colors.orange : Colors.teal,
            inactiveColor: Colors.grey,
            onChanged: (v) {
              setState(() {
                _currentValue = v;
              });
              widget.onChanged(_useMinutes
                  ? -v.round() // negative = minutes
                  : v.round());
            },
          ),
          if (_useMinutes)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                '🧪 Test mode: using minutes instead of hours',
                style: TextStyle(
                  fontSize: 11,
                  color: Colors.orange.shade700,
                  fontStyle: FontStyle.italic,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
