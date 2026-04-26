def build_garage_grid():
    """
    Exact grid based on database structure:
    
    ENTER  → row=0,  col=1
    EXIT   → row=51, col=1
    
    A slots → col=0,  rows 1-50
    B slots → col=2,  rows 2-18  (B1=row2 ... B17=row18)
    C slots → col=3,  rows 2-18  (C1=row2 ... C17=row18)
    D slots → col=5,  rows 1-45
    
    Allowed road cells:
    - col=1: rows 1-50   (left lane)
    - col=4: rows 1-50   (right lane)
    - row=1:  cols 2,3   (top connector)
    - row=50: cols 2,3   (bottom connector)
    """

    ROWS = 52   # 0 → 51
    COLS = 6    # 0 → 5

    # ── Start: everything is a wall ──────────────────────────
    grid = [["X"] * COLS for _ in range(ROWS)]

    # ── ENTER / EXIT ─────────────────────────────────────────
    grid[0][1]  = "ENTER"
    grid[51][1] = "EXIT"

    # ── Left road lane  (col=1, rows 1-50) ───────────────────
    for r in range(1, 51):
        grid[r][1] = "."

    # ── Right road lane (col=4, rows 1-50) ───────────────────
    for r in range(1, 51):
        grid[r][4] = "."

    # ── Top connector   (row=1,  cols 2-3) ───────────────────
    grid[1][2] = "."
    grid[1][3] = "."

    # ── Bottom connector (row=50, cols 2-3) ──────────────────
    grid[50][2] = "."
    grid[50][3] = "."

    # ── A slots: col=0, rows 1-50 ────────────────────────────
    for r in range(1, 51):
        grid[r][0] = f"A{r}"

    # ── B slots: col=2, rows 2-21 ────────────────────────────
    # B1 → row=2 ... B17 → row=21
    for i in range(1, 21):         # i = slot number
        grid[i + 1][2] = f"B{i}"  # row = i+1

    # ── C slots: col=3, rows 2-21 ────────────────────────────
    # C1 → row=2 ... C17 → row=21
    for i in range(1, 21):
        grid[i + 1][3] = f"C{i}"

    # ── D slots: col=5, rows 1-45 ────────────────────────────
    for i in range(1, 46):
        grid[i][5] = f"D{i}"

    return grid


def build_slot_coordinates():
    """
    Returns dict: slot_name → (row, col)
    Matches exactly the database INSERT logic.
    """
    coords = {}

    # A1-A50 → col=0
    for r in range(1, 51):
        coords[f"A{r}"] = (r, 0)

    # B1-B17 → col=2, row=2..21 
    for i in range(1, 21):
        coords[f"B{i}"] = (i + 1, 2)

    # C1-C17 → col=3, row=2..21
    for i in range(1, 21):
        coords[f"C{i}"] = (i + 1, 3)

    # D1-D45 → col=5, row=1..45
    for i in range(1, 46):
        coords[f"D{i}"] = (i, 5)

    return coords


# ── Allowed road cells set (for fast lookup) ─────────────────
def build_road_cells_set():
    """
    Exact set of coordinates where car is allowed to drive.
    """
    roads = set()

    roads.add((0, 1))    # ENTER
    roads.add((51, 1))   # EXIT

    # Left lane:  col=1, rows 1-50
    for r in range(1, 51):
        roads.add((r, 1))

    # Right lane: col=4, rows 1-50
    for r in range(1, 51):
        roads.add((r, 4))

    # Top connector:    row=1, cols 2-3
    roads.add((1, 2))
    roads.add((1, 3))

    # Bottom connector: row=50, cols 2-3
    roads.add((50, 2))
    roads.add((50, 3))

    return roads


# ── Singletons ────────────────────────────────────────────────
GARAGE_GRID      = build_garage_grid()
SLOT_COORDINATES = build_slot_coordinates()
ROAD_CELLS_SET   = build_road_cells_set()