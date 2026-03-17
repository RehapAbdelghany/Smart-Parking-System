from heapq import heappush, heappop
from .grid import ROAD_CELLS_SET


def heuristic(a: tuple, b: tuple) -> int:
    """Manhattan distance heuristic."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def reconstruct_path(came_from: dict, current: tuple) -> list:
    """Trace back path from goal to start."""
    path = []
    while current in came_from:
        path.append(current)
        current = came_from[current]
    path.append(current)
    path.reverse()
    return path


def get_road_cell_next_to_slot(slot_row: int, slot_col: int) -> tuple:
    """
    Every slot is adjacent to exactly one road cell:

    A slots (col=0)  → road at col=1  (same row)
    B slots (col=2)  → road at col=1  (same row) ← row 1 or col=1
    C slots (col=3)  → road at col=4  (same row)
    D slots (col=5)  → road at col=4  (same row)

    Special cases for B/C at row=1 (top connector):
    B1 is at row=2 → (2,1) is road ✅
    """
    candidates = [
        (slot_row, slot_col - 1),   # left
        (slot_row, slot_col + 1),   # right
        (slot_row - 1, slot_col),   # up
        (slot_row + 1, slot_col),   # down
    ]

    # Return the first candidate that is a valid road cell
    for cell in candidates:
        if cell in ROAD_CELLS_SET:
            return cell

    return None


def astar(start: tuple, goal_road: tuple) -> list:
    """
    A* pathfinding - ONLY walks on ROAD_CELLS_SET.

    Parameters
    ----------
    start     : (row, col) - ENTER position (0, 1)
    goal_road : (row, col) - road cell adjacent to destination slot

    Returns
    -------
    List of (row, col) tuples representing the path.
    Empty list if no path exists.
    """

    if start not in ROAD_CELLS_SET:
        return []

    if goal_road not in ROAD_CELLS_SET:
        return []

    open_set = []
    heappush(open_set, (0, start))

    came_from = {}
    g_score   = {start: 0}

    while open_set:
        _, current = heappop(open_set)

        # ── Goal reached ──────────────────────────────────────
        if current == goal_road:
            return reconstruct_path(came_from, current)

        row, col = current

        # ── Explore 4 neighbours ──────────────────────────────
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (row + dr, col + dc)

            # ✅ ONLY move to road cells
            if neighbor not in ROAD_CELLS_SET:
                continue

            tentative_g = g_score[current] + 1

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor]   = tentative_g
                f_score             = tentative_g + heuristic(neighbor, goal_road)
                heappush(open_set, (f_score, neighbor))
                came_from[neighbor] = current

    return []   # No path found