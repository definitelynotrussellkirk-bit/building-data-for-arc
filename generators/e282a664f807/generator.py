"""Generator for S9_E2 — fill the bbox of the unique two-cell color.

The unique non-background color occurring exactly twice identifies opposite
corners of a non-degenerate rectangle.  The output is a fresh zero background
with that rectangle filled in the repeated color; all other colors are decoys.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e282a664f807"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
SUMMARY = "Exactly one color appears twice; its two cells define a filled rectangle."

INVARIANTS = [
    "background is 0",
    "exactly one nonzero color appears in exactly two cells",
    "the two selected cells differ in both row and column",
    "the output is a fresh zero grid containing the selected color's filled bounding box",
]

PAIR_SLOPES = ("positive", "negative")
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-banded", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "difficulty-banded", "valid": "6..16"},
    "box_height": {"type": "int", "default": "difficulty-banded", "valid": "2..8"},
    "box_width": {"type": "int", "default": "difficulty-banded", "valid": "2..8"},
    "pair_slope": {
        "type": "str",
        "default": "alternates by sample_index",
        "valid": "positive|negative",
    },
    "distractor_count": {"type": "int", "default": "difficulty-banded", "valid": "0..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"when": "box_height > grid_h", "reason": "the rectangle must fit"},
    {"when": "box_width > grid_w", "reason": "the rectangle must fit"},
]
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return 0, 0, ["grid rows must be non-empty"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return h, w, ["grid must be rectangular"]
    errors: list[str] = []
    if h > 30 or w > 30:
        errors.append(f"grid exceeds ARC bounds: {h}x{w}")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or value outside ARC palette 0..9")
    return h, w, errors


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    h, w, errors = _validate_grid(grid)
    info: dict[str, Any] = {"grid_h": h, "grid_w": w}
    if errors:
        return info, errors
    counts = Counter(value for row in grid for value in row if value != 0)
    pair_colors = [color for color, count in counts.items() if count == 2]
    if len(pair_colors) != 1:
        errors.append(f"expected exactly one nonzero color with count=2, got {len(pair_colors)}")
        return info, errors
    color = pair_colors[0]
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    if points[0][0] == points[1][0] or points[0][1] == points[1][1]:
        errors.append("the selected pair is collinear, so the bbox is a line")
        return info, errors
    r1, r2 = sorted((points[0][0], points[1][0]))
    c1, c2 = sorted((points[0][1], points[1][1]))
    slope = "positive" if (points[0][0] - points[1][0]) * (points[0][1] - points[1][1]) > 0 else "negative"
    info.update(
        {
            "selected_color": color,
            "selected_points": tuple(points),
            "box_height": r2 - r1 + 1,
            "box_width": c2 - c1 + 1,
            "pair_slope": slope,
            "distractor_count": sum(counts.values()) - 2,
            "bbox": (r1, c1, r2, c2),
        }
    )
    return info, errors


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return _analyse(grid)[1]


def strict_canonical_like(grid: Any) -> list[str]:
    """The exact source examples and the generated curriculum share this rule domain."""
    return self_check(grid)


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {name: info[name] for name in AXES}


def rule_mirror(grid: Any) -> list[list[int]]:
    """Independent Python mirror; protected Racket remains the label authority."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = full_grid(info["grid_h"], info["grid_w"], 0)
    r1, c1, r2, c2 = info["bbox"]
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            output[r][c] = info["selected_color"]
    return output


def _draw_int(ctx, overrides: dict[str, Any], label: str, global_lo: int, global_hi: int, default_lo: int, default_hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, global_lo, global_hi)
    return ctx.draw_int_strict(label, default_lo, default_hi)


def _draw_choice(ctx, overrides: dict[str, Any], label: str, options: Sequence[str], scheduled: str) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    dimension_bands = {
        "easy": ((7, 8), (8, 9)),
        "medium": ((8, 11), (9, 13)),
        "hard": ((10, 14), (12, 16)),
    }
    (h_lo, h_hi), (w_lo, w_hi) = dimension_bands[band]
    h = _draw_int(ctx, overrides, "grid_h", 5, 14, h_lo, h_hi)
    w = _draw_int(ctx, overrides, "grid_w", 6, 16, w_lo, w_hi)

    box_bands = {"easy": (2, 3), "medium": (2, 6), "hard": (4, 8)}
    b_lo, b_hi = box_bands[band]
    box_h = _draw_int(ctx, overrides, "box_height", 2, min(8, h), min(b_lo, h), min(b_hi, h))
    box_w = _draw_int(ctx, overrides, "box_width", 2, min(8, w), min(b_lo, w), min(b_hi, w))
    slope = _draw_choice(
        ctx,
        overrides,
        "pair_slope",
        PAIR_SLOPES,
        PAIR_SLOPES[int(sample_index) % len(PAIR_SLOPES)],
    )
    decoy_bands = {"easy": (0, 2), "medium": (1, 3), "hard": (2, 4)}
    d_lo, d_hi = decoy_bands[band]
    n_decoy = _draw_int(ctx, overrides, "distractor_count", 0, 4, d_lo, d_hi)

    rng = ctx.draw_rng("layout")
    r1 = rng.randint(0, h - box_h)
    c1 = rng.randint(0, w - box_w)
    r2, c2 = r1 + box_h - 1, c1 + box_w - 1
    selected = rng.choice((2, 3, 4, 5, 6, 7))
    grid = full_grid(h, w, 0)
    if slope == "positive":
        pair = ((r1, c1), (r2, c2))
    else:
        pair = ((r1, c2), (r2, c1))
    for r, c in pair:
        grid[r][c] = selected

    decoy_colors = [color for color in range(1, 10) if color != selected]
    rng.shuffle(decoy_colors)
    free = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0]
    rng.shuffle(free)
    for color, (r, c) in zip(decoy_colors[:n_decoy], free[:n_decoy]):
        grid[r][c] = color

    observed = observe_overrides(grid)
    for name, value in ctx.recorded_draws().items():
        if name in AXES and observed[name] != value:
            raise RuntimeError(f"axis {name} requested {value!r} but grid realizes {observed[name]!r}")
    return grid
