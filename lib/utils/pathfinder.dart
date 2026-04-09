import 'dart:collection';

class PathFinder {
  static List<List<int>>? findPath({
    required List<List<String>> grid,
    required List<int> start,
    required List<int> target,
  }) {
    final rows = grid.length;
    final cols = grid[0].length;

    final queue = Queue<List<dynamic>>();
    final visited = <String>{};

    queue.add([
      start[0],
      start[1],
      [
        [start[0], start[1]]
      ]
    ]);
    visited.add('${start[0]},${start[1]}');

    const directions = [
      [-1, 0],
      [1, 0],
      [0, 1],
      [0, -1]
    ];

    while (queue.isNotEmpty) {
      final current = queue.removeFirst();
      final row = current[0] as int;
      final col = current[1] as int;
      final path = current[2] as List<List<int>>;

      if (row == target[0] && col == target[1]) {
        return path;
      }

      for (final dir in directions) {
        final newRow = row + dir[0];
        final newCol = col + dir[1];
        final key = '$newRow,$newCol';

        if (newRow >= 0 &&
            newRow < rows &&
            newCol >= 0 &&
            newCol < cols &&
            !visited.contains(key)) {
          final cellValue = grid[newRow][newCol];
          final isTarget =
              newRow == target[0] && newCol == target[1];

          if (_isWalkable(cellValue, isTarget)) {
            visited.add(key);
            final newPath = List<List<int>>.from(path)
              ..add([newRow, newCol]);
            queue.add([newRow, newCol, newPath]);
          }
        }
      }
    }
    return null;
  }

  static bool _isWalkable(String cell, bool isTarget) {
    if (isTarget) return true;
    return cell == '.' || cell == 'ENTER' || cell == 'EXIT';
  }

  static List<int>? findEnter(List<List<String>> grid) =>
      _findCell(grid, 'ENTER');

  static List<int>? findSlot(
      List<List<String>> grid, String slotId) =>
      _findCell(grid, slotId);

  static List<int>? _findCell(
      List<List<String>> grid, String value) {
    for (int r = 0; r < grid.length; r++) {
      for (int c = 0; c < grid[r].length; c++) {
        if (grid[r][c] == value) return [r, c];
      }
    }
    return null;
  }
}