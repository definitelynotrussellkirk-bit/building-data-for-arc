"""Generator for ``0c4c1974cbf2`` — Folded Overlap Only.

A centered full-height color-8 bar is the fold axis.  For each nonzero cell on
its left, inspect the exactly reflected cell on the right.  If both cells are
nonzero, emit color 2 at the reflected right-side position.  The output starts
blank, so the bar, left cells, right-only cells, and every non-overlap disappear.
Input colors do not affect membership in the overlap.

The five-slot schedule contains two transformed canonical-profile anchors and
three contrast-rich scenes.  Every contrast-rich scene contains a left-only
cell, a right-only cell, one same-color overlap, one different-color overlap,
and a same-row wrong-position decoy.  Consequently any three consecutive
production demonstrations contain a scene that refutes the declared one-sided,
color-sensitive, copy-color, row-local, and copy-input shortcuts.
"""
from __future__ import annotations

import copy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0c4c1974cbf2"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ceb28731a942"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.35

SUMMARY = (
    "A zero-background odd-width grid has one centered full-height color-8 "
    "fold bar. Compare each nonzero left cell with the cell at its exact "
    "reflection on the right. Emit a same-size blank grid containing color 2 "
    "only at reflected positions where both sides were nonzero. Input colors "
    "are irrelevant; left-only, right-only, bar, and all other cells vanish. "
    "Two scheduled canonical-profile anchors preserve source support, while "
    "three contrast scenes jointly expose both occupancy branches, same- and "
    "different-color overlaps, constant-red output, and exact-position logic."
)

INVARIANTS = [
    "the grid is rectangular with one centered full-height color-8 fold bar",
    "color 8 occurs only on that bar",
    "there are 5..8 nonzero left cells, including at least one left-only cell",
    "there are 2..4 exact mirrored overlaps",
    "the input uses 2..4 nonzero non-bar colors",
    "the output is blank except for color-2 marks at overlapped right mirrors",
]

SCHEDULE_PROFILES = (
    "canonical_marker_present",
    "canonical_marker_absent",
    "contrast_compact",
    "contrast_spread",
    "contrast_dense",
)
_ALLOWED_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_NONRED_COLORS = (1, 3, 4, 5, 6, 7, 9)

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES = ("no_bar", "no_overlap", "all_overlap")
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-slot schedule with two 7-row canonical anchors",
        "valid": "5..14",
        "doc": "full grid height",
    },
    "half_w": {
        "type": "int",
        "default": "five-slot schedule with canonical half-widths 5 and 6",
        "valid": "2..7",
        "doc": "columns on each side of the centered fold bar",
    },
    "left_cells": {
        "type": "int",
        "default": "scheduled 5..8",
        "valid": "5..8",
        "doc": "number of nonzero cells left of the bar",
    },
    "overlap_count": {
        "type": "int",
        "default": "scheduled 2..4",
        "valid": "2..4",
        "doc": "left cells whose exact reflected right cell is nonzero",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled 2..4",
        "valid": "2..4",
        "doc": "distinct nonzero, non-bar input colors",
    },
}

# Exact canonical inputs, used only as geometry masks for two scheduled anchors.
# Object colors are deterministically recolored and the masks may be translated
# or reflected, so these are support anchors rather than literal replay records.
_ANCHOR_ROWS = {
    "canonical_marker_present": (
        "00000800000",
        "02200800020",
        "02200800220",
        "00000800000",
        "00300800300",
        "00300800000",
        "00000800000",
    ),
    "canonical_marker_absent": (
        "0000008000000",
        "0110008000010",
        "0011008000110",
        "0000008000000",
        "0044408000440",
        "0004008000040",
        "0000008000000",
    ),
}


def _normalize_band(difficulty: Any) -> str:
    if difficulty in (None, "default", "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_call(seed: Any, sample_index: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the deterministic semantic schedule slot."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _scheduled_int(
    ctx,
    overrides: dict[str, Any],
    label: str,
    default: int,
    lo: int,
    hi: int,
) -> int:
    if label in overrides and overrides[label] is not None:
        return int(ctx.draw_int_strict(label, lo, hi))
    return int(ctx.draw_choice(label, (default,)))


def _profile_defaults(profile: str, band: str) -> tuple[int, int, int, int, int]:
    """Return ``grid_h, half_w, left_cells, overlap_count, palette_size``."""
    if profile == "canonical_marker_present":
        return 7, 5, 6, 4, 2
    if profile == "canonical_marker_absent":
        return 7, 6, 8, 3, 2
    if profile == "contrast_compact":
        return {
            "easy": (6, 3, 5, 2, 2),
            "medium": (9, 4, 7, 3, 2),
            "hard": (13, 6, 8, 4, 3),
        }[band]
    if profile == "contrast_spread":
        return {
            "easy": (5, 2, 5, 2, 2),
            "medium": (10, 5, 8, 4, 3),
            "hard": (14, 7, 8, 4, 4),
        }[band]
    if profile == "contrast_dense":
        return {
            "easy": (7, 3, 6, 3, 3),
            "medium": (11, 5, 7, 3, 3),
            "hard": (12, 6, 8, 4, 4),
        }[band]
    raise ValueError(f"unknown schedule profile: {profile!r}")


def _mirror_side_column(col: int, half: int) -> int:
    """Reflect a column within its own half, preserving its side of the bar."""
    if col < half:
        return half - 1 - col
    if col > half:
        local = col - (half + 1)
        return half + 1 + (half - 1 - local)
    return col


def _draw_anchor(profile: str, ctx) -> list[list[int]]:
    rows = _ANCHOR_ROWS[profile]
    source = [[int(value) for value in row] for row in rows]
    height, width = len(source), len(source[0])
    half = width // 2
    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][half] = 8

    transform_rng = ctx.draw_rng("anchor_transform")
    row_shift = transform_rng.choice((-1, 0, 1))
    reflect_halves = transform_rng.choice((False, True))

    palette_rng = ctx.draw_rng("anchor_palette")
    if profile == "canonical_marker_present":
        color_map = {2: 2, 3: palette_rng.choice(_NONRED_COLORS)}
    else:
        first, second = palette_rng.sample(_NONRED_COLORS, 2)
        color_map = {1: first, 4: second}

    for row, values in enumerate(source):
        for col, value in enumerate(values):
            if value in (0, 8):
                continue
            out_row = row + row_shift
            out_col = _mirror_side_column(col, half) if reflect_halves else col
            grid[out_row][out_col] = color_map[value]
    return grid


def _choose_palette(profile: str, size: int, ctx) -> tuple[int, ...]:
    rng = ctx.draw_rng("object_palette")
    if profile == "canonical_marker_present":
        chosen = [2, *rng.sample(_NONRED_COLORS, size - 1)]
        # Put a non-red color first so the generic same-color witness always
        # makes copy-left and copy-right disagree with constant-red output.
        return tuple(chosen[1:] + chosen[:1])
    return tuple(rng.sample(_NONRED_COLORS, size))


def _draw_contrast_grid(
    profile: str,
    ctx,
    height: int,
    half: int,
    left_count: int,
    overlap_count: int,
    palette_size: int,
) -> list[list[int]]:
    grid = full_grid(height, 2 * half + 1, 0)
    for row in range(height):
        grid[row][half] = 8

    layout_rng = ctx.draw_rng(f"layout:{profile}")
    decoy_row = layout_rng.randrange(height)
    left_only_col, empty_col = layout_rng.sample(range(half), 2)
    left_only_witness = (decoy_row, left_only_col)
    reserved_empty = (decoy_row, empty_col)

    candidates = [
        (row, col)
        for row in range(height)
        for col in range(half)
        if (row, col) not in (left_only_witness, reserved_empty)
    ]
    layout_rng.shuffle(candidates)
    left_positions = [left_only_witness, *candidates[: left_count - 1]]

    overlap_candidates = [position for position in left_positions if position != left_only_witness]
    layout_rng.shuffle(overlap_candidates)
    overlaps = overlap_candidates[:overlap_count]
    overlap_set = set(overlaps)
    same_position, mismatch_position = overlaps[:2]

    palette = _choose_palette(profile, palette_size, ctx)
    witness_color = next(color for color in palette if color != 2)
    left_colors: dict[tuple[int, int], int] = {
        same_position: witness_color,
        mismatch_position: witness_color,
    }
    unpainted = [
        position
        for position in sorted(left_positions)
        if position not in left_colors
    ]
    required = [color for color in palette if color != witness_color]
    fill = required + [palette[index % len(palette)] for index in range(len(unpainted))]
    for position, color in zip(unpainted, fill):
        left_colors[position] = color

    for row, col in left_positions:
        grid[row][col] = left_colors[(row, col)]

    # Same-color and different-color exact overlaps coexist.  Membership is
    # therefore visibly about nonzero occupancy, not color equality/inequality.
    for index, (row, col) in enumerate(overlaps):
        mirror_col = 2 * half - col
        left_color = left_colors[(row, col)]
        if (row, col) == same_position:
            right_color = left_color
        elif (row, col) == mismatch_position:
            right_color = next(color for color in palette if color != left_color)
        elif index % 2:
            right_color = next(color for color in palette if color != left_color)
        else:
            right_color = left_color
        grid[row][mirror_col] = right_color

    # The exact mirror of ``reserved_empty`` is a right-only cell in the same
    # row as a left-only witness.  A same-row-anywhere shortcut falsely marks
    # the witness's own mirror; exact-position logic does not.
    grid[decoy_row][2 * half - empty_col] = palette[-1]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index)
    band = _normalize_band(difficulty)

    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(sorted(unknown))}")

    texture = overrides.get("texture")
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(f"unknown texture fixture: {texture!r}")
        conflicts = sorted(set(overrides) & set(AXES))
        if conflicts:
            raise ValueError(
                "negative texture fixture is incompatible with exact axes: "
                + ", ".join(conflicts)
            )
        return _draw_from_degenerate(str(texture))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, band)
    defaults = _profile_defaults(profile, band)
    grid_h = _scheduled_int(ctx, overrides, "grid_h", defaults[0], 5, 14)
    half_w = _scheduled_int(ctx, overrides, "half_w", defaults[1], 2, 7)
    left_cells = _scheduled_int(ctx, overrides, "left_cells", defaults[2], 5, 8)
    overlap_count = _scheduled_int(ctx, overrides, "overlap_count", defaults[3], 2, 4)
    palette_size = _scheduled_int(ctx, overrides, "palette_size", defaults[4], 2, 4)

    axis_override_used = any(
        name in overrides and overrides[name] is not None for name in AXES
    )
    if profile in _ANCHOR_ROWS and not axis_override_used:
        return _draw_anchor(profile, ctx)
    return _draw_contrast_grid(
        profile,
        ctx,
        grid_h,
        half_w,
        left_cells,
        overlap_count,
        palette_size,
    )


def _draw_from_degenerate(name: str) -> list[list[int]]:
    height, half = 8, 4
    grid = full_grid(height, 2 * half + 1, 0)
    if name == "no_bar":
        grid[1][1] = 4
        grid[1][7] = 6
        grid[4][2] = 3
        grid[4][6] = 7
        return grid

    for row in range(height):
        grid[row][half] = 8
    if name == "no_overlap":
        for row, col, color in ((0, 0, 3), (1, 1, 4), (2, 2, 5), (3, 3, 6), (5, 1, 7)):
            grid[row][col] = color
        grid[6][half + 1] = 9
        return grid
    if name == "all_overlap":
        for row in range(height):
            for col in range(half):
                grid[row][col] = 4
                grid[row][2 * half - col] = 6
        return grid
    raise ValueError(f"unknown degenerate fixture: {name!r}")


def _validate_grid(grid: Any) -> tuple[list[str], list[list[int]] | None]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list of rows"], None
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["rows must be nonempty lists"], None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"], None
    normalized = [list(row) for row in grid]
    errors: list[str] = []
    if len(normalized) > 30 or width > 30:
        errors.append("grid dimensions exceed ARC 30x30")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in normalized
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
    return errors, normalized


def _analysis(grid: Any) -> dict[str, Any]:
    errors, normalized = _validate_grid(grid)
    if normalized is None:
        return {"errors": errors}

    height, width = len(normalized), len(normalized[0])
    bars = [
        col
        for col in range(width)
        if all(normalized[row][col] == 8 for row in range(height))
    ]
    if len(bars) != 1:
        errors.append(f"expected exactly one full-height color-8 bar, got {bars}")
        return {
            "errors": errors,
            "grid": normalized,
            "grid_h": height,
            "grid_w": width,
            "bars": tuple(bars),
        }

    half = bars[0]
    if width != 2 * half + 1:
        errors.append(
            f"color-8 bar must be centered in an odd-width grid, got width={width}, col={half}"
        )
    stray_eights = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if normalized[row][col] == 8 and col != half
    ]
    if stray_eights:
        errors.append(f"color 8 occurs outside the fold bar at {stray_eights[:5]}")

    left = [
        (row, col, normalized[row][col])
        for row in range(height)
        for col in range(min(half, width))
        if normalized[row][col] not in (0, 8)
    ]
    right = [
        (row, col, normalized[row][col])
        for row in range(height)
        for col in range(half + 1, width)
        if normalized[row][col] not in (0, 8)
    ]
    overlaps: list[tuple[int, int, int, int]] = []
    left_only: list[tuple[int, int, int]] = []
    for row, col, value in left:
        mirror_col = 2 * half - col
        if 0 <= mirror_col < width and normalized[row][mirror_col] not in (0, 8):
            overlaps.append((row, col, value, normalized[row][mirror_col]))
        else:
            left_only.append((row, col, value))

    right_only: list[tuple[int, int, int]] = []
    for row, col, value in right:
        mirror_col = 2 * half - col
        if not (0 <= mirror_col < half) or normalized[row][mirror_col] in (0, 8):
            right_only.append((row, col, value))

    same_color = [item for item in overlaps if item[2] == item[3]]
    mismatched = [item for item in overlaps if item[2] != item[3]]
    palette = sorted(
        {value for row in normalized for value in row if value not in (0, 8)}
    )
    row_decoy = any(
        left_row == right_row
        for left_row, _, _ in left_only
        for right_row, _, _ in right_only
    )

    if not 5 <= height <= 14:
        errors.append(f"grid height must be in 5..14, got {height}")
    if not 2 <= half <= 7:
        errors.append(f"half-width must be in 2..7, got {half}")
    if not 5 <= len(left) <= 8:
        errors.append(f"left-cell count must be in 5..8, got {len(left)}")
    if not 2 <= len(overlaps) <= 4:
        errors.append(f"overlap count must be in 2..4, got {len(overlaps)}")
    if not left_only:
        errors.append("at least one left-only cell is required")
    if not 2 <= len(palette) <= 4:
        errors.append(f"object palette size must be in 2..4, got {len(palette)}")

    return {
        "errors": errors,
        "grid": normalized,
        "grid_h": height,
        "grid_w": width,
        "bar_col": half,
        "half_w": half,
        "left": tuple(left),
        "left_cells": len(left),
        "right": tuple(right),
        "overlaps": tuple(overlaps),
        "overlap_count": len(overlaps),
        "left_only": tuple(left_only),
        "right_only": tuple(right_only),
        "same_color_overlaps": tuple(same_color),
        "mismatched_overlaps": tuple(mismatched),
        "palette": tuple(palette),
        "palette_size": len(palette),
        "row_decoy": row_decoy,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the bounded generator domain without mutating ``grid``."""
    del difficulty
    facts = _analysis(grid)
    errors = list(facts.get("errors", []))
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - set(AXES) - {"texture"}
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        if not errors and "texture" not in overrides:
            observed = observe_overrides(grid)
            for name, requested in overrides.items():
                if name in AXES and requested is not None and observed[name] != requested:
                    errors.append(
                        f"requested {name}={requested!r}, observed {observed[name]!r}"
                    )
    return sorted(set(errors))


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical 7x11/7x13, two-object-color envelopes."""
    facts = _analysis(grid)
    reasons = list(facts.get("errors", []))
    if reasons:
        return reasons
    if facts["grid_h"] != 7:
        reasons.append(f"canonical height is 7, got {facts['grid_h']}")
    if facts["half_w"] not in (5, 6):
        reasons.append(f"canonical half-width is 5 or 6, got {facts['half_w']}")
    if facts["palette_size"] != 2:
        reasons.append(f"canonical inputs use two object colors, got {facts['palette_size']}")
    if facts["left_cells"] not in (6, 7, 8):
        reasons.append(f"canonical left-cell count is 6..8, got {facts['left_cells']}")
    if facts["overlap_count"] not in (3, 4):
        reasons.append(f"canonical overlap count is 3 or 4, got {facts['overlap_count']}")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    return {
        "grid_h": facts["grid_h"],
        "half_w": facts["half_w"],
        "left_cells": facts["left_cells"],
        "overlap_count": facts["overlap_count"],
        "palette_size": facts["palette_size"],
    }


def semantic_observables(grid) -> dict[str, Any]:
    facts = _analysis(grid)
    if facts.get("errors"):
        return {"errors": list(facts["errors"])}
    return {
        **observe_overrides(grid),
        "left_only_count": len(facts["left_only"]),
        "right_only_count": len(facts["right_only"]),
        "same_color_overlap_count": len(facts["same_color_overlaps"]),
        "mismatched_overlap_count": len(facts["mismatched_overlaps"]),
        "row_decoy": facts["row_decoy"],
        "input_contains_output_color": 2 in facts["palette"],
    }


def _blank_for(facts: dict[str, Any]) -> list[list[int]]:
    return full_grid(facts["grid_h"], facts["grid_w"], 0)


def rule_mirror(grid) -> list[list[int]]:
    """Input-pure Python audit mirror; canonical Racket remains authoritative."""
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = _blank_for(facts)
    half = facts["half_w"]
    for row, col, _, _ in facts["overlaps"]:
        output[row][2 * half - col] = 2
    return output


def _rival_mirror_all_left(grid) -> list[list[int]]:
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = _blank_for(facts)
    half = facts["half_w"]
    for row, col, _ in facts["left"]:
        output[row][2 * half - col] = 2
    return output


def _rival_mark_all_right(grid) -> list[list[int]]:
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = _blank_for(facts)
    for row, col, _ in facts["right"]:
        output[row][col] = 2
    return output


def _rival_same_color_only(grid) -> list[list[int]]:
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = _blank_for(facts)
    half = facts["half_w"]
    for row, col, _, _ in facts["same_color_overlaps"]:
        output[row][2 * half - col] = 2
    return output


def _rival_different_color_only(grid) -> list[list[int]]:
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = _blank_for(facts)
    half = facts["half_w"]
    for row, col, _, _ in facts["mismatched_overlaps"]:
        output[row][2 * half - col] = 2
    return output


def _rival_copy_left_color(grid) -> list[list[int]]:
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = _blank_for(facts)
    half = facts["half_w"]
    for row, col, left_color, _ in facts["overlaps"]:
        output[row][2 * half - col] = left_color
    return output


def _rival_copy_right_color(grid) -> list[list[int]]:
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = _blank_for(facts)
    half = facts["half_w"]
    for row, col, _, right_color in facts["overlaps"]:
        output[row][2 * half - col] = right_color
    return output


def _rival_any_right_in_row(grid) -> list[list[int]]:
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = _blank_for(facts)
    half = facts["half_w"]
    occupied_rows = {row for row, _, _ in facts["right"]}
    for row, col, _ in facts["left"]:
        if row in occupied_rows:
            output[row][2 * half - col] = 2
    return output


def _rival_copy_input_then_mark(grid) -> list[list[int]]:
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = copy.deepcopy(facts["grid"])
    half = facts["half_w"]
    for row, col, _, _ in facts["overlaps"]:
        output[row][2 * half - col] = 2
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "mirror_every_left_cell": _rival_mirror_all_left,
    "mark_every_right_cell": _rival_mark_all_right,
    "same_color_only": _rival_same_color_only,
    "different_color_only": _rival_different_color_only,
    "copy_left_overlap_color": _rival_copy_left_color,
    "copy_right_overlap_color": _rival_copy_right_color,
    "any_right_cell_in_same_row": _rival_any_right_in_row,
    "copy_input_then_mark": _rival_copy_input_then_mark,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {"same_color_only": _rival_same_color_only}


def _has_left_only(grid) -> bool:
    return bool(_analysis(grid).get("left_only"))


def _has_right_only(grid) -> bool:
    return bool(_analysis(grid).get("right_only"))


def _has_mismatched_overlap(grid) -> bool:
    return bool(_analysis(grid).get("mismatched_overlaps"))


def _has_same_color_overlap(grid) -> bool:
    return bool(_analysis(grid).get("same_color_overlaps"))


def _has_nonred_both_sides_overlap(grid) -> bool:
    return any(
        left_color != 2 and right_color != 2
        for _, _, left_color, right_color in _analysis(grid).get("overlaps", ())
    )


def _has_row_decoy(grid) -> bool:
    return bool(_analysis(grid).get("row_decoy"))


def _has_erased_foreground(grid) -> bool:
    facts = _analysis(grid)
    return not facts.get("errors") and bool(facts.get("left"))


SEMANTIC_WITNESSES = {
    "left_only_cells_are_erased": _has_left_only,
    "right_only_cells_are_erased": _has_right_only,
    "different_colors_still_overlap": _has_mismatched_overlap,
    "same_colors_also_overlap": _has_same_color_overlap,
    "overlap_output_is_constant_red": _has_nonred_both_sides_overlap,
    "exact_mirror_not_same_row": _has_row_decoy,
    "output_starts_blank": _has_erased_foreground,
}
WITNESS_RIVALS = {
    "left_only_cells_are_erased": ["mirror_every_left_cell"],
    "right_only_cells_are_erased": ["mark_every_right_cell"],
    "different_colors_still_overlap": ["same_color_only"],
    "same_colors_also_overlap": ["different_color_only"],
    "overlap_output_is_constant_red": [
        "copy_left_overlap_color",
        "copy_right_overlap_color",
    ],
    "exact_mirror_not_same_row": ["any_right_cell_in_same_row"],
    "output_starts_blank": ["copy_input_then_mark"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every declared plausible shortcut to fail on the demonstrations."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with exact folded overlap")
            continue
        valid_demos.append(pair)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with exact folded overlap")

    if len(valid_demos) == len(demos):
        for name, rival in LESSON_COMPETITORS.items():
            try:
                if all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
                    reasons.append(f"rival rule {name!r} still fits every demonstration")
            except Exception as exc:  # pragma: no cover - retained as review evidence
                reasons.append(f"rival rule {name!r} failed to execute: {exc}")
    return reasons


def mutation_fixtures():
    base = generate(
        73,
        2,
        difficulty="medium",
        grid_h=9,
        half_w=4,
        left_cells=7,
        overlap_count=3,
        palette_size=3,
    )
    half = observe_overrides(base)["half_w"]

    missing_bar = copy.deepcopy(base)
    for row in range(len(missing_bar)):
        missing_bar[row][half] = 0

    extra_bar = copy.deepcopy(base)
    for row in range(len(extra_bar)):
        extra_bar[row][0] = 8

    off_center_bar = copy.deepcopy(base)
    for row in range(len(off_center_bar)):
        off_center_bar[row][half] = 0
        off_center_bar[row][half - 1] = 8

    stray_eight = copy.deepcopy(base)
    stray_eight[0][0] = 8

    no_overlap = copy.deepcopy(base)
    facts = _analysis(no_overlap)
    for row, col, _, _ in facts["overlaps"]:
        no_overlap[row][2 * half - col] = 0

    all_overlap = copy.deepcopy(base)
    facts = _analysis(all_overlap)
    for row, col, _ in facts["left"]:
        all_overlap[row][2 * half - col] = facts["palette"][0]

    one_color = copy.deepcopy(base)
    for row in range(len(one_color)):
        for col in range(len(one_color[0])):
            if one_color[row][col] not in (0, 8):
                one_color[row][col] = 3

    too_few_left = copy.deepcopy(base)
    facts = _analysis(too_few_left)
    for row, col, _ in facts["left"][4:]:
        too_few_left[row][col] = 0
        mirror_col = 2 * half - col
        if 0 <= mirror_col < len(too_few_left[0]):
            too_few_left[row][mirror_col] = 0

    return [
        ("missing_bar", missing_bar),
        ("extra_bar", extra_bar),
        ("off_center_bar", off_center_bar),
        ("stray_eight", stray_eight),
        ("no_overlap", no_overlap),
        ("all_overlap", all_overlap),
        ("one_color", one_color),
        ("too_few_left", too_few_left),
    ]
