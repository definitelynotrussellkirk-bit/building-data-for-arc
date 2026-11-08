"""Sample lawful crosses for 67a423a3; Racket supplies every output label.

The fixed rule paints the eight-cell yellow (4) ring around the crossing,
including the line arms, while preserving its original centre color.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "95524d104174"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "aeef8458b6d7"
SUMMARY = (
    "A zero-background grid contains one full-height vertical line and one "
    "full-width horizontal line in distinct nonzero colors. Either line may "
    "win at their interior intersection. Paint all eight surrounding cells "
    "yellow (4), overwriting both background and line arms; preserve the "
    "intersection and every cell outside its 3x3 neighborhood. Sample square "
    "and rectangular grids, margin-one crossings, all line colors, and both "
    "overlap winners."
)
INVARIANTS = [
    "exactly one full-height column and full-width row form a clean cross",
    "two distinct integer nonzero line colors; all off-cross cells are zero",
    "the intersection keeps either original line color and is at least one cell from each edge",
    "sampled dimensions are 4..14; the structural validator accepts lawful 4..30 grids",
]
AXES = {
    "grid_h": {"type": "int", "default": "scheduled core and broad 4..14", "valid": "4..14"},
    "grid_w": {"type": "int", "default": "scheduled core and broad 4..14", "valid": "4..14"},
    "vertical_color": {"type": "int", "default": "uniform 1..9", "valid": "1..9"},
    "horizontal_color": {"type": "int", "default": "uniform distinct 1..9", "valid": "1..9"},
    "crossing_winner": {"type": "int", "default": "0 vertical or 1 horizontal", "valid": "0..1"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"vertical_color": color, "horizontal_color": color} for color in range(1, 10)
]
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (0, 1, 2, 3)


def schedule_profile(seed, sample_index, difficulty=None):
    """Semantic schedule only; keyed RNG still changes each concrete input."""
    return sample_index % LESSON_SCHEDULE_PERIOD


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    a, b = overrides.get("vertical_color"), overrides.get("horizontal_color")
    if a is not None and a == b:
        raise ValueError("vertical_color and horizontal_color must differ")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer, excluding bool")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer, excluding bool")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    active = any(value is not None for value in overrides.values())
    profile = schedule_profile(seed, sample_index, difficulty)
    # Exact controls select the full lawful Cartesian domain (except equal
    # colors). The teaching schedule applies only to unoverridden lessons.
    if active:
        h = ctx.draw_int("grid_h", 4, 14)
        w = ctx.draw_int("grid_w", 4, 14)
        winner = ctx.draw_int("crossing_winner", 0, 1)
    elif profile == 0:
        favored = (4, 4, 6) if difficulty == "easy" else ((12, 12, 8) if difficulty == "hard" else (6, 8))
        h = ctx.draw_choice("grid_h", (4, 6, 8, 12) + favored)
        w = ctx.draw_choice("grid_w", (h,))
        winner = ctx.draw_int("crossing_winner", 0, 1)
    elif profile == 1:
        h = ctx.draw_int("grid_h", 4, 12)
        w = ctx.draw_int("grid_w", h + 2, 14)
        winner = ctx.draw_choice("crossing_winner", (0,))
    elif profile == 3:
        w = ctx.draw_int("grid_w", 4, 12)
        h = ctx.draw_int("grid_h", w + 2, 14)
        winner = ctx.draw_choice("crossing_winner", (1,))
    else:
        # This unrestricted component includes near-square rectangles and
        # majority-color winners as well as every sampled size and position.
        h = ctx.draw_int("grid_h", 4, 14)
        w = ctx.draw_int("grid_w", 4, 14)
        winner = ctx.draw_int("crossing_winner", 0, 1)
    pinned_horizontal = overrides.get("horizontal_color")
    vertical = ctx.draw_choice("vertical_color", [v for v in range(1, 10) if v != pinned_horizontal])
    horizontal = ctx.draw_choice("horizontal_color", [v for v in range(1, 10) if v != vertical])
    positions = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)
                 if active or profile not in (1, 3) or r != c]
    row, col = ctx.draw_choice("intersection", positions)
    grid = full_grid(h, w, 0)
    for r in range(h):
        grid[r][col] = vertical
    for c in range(w):
        grid[row][c] = horizontal
    grid[row][col] = (vertical, horizontal)[winner]
    return grid


def _cross(grid):
    """Recognize structure from pixels, allowing either crossing winner."""
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)):
        raise ValueError("expected a nonempty rectangular grid")
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        raise ValueError("ragged grid")
    if not (4 <= h <= 30 and 4 <= w <= 30):
        raise ValueError("cross grids need 4..30 rows and columns")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be integer colors 0..9, excluding bool")
    rows = [r for r in range(h) if all(grid[r][c] != 0 for c in range(w))]
    cols = [c for c in range(w) if all(grid[r][c] != 0 for r in range(h))]
    if len(rows) != 1 or len(cols) != 1:
        raise ValueError("expected exactly one complete row and column")
    r, c = rows[0], cols[0]
    if not (1 <= r < h - 1 and 1 <= c < w - 1):
        raise ValueError("intersection must be interior with margin at least one")
    vertical, horizontal = grid[0][c], grid[r][0]
    if vertical == horizontal:
        raise ValueError("line colors must differ")
    if grid[r][c] not in (vertical, horizontal):
        raise ValueError("intersection must keep an original line color")
    for rr in range(h):
        for cc in range(w):
            if (rr, cc) == (r, c):
                continue
            expected = vertical if cc == c else (horizontal if rr == r else 0)
            if grid[rr][cc] != expected:
                raise ValueError("broken/nonuniform line or nonzero off-cross cell")
    return r, c, vertical, horizontal, int(grid[r][c] == horizontal)


def self_check(grid, *, difficulty=None, meta=None):
    try:
        _cross(grid)
    except ValueError as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    _, _, vertical, horizontal, winner = _cross(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "vertical_color": vertical,
            "horizontal_color": horizontal, "crossing_winner": winner}


def _rival_ring(grid, center=None, diagonals_only=False):
    """Shared construction for wrong-rule competitors, never a label authority."""
    r, c, _, _, _ = _cross(grid)
    if center is not None:
        r, c = center
    out = [list(row) for row in grid]
    for rr in range(max(0, r - 1), min(len(grid), r + 2)):
        for cc in range(max(0, c - 1), min(len(grid[0]), c + 2)):
            if (rr, cc) != (r, c) and (not diagonals_only or rr != r and cc != c):
                out[rr][cc] = 4
    return out


def _diagonals_only(grid):
    return _rival_ring(grid, diagonals_only=True)


def _row_coordinate_twice(grid):
    r, _, _, _, _ = _cross(grid)
    return _rival_ring(grid, center=(r, r))


def _column_coordinate_twice(grid):
    _, c, _, _, _ = _cross(grid)
    return _rival_ring(grid, center=(c, c))


def _modal_center(grid):
    r, c, _, _, _ = _cross(grid)
    counts = Counter(v for row in grid for v in row if v != 0)
    mode = min(counts, key=lambda v: (-counts[v], v))
    out = _rival_ring(grid)
    out[r][c] = mode
    return out


def _off_diagonal(grid):
    r, c, _, _, _ = _cross(grid)
    return r != c


def _minority_center(grid):
    r, c, vertical, horizontal, _ = _cross(grid)
    counts = Counter(v for row in grid for v in row if v != 0)
    return counts[grid[r][c]] < max(counts[vertical], counts[horizontal])


def _overwritten_arms(grid):
    _cross(grid)
    return True


SEMANTIC_RIVALS = {
    "diagonals_only": _diagonals_only,
    "row_coordinate_twice": _row_coordinate_twice,
    "column_coordinate_twice": _column_coordinate_twice,
    "modal_center": _modal_center,
}
SEMANTIC_WITNESSES = {
    "off_diagonal": _off_diagonal,
    "minority_center": _minority_center,
    "overwritten_arms": _overwritten_arms,
}
WITNESS_RIVALS = {
    "off_diagonal": ["row_coordinate_twice", "column_coordinate_twice"],
    "minority_center": ["modal_center"],
    "overwritten_arms": ["diagonals_only"],
}
CANONICAL_SHORTCUTS = {"modal_center": _modal_center}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite declared-rival claim only; the supplied labels come from Racket."""
    return [f"{name} fits demonstrations but changes query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
