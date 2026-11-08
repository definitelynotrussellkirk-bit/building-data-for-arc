"""Collision-free completion across the main diagonal.

The canonical Racket authority remains (overlay g (transpose g)). Inputs may
use either triangle and the diagonal. Conflicting occupied mirror partners are
outside this completion domain; the unrestricted overlay would swap them.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "17f92e205b34"
VERSION = "1.2.0"
RULE_HASH = "2b970065d6a3"
SUMMARY = "Complete a colored pattern across the main diagonal, preserving its source cells."
INVARIANTS = [
    "square integer-color grid of size 1..30, with background 0",
    "source cells may be above, below, or on the main diagonal",
    "occupied mirror partners have equal colors; conflicting colors are excluded",
    "at least one off-diagonal source has an empty mirror partner",
]
AXES = {
    "size": {"type": "int", "default": "core 6|7; otherwise varied 6..16", "valid": "6..16"},
    "markers": {"type": "int", "default": "core 3|4; otherwise varied 3..12", "valid": "3..12"},
    "palette_size": {"type": "int", "default": "core 2; otherwise 1..3", "valid": "1..3"},
    "diagonal_markers": {"type": "int", "default": "teaching 1; otherwise 0..2", "valid": "0..2"},
}
# Independent axes: even size=6, markers=12, diagonal_markers=0 is constructive.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("teaching_core", "teaching_broad", "ordinary_core", "ordinary_broad")


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % 4]


def _axis(ctx, overrides, name, lo, hi, choices):
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, choices)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    core, teaching = profile.endswith("_core"), profile.startswith("teaching_")
    favored_sizes = list(range(6, 10)) if difficulty == "easy" else (
        list(range(10, 17)) if difficulty == "hard" else list(range(6, 17)))
    favored_counts = list(range(3, 7)) if difficulty == "easy" else (
        list(range(7, 13)) if difficulty == "hard" else list(range(3, 13)))
    n = _axis(ctx, overrides, "size", 6, 16, (6, 7) if core else list(range(6, 17)) + favored_sizes)
    markers = _axis(ctx, overrides, "markers", 3, 12, (3, 4) if core else list(range(3, 13)) + favored_counts)
    palette_size = _axis(ctx, overrides, "palette_size", 1, 3, (2,) if core else (1, 2, 2, 2, 3))
    diagonal = _axis(ctx, overrides, "diagonal_markers", 0, 2, (1,) if teaching else (0, 1, 2))
    off_count = markers - diagonal
    layout = ctx.draw_rng("layout")
    orbits = [(r, c) for r in range(n) for c in range(r + 1, n)]
    positions = []
    used = set()

    if teaching:
        # An empty mirror partner on coordinate zero at distance >=3 refutes
        # two shortcuts that fit every canonical pair. Avoid the anti-diagonal.
        anchor = (0, layout.randrange(3, n - 1))
        upper = ctx.draw_choice("anchor_side", (True, False))
        positions.append(anchor if upper else anchor[::-1])
        used.add(anchor)
        # Without the anchor's 180-degree counterpart, anti-diagonal reflection
        # cannot fill its main-diagonal destination. This is a semantic witness,
        # and leaves at least 14 orbits for the maximum 12 off-diagonal sources.
        reserved = (n - 1 - anchor[1], n - 1)
        if off_count >= 2:
            second = layout.choice([(c, r) for r in range(2, n - 1) for c in range(1, r)])
            positions.append(second[::-1] if upper else second)
            used.add(second)
        for orbit in layout.sample([p for p in orbits if p not in used and p != reserved],
                                   off_count - len(positions)):
            positions.append(orbit if layout.randrange(2) else orbit[::-1])
    else:
        chosen = layout.sample(orbits, off_count)
        modes = ("upper", "lower", "mixed") if off_count >= 2 else ("upper", "lower")
        mode = ctx.draw_choice("source_side", modes)
        if mode == "mixed":
            sides = [True, False] + [bool(layout.randrange(2)) for _ in range(off_count - 2)]
            layout.shuffle(sides)
        else:
            sides = [mode == "upper"] * off_count
        positions.extend(orbit if upper else orbit[::-1] for orbit, upper in zip(chosen, sides))

    positions.extend((i, i) for i in ctx.draw_rng("diagonal_positions").sample(range(n), diagonal))
    palette = ctx.draw_distinct_colors("colors", n=palette_size, exclude=(0,))
    colors_rng = ctx.draw_rng("cell_colors")
    colors = list(palette) + [colors_rng.choice(palette) for _ in range(markers - palette_size)]
    colors_rng.shuffle(colors)
    grid = full_grid(n, n, 0)
    for (r, c), color in zip(positions, colors):
        grid[r][c] = color
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the completion domain; metadata never bypasses real checks."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty square grid"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["rows must be sequences"]
    n = len(grid)
    if not 1 <= n <= 30 or any(len(row) != n for row in grid):
        return ["grid must be square with size 1..30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9, excluding booleans"]
    if not any(value == 0 for row in grid for value in row):
        return ["background 0 must be present"]
    if any(grid[r][c] and grid[c][r] and grid[r][c] != grid[c][r]
           for r in range(n) for c in range(r + 1, n)):
        return ["conflicting occupied mirror partners are outside the completion domain"]
    if not any(bool(grid[r][c]) != bool(grid[c][r])
               for r in range(n) for c in range(r + 1, n)):
        return ["at least one off-diagonal source must have an empty mirror partner"]
    return []


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    cells = [(r, c, value) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value]
    return {
        "size": len(grid),
        "markers": len(cells),
        "palette_size": len({value for _, _, value in cells}),
        "diagonal_markers": sum(r == c for r, c, _ in cells),
    }


def _restricted_reflection(grid, keep):
    """Deliberately incomplete rival, never a source of training labels."""
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value and keep(r, c):
                out[c][r] = value
    return out


def _near_diagonal_only(grid):
    return _restricted_reflection(grid, lambda r, c: abs(r - c) <= 2)


def _ignore_coordinate_zero(grid):
    return _restricted_reflection(grid, lambda r, c: r > 0 and c > 0)


def _upper_only(grid):
    return _restricted_reflection(grid, lambda r, c: r < c)


def _lower_only(grid):
    return _restricted_reflection(grid, lambda r, c: r > c)


def _identity(grid):
    return [list(row) for row in grid]


def _transpose_only(grid):
    return [list(row) for row in zip(*grid)]


def _delete_diagonal(grid):
    out = [[grid[c][r] or grid[r][c] for c in range(len(grid))] for r in range(len(grid))]
    for i in range(len(grid)):
        out[i][i] = 0
    return out


def _anti_diagonal(grid):
    n = len(grid)
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                out[n - 1 - c][n - 1 - r] = value
    return out


def _unmatched(grid, predicate):
    return any(value and r != c and grid[c][r] == 0 and predicate(r, c)
               for r, row in enumerate(grid) for c, value in enumerate(row))


def _far_source(grid):
    return _unmatched(grid, lambda r, c: abs(r - c) > 2)


def _zero_edge_source(grid):
    return _unmatched(grid, lambda r, c: r == 0 or c == 0)


def _upper_source(grid):
    return _unmatched(grid, lambda r, c: r < c)


def _lower_source(grid):
    return _unmatched(grid, lambda r, c: r > c)


def _diagonal_source(grid):
    return any(grid[i][i] != 0 for i in range(len(grid)))


SEMANTIC_WITNESSES = {
    "far_source": _far_source, "coordinate_zero_source": _zero_edge_source,
    "upper_source": _upper_source, "lower_source": _lower_source,
    "preserved_diagonal": _diagonal_source,
}
SEMANTIC_RIVALS = {
    "near_diagonal_only": _near_diagonal_only,
    "ignore_coordinate_zero": _ignore_coordinate_zero,
    "upper_only": _upper_only, "lower_only": _lower_only,
    "delete_diagonal": _delete_diagonal,
}
WITNESS_RIVALS = {
    "far_source": ["near_diagonal_only"],
    "coordinate_zero_source": ["ignore_coordinate_zero"],
    "upper_source": ["lower_only"], "lower_source": ["upper_only"],
    "preserved_diagonal": ["delete_diagonal"],
}
CANONICAL_SHORTCUTS = {
    "near_diagonal_only": _near_diagonal_only,
    "ignore_coordinate_zero": _ignore_coordinate_zero,
}
LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS, "identity": _identity, "transpose_only": _transpose_only,
    "anti_diagonal": _anti_diagonal,
}
