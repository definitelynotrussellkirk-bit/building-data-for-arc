"""Generator for arc_puzzle_bank_nineteenth21:M127 — reflect across a cyan axis.

A full-height color-8 column is the mirror axis.  The input contains one small,
single-color connected shape entirely to the left of that axis and an empty
right side.  The Racket authority preserves the input and paints every source
cell at the reflected column ``2 * axis - c`` with the same color.

The ordinary teaching schedule deliberately alternates left/right/center axis
placements and asymmetric/symmetric source shapes.  Every three consecutive
examples contain an off-center axis, a horizontally asymmetric shape, a
non-adjacent source, and a source color other than 2, so four plausible
shortcuts are refuted in every materialized lesson rather than only in aggregate.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "a16cf9241d71"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "13927b48170d"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A zero-background grid has exactly one full-height cyan (8) divider "
    "column and one small connected, single-color shape entirely on its left; "
    "the right side is empty. Preserve the divider and source shape, then "
    "reflect every non-{0,8} source cell across the cyan column to "
    "(row, 2*axis-col), preserving its color."
)

INVARIANTS = [
    "background is color 0 and the only cyan cells form one full-height axis column",
    "there is exactly one 3-5 cell, 4-connected, single-color source shape left of the axis",
    "the input right side is empty and every reflected source cell lands in bounds to the right",
    "the Racket output preserves the input and adds the same-color horizontal reflection",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (1, 0), (1, 1)),                  # lower-right L
    ((0, 0), (0, 1), (1, 0)),                  # upper-right L
    ((0, 0), (1, 0), (2, 0), (2, 1)),          # long lower-right L
    ((0, 0), (0, 1), (1, 1)),                  # upper-left L
    ((0, 0), (1, 0), (2, 0)),                  # vertical bar (symmetric control)
)
_SHAPE_LOOKUP = {tuple(sorted(shape)): index for index, shape in enumerate(_SHAPES)}
_AXIS_PROFILES = ("left", "center", "right")
_VERTICAL_PROFILES = ("top", "middle", "bottom")
_SOURCE_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "six-slot schedule; canonical anchors use h=5",
        "valid": "5..12",
    },
    "grid_w": {
        "type": "int",
        "default": "six-slot schedule; canonical anchors use w=7..9",
        "valid": "7..15",
    },
    "shape_idx": {
        "type": "int",
        "default": "scheduled asymmetric/symmetric source shape",
        "valid": "0..4",
    },
    "shape_color": {
        "type": "color",
        "default": "seed-varied nonzero, non-cyan source color",
        "valid": "1..9 (≠8)",
    },
    "axis_gap": {
        "type": "int",
        "default": "semantic schedule alternates canonical gap 0/1",
        "valid": "0..1",
    },
    "vertical_profile": {
        "type": "str",
        "default": "seed-varied top/middle/bottom placement",
        "valid": "|".join(_VERTICAL_PROFILES),
    },
}

# No valid combination of the declared axes is intentionally incompatible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Every cyclic length-3 window contains:
#   * an off-center axis (refutes grid-center reflection),
#   * a horizontally asymmetric shape (refutes copy/translate without flip),
#   * a non-adjacent source (refutes "flip immediately across the divider"),
#   * a source color != 2 (refutes painting every mirror red).
# Slots 0/2/4 also anchor exact canonical dimensions in every length-3 window.
# Axis profile is intentionally schedule-only rather than an AXES control: at
# narrow canonical widths some feasible left/center/right positions coincide,
# so exposing it as an exact override would make the metadata dishonest.
_SCHEDULE = (
    {"axis_profile": "left",   "axis_gap": 0, "shape_pool": (0, 1),    "color_pool": (2,)},
    {"axis_profile": "right",  "axis_gap": 1, "shape_pool": (4,),       "color_pool": (4, 5, 6, 7, 9)},
    {"axis_profile": "center", "axis_gap": 1, "shape_pool": (0, 1, 3), "color_pool": (3, 4, 5, 6, 7, 9)},
    {"axis_profile": "left",   "axis_gap": 0, "shape_pool": (2, 3),    "color_pool": (3, 4, 5, 6, 7, 9)},
    {"axis_profile": "right",  "axis_gap": 1, "shape_pool": (4,),       "color_pool": (3, 4, 5, 6, 7, 9)},
    {"axis_profile": "center", "axis_gap": 1, "shape_pool": (0, 2, 3), "color_pool": (3, 4, 5, 6, 7, 9)},
)
SCHEDULE_PROFILES = tuple(range(len(_SCHEDULE)))

_CANONICAL_DIMS = ((5, 7), (5, 8), (5, 9))
_NONCANONICAL_DIMS = {
    "easy": ((6, 8), (6, 9), (7, 10)),
    "medium": ((6, 10), (7, 11), (8, 12)),
    "hard": ((9, 13), (10, 14), (12, 15)),
    None: ((6, 9), (7, 11), (9, 13)),
}


def _is_arc_grid(grid: Any) -> bool:
    return bool(
        isinstance(grid, list)
        and grid
        and isinstance(grid[0], list)
        and grid[0]
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")


def _draw_int_axis(ctx, overrides: dict[str, Any], label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_axis(
    ctx,
    overrides: dict[str, Any],
    label: str,
    default: str,
    options: Sequence[str],
) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, tuple(options))
    return ctx.draw_choice(label, (default,))


def _draw_color_axis(ctx, overrides: dict[str, Any], label: str, default: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_color(label, exclude={0, 8})
    # A one-value keyed choice records the exact scheduled value in GenCtx while
    # keeping explicit overrides validated by draw_color's legal-color contract.
    return int(ctx.draw_choice(label, (default,)))


def _shape_dims(shape: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return (
        max(r for r, _ in shape) + 1,
        max(c for _, c in shape) + 1,
    )


def _axis_col(width: int, shape_width: int, gap: int, profile: str) -> int:
    reach = shape_width + gap
    leftmost = reach
    rightmost = width - reach - 1
    if rightmost < leftmost:
        raise ValueError(
            f"grid width {width} cannot fit shape width {shape_width} on both sides of an axis"
        )
    if profile == "left":
        return leftmost
    if profile == "right":
        return rightmost
    if profile == "center":
        return min(max(width // 2, leftmost), rightmost)
    raise ValueError(f"unknown axis profile {profile!r}")


def _row_start(height: int, shape_height: int, profile: str) -> int:
    bottom = height - shape_height
    if bottom < 0:
        raise ValueError(f"shape height {shape_height} exceeds grid height {height}")
    if profile == "top":
        return 0
    if profile == "bottom":
        return bottom
    if profile == "middle":
        return bottom // 2
    raise ValueError(f"unknown vertical profile {profile!r}")


def _connected4(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if q in cells and q not in seen:
                seen.add(q)
                stack.append(q)
    return seen == cells


def _normalized_cells(cells: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _analyze(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "errors": [],
        "height": 0,
        "width": 0,
        "axis": None,
        "source_cells": (),
        "source_color": None,
        "axis_gap": None,
        "shape_idx": None,
        "shape_height": None,
        "shape_width": None,
        "axis_profile": None,
        "vertical_profile": None,
    }
    errors: list[str] = facts["errors"]
    if not _is_arc_grid(grid):
        errors.append("grid must be a nonempty rectangular ARC grid")
        return facts

    h, w = len(grid), len(grid[0])
    facts["height"], facts["width"] = h, w
    if not 5 <= h <= 12:
        errors.append(f"grid height must be 5..12, got {h}")
    if not 7 <= w <= 15:
        errors.append(f"grid width must be 7..15, got {w}")

    axes = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if len(axes) != 1:
        errors.append(f"expected exactly one full-height 8-column, got {len(axes)}")
        return facts
    axis = axes[0]
    facts["axis"] = axis

    extra_eights = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8 and c != axis]
    if extra_eights:
        errors.append(f"cyan must occur only on the axis; found {len(extra_eights)} off-axis cyan cell(s)")

    source = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 8)]
    facts["source_cells"] = tuple(source)
    if not 3 <= len(source) <= 5:
        errors.append(f"source shape must contain 3..5 cells, got {len(source)}")
        return facts

    colors = {grid[r][c] for r, c in source}
    if len(colors) != 1:
        errors.append(f"source shape must use exactly one color, got {sorted(colors)}")
        return facts
    source_color = next(iter(colors))
    facts["source_color"] = source_color

    source_set = set(source)
    if not _connected4(source_set):
        errors.append("source shape must be 4-connected")
    if any(c >= axis for _, c in source):
        errors.append("every source cell must lie strictly left of the cyan axis")
    right_foreground = [
        (r, c) for r in range(h) for c in range(axis + 1, w) if grid[r][c] != 0
    ]
    if right_foreground:
        errors.append(f"input right side must be empty, got {len(right_foreground)} foreground cell(s)")

    for r, c in source:
        mirror_col = 2 * axis - c
        if not axis < mirror_col < w:
            errors.append(f"mirror of ({r},{c}) lands out of bounds at column {mirror_col}")
            break

    rows = [r for r, _ in source]
    cols = [c for _, c in source]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    sh, sw = r1 - r0 + 1, c1 - c0 + 1
    gap = axis - c1 - 1
    facts["shape_height"], facts["shape_width"] = sh, sw
    facts["axis_gap"] = gap
    facts["shape_idx"] = _SHAPE_LOOKUP.get(_normalized_cells(source))

    # These classifications are exact for this generator's own outputs.  They
    # are deliberately not part of canonical-input acceptance: external
    # canonical layouts need not correspond to a generated override value.
    reach = sw + gap
    if axis == reach:
        facts["axis_profile"] = "left"
    elif axis == w - reach - 1:
        facts["axis_profile"] = "right"
    elif axis == min(max(w // 2, reach), w - reach - 1):
        facts["axis_profile"] = "center"

    bottom = h - sh
    if r0 == 0:
        facts["vertical_profile"] = "top"
    elif r0 == bottom:
        facts["vertical_profile"] = "bottom"
    elif r0 == bottom // 2:
        facts["vertical_profile"] = "middle"

    return facts


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return int(sample_index) % len(_SCHEDULE)


def _scheduled_defaults(ctx, seed: int, sample_index: int, difficulty: str | None) -> dict[str, Any]:
    slot = schedule_profile(seed, sample_index, difficulty)
    spec = _SCHEDULE[slot]
    rng = ctx.draw_rng("scheduled-defaults")

    if slot in (0, 2, 4):
        h, w = rng.choice(_CANONICAL_DIMS)
    else:
        dims = _NONCANONICAL_DIMS.get(difficulty, _NONCANONICAL_DIMS[None])
        h, w = rng.choice(dims)

    return {
        "grid_h": h,
        "grid_w": w,
        "shape_idx": rng.choice(spec["shape_pool"]),
        "shape_color": rng.choice(spec["color_pool"]),
        "axis_gap": spec["axis_gap"],
        "axis_profile": spec["axis_profile"],
        "vertical_profile": rng.choice(_VERTICAL_PROFILES),
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _scheduled_defaults(ctx, seed, sample_index, difficulty)

    h = _draw_int_axis(ctx, overrides, "grid_h", defaults["grid_h"], 5, 12)
    w = _draw_int_axis(ctx, overrides, "grid_w", defaults["grid_w"], 7, 15)
    shape_idx = _draw_int_axis(ctx, overrides, "shape_idx", defaults["shape_idx"], 0, 4)
    shape_color = _draw_color_axis(ctx, overrides, "shape_color", defaults["shape_color"])
    axis_gap = _draw_int_axis(ctx, overrides, "axis_gap", defaults["axis_gap"], 0, 1)
    axis_profile = defaults["axis_profile"]
    vertical_profile = _draw_choice_axis(
        ctx, overrides, "vertical_profile", defaults["vertical_profile"], _VERTICAL_PROFILES
    )

    shape = _SHAPES[shape_idx]
    sh, sw = _shape_dims(shape)
    axis = _axis_col(w, sw, axis_gap, axis_profile)
    r0 = _row_start(h, sh, vertical_profile)
    c0 = axis - axis_gap - sw

    grid = full_grid(h, w, 0)
    for r in range(h):
        grid[r][axis] = 8
    paint_at(grid, r0, c0, shape, shape_color)

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"generator emitted invalid grid: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "shape_idx": shape_idx,
        "shape_color": shape_color,
        "axis_gap": axis_gap,
        "vertical_profile": vertical_profile,
    }
    if observed != expected:
        raise AssertionError(f"axis observer mismatch: observed={observed}, expected={expected}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical manifold: explicit 8-axis + one left source shape."""
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    if facts["shape_idx"] is None:
        raise ValueError("source shape is valid but is not one of the generated shape-bank forms")
    if facts["axis_gap"] not in (0, 1):
        raise ValueError("source gap is valid for the rule but outside the generated axis_gap domain")
    if facts["vertical_profile"] is None:
        raise ValueError("source row does not encode a generated vertical_profile")
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "shape_idx": facts["shape_idx"],
        "shape_color": facts["source_color"],
        "axis_gap": facts["axis_gap"],
        "vertical_profile": facts["vertical_profile"],
    }


def _true_rule(grid: list[list[int]]) -> list[list[int]]:
    """Diagnostic Python mirror of the Racket authority; never output authority."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    axis = int(facts["axis"])
    out = deepcopy(grid)
    for r, c in facts["source_cells"]:
        out[r][2 * axis - c] = grid[r][c]
    return out


def _mirror_about_grid_center(grid: list[list[int]]) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"]:
        return deepcopy(grid)
    w = facts["width"]
    out = deepcopy(grid)
    for r, c in facts["source_cells"]:
        out[r][w - 1 - c] = grid[r][c]
    return out


def _translate_without_flip(grid: list[list[int]]) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"]:
        return deepcopy(grid)
    axis = int(facts["axis"])
    source = list(facts["source_cells"])
    c0 = min(c for _, c in source)
    out = deepcopy(grid)
    for r, c in source:
        out[r][axis + 1 + (c - c0)] = grid[r][c]
    return out


def _mirror_adjacent_to_axis(grid: list[list[int]]) -> list[list[int]]:
    """Shortcut: flip the shape but always place the copy immediately right of the axis."""
    facts = _analyze(grid)
    if facts["errors"]:
        return deepcopy(grid)
    axis = int(facts["axis"])
    source = list(facts["source_cells"])
    c1 = max(c for _, c in source)
    out = deepcopy(grid)
    for r, c in source:
        out[r][axis + 1 + (c1 - c)] = grid[r][c]
    return out


def _mirror_in_fixed_color_2(grid: list[list[int]]) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"]:
        return deepcopy(grid)
    axis = int(facts["axis"])
    out = deepcopy(grid)
    for r, c in facts["source_cells"]:
        out[r][2 * axis - c] = 2
    return out


def _witness_off_center_axis(grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and 2 * int(facts["axis"]) != facts["width"] - 1


def _witness_asymmetric_shape(grid) -> bool:
    facts = _analyze(grid)
    if facts["errors"]:
        return False
    cells = _normalized_cells(facts["source_cells"])
    max_col = max(c for _, c in cells)
    flipped = tuple(sorted((r, max_col - c) for r, c in cells))
    return cells != flipped


def _witness_nonadjacent_source(grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and int(facts["axis_gap"]) > 0


def _witness_non_red_source(grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and facts["source_color"] != 2


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "mirror_about_grid_center": _mirror_about_grid_center,
    "translate_without_flip": _translate_without_flip,
    "mirror_adjacent_to_axis": _mirror_adjacent_to_axis,
    "mirror_in_fixed_color_2": _mirror_in_fixed_color_2,
}

SEMANTIC_WITNESSES = {
    "off_center_axis": _witness_off_center_axis,
    "horizontally_asymmetric_source": _witness_asymmetric_shape,
    "nonadjacent_source_gap": _witness_nonadjacent_source,
    "source_color_not_2": _witness_non_red_source,
}

WITNESS_RIVALS = {
    "off_center_axis": ["mirror_about_grid_center"],
    "horizontally_asymmetric_source": ["translate_without_flip"],
    "nonadjacent_source_gap": ["mirror_adjacent_to_axis"],
    "source_color_not_2": ["mirror_in_fixed_color_2"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    findings = strict_canonical_like(pair["input"])
    if findings:
        return [f"{label}: {reason}" for reason in findings]
    expected = _true_rule(pair["input"])
    if pair["output"] != expected:
        return [f"{label}: output is not the same-color reflection across the cyan axis"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where named shortcuts fit all demos but alter the query."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {index}"))
    reasons.extend(_pair_errors(query, "query"))
    if reasons:
        return reasons

    inputs = [pair["input"] for pair in demos]
    if not any(_witness_off_center_axis(grid) for grid in inputs):
        reasons.append("demonstrations never distinguish the cyan axis from the grid center")
    if not any(_witness_asymmetric_shape(grid) for grid in inputs):
        reasons.append("demonstrations never distinguish reflection from same-orientation translation")
    if not any(_witness_nonadjacent_source(grid) for grid in inputs):
        reasons.append("demonstrations never prove that reflection preserves source distance from the cyan axis")
    if not any(_witness_non_red_source(grid) for grid in inputs):
        reasons.append("demonstrations never prove that reflected cells preserve a non-red source color")

    for name, competitor in LESSON_COMPETITORS.items():
        fits_every_demo = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if fits_every_demo and competitor(query["input"]) != query["output"]:
            reasons.append(f"competing rule {name!r} fits every demo but changes the query answer")
    return reasons
