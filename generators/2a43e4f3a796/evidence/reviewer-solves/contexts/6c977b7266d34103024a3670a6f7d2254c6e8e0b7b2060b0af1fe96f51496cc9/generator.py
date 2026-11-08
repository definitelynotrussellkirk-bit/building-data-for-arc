"""Inputs for stable, independent downward compaction of nonzero column cells.

The Racket rule is the label authority. Python transformations below are named
adversarial hypotheses and witness diagnostics, never generated labels.
Ordinary draws mix dense teaching, sparse long-column teaching, and free draws.
Exact overrides are research controls; their lessons need separate checking.
"""
from __future__ import annotations

from collections import Counter
from math import ceil

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2a43e4f3a796"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "7b698fc27b90"
SUMMARY = (
    "Compact each column's nonzero cells to the bottom, retaining multiplicity "
    "and top-to-bottom order. Zero is background even when another color is "
    "more frequent; gray 5 moves like every other nonzero color."
)
INVARIANTS = [
    "rectangular ARC grids with integer colors 0..9; zero is the fixed background",
    "columns are independent; all nonzero values and their relative order survive",
    "occupied bottom cells, singleton columns, and canonical height 7 are supported",
    "ordinary teaching draws distinguish gray barriers, five-cell capacity, and modal background",
    "blank, singleton, full, and already-compacted grids are lawful edge inputs",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical mixture; teaching 7..24, free 3..24", "valid": "3..24"},
    "grid_w": {"type": "int", "default": "canonical mixture; teaching 6..18, free 2..18", "valid": "2..18"},
    "active_cols": {"type": "int", "default": "all columns for teaching; 1..grid_w for free", "valid": "1..18"},
    "n_distinct_colors": {"type": "int", "default": "canonical mixture, bounded by occupied capacity", "valid": "1..9"},
    # These are overlapping construction modes, not uniquely recoverable classes:
    # a scattered draw can by chance already be settled. Exact sizes/counts still apply.
    "texture": {"type": "str", "default": "scattered", "valid": "scattered|all_at_bottom|single_value_columns|no_cells", "probe": "diagnostic"},
}
# Retain one compatibility spelling, without counting an alias as an independent axis.
OVERRIDE_ALIASES = {"palette_size": "n_distinct_colors"}
HELPFUL_TEXTURES = ("scattered", "all_at_bottom", "single_value_columns", "no_cells")
DEGENERATE_TEXTURES = ()
LAWFUL_DEGENERATE_TEXTURES = ("all_at_bottom", "single_value_columns", "no_cells")
SOLID_OUTPUT_JUSTIFICATION = (
    "Stable column compaction is defined on every rectangular ARC grid. A blank "
    "or solid input remains blank or solid; these are explicit lawful endpoints."
)
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    ("grid_w", "active_cols"),
    ("grid_h", "active_cols", "n_distinct_colors"),
    ("grid_h", "grid_w", "n_distinct_colors"),
    ("palette_size", "n_distinct_colors"),
    {"texture": "no_cells", "active_cols": None},
    {"texture": "no_cells", "n_distinct_colors": None},
    {"texture": "single_value_columns", "active_cols": None, "n_distinct_colors": None},
    {"texture": "single_value_columns", "grid_w": None, "n_distinct_colors": None},
]
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 5
SCHEDULE_PROFILES = ("dense_teaching", "sparse_teaching", "free")
_PROFILE_CYCLE = ("dense_teaching", "sparse_teaching", "dense_teaching", "sparse_teaching", "free")
_CANONICAL_PROFILES = ((7, 8, 6), (8, 8, 8), (7, 9, 8), (8, 7, 6), (7, 7, 8))


def schedule_profile(seed, sample_index, difficulty=None):
    return _PROFILE_CYCLE[sample_index % LESSON_SCHEDULE_PERIOD]


def _conflict(message, overrides):
    error = ValueError(message)
    error.incompatible_axes = tuple(sorted(overrides))
    raise error


def _normalize(overrides):
    unknown = set(overrides) - set(AXES) - set(OVERRIDE_ALIASES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    values = {name: value for name, value in overrides.items() if value is not None}
    for name in ("grid_h", "grid_w", "active_cols", "n_distinct_colors", "palette_size"):
        if name in values and type(values[name]) is not int:
            raise ValueError(f"{name} must be an integer, not {type(values[name]).__name__}")
    for name, (lo, hi) in {"grid_h": (3, 24), "grid_w": (2, 18), "active_cols": (1, 18),
                            "n_distinct_colors": (1, 9), "palette_size": (1, 9)}.items():
        if name in values and not lo <= values[name] <= hi:
            raise ValueError(f"{name} outside [{lo}, {hi}]")
    if "palette_size" in values:
        if "n_distinct_colors" in values and values["palette_size"] != values["n_distinct_colors"]:
            _conflict("palette_size and n_distinct_colors must agree", values)
        values["n_distinct_colors"] = values.pop("palette_size")
    if "texture" in values and values["texture"] not in HELPFUL_TEXTURES:
        raise ValueError(f"unknown texture {values['texture']!r}")
    return values


def _draw_axis(ctx, name, lo, hi, anchor, *, weight=30):
    if hi < lo:
        _conflict(f"no feasible {name} in [{lo}, {hi}]", ctx.overrides)
    if name in ctx.overrides:
        value = ctx.overrides[name]
        if not lo <= value <= hi:
            _conflict(f"{name}={value} is incompatible with capacity [{lo}, {hi}]", ctx.overrides)
        return ctx.draw_int_strict(name, lo, hi)
    options = list(range(lo, hi + 1))
    if lo <= anchor <= hi:
        options.extend([anchor] * weight)
    return ctx.draw_choice(name, options)


def _teaching_grid(ctx, h, w, k, sample_index, *, dense):
    """A long, gapped column with either zero or a foreground color as the mode."""
    rng = ctx.draw_rng("teaching_layout")
    dominant = ctx.draw_color("dominant_color", exclude=(0,))
    other = 5 if dominant != 5 else rng.choice([c for c in range(1, 10) if c != 5])
    palette = [dominant, other]
    palette.extend(rng.sample([c for c in range(1, 10) if c not in palette], k - 2))
    # Dense: the dominant exceeds zero. Sparse: hw > 2(h+w-2), so zero
    # dominates despite the long column. This breaks conditional capacity rivals.
    occupied = max(h + w - 2, (h * w + k - 1) // 2 + 1, k + 2) if dense else h + w - 2
    main = (sample_index // 2) % w
    counts = [1] * w
    counts[main] = h - 1
    for _ in range(occupied - sum(counts)):
        candidates = [c for c in range(w) if c != main and counts[c] < h - 2]
        if not candidates:
            raise RuntimeError("teaching capacity calculation failed")
        counts[rng.choice(candidates)] += 1
    rows = {}
    gap = rng.randint(2, h - 2)
    rows[main] = [r for r in range(h) if r != gap]
    for c in range(w):
        if c != main:
            rows[c] = sorted(rng.sample(range(h), counts[c]))
    g = full_grid(h, w, 0)
    positions = [(r, c) for c in range(w) for r in rows[c]]
    for r, c in positions:
        g[r][c] = dominant
    # Prefix a,b,a and suffix a: neither numeric sort nor reversal can reproduce it.
    main_rows = rows[main]
    reserved = {(main_rows[i], main) for i in (0, 1, 2, len(main_rows) - 1)}
    g[main_rows[1]][main] = other
    free = [p for p in positions if p not in reserved]
    for (r, c), color in zip(rng.sample(free, k - 2), palette[2:]):
        g[r][c] = color
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    values = _normalize(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=values)
    texture = ctx.draw_choice("texture", ("scattered",)) if "texture" not in values else ctx.draw_choice("texture", HELPFUL_TEXTURES)
    profile = schedule_profile(seed, sample_index, difficulty)
    teaching = not values and profile != "free"
    profiles = list(_CANONICAL_PROFILES)
    profiles += [profiles[{"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 1)]] * 3
    anchor_h, anchor_w, anchor_k = ctx.draw_choice("canonical_profile", profiles)
    requested_k = values.get("n_distinct_colors", 1)
    requested_a = values.get("active_cols")
    single = texture == "single_value_columns"
    if texture == "no_cells" and (requested_a is not None or "n_distinct_colors" in values):
        _conflict("no_cells is incompatible with positive active_cols or n_distinct_colors", values)
    if single and requested_a is not None and requested_a < requested_k:
        _conflict("single_value_columns requires active_cols >= n_distinct_colors", values)
    max_per_column = 1 if single else values.get("grid_h", 24)
    min_width = max(6 if teaching else 2, requested_a or 1,
                    ceil(requested_k / max_per_column) if requested_a is None else 1)
    w = _draw_axis(ctx, "grid_w", min_width, 18, anchor_w, weight=160)
    min_height = max(7 if teaching else 3, ceil(requested_k / (requested_a or w)) if not single else 3)
    h = _draw_axis(ctx, "grid_h", min_height, 24, anchor_h, weight=200)
    if texture == "no_cells":
        return full_grid(h, w, 0)
    capacity = (requested_a or w) * (1 if single else h)
    k = _draw_axis(ctx, "n_distinct_colors", 3 if teaching else 1,
                   min(9, capacity), anchor_k, weight=90)
    count_limit = 1 if single else (h if values else min(5, h))
    min_active = max(1, ceil(k / count_limit))
    if teaching:
        active = ctx.draw_choice("active_cols", (w,))
        return _teaching_grid(ctx, h, w, k, sample_index, dense=profile == "dense_teaching")
    active = _draw_axis(ctx, "active_cols", min_active, w,
                        max(min_active, min(w, 4 if difficulty == "easy" else 6)), weight=8)
    rng = ctx.draw_rng("free_layout")
    columns = rng.sample(range(w), active)
    counts = [1 if single else rng.randint(1, min(5, h)) for _ in columns]
    # Capacity was validated above. Increase occupation before assigning colors;
    # no requested color can disappear because of a sparse random draw.
    while sum(counts) < k:
        candidates = [i for i, count in enumerate(counts) if count < count_limit]
        counts[rng.choice(candidates)] += 1
    positions = []
    for c, count in zip(columns, counts):
        selected = list(range(h - count, h)) if texture == "all_at_bottom" else sorted(rng.sample(range(h), count))
        positions.extend((r, c) for r in selected)
    palette = ctx.draw_distinct_colors("palette", n=k, exclude=(0,))
    colors = list(palette) + [rng.choice(palette) for _ in range(len(positions) - k)]
    rng.shuffle(colors)
    g = full_grid(h, w, 0)
    for (r, c), color in zip(positions, colors):
        g[r][c] = color
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the rule's full rectangular ARC domain, including lawful endpoints."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["expected a nonempty list of nonempty rows"]
    h, w = len(grid), len(grid[0])
    if not (1 <= h <= 30 and 1 <= w <= 30):
        return ["ARC dimensions must be in 1..30"]
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["colors must be integers 0..9, excluding booleans"]
    return []


def strict_canonical_like(grid):
    # The manifold is the total column-gravity domain, not a canonical-size whitelist.
    return self_check(grid)


def observe_overrides(grid):
    colors = {value for row in grid for value in row if value != 0}
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "active_cols": sum(any(col) for col in zip(*grid)),
            "n_distinct_colors": len(colors), "palette_size": len(colors)}


def mutation_fixtures():
    return [("ragged", [[0, 1], [0]]), ("boolean", [[True, 0]]),
            ("negative_color", [[-1, 0]]), ("noninteger", [[1.5, 0]])]


# Adversarial hypotheses below are diagnostic Python, not reference labels.
def _pack(grid, transform=None, background=0):
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, background)
    for c, column in enumerate(zip(*grid)):
        values = [value for value in column if value != background]
        if transform is not None:
            values = transform(values)
        for r, value in enumerate(values, h - len(values)):
            out[r][c] = value
    return out


def _gray_barriers(grid):
    out = [row[:] for row in grid]
    h = len(grid)
    for c, column in enumerate(zip(*grid)):
        boundaries = [-1] + [r for r, value in enumerate(column) if value == 5] + [h]
        for start, stop in zip(boundaries, boundaries[1:]):
            values = [grid[r][c] for r in range(start + 1, stop) if grid[r][c] != 0]
            for r in range(start + 1, stop):
                out[r][c] = 0
            for r, value in enumerate(values, stop - len(values)):
                out[r][c] = value
    return out


def _cap_five(grid):
    return _pack(grid, lambda values: values[-5:])


def _mode(grid):
    counts = Counter(value for row in grid for value in row)
    return min(counts, key=lambda value: (-counts[value], value))


def _modal_background(grid):
    return _pack(grid, background=_mode(grid))


def _zero_modal_cap(grid):
    """Rival: use a five-cell capacity only on grids whose modal color is zero."""
    return _cap_five(grid) if _mode(grid) == 0 else _pack(grid)


def _ignore_bottom(grid):
    truncated = [row[:] for row in grid]
    truncated[-1] = [0] * len(grid[0])
    return _pack(truncated)


def _reverse(grid):
    return _pack(grid, lambda values: values[::-1])


def _sort_ascending(grid):
    return _pack(grid, sorted)


def _sort_descending(grid):
    return _pack(grid, lambda values: sorted(values, reverse=True))


def _rigid_columns(grid):
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for c, column in enumerate(zip(*grid)):
        occupied = [r for r, value in enumerate(column) if value != 0]
        if occupied:
            shift = h - 1 - occupied[-1]
            for r in occupied:
                out[r + shift][c] = grid[r][c]
    return out


def _rightward(grid):
    return [[0] * row.count(0) + [value for value in row if value != 0] for row in grid]


def _identity(grid):
    return [row[:] for row in grid]


def _gray_moves(grid):
    return any(value == 5 and 0 in column[r + 1:]
               for column in zip(*grid) for r, value in enumerate(column))


def _long_column(grid):
    return any(sum(value != 0 for value in column) > 5 for column in zip(*grid))


def _bottom_occupied(grid):
    return any(grid[-1])


def _nonzero_mode_with_gap(grid):
    mode = _mode(grid)
    return mode != 0 and any(mode in column and 0 in column for column in zip(*grid))


def _zero_mode_long_column(grid):
    return _mode(grid) == 0 and _long_column(grid)


def _order_sensitive(grid):
    for column in zip(*grid):
        values = [value for value in column if value]
        if values != values[::-1] and values != sorted(values) and values != sorted(values, reverse=True):
            return True
    return False


def _internal_gap(grid):
    for column in zip(*grid):
        occupied = [r for r, value in enumerate(column) if value]
        if occupied and 0 in column[occupied[0]:occupied[-1]]:
            return True
    return False


def _vertical_motion(grid):
    return any(grid[0]) and all(0 in column for column in zip(*grid))


CANONICAL_SHORTCUTS = {"gray5_fixed_barrier": _gray_barriers,
                       "bottom_five_capacity": _cap_five,
                       "modal_background": _modal_background,
                       "zero_modal_cap": _zero_modal_cap}
LESSON_COMPETITORS = {
    **CANONICAL_SHORTCUTS,
    "ignore_bottom_row": _ignore_bottom, "reverse_order": _reverse,
    "sort_ascending": _sort_ascending, "sort_descending": _sort_descending,
    "rigid_column_translation": _rigid_columns,
    "right_compaction": _rightward, "identity": _identity,
}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
SEMANTIC_WITNESSES = {
    "gray_mobility": _gray_moves, "long_column": _long_column,
    "bottom_participation": _bottom_occupied, "nonzero_modal_background": _nonzero_mode_with_gap,
    "zero_modal_long_column": _zero_mode_long_column,
    "order_preservation": _order_sensitive, "internal_gap_removal": _internal_gap,
    "vertical_motion": _vertical_motion,
}
WITNESS_RIVALS = {
    "gray_mobility": ["gray5_fixed_barrier"], "long_column": ["bottom_five_capacity"],
    "bottom_participation": ["ignore_bottom_row"], "nonzero_modal_background": ["modal_background"],
    "zero_modal_long_column": ["zero_modal_cap"],
    "order_preservation": ["reverse_order", "sort_ascending", "sort_descending"],
    "internal_gap_removal": ["rigid_column_translation"],
    "vertical_motion": ["right_compaction", "identity"],
}
