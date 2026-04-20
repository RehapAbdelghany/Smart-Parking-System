import 'dart:async';
import 'package:flutter/material.dart';
import '../services/navigation_service.dart';

class NavigationPage extends StatefulWidget {
  final String slotId;
  final String licensePlate; // ✅ NEW

  const NavigationPage({
    super.key,
    required this.slotId,
    required this.licensePlate, // ✅ NEW
  });

  @override
  State<NavigationPage> createState() => _NavigationPageState();
}

class _NavigationPageState extends State<NavigationPage>
    with TickerProviderStateMixin {
  final NavigationService _service = NavigationService();

  NavigationData? _navData;
  bool _isLoading = true;
  String? _error;

  // ✅ NEW: Tracking state
  CarLocation? _carLocation;
  Timer? _trackingTimer;
  bool _hasArrived = false;
  bool _isTracking = false;

  // ✅ NEW: Animation controller for car pulse
  late AnimationController _pulseController;

  // ── بناء الـ Grid بنفس منطق الـ Backend ──────────────────
  static List<List<String>> buildGarageGrid() {
    const rows = 52;
    const cols = 6;

    final grid = List.generate(
      rows,
          (_) => List.generate(cols, (_) => 'X'),
    );

    grid[0][1] = 'ENTER';
    grid[51][1] = 'EXIT';

    for (int r = 1; r <= 50; r++) {
      grid[r][1] = '.';
    }

    for (int r = 1; r <= 50; r++) {
      grid[r][4] = '.';
    }

    grid[1][2] = '.';
    grid[1][3] = '.';

    grid[50][2] = '.';
    grid[50][3] = '.';

    for (int r = 1; r <= 50; r++) {
      grid[r][0] = 'A$r';
    }

    for (int i = 1; i <= 17; i++) {
      grid[i + 1][2] = 'B$i';
    }

    for (int i = 1; i <= 17; i++) {
      grid[i + 1][3] = 'C$i';
    }

    for (int i = 1; i <= 45; i++) {
      grid[i][5] = 'D$i';
    }

    return grid;
  }

  static final List<List<String>> garageGrid = buildGarageGrid();

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat(reverse: true);
    _loadNavigation();
  }

  @override
  void dispose() {
    _trackingTimer?.cancel();
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _loadNavigation() async {
    try {
      setState(() {
        _isLoading = true;
        _error = null;
      });

      final data = await _service.fetchNavigation(widget.slotId);

      setState(() {
        _navData = data;
        _isLoading = false;
      });

      // ✅ NEW: Start tracking after navigation loads
      _startTracking();
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  // ✅ NEW: Start polling car location every 3 seconds
  void _startTracking() {
    if (widget.licensePlate.isEmpty) return;

    _isTracking = true;

    // Fetch immediately
    _fetchCarLocation();

    // Then poll every 3 seconds
    _trackingTimer = Timer.periodic(
      const Duration(seconds: 3),
          (_) => _fetchCarLocation(),
    );
  }

  // ✅ NEW: Fetch car location from camera API
  Future<void> _fetchCarLocation() async {
    if (!mounted || _hasArrived) return;

    final location = await _service.fetchCarLocation(widget.licensePlate);

    if (!mounted) return;

    if (location != null) {
      setState(() {
        _carLocation = location;
      });

      // Check if car arrived at destination
      _checkArrival(location);
    }
  }

  // ✅ NEW: Check if car has arrived at destination
  void _checkArrival(CarLocation location) {
    if (_navData == null || _hasArrived) return;

    final dest = _navData!.destination;
    final carPos = location.toPosition();

    // Car is at destination OR adjacent to it (within 1 cell)
    final rowDiff = (carPos.row - dest.row).abs();
    final colDiff = (carPos.col - dest.col).abs();

    if (rowDiff <= 1 && colDiff <= 1) {
      _onArrived();
    }
  }

  // ✅ NEW: Car has arrived
  void _onArrived() {
    if (_hasArrived) return;

    setState(() => _hasArrived = true);
    _trackingTimer?.cancel();

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF00E676).withOpacity(0.15),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.check_circle,
                color: Color(0xFF00E676),
                size: 56,
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'You Have Arrived!',
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'Park your car at slot ${widget.slotId}',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey.shade600,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0xFF00E676).withOpacity(0.15),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                widget.slotId,
                style: const TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF00E676),
                ),
              ),
            ),
          ],
        ),
        actions: [
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () {
                Navigator.pop(ctx);
                Navigator.of(context).popUntil((route) => route.isFirst);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF00E676),
                foregroundColor: Colors.black,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text(
                'Done',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ✅ NEW: Check if a cell is the car's current position
  bool _isCarPosition(int row, int col) {
    if (_carLocation == null) return false;
    return _carLocation!.row == row && _carLocation!.col == col;
  }

  // ✅ NEW: Check if a path cell has been passed by the car
  bool _isPassedPath(int row, int col) {
    if (_navData == null || _carLocation == null) return false;
    if (!_isOnPath(row, col)) return false;

    final carPos = _carLocation!.toPosition();

    // Find car's index on path (or closest)
    int carPathIndex = -1;
    double minDist = double.infinity;
    for (int i = 0; i < _navData!.path.length; i++) {
      final p = _navData!.path[i];
      final dist = ((p.row - carPos.row).abs() + (p.col - carPos.col).abs())
          .toDouble();
      if (dist < minDist) {
        minDist = dist;
        carPathIndex = i;
      }
    }

    // Find this cell's index on path
    int cellPathIndex = -1;
    for (int i = 0; i < _navData!.path.length; i++) {
      final p = _navData!.path[i];
      if (p.row == row && p.col == col) {
        cellPathIndex = i;
        break;
      }
    }

    // If cell is before car position on path, it's passed
    return cellPathIndex >= 0 &&
        carPathIndex >= 0 &&
        cellPathIndex < carPathIndex;
  }

  bool _isOnPath(int row, int col) {
    if (_navData == null) return false;
    return _navData!.path.any((p) => p.row == row && p.col == col);
  }

  bool _isDestination(int row, int col) {
    if (_navData == null) return false;
    return _navData!.destination.row == row &&
        _navData!.destination.col == col;
  }

  Color _getCellColor(int row, int col, String value) {
    // ✅ NEW: Car position - blue
    if (_isCarPosition(row, col)) return const Color(0xFF2196F3);
    // Destination slot
    if (_isDestination(row, col)) return const Color(0xFF00E676);
    // ENTER
    if (value == 'ENTER') return const Color(0xFF4CAF50);
    // EXIT
    if (value == 'EXIT') return const Color(0xFFF44336);
    // ✅ UPDATED: Passed path - dimmer
    if (_isPassedPath(row, col)) return const Color(0xFF8D6E00);
    // Active path - bright yellow
    if (_isOnPath(row, col)) return const Color(0xFFFFD600);
    // Wall
    if (value == 'X') return const Color(0xFF37474F);
    // Regular slot
    if (value != '.') return const Color(0xFF455A64);
    // Road
    return const Color(0xFF263238);
  }

  Widget? _buildCellContent(int row, int col, String value) {
    final isDestination = _isDestination(row, col);
    final isOnPath = _isOnPath(row, col);
    final isCarPos = _isCarPosition(row, col);

    // ✅ NEW: Car position marker
    if (isCarPos) {
      return AnimatedBuilder(
        animation: _pulseController,
        builder: (context, child) {
          return Container(
            decoration: BoxDecoration(
              color: Colors.blue.withOpacity(
                0.7 + _pulseController.value * 0.3,
              ),
              borderRadius: BorderRadius.circular(2),
              boxShadow: [
                BoxShadow(
                  color: Colors.blue.withOpacity(0.5),
                  blurRadius: 4 + _pulseController.value * 4,
                  spreadRadius: _pulseController.value * 2,
                ),
              ],
            ),
            child: const FittedBox(
              child: Padding(
                padding: EdgeInsets.all(1),
                child: Icon(Icons.directions_car, size: 10, color: Colors.white),
              ),
            ),
          );
        },
      );
    }

    // Destination slot
    if (isDestination) {
      return const FittedBox(
        child: Padding(
          padding: EdgeInsets.all(1),
          child: Icon(Icons.local_parking, size: 8, color: Colors.black),
        ),
      );
    }

    // ENTER
    if (value == 'ENTER') {
      return const FittedBox(
        child: Padding(
          padding: EdgeInsets.all(1),
          child: Text(
            'IN',
            style: TextStyle(
              fontSize: 6,
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      );
    }

    // EXIT
    if (value == 'EXIT') {
      return const FittedBox(
        child: Padding(
          padding: EdgeInsets.all(1),
          child: Text(
            'OUT',
            style: TextStyle(
              fontSize: 6,
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      );
    }

    // ✅ UPDATED: Path dots - different for passed vs upcoming
    if (value == '.' && isOnPath) {
      final isPassed = _isPassedPath(row, col);
      return Center(
        child: Container(
          width: isPassed ? 2 : 3,
          height: isPassed ? 2 : 3,
          decoration: BoxDecoration(
            color: isPassed ? Colors.orange.shade300 : Colors.orange,
            shape: BoxShape.circle,
          ),
        ),
      );
    }

    // Slot name
    if (value != '.' && value != 'X') {
      return FittedBox(
        child: Padding(
          padding: const EdgeInsets.all(0.5),
          child: Text(
            value,
            style: TextStyle(
              fontSize: 6,
              color: isOnPath ? Colors.black87 : Colors.white60,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      );
    }

    return null;
  }

  Widget _buildCell(int row, int col, String value) {
    return Container(
      decoration: BoxDecoration(
        color: _getCellColor(row, col, value),
        border: Border.all(color: Colors.black26, width: 0.3),
        borderRadius: BorderRadius.circular(1),
      ),
      child: _buildCellContent(row, col, value),
    );
  }

  Widget _buildGrid() {
    return LayoutBuilder(
      builder: (context, constraints) {
        final cols = garageGrid[0].length;
        final cellSize = constraints.maxWidth / cols;

        return SingleChildScrollView(
          child: Column(
            children: List.generate(garageGrid.length, (row) {
              return Row(
                children: List.generate(garageGrid[row].length, (col) {
                  return SizedBox(
                    width: cellSize,
                    height: cellSize * 1.1,
                    child: _buildCell(row, col, garageGrid[row][col]),
                  );
                }),
              );
            }),
          ),
        );
      },
    );
  }

  Widget _buildLegend() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      color: const Color(0xFF16213E),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _legendItem(const Color(0xFF2196F3), 'You'),
          _legendItem(const Color(0xFF4CAF50), 'Entry'),
          _legendItem(const Color(0xFFFFD600), 'Path'),
          _legendItem(const Color(0xFF00E676), 'Slot'),
          _legendItem(const Color(0xFF37474F), 'Wall'),
        ],
      ),
    );
  }

  Widget _legendItem(Color color, String label) {
    return Row(
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: const TextStyle(color: Colors.white, fontSize: 10),
        ),
      ],
    );
  }

  // ✅ NEW: Tracking info bar at top
  Widget _buildTrackingBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      color: const Color(0xFF16213E),
      child: Row(
        children: [
          // Car info
          Expanded(
            child: Row(
              children: [
                // Pulsing dot
                AnimatedBuilder(
                  animation: _pulseController,
                  builder: (context, _) {
                    return Container(
                      width: 10,
                      height: 10,
                      decoration: BoxDecoration(
                        color: _carLocation != null
                            ? Colors.green.withOpacity(
                            0.5 + _pulseController.value * 0.5)
                            : Colors.orange,
                        shape: BoxShape.circle,
                      ),
                    );
                  },
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _carLocation != null
                      ? Text(
                    '🚗 Zone ${_carLocation!.zone} (Row ${_carLocation!.row}, Col ${_carLocation!.col})',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                    ),
                    overflow: TextOverflow.ellipsis,
                  )
                      : const Text(
                    'Waiting for camera detection...',
                    style: TextStyle(
                      color: Colors.orange,
                      fontSize: 13,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Last seen
          if (_carLocation != null)
            Text(
              _carLocation!.lastSeen,
              style: const TextStyle(color: Colors.white38, fontSize: 11),
            ),
        ],
      ),
    );
  }

  Widget _buildInfoBar() {
    // ✅ UPDATED: Calculate remaining steps from car position
    int remainingSteps = _navData?.totalSteps ?? 0;

    if (_carLocation != null && _navData != null) {
      final carPos = _carLocation!.toPosition();

      // Find closest point on path to car
      int carPathIndex = 0;
      double minDist = double.infinity;
      for (int i = 0; i < _navData!.path.length; i++) {
        final p = _navData!.path[i];
        final dist =
        ((p.row - carPos.row).abs() + (p.col - carPos.col).abs())
            .toDouble();
        if (dist < minDist) {
          minDist = dist;
          carPathIndex = i;
        }
      }
      remainingSteps = _navData!.path.length - carPathIndex;
      if (remainingSteps < 0) remainingSteps = 0;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      color: const Color(0xFF16213E),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Slot: ${widget.slotId}',
                style: const TextStyle(
                  color: Color(0xFF00E676),
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              // ✅ UPDATED: Show remaining steps
              Text(
                _hasArrived
                    ? '✅ Arrived!'
                    : _carLocation != null
                    ? '$remainingSteps steps remaining'
                    : 'Steps: ${_navData?.totalSteps ?? 0}',
                style: TextStyle(
                  color: _hasArrived ? const Color(0xFF00E676) : Colors.white70,
                  fontSize: 12,
                ),
              ),
            ],
          ),
          ElevatedButton.icon(
            onPressed: () {
              Navigator.of(context).popUntil((route) => route.isFirst);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF00E676),
              foregroundColor: Colors.black,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              padding: const EdgeInsets.symmetric(
                horizontal: 20,
                vertical: 12,
              ),
            ),
            icon: const Icon(Icons.home),
            label: const Text(
              'Done',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1A1A2E),
      appBar: AppBar(
        backgroundColor: const Color(0xFF16213E),
        title: Text(
          'Navigate to ${widget.slotId}',
          style: const TextStyle(color: Colors.white),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          // ✅ NEW: Tracking status icon
          if (_isTracking)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: AnimatedBuilder(
                animation: _pulseController,
                builder: (context, _) {
                  return Icon(
                    Icons.videocam,
                    color: _carLocation != null
                        ? Colors.green
                        .withOpacity(0.5 + _pulseController.value * 0.5)
                        : Colors.orange,
                    size: 20,
                  );
                },
              ),
            ),
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white),
            onPressed: _loadNavigation,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(color: Color(0xFF00E676)),
            SizedBox(height: 16),
            Text(
              'Loading map...',
              style: TextStyle(color: Colors.white, fontSize: 16),
            ),
          ],
        ),
      )
          : _error != null
          ? Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.error_outline,
                color: Colors.red,
                size: 56,
              ),
              const SizedBox(height: 16),
              Text(
                _error!,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: _loadNavigation,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00E676),
                  foregroundColor: Colors.black,
                ),
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      )
          : Column(
        children: [
          _buildLegend(),
          // ✅ NEW: Tracking bar
          if (_isTracking) _buildTrackingBar(),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: InteractiveViewer(
                minScale: 0.3,
                maxScale: 10.0,
                child: _buildGrid(),
              ),
            ),
          ),
          _buildInfoBar(),
        ],
      ),
    );
  }
}