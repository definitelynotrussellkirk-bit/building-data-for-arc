"""Cyan-count inputs for b1fc8b8e; labels come from the unchanged Racket rule.

Count 8-cells, floor-divide by four, and repeat the specified 2x2 glyph in
four quadrants of a 5x5 zero-cross output. Geometry does not change the answer.
Counts 4..19 exercise every nonempty glyph and every remainder.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import permutations

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5dc10de63325"
TASK_ID = GENERATOR_ID
RULE_HASH = "f2b1ab0d6fcb"
VERSION = "4.0.0"
EXPECTED_OUTPUT_CODOMAIN = 4
EXAMPLES_NEEDED = 10
MIN_STRICT_FRAC = 1.0
SUMMARY = (
    "Count 4..19 cyan cells on a 5..18 by 5..18 zero background; floor-divide "
    "by four and repeat the prescribed 2x2 glyph across a 5x5 zero-cross. "
    "Five spatial distributions, canonical-size support in every band, exact "
    "dimension/count controls, and ten-demo lessons with repeated glyph witnesses."
)
INVARIANTS = [
    "rectangular integer grid; height and width each 5..18",
    "only background 0 and cyan 8; at least one background cell",
    "exactly 4..19 cyan cells; floor(count/4) is one of 1,2,3,4",
    "cyan geometry and connectivity do not affect the authoritative output",
]
DISTRIBUTIONS = ("clustered", "row_aligned", "block", "snake", "scattered")
HELPFUL_TEXTURES = DISTRIBUTIONS
# Explicit negative fixtures remain callable but are outside AXES' lawful domain.
DEGENERATE_TEXTURES = ("no_cyans", "full_grid", "single_cyan")
AXES = {
    "grid_h": {"type": "int", "default": "canonical/broad mixture", "valid": "5..18"},
    "grid_w": {"type": "int", "default": "canonical/broad mixture", "valid": "5..18"},
    "n_cyans": {"type": "int", "default": "source-bound teaching schedule", "valid": "4..19"},
    "distribution": {"type": "str", "default": "uniform helpful", "valid": "|".join(DISTRIBUTIONS)},
    "texture": {"type": "str", "default": "alias for distribution", "valid": "|".join(DISTRIBUTIONS)},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [("distribution", "texture")]


@lru_cache(maxsize=256)
def _schedule(seed):
    """Immutable seed-specific cycle; optional q4 slots avoid a fixed histogram.

    Each independently shuffled block contains (1,2,3) and optionally q4.
    Low buckets alternate protected remainders 2/3 and free remainders 0/1.
    Eleven consecutive draws contain two complete adjacent blocks: two examples
    of each nontrivial glyph and three rounding witnesses. Every single holdout
    retains support. Opposite remainder classes cannot be duplicate inputs,
    so duplicate removal keeps both glyph witnesses. Independent block shuffles
    remove the global bucket cycle. Bucket four retains all four remainders.
    """
    rng = stable_rng(seed, TASK_ID + ":lesson_schedule", VERSION)
    mask = rng.randrange(1, 255)
    protected_half = rng.randrange(2)
    entries = []
    for block in range(8):
        order = [1, 2, 3]
        rng.shuffle(order)
        entries.extend((bucket, block % 2 == protected_half) for bucket in order)
        if mask & (1 << block):
            entries.append((4, False))
    return tuple(entries), rng.randrange(len(entries)), rng.choice((-1, 1))


def _scheduled_slot(seed, sample_index):
    entries, phase, direction = _schedule(seed)
    return entries[(phase + direction * sample_index) % len(entries)]


def schedule_profile(seed, sample_index, difficulty=None):
    bucket, protected = _scheduled_slot(seed, sample_index)
    return f"q{bucket}_{'rounding' if protected else 'free'}"


SCHEDULE_PROFILES = tuple(
    f"q{bucket}_{kind}" for bucket in (1, 2, 3) for kind in ("rounding", "free")
) + ("q4_free",)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "n_cyans"):
        value = overrides.get(name)
        if name in overrides and type(value) is not int:
            raise ValueError(f"{name} must be a Python integer, not {type(value).__name__}")
    for name in ("distribution", "texture"):
        value = overrides.get(name)
        allowed = DISTRIBUTIONS + (DEGENERATE_TEXTURES if name == "texture" else ())
        if name in overrides and (not isinstance(value, str) or value not in allowed):
            raise ValueError(f"unknown {name}: {value!r}")
    distribution, texture = overrides.get("distribution"), overrides.get("texture")
    if distribution is not None and texture is not None and distribution != texture:
        error = ValueError("distribution and texture aliases must agree")
        error.incompatible_axes = ("distribution", "texture")
        raise error


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    core = ctx.draw_choice("input_profile", ("canonical", "broad")) == "canonical"
    favored = range(5, 9) if difficulty == "easy" else (
        range(12, 19) if difficulty == "hard" else range(6, 13))
    dimensions = list(range(5, 19)) + list(favored) * 2 + ([6] * 100 if core else [])
    h = ctx.draw_choice("grid_h", dimensions)
    w = ctx.draw_choice("grid_w", dimensions)
    rng = ctx.draw_rng("placement")
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        if overrides.get("n_cyans") is not None:
            error = ValueError("negative texture and exact n_cyans are incompatible")
            error.incompatible_axes = ("texture", "n_cyans")
            raise error
        return _draw_from_degenerate(texture, h, w)

    if overrides.get("n_cyans") is not None:
        n_cyans = ctx.draw_int_strict("n_cyans", 4, 19)
    else:
        bucket, protected = _scheduled_slot(seed, sample_index)
        choices = (0, 1, 2, 3) if bucket == 4 else ((2, 3) if protected else (0, 1))
        remainder = ctx.draw_choice("count_remainder", choices)
        # Conditional default recorded as a default draw, not a forged override.
        # Explicit requests retain the full documented domain.
        n_cyans = ctx.draw_choice("n_cyans", (4 * bucket + remainder,))

    selected = overrides.get("distribution") or texture
    distribution = ctx.draw_choice("distribution", (selected,) if selected else DISTRIBUTIONS)
    ctx.draw_choice("texture", (distribution,))
    positions = _pick_positions(distribution, h, w, n_cyans, rng)
    grid = full_grid(h, w, 0)
    for row, col in positions:
        grid[row][col] = 8
    return grid


def _pick_positions(distribution, h, w, n, rng):
    if distribution == "scattered":
        return rng.sample([(r, c) for r in range(h) for c in range(w)], n)
    if distribution == "clustered":
        cr, cc = rng.randrange(h), rng.randrange(w)
        cells = [(r, c) for r in range(h) for c in range(w)]
        cells.sort(key=lambda p: (abs(p[0] - cr) + abs(p[1] - cc), rng.random()))
        return cells[:n]
    if distribution == "block":
        heights = [bh for bh in range(1, min(h, n) + 1) if (n + bh - 1) // bh <= w]
        bh = rng.choice(heights)
        bw = (n + bh - 1) // bh
        r0, c0 = rng.randrange(h - bh + 1), rng.randrange(w - bw + 1)
        cells = [(r, c) for r in range(r0, r0 + bh) for c in range(c0, c0 + bw)][:n]
    elif distribution == "row_aligned":
        rows = list(range(h))
        rng.shuffle(rows)
        offset = rng.randrange(w)
        cols = [(offset + c) % w for c in range(w)]
        cells = [(r, c) for r in rows for c in cols][:n]
    elif distribution == "snake":
        if rng.randrange(2):
            cells = [(r, c) for r in range(h)
                     for c in (range(w) if r % 2 == 0 else range(w - 1, -1, -1))][:n]
        else:
            cells = [(r, c) for c in range(w)
                     for r in (range(h) if c % 2 == 0 else range(h - 1, -1, -1))][:n]
    else:
        raise ValueError(f"unknown distribution: {distribution!r}")
    flip_r, flip_c = rng.randrange(2), rng.randrange(2)
    return [(h - 1 - r if flip_r else r, w - 1 - c if flip_c else c) for r, c in cells]


def _draw_from_degenerate(name, h, w):
    grid = full_grid(h, w, 8 if name == "full_grid" else 0)
    if name == "single_cyan":
        grid[h // 2][w // 2] = 8
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    """Task domain, not a connectivity or visual-complexity filter."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty or malformed grid"]
    if any(not isinstance(row, (list, tuple)) for row in grid) or not grid[0]:
        return ["empty or malformed row"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    if not (5 <= h <= 18 and 5 <= w <= 18):
        errors.append("height and width must each be 5..18")
    if any(type(v) is not int or v not in (0, 8) for row in grid for v in row):
        errors.append("all cells must be integer background 0 or cyan 8")
    count = sum(v == 8 for row in grid for v in row)
    if not 4 <= count <= 19:
        errors.append(f"cyan count must be 4..19, got {count}")
    if not any(v == 0 for row in grid for v in row):
        errors.append("at least one background cell is required")
    return errors


def strict_canonical_like(grid):
    # Counting is geometry-invariant: lines, blocks and disconnected fields
    # are lawful. No visual-complexity requirement is invented.
    return self_check(grid)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_cyans": sum(v == 8 for row in grid for v in row)}


def _count(grid):
    return sum(v == 8 for row in grid for v in row)


_ROW_ORDER = ((1, 1), (1, 0), (0, 1), (0, 0))


def _rival_glyph(bucket, order=_ROW_ORDER):
    """Rival-only rendering; never used to emit authoritative labels."""
    on = set(order[:max(0, min(4, bucket))])
    return [[8 if r != 2 and c != 2 and
             (r if r < 2 else r - 3, c if c < 2 else c - 3) in on else 0
             for c in range(5)] for r in range(5)]


def _ceiling(grid):
    return _rival_glyph((_count(grid) + 3) // 4)


def _nearest(grid):
    return _rival_glyph((_count(grid) + 2) // 4)


def _canonical_threshold(grid):
    return _rival_glyph(4 if _count(grid) >= 16 else 3)


def _column_first(grid):
    return _rival_glyph(_count(grid) // 4, ((1, 1), (0, 1), (1, 0), (0, 0)))


def _bottom_left_first(grid):
    return _rival_glyph(_count(grid) // 4, ((1, 0), (1, 1), (0, 1), (0, 0)))


def _third_top_left(grid):
    return _rival_glyph(_count(grid) // 4, ((1, 1), (1, 0), (0, 0), (0, 1)))


SEMANTIC_RIVALS = {
    "ceiling_quarters": _ceiling,
    "nearest_quarters": _nearest,
    "canonical_two_glyphs": _canonical_threshold,
    "column_first": _column_first,
    "bottom_left_first": _bottom_left_first,
    "third_top_left": _third_top_left,
}
CANONICAL_SHORTCUTS = {name: rival for name, rival in SEMANTIC_RIVALS.items()
                       if name != "third_top_left"}
SEMANTIC_WITNESSES = {
    "rounding_boundary": lambda g: _count(g) < 16 and _count(g) % 4 >= 2,
    "low_count": lambda g: _count(g) < 12,
    "one_cell_glyph": lambda g: _count(g) // 4 == 1,
    "two_cell_glyph": lambda g: _count(g) // 4 == 2,
    "three_cell_glyph": lambda g: _count(g) // 4 == 3,
}
WITNESS_RIVALS = {
    "rounding_boundary": ["ceiling_quarters", "nearest_quarters"],
    "low_count": ["canonical_two_glyphs"],
    "one_cell_glyph": ["bottom_left_first"],
    "two_cell_glyph": ["column_first"],
    "three_cell_glyph": ["third_top_left"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
for _bucket in range(1, 5):
    LESSON_COMPETITORS[f"constant_q{_bucket}"] = lambda grid, q=_bucket: _rival_glyph(q)
for _index, _order in enumerate(permutations(_ROW_ORDER)):
    if _order != _ROW_ORDER:
        LESSON_COMPETITORS[f"tile_order_{_index:02d}"] = (
            lambda grid, order=_order: _rival_glyph(_count(grid) // 4, order)
        )
