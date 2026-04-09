import 'package:flutter/material.dart';
import '../services/navigation_service.dart';

class NavigationPage extends StatefulWidget {
  final String slotId;

  const NavigationPage({super.key, required this.slotId});

  @override
  State<NavigationPage> createState() => _NavigationPageState();
}

class _NavigationPageState extends State<NavigationPage> {
  final NavigationService _service = NavigationService();

  NavigationData? _navData;
  bool _isLoading = true;
  String? _error;

  // ── بناء الـ Grid بنفس منطق الـ Backend ──────────────────
  static List<List<String>> buildGarageGrid() {
    const rows = 52;
    const cols = 6;

    // كل حاجة جدار في الأول
    final grid = List.generate(
      rows,
          (_) => List.generate(cols, (_) => 'X'),
    );

    // ENTER / EXIT
    grid[0][1] = 'ENTER';
    grid[51][1] = 'EXIT';

    // Left road lane (col=1, rows 1-50)
    for (int r = 1; r <= 50; r++) {
      grid[r][1] = '.';
    }

    // Right road lane (col=4, rows 1-50)
    for (int r = 1; r <= 50; r++) {
      grid[r][4] = '.';
    }

    // Top connector (row=1, cols 2-3)
    grid[1][2] = '.';
    grid[1][3] = '.';

    // Bottom connector (row=50, cols 2-3)
    grid[50][2] = '.';
    grid[50][3] = '.';

    // A slots: col=0, rows 1-50
    for (int r = 1; r <= 50; r++) {
      grid[r][0] = 'A$r';
    }

    // B slots: col=2, rows 2-18
    for (int i = 1; i <= 17; i++) {
      grid[i + 1][2] = 'B$i';
    }

    // C slots: col=3, rows 2-18
    for (int i = 1; i <= 17; i++) {
      grid[i + 1][3] = 'C$i';
    }

    // D slots: col=5, rows 1-45
    for (int i = 1; i <= 45; i++) {
      grid[i][5] = 'D$i';
    }

    return grid;
  }

  static final List<List<String>> garageGrid = buildGarageGrid();

  @override
  void initState() {
    super.initState();
    _loadNavigation();
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
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
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
    // الـ Slot المحجوز
    if (_isDestination(row, col)) return const Color(0xFF00E676);
    // ENTER
    if (value == 'ENTER') return const Color(0xFF4CAF50);
    // EXIT
    if (value == 'EXIT') return const Color(0xFFF44336);
    // المسار
    if (_isOnPath(row, col)) return const Color(0xFFFFD600);
    // جدار
    if (value == 'X') return const Color(0xFF37474F);
    // سلوت عادي
    if (value != '.') return const Color(0xFF455A64);
    // ممر
    return const Color(0xFF263238);
  }

  Widget? _buildCellContent(int row, int col, String value) {
    final isDestination = _isDestination(row, col);
    final isOnPath = _isOnPath(row, col);

    // السلوت المحجوز
    if (isDestination) {
      return const FittedBox(
        child: Padding(
          padding: EdgeInsets.all(1),
          child: Icon(Icons.directions_car, size: 8, color: Colors.black),
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

    // نقطة على المسار
    if (value == '.' && isOnPath) {
      return Center(
        child: Container(
          width: 3,
          height: 3,
          decoration: const BoxDecoration(
            color: Colors.orange,
            shape: BoxShape.circle,
          ),
        ),
      );
    }

    // اسم السلوت
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
          _legendItem(const Color(0xFF4CAF50), 'Entry'),
          _legendItem(const Color(0xFFFFD600), 'Path'),
          _legendItem(const Color(0xFF00E676), 'Your Slot'),
          _legendItem(const Color(0xFF455A64), 'Slot'),
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

  Widget _buildInfoBar() {
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
              Text(
                'Steps: ${_navData?.totalSteps ?? 0}',
                style: const TextStyle(
                  color: Colors.white70,
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