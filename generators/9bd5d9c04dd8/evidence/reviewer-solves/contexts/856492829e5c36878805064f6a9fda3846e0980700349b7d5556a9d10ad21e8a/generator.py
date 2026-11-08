"""Generator for selecting the isolated 3×3 tile with the most color-1 cells.

The selected Racket authority scans row-major for orthogonally isolated,
fully-nonzero 3×3 tiles and returns the tile with the largest number of color-1
cells.  Generated instances use one shared nonzero fill color, distinct blue
counts, and no stray nonzero cells.  Default lessons deliberately vary the fill
away from canonical color 8 so that a color-8-specific shortcut is falsified.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9bd5d9c04dd8"
TASK_ID = GENERATOR_ID
RULE_HASH = "b484d9374fb6"
VERSION = "3.0.2"
SUMMARY = (
    "A zero-background grid contains 2–4 orthogonally isolated 3×3 tiles. "
    "Every tile is filled by color 1 and one shared nonzero fill color, and "
    "the color-1 counts are distinct. Return the tile with the most color-1 cells."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SOLID_OUTPUT_JUSTIFICATION = (
    "A lawful winner may contain nine color-1 cells, so the canonical rule "
    "can crop a solid 3x3 blue tile from a larger multi-tile input."
)

INVARIANTS = [
    "background is color 0",
    "2–4 isolated fully-nonzero 3×3 tiles and no other nonzero cells",
    "all tiles share one fill color in 2..9 in addition to color 1",
    "tile color-1 counts are distinct, so the winner is unambiguous",
    "default lessons put the winner after the first row-major tile",
]

AXES = {
    "grid_h": {"type": "int", "default": "9 (canonical); exact override", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "9 (canonical); exact override", "valid": "9..18"},
    "tile_count": {"type": "int", "default": "2/3/4 by band; uniform if unset", "valid": "2..4"},
    "fill_color": {"type": "color", "default": "rng 2..7|9; exact override includes 8", "valid": "2..9"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_DOMAINS = {
    "grid_h": tuple(range(8, 17)),
    "grid_w": tuple(range(9, 19)),
    "tile_count": (2, 3, 4),
    "fill_color": tuple(range(2, 10)),
}
_DEFAULT_FILL_COLORS = (2, 3, 4, 5, 6, 7, 9)


def _validate_call(seed, sample_index, difficulty):
    """Reject malformed request scalars before constructing generator state."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = min(_DOMAINS[name]), max(_DOMAINS[name])
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _draw_axis(ctx, name, default_options, overrides):
    """Draw an honest exact axis; explicit overrides retain the full domain."""
    options = _DOMAINS[name] if overrides.get(name) is not None else tuple(default_options)
    return ctx.draw_choice(name, options)


def _separated(a, b):
    """One blank row or column separates the two 3×3 bounding boxes."""
    return abs(a[0] - b[0]) >= 4 or abs(a[1] - b[1]) >= 4


def _choose_anchors(ctx, h, w, count):
    """Constructively choose ``count`` anchors; never silently shorten a draw."""
    candidates = [(r, c) for r in range(h - 2) for c in range(w - 2)]
    ctx.draw_rng("tile_positions").shuffle(candidates)
    chosen = []

    def search(start):
        if len(chosen) == count:
            return True
        needed = count - len(chosen)
        if len(candidates) - start < needed:
            return False
        for index in range(start, len(candidates)):
            point = candidates[index]
            if all(_separated(point, other) for other in chosen):
                chosen.append(point)
                if search(index + 1):
                    return True
                chosen.pop()
        return False

    if not search(0):
        raise RuntimeError(f"cannot place {count} isolated 3x3 tiles in {h}x{w}")
    return sorted(chosen)


def _assign_blue_counts(ctx, tile_count):
    """Return distinct counts with the unique maximum after row-major tile 0."""
    rng = ctx.draw_rng("blue_counts")
    values = sorted(rng.sample(range(10), tile_count))
    lower = values[:-1]
    rng.shuffle(lower)
    winner_index = ctx.draw_rng("winner_position").randrange(1, tile_count)
    assigned = []
    lower_index = 0
    for index in range(tile_count):
        if index == winner_index:
            assigned.append(values[-1])
        else:
            assigned.append(lower[lower_index])
            lower_index += 1
    return assigned


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty)
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Canonical data are all 9×9. Even schedule slots preserve that profile;
    # odd slots explore the full declared shape domain. Exact overrides always
    # supersede the schedule and remain available in every difficulty band.
    canonical_shape = sample_index % 2 == 0
    h_defaults = (9,) if canonical_shape else _DOMAINS["grid_h"]
    w_defaults = (9,) if canonical_shape else _DOMAINS["grid_w"]
    h = _draw_axis(ctx, "grid_h", h_defaults, overrides)
    w = _draw_axis(ctx, "grid_w", w_defaults, overrides)
    default_count = {
        "easy": (2,),
        "medium": (3,),
        "hard": (4,),
    }.get(difficulty, _DOMAINS["tile_count"])
    tile_count = _draw_axis(ctx, "tile_count", default_count, overrides)
    fill_options = _DOMAINS["fill_color"] if overrides.get("fill_color") is not None else _DEFAULT_FILL_COLORS
    fill_color = ctx.draw_choice("fill_color", fill_options)

    anchors = _choose_anchors(ctx, h, w, tile_count)
    blue_counts = _assign_blue_counts(ctx, tile_count)
    grid = full_grid(h, w, 0)
    pattern_rng = ctx.draw_rng("tile_patterns")
    local_cells = [(dr, dc) for dr in range(3) for dc in range(3)]
    for (r0, c0), blue_count in zip(anchors, blue_counts):
        for dr, dc in local_cells:
            grid[r0 + dr][c0 + dc] = fill_color
        for dr, dc in pattern_rng.sample(local_cells, blue_count):
            grid[r0 + dr][c0 + dc] = 1
    return grid


def _grid_error(grid):
    if not isinstance(grid, list) or not grid:
        return "grid must be a nonempty list"
    if any(not isinstance(row, list) or not row for row in grid):
        return "grid rows must be nonempty lists"
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return "grid must be rectangular"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "grid cells must be integer ARC colors 0..9"
    return None


def _isolated_tiles(grid):
    """Enumerate candidates with the selected Racket authority's geometry."""
    h, w = len(grid), len(grid[0])
    found = []
    for r0 in range(h - 2):
        for c0 in range(w - 2):
            if not all(grid[r0 + dr][c0 + dc] != 0 for dr in range(3) for dc in range(3)):
                continue
            if r0 and any(grid[r0 - 1][c0 + dc] != 0 for dc in range(3)):
                continue
            if r0 + 3 < h and any(grid[r0 + 3][c0 + dc] != 0 for dc in range(3)):
                continue
            if c0 and any(grid[r0 + dr][c0 - 1] != 0 for dr in range(3)):
                continue
            if c0 + 3 < w and any(grid[r0 + dr][c0 + 3] != 0 for dr in range(3)):
                continue
            tile = [row[c0:c0 + 3] for row in grid[r0:r0 + 3]]
            found.append((r0, c0, tile))
    return found


def _blue_count(tile):
    return sum(value == 1 for row in tile for value in row)


def _intended_output(grid):
    """Independent-of-sampling Python mirror used only for review hooks/tests."""
    error = _grid_error(grid)
    if error:
        raise ValueError(error)
    candidates = _isolated_tiles(grid)
    if not candidates:
        raise ValueError("no isolated 3x3 candidate")
    # Python max preserves the first item on ties, matching Racket's strict >.
    return max(candidates, key=lambda item: _blue_count(item[2]))[2]


def _most_non_eight_tile(grid):
    """Canonical-fit rival: select the tile with most cells not equal to 8."""
    error = _grid_error(grid)
    if error:
        raise ValueError(error)
    candidates = _isolated_tiles(grid)
    if not candidates:
        raise ValueError("no isolated 3x3 candidate")
    return max(
        candidates,
        key=lambda item: sum(value != 8 for row in item[2] for value in row),
    )[2]


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the generated teaching manifold without weakening the rule."""
    error = _grid_error(grid)
    if error:
        return [error]
    h, w = len(grid), len(grid[0])
    messages = []
    if not 8 <= h <= 16:
        messages.append(f"grid height {h} outside 8..16")
    if not 9 <= w <= 18:
        messages.append(f"grid width {w} outside 9..18")

    candidates = _isolated_tiles(grid)
    if not 2 <= len(candidates) <= 4:
        messages.append(f"expected 2..4 isolated tiles, found {len(candidates)}")

    covered = set()
    overlap = False
    for r0, c0, _ in candidates:
        cells = {(r0 + dr, c0 + dc) for dr in range(3) for dc in range(3)}
        overlap = overlap or bool(covered & cells)
        covered.update(cells)
    if overlap:
        messages.append("isolated tile candidates overlap")
    nonzero = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    if covered != nonzero:
        messages.append("every nonzero cell must belong to exactly one isolated 3x3 tile")
    if not any(value == 0 for row in grid for value in row):
        messages.append("background color 0 is absent")

    fills = {value for row in grid for value in row if value not in (0, 1)}
    if len(fills) != 1:
        messages.append(f"expected one shared fill color in 2..9, found {sorted(fills)}")
    if not any(value == 1 for row in grid for value in row):
        messages.append("color 1 is absent")

    counts = [_blue_count(tile) for _, _, tile in candidates]
    if len(counts) != len(set(counts)):
        messages.append("tile color-1 counts must be distinct")
    return messages


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    """Recover every advertised exact axis directly from returned pixels."""
    issues = self_check(grid)
    if issues:
        raise ValueError("; ".join(issues))
    candidates = _isolated_tiles(grid)
    fills = {value for row in grid for value in row if value not in (0, 1)}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "tile_count": len(candidates),
        "fill_color": next(iter(fills)),
    }


def _non_eight_shortcut_witness(grid):
    """True exactly when the canonical-fit color-8 shortcut is refuted."""
    try:
        return _intended_output(grid) != _most_non_eight_tile(grid)
    except ValueError:
        return False


SEMANTIC_WITNESSES = {"non_eight_shortcut": _non_eight_shortcut_witness}
SEMANTIC_RIVALS = {"most_non_eight": _most_non_eight_tile}
WITNESS_RIVALS = {"non_eight_shortcut": ["most_non_eight"]}
CANONICAL_SHORTCUTS = {"most_non_eight": _most_non_eight_tile}
LESSON_COMPETITORS = {"most_non_eight": _most_non_eight_tile}
