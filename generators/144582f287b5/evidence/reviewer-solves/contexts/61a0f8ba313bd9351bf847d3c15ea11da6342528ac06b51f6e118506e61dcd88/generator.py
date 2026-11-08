"""Compact, contrastive generator for ARC task 144582f287b5.

The selected rule reads the fixed 2x2 source at rows 1-2 and columns 1-2,
then scatters those four values to the four output corners while clearing every
other output cell.  A four-profile schedule keeps one exact canonical 4x4
anchor, one canonical-scale corner-decoy contrast, and two compact shape/decoy
witnesses in every lesson so plausible canonical-fitting shortcuts are refuted.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "144582f287b5"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "acb1a0ae5f73"

SUMMARY = (
    "A compact 4x4-to-8x8 grid contains four distinct nonzero values at the "
    "fixed source cells (1,1), (1,2), (2,1), and (2,2). The output preserves "
    "the input shape, places those values at top-left, top-right, bottom-left, "
    "and bottom-right respectively, and makes every other cell zero. A "
    "four-profile lesson schedule includes an exact canonical 4x4 anchor, a "
    "canonical-scale corner-decoy contrast, and two larger fixed decoy layouts "
    "whose cells are ignored by the rule."
)

INVARIANTS = [
    "4 <= height,width <= 8",
    "the fixed source 2x2 contains four distinct colors from 1..9",
    "outside-source nonzero cells are either absent or one declared four-cell decoy layout",
    "all decoys share one nonzero color; the 4x4 corner contrast reuses a source color to preserve canonical palette scale",
]

DECOY_PATTERNS = ("none", "corners", "source_halo", "edge_midpoints")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "four-profile schedule", "valid": "4..8"},
    "grid_w": {"type": "int", "default": "four-profile schedule", "valid": "4..8"},
    "decoy_pattern": {
        "type": "str",
        "default": "four-profile schedule",
        "valid": "|".join(DECOY_PATTERNS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = DECOY_PATTERNS
MIN_STRICT_FRAC = 0.20

_SOURCE_POSITIONS = ((1, 1), (1, 2), (2, 1), (2, 2))
_DEFAULT_DIMS = {
    "easy": ((4, 4), (4, 4), (6, 6), (6, 4)),
    "medium": ((4, 4), (4, 4), (7, 7), (7, 5)),
    "hard": ((4, 4), (4, 4), (8, 8), (8, 6)),
}


def _validate_difficulty(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in _DEFAULT_DIMS:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    return str(difficulty)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic lesson profile for this sample index."""
    del seed
    _validate_difficulty(difficulty)
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _scheduled_defaults(sample_index: int, difficulty: Any) -> dict[str, Any]:
    band = _validate_difficulty(difficulty)
    residue = sample_index % LESSON_SCHEDULE_PERIOD
    h, w = _DEFAULT_DIMS[band][residue]
    return {
        "grid_h": h,
        "grid_w": w,
        "decoy_pattern": SCHEDULE_PROFILES[residue],
    }


def _decoy_positions(pattern: str, h: int, w: int) -> frozenset[tuple[int, int]]:
    if pattern == "none":
        return frozenset()
    if pattern == "corners":
        return frozenset(((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)))
    if pattern == "source_halo":
        return frozenset(((0, 1), (1, 0), (2, 3), (3, 2)))
    if pattern == "edge_midpoints":
        return frozenset(
            (
                (0, w // 2),
                (h // 2, w - 1),
                (h - 1, (w - 1) // 2),
                ((h - 1) // 2, 0),
            )
        )
    raise ValueError(f"unknown decoy pattern {pattern!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")

    defaults = _scheduled_defaults(sample_index, difficulty)
    effective = dict(defaults)
    effective.update({name: value for name, value in overrides.items() if value is not None})
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int_strict("grid_h", 4, 8)
    w = ctx.draw_int_strict("grid_w", 4, 8)
    pattern = ctx.draw_choice("decoy_pattern", DECOY_PATTERNS)
    source_and_decoy = ctx.draw_distinct_colors(
        "source_and_decoy_colors", n=5, exclude={0}
    )

    grid = full_grid(h, w, 0)
    for (r, c), value in zip(_SOURCE_POSITIONS, source_and_decoy[:4]):
        grid[r][c] = value
    # The 4x4 corner contrast deliberately stays inside the canonical
    # (height, width, palette-size) envelope while still refuting source-selection
    # shortcuts. Other layouts use a fifth, disjoint color.
    decoy_color = source_and_decoy[0] if pattern == "corners" and h == 4 and w == 4 else source_and_decoy[4]
    for r, c in _decoy_positions(pattern, h, w):
        grid[r][c] = decoy_color
    return grid


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _outside_nonzero_positions(grid) -> frozenset[tuple[int, int]]:
    source = set(_SOURCE_POSITIONS)
    return frozenset(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) not in source
    )


def _infer_decoy_pattern(grid) -> str:
    h, w = len(grid), len(grid[0])
    observed = _outside_nonzero_positions(grid)
    matches = [
        pattern
        for pattern in DECOY_PATTERNS
        if observed == _decoy_positions(pattern, h, w)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"outside-source nonzero positions do not match exactly one declared layout: {sorted(observed)}"
        )
    return matches[0]


def self_check(grid, *, difficulty=None, meta=None):
    """Recognize exactly the compact grammar emitted by :func:`generate`."""
    del meta
    errors = _basic_grid_errors(grid)
    if errors:
        return errors
    try:
        _validate_difficulty(difficulty)
    except ValueError as exc:
        return [str(exc)]

    h, w = len(grid), len(grid[0])
    if not 4 <= h <= 8:
        errors.append(f"grid height {h} outside 4..8")
    if not 4 <= w <= 8:
        errors.append(f"grid width {w} outside 4..8")
    if errors:
        return errors

    source = [grid[r][c] for r, c in _SOURCE_POSITIONS]
    if any(value == 0 for value in source):
        errors.append("the fixed source 2x2 must contain four nonzero colors")
    if len(set(source)) != 4:
        errors.append("the fixed source 2x2 colors must be pairwise distinct")

    try:
        pattern = _infer_decoy_pattern(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return errors

    positions = _decoy_positions(pattern, h, w)
    if positions:
        values = [grid[r][c] for r, c in positions]
        if any(value == 0 for value in values):
            errors.append("every declared decoy position must be nonzero")
        if len(set(values)) != 1:
            errors.append("all decoys must share one color")
        # Reusing one source color is intentional for the canonical-scale
        # 4x4 corner contrast; exact positions and a uniform decoy color remain
        # sufficient to recognize the grammar.
    return errors


def observe_overrides(grid):
    """Recover every declared exact axis from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "decoy_pattern": _infer_decoy_pattern(grid),
    }


def strict_canonical_like(grid):
    """Accept the exact canonical 4x4/no-decoy input manifold."""
    errors = self_check(grid)
    if errors:
        return errors
    observed = observe_overrides(grid)
    reasons = []
    if observed["grid_h"] != 4 or observed["grid_w"] != 4:
        reasons.append("canonical inputs are 4x4")
    if observed["decoy_pattern"] != "none":
        reasons.append("canonical inputs contain no outside-source decoys")
    return reasons


def _scatter(values, h: int, w: int):
    output = full_grid(h, w, 0)
    output[0][0], output[0][w - 1] = values[0], values[1]
    output[h - 1][0], output[h - 1][w - 1] = values[2], values[3]
    return output


def rule_mirror(grid):
    """Python mirror of the selected fixed-offset Racket rule."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid task input: " + "; ".join(errors))
    values = [grid[r][c] for r, c in _SOURCE_POSITIONS]
    return _scatter(values, len(grid), len(grid[0]))


def _geometric_center(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid task input: " + "; ".join(errors))
    h, w = len(grid), len(grid[0])
    r0, c0 = (h - 2) // 2, (w - 2) // 2
    values = (grid[r0][c0], grid[r0][c0 + 1], grid[r0 + 1][c0], grid[r0 + 1][c0 + 1])
    return _scatter(values, h, w)


def _first_four_nonzero(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid task input: " + "; ".join(errors))
    hits = [value for row in grid for value in row if value != 0]
    return _scatter(hits[:4], len(grid), len(grid[0]))


def _nonzero_bbox_corners(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid task input: " + "; ".join(errors))
    h, w = len(grid), len(grid[0])
    hits = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    rows = [r for r, _ in hits]
    cols = [c for _, c in hits]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    values = (grid[r0][c0], grid[r0][c1], grid[r1][c0], grid[r1][c1])
    return _scatter(values, h, w)


def _fixed_4x4_output(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid task input: " + "; ".join(errors))
    values = [grid[r][c] for r, c in _SOURCE_POSITIONS]
    return _scatter(values, 4, 4)


SEMANTIC_RIVALS = {
    "geometric_center": _geometric_center,
    "first_four_nonzero": _first_four_nonzero,
    "nonzero_bbox_corners": _nonzero_bbox_corners,
    "fixed_4x4_output": _fixed_4x4_output,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness_disagreement(grid, rival_name: str) -> bool:
    try:
        return self_check(grid) == [] and SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)
    except (TypeError, ValueError, IndexError):
        return False


def _fixed_offset_witness(grid):
    return _witness_disagreement(grid, "geometric_center")


def _scan_decoy_witness(grid):
    return _witness_disagreement(grid, "first_four_nonzero")


def _bbox_decoy_witness(grid):
    return _witness_disagreement(grid, "nonzero_bbox_corners")


def _shape_witness(grid):
    return _witness_disagreement(grid, "fixed_4x4_output")


SEMANTIC_WITNESSES = {
    "fixed_offset_not_geometric": _fixed_offset_witness,
    "decoys_not_row_major_sources": _scan_decoy_witness,
    "decoys_not_bbox_sources": _bbox_decoy_witness,
    "output_preserves_input_shape": _shape_witness,
}
WITNESS_RIVALS = {
    "fixed_offset_not_geometric": ["geometric_center"],
    "decoys_not_row_major_sources": ["first_four_nonzero"],
    "decoys_not_bbox_sources": ["nonzero_bbox_corners"],
    "output_preserves_input_shape": ["fixed_4x4_output"],
}


def _plain_grid_errors(grid: Any) -> list[str]:
    return _basic_grid_errors(grid)


def _strict_grid_equal(left: Any, right: Any) -> bool:
    if _plain_grid_errors(left) or _plain_grid_errors(right):
        return False
    if len(left) != len(right) or len(left[0]) != len(right[0]):
        return False
    return all(
        type(a) is int and type(b) is int and a == b
        for left_row, right_row in zip(left, right)
        for a, b in zip(left_row, right_row)
    )


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict):
        return [f"{label} must be a labeled-pair dict"]
    if "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output"]
    input_errors = self_check(pair["input"])
    if input_errors:
        return [f"{label} has malformed input: {input_errors[0]}"]
    output_errors = _plain_grid_errors(pair["output"])
    if output_errors:
        return [f"{label} has a malformed output grid"]
    expected = rule_mirror(pair["input"])
    if not _strict_grid_equal(pair["output"], expected):
        return [f"{label} output does not match the selected rule"]
    return []


def lesson_identifiable(demos, query):
    """Report declared rivals that fit all demos but change the query answer."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)):
        return ["demos must be a sequence of labeled pairs"]
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"pair {index}"))
    reasons.extend(_pair_errors(query, "query"))
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                _strict_grid_equal(rival(pair["input"]), pair["output"])
                for pair in demos
            )
            changes_query = not _strict_grid_equal(
                rival(query["input"]), query["output"]
            )
        except (TypeError, ValueError, IndexError) as exc:
            reasons.append(f"competitor {name} could not be evaluated: {type(exc).__name__}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name} fits all demonstrations but changes the query")
    return reasons
