"""Two-red chambers, with constructive lessons that distinguish rival rules.

The unchanged Racket reference owns labels: partition through all non-5 cells
using four-neighbor connectivity; in a component containing exactly two red
cells, change original zeros to 8 and preserve every nonzero cell.

Default draws repeat a three-slot schedule: framed rectangular rooms, then two
diagnostic layouts. Every diagnostic layout alone distinguishes the declared
finite rival bank. Thus any three demonstrations from four consecutive default
draws retain a diagnostic layout. Explicit small size controls use framed rooms
and have no corresponding identifiability promise. See notes.md for domains,
canonical support, migration from 2.0.0, and limits of the finite rival bank.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers import grid as grid_ops
from puzzle_generators.helpers.objects import find_generator_objects

GENERATOR_ID = "f48cc30d7943"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "8c735fdd2a75"
SUMMARY = (
    "Four-connected non-gray chambers with exactly two red cells fill their "
    "original zeros cyan. Framed rooms retain canonical support; diagnostic "
    "chambers distinguish connectivity, counting, shape, reach, and preservation."
)
INVARIANTS = [
    "rectangular ARC digit grid with at least two four-connected non-5 chambers",
    "a chamber with exactly two red cells and an original zero",
    "a contrasting chamber with a different red-cell count and an original zero",
]
AXES = {
    "grid_h": {"type": "int", "default": "varies", "valid": "7..26"},
    "grid_w": {"type": "int", "default": "varies", "valid": "7..28"},
}
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("framed_rooms", "diagnostic_chambers")
_D4 = ((-1, 0), (0, -1), (0, 1), (1, 0))
_FOREIGN_COLORS = (1, 3, 4, 6, 7, 9)


def schedule_profile(seed, sample_index, *, difficulty=None):
    """The schedule is independent of seed, band, geometry, and private labels."""
    return SCHEDULE_PROFILES[0 if sample_index % LESSON_SCHEDULE_PERIOD == 0 else 1]


def _composition(total, count, rng):
    """Every composition with parts >=2 has positive probability, without retry."""
    extra = total - 2 * count
    cuts = [-1] + sorted(rng.sample(range(extra + count - 1), count - 1))
    cuts.append(extra + count - 1)
    return [2 + cuts[i + 1] - cuts[i] - 1 for i in range(count)]


def _framed_rooms(height, width, rng):
    possibilities = [(nr, nc) for nr in range(1, 4) for nc in range(1, 4)
                     if nr * nc >= 2 and 3 * nr + 1 <= height
                     and 3 * nc + 1 <= width]
    # Retain substantial four-room canonical support while varying room counts.
    nr, nc = (2, 2) if rng.randrange(3) else rng.choice(possibilities)
    heights = _composition(height - nr - 1, nr, rng)
    widths = _composition(width - nc - 1, nc, rng)
    grid = grid_ops.full_grid(height, width, 5)
    rooms = []
    row_start = 1
    for room_height in heights:
        col_start = 1
        for room_width in widths:
            cells = [(r, c) for r in range(row_start, row_start + room_height)
                     for c in range(col_start, col_start + room_width)]
            rooms.append(cells)
            for r, c in cells:
                grid[r][c] = 0
            col_start += room_width + 1
        row_start += room_height + 1
    counts = [rng.randint(0, 3) for _ in rooms]
    if 2 not in counts:
        counts[rng.randrange(len(rooms))] = 2
    if all(count == 2 for count in counts):
        counts[rng.randrange(len(rooms))] = rng.choice((0, 1, 3))
    for cells, count in zip(rooms, counts):
        for r, c in rng.sample(cells, count):
            grid[r][c] = 2
    return grid


def _diagnostic_chambers(height, width, rng):
    turns, reflected = rng.randrange(4), bool(rng.randrange(2))
    canvas_h, canvas_w = (width, height) if turns % 2 else (height, width)
    # Widely separated red seeds and a graph tail longer than the canvas must
    # coexist, including on 12x28 and 28x12. Choose feasible dimensions directly.
    feasible = [(ah, aw) for ah in range(11, canvas_h)
                for aw in range(10, canvas_w - 1)
                if 2 * ah + aw - 6 > max(canvas_h, canvas_w)]
    active_h, active_w = rng.choice(feasible)
    offset = rng.randint(0, canvas_w - active_w - 2)
    foreign = rng.choice(_FOREIGN_COLORS)
    grid = grid_ops.full_grid(canvas_h, canvas_w, 5)

    # A: boundary-touching C, foreign articulation between red cells, cyan
    # beyond them. Its farthest graph distance exceeds the whole canvas.
    open_chamber = (
        {(0, c) for c in range(active_w)}
        | {(r, active_w - 1) for r in range(1, active_h)}
        | {(active_h - 1, c) for c in range(active_w - 1)}
        | {(r, 0) for r in range(3, active_h - 1)}
    )
    # B: four reds, zeros, and BOTH marker controls; diagonally touches A.
    four_chamber = {(r, 2) for r in range(2, active_h - 2)} | {(2, 1)}
    # A thick nonrectangular negative prevents shape alone from selecting D.
    five_chamber = ({(r, c) for r in (2, 3) for c in range(4, active_w - 2)}
                    - {(3, active_w - 3)})
    # D: enclosed thick L with a cycle and adjacent reds. active_h >=11 is
    # essential: height10 would join this chamber to E orthogonally.
    bent_chamber = (
        {(5, c) for c in range(4, active_w - 2)}
        | {(r, 4) for r in range(6, active_h - 3)} | {(6, 5)}
    )
    one_chamber = {(active_h - 3, c) for c in range(5, active_w - 2)}

    def put(cell, color):
        r, c = cell
        grid[r][c + offset] = color

    for chamber in (open_chamber, four_chamber, five_chamber,
                    bent_chamber, one_chamber):
        for cell in chamber:
            put(cell, 0)
    for cell in ((0, 0), (0, active_w - 1)):
        put(cell, 2)
    put((0, 1), foreign)
    put((1, active_w - 1), 8)
    put((2, 1), 8)
    put((2, 2), foreign)
    for chamber, count in ((four_chamber, 4), (five_chamber, 5), (one_chamber, 1)):
        free = sorted((r, c) for r, c in chamber if grid[r][c + offset] == 0)
        for cell in rng.sample(free, count):
            put(cell, 2)
    adjacent_pairs = [(cell, (cell[0] + dr, cell[1] + dc))
                      for cell in sorted(bent_chamber) for dr, dc in ((0, 1), (1, 0))
                      if (cell[0] + dr, cell[1] + dc) in bent_chamber]
    for cell in rng.choice(adjacent_pairs):
        put(cell, 2)
    # F: a visible open negative, behind the full gray column canvas_w-2.
    # Boundary contact now occurs in both positive and negative chambers.
    for r in range(canvas_h):
        grid[r][canvas_w - 1] = 0
    for r in rng.sample(range(canvas_h), 3):
        grid[r][canvas_w - 1] = 2
    if reflected:
        grid = grid_ops.flip_lr(grid)
    for _ in range(turns):
        grid = grid_ops.rot90_cw(grid)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"Unknown override(s): {sorted(unknown)}; supported: {sorted(AXES)}")
    if difficulty is not None and (type(difficulty) is not str
                                   or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    band = difficulty if difficulty is not None else "medium"
    controls = {name: value for name, value in overrides.items() if value is not None}
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=band, overrides=controls)
    profile = schedule_profile(seed, sample_index, difficulty=band)
    if profile == "framed_rooms":
        height_range, width_range = (10, 12), (10, 12)
    else:
        height_range, width_range = {
            "easy": ((12, 16), (12, 16)),
            "medium": ((12, 20), (12, 22)),
            "hard": ((12, 26), (12, 28)),
        }[band]
    height_bounds = (7, 26) if "grid_h" in controls else height_range
    width_bounds = (7, 28) if "grid_w" in controls else width_range
    height = ctx.draw_int_strict("grid_h", *height_bounds)
    width = ctx.draw_int_strict("grid_w", *width_bounds)
    rng = ctx.draw_rng("layout")
    if profile == "framed_rooms" or height < 12 or width < 12:
        return _framed_rooms(height, width, rng)
    return _diagnostic_chambers(height, width, rng)


def rule_grid_errors(grid):
    """JSON ARC envelope for the reference, distinct from teaching restrictions."""
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        return ["grid must be a list with height 1..30"]
    if any(type(row) is not list for row in grid):
        return ["each row must be a list"]
    width = len(grid[0])
    if not 1 <= width <= 30 or any(len(row) != width for row in grid):
        return ["grid must be rectangular with width 1..30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact integers 0..9 (not bool)"]
    return []


def _components(grid, *, diagonal=False, allowed=None):
    observed = grid if allowed is None else [
        [value if allowed(value) else 5 for value in row] for row in grid
    ]
    return [{cell for _, cell in obj} for obj in find_generator_objects(
        observed, bg=5, univalued=False, diagonal=diagonal, without_bg=True
    )]


def _red_count(grid, cells):
    return sum(grid[r][c] == 2 for r, c in cells)


def _box_cells(cells):
    rows, columns = zip(*cells)
    return {(r, c) for r in range(min(rows), max(rows) + 1)
            for c in range(min(columns), max(columns) + 1)}


def self_check(grid, *, difficulty=None, meta=None):
    """Broad teaching grammar; generated layouts are a constructive subset."""
    errors = rule_grid_errors(grid)
    if errors:
        return errors
    chambers = _components(grid)
    if len(chambers) < 2:
        errors.append("need at least two non-5 chambers")
    visible = [(cells, _red_count(grid, cells)) for cells in chambers
               if any(grid[r][c] == 0 for r, c in cells)]
    if not any(count == 2 for _, count in visible):
        errors.append("need a two-red chamber with an original zero")
    if not any(count != 2 for _, count in visible):
        errors.append("need a contrasting chamber with an original zero")
    return errors


def observe_overrides(grid):
    errors = rule_grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def strict_canonical_like(grid):
    """Recognize canonical geometry without reading or memorizing examples."""
    errors = self_check(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not (10 <= height <= 12 and 10 <= width <= 12):
        errors.append("canonical dimensions are 10..12 on each axis")
    if any(value not in (0, 2, 5) for row in grid for value in row):
        errors.append("canonical palette is 0,2,5")
    wall_rows = [r for r, row in enumerate(grid) if all(value == 5 for value in row)]
    wall_cols = [c for c in range(width) if all(grid[r][c] == 5 for r in range(height))]
    if (len(wall_rows) != 3 or len(wall_cols) != 3
            or wall_rows[0] != 0 or wall_rows[-1] != height - 1
            or wall_cols[0] != 0 or wall_cols[-1] != width - 1):
        errors.append("need a full frame and one internal wall on each axis")
    elif any(b - a < 3 for walls in (wall_rows, wall_cols) for a, b in zip(walls, walls[1:])):
        errors.append("canonical room side lengths are at least two")
    if any(grid[r][c] == 5 and r not in wall_rows and c not in wall_cols
           for r in range(height) for c in range(width)):
        errors.append("canonical walls are full rows and columns")
    chambers = _components(grid)
    if len(chambers) != 4 or any(cells != _box_cells(cells) for cells in chambers):
        errors.append("need four solid rectangular chambers")
    if any(_red_count(grid, cells) > 3 for cells in chambers):
        errors.append("canonical chamber red counts lie in 0..3")
    return errors


def reference_model(grid):
    """Authoring diagnostic only. Dataset labels always come from Racket."""
    answer = [row[:] for row in grid]
    for cells in _components(grid):
        if _red_count(grid, cells) == 2:
            for r, c in cells:
                if grid[r][c] == 0:
                    answer[r][c] = 8
    return answer


def _red_objects(grid, cells):
    masked = [[5] * len(grid[0]) for _ in grid]
    for r, c in cells:
        if grid[r][c] == 2:
            masked[r][c] = 2
    return len(_components(masked))


def _distances(cells, starts):
    distances = {cell: 0 for cell in starts}
    queue = deque(sorted(starts))
    while queue:
        r, c = queue.popleft()
        for dr, dc in _D4:
            neighbor = r + dr, c + dc
            if neighbor in cells and neighbor not in distances:
                distances[neighbor] = distances[(r, c)] + 1
                queue.append(neighbor)
    return distances


def _rival_prediction(grid, mode):
    """Literal, finite alternative rules; none participates in input sampling."""
    answer = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    if mode == "full_line_partition":
        wall_rows = [r for r, row in enumerate(grid) if all(value == 5 for value in row)]
        wall_cols = [c for c in range(width) if all(row[c] == 5 for row in grid)]
        partitions = {}
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value != 5:
                    key = sum(wall < r for wall in wall_rows), sum(wall < c for wall in wall_cols)
                    partitions.setdefault(key, set()).add((r, c))
        chambers = list(partitions.values())
    elif mode == "eight_connected_rooms":
        chambers = _components(grid, diagonal=True)
    elif mode == "zero_red_only_passable":
        chambers = _components(grid, allowed=lambda value: value in (0, 2))
    elif mode == "eight_as_wall":
        chambers = _components(grid, allowed=lambda value: value not in (5, 8))
    else:
        chambers = _components(grid)
    for cells in chambers:
        scanned = _box_cells(cells) if mode == "component_bbox_seed_count" else cells
        reds = {(r, c) for r, c in scanned if grid[r][c] == 2}
        count = len(reds)
        if mode == "all_nonwall_marks_are_seeds":
            count = sum(grid[r][c] not in (0, 5) for r, c in scanned)
        elif mode == "red_plus_eight_seed_count":
            count = sum(grid[r][c] in (2, 8) for r, c in scanned)
        elif mode == "two_red_objects_four":
            count = _red_objects(grid, scanned)
        qualifies = count == 2
        if mode == "positive_even_seed_count":
            qualifies = count > 0 and count % 2 == 0
        elif mode == "two_modulo_three":
            qualifies = count % 3 == 2
        elif mode == "two_or_at_least_four":
            qualifies = count == 2 or count >= 4
        elif mode == "at_least_two":
            qualifies = count >= 2
        elif mode == "one_or_two":
            qualifies = 1 <= count <= 2
        elif mode == "cyan_marker_activates":
            qualifies = qualifies or any(grid[r][c] == 8 for r, c in cells)
        elif mode == "foreign_marker_activates":
            qualifies = qualifies or any(grid[r][c] in _FOREIGN_COLORS for r, c in cells)
        elif mode == "nearby_red_pair_only":
            qualifies = count == 2 and max(
                abs(r - rr) + abs(c - cc) for r, c in reds for rr, cc in reds
            ) <= 8
        elif mode == "boundary_component_activates":
            qualifies = qualifies or any(
                r in (0, height - 1) or c in (0, width - 1) for r, c in cells
            )
        elif mode == "boundary_or_thick_shape_selector" and cells != _box_cells(cells):
            qualifies = any(r in (0, height - 1) or c in (0, width - 1)
                            for r, c in cells) or any(
                {(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)} <= cells
                for r, c in cells
            )
        if not qualifies:
            continue
        rectangle = cells == _box_cells(cells)
        open_boundary = any(r in (0, height - 1) or c in (0, width - 1) for r, c in cells)
        if mode == "solid_rectangles_only" and not rectangle:
            continue
        if mode == "enclosed_rooms_only" and open_boundary:
            continue
        if mode == "rectangles_or_open_components" and not (rectangle or open_boundary):
            continue
        if mode == "rectangles_or_thin_paths" and not rectangle and any(
            {(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)} <= cells for r, c in cells
        ):
            continue
        if mode == "rectangles_or_trees" and not rectangle:
            edges = sum((r + dr, c + dc) in cells for r, c in cells for dr, dc in ((0, 1), (1, 0)))
            if edges != len(cells) - 1:
                continue
        distances = _distances(cells, reds) if mode == "graph_flood_at_most_max_dimension" else {}
        painted = _box_cells(cells) if mode == "component_bbox_fill" else cells
        for r, c in painted:
            if mode == "nearest_seed_radius_eight" and min(
                abs(r - sr) + abs(c - sc) for sr, sc in reds
            ) > 8:
                continue
            if mode == "graph_flood_at_most_max_dimension" and distances[(r, c)] > max(height, width):
                continue
            if grid[r][c] == 0 or (mode == "paint_every_nonwall_nonred_cell"
                                   and grid[r][c] not in (2, 5)):
                answer[r][c] = 8
    return answer


def _rival(mode):
    def predict(grid):
        return _rival_prediction(grid, mode)
    predict.__name__ = mode
    return predict


CANONICAL_SHORTCUTS = {
    name: _rival(name) for name in (
        "full_line_partition", "eight_connected_rooms", "zero_red_only_passable",
        "component_bbox_fill", "component_bbox_seed_count", "solid_rectangles_only",
        "positive_even_seed_count", "two_modulo_three", "two_or_at_least_four",
        "all_nonwall_marks_are_seeds", "paint_every_nonwall_nonred_cell",
        "nearest_seed_radius_eight", "enclosed_rooms_only", "rectangles_or_thin_paths",
        "rectangles_or_trees", "rectangles_or_open_components",
        "graph_flood_at_most_max_dimension", "eight_as_wall",
        "red_plus_eight_seed_count", "cyan_marker_activates", "foreign_marker_activates",
        "nearby_red_pair_only", "boundary_component_activates", "boundary_or_thick_shape_selector",
    )
}
SEMANTIC_RIVALS = {
    **CANONICAL_SHORTCUTS,
    **{name: _rival(name) for name in ("two_red_objects_four", "at_least_two", "one_or_two")},
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness(rival):
    def differs(grid):
        return not rule_grid_errors(grid) and reference_model(grid) != rival(grid)
    return differs


SEMANTIC_WITNESSES = {name: _witness(rival) for name, rival in SEMANTIC_RIVALS.items()}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_WITNESSES}


def lesson_identifiable(demos, query):
    """Return finite-bank ambiguity reasons, respecting the supplied labels.

    A rival fitting the demonstrations is a problem only if it contradicts a
    supplied query label. This does not certify uniqueness among arbitrary rules.
    """
    queries = query if isinstance(query, list) else [query]
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if any(rival(pair["input"]) != pair["output"] for pair in queries):
                reasons.append(f"{name} fits the supplied demonstrations but contradicts the query")
    return reasons

