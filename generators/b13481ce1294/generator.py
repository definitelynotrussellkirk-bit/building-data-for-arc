"""Reviewed generator for ARC task b13481ce1294 (Panel XOR overlay).

A full color-8 column separates equal-width left and right panels.  At each
panel coordinate the canonical rule keeps the unique nonzero color when
exactly one side is nonzero, and writes 0 when both sides are zero or both are
nonzero.  Ordinary draws deliberately include every branch, including both
same-color and different-color overlaps, so equality-cancellation and simple
union shortcuts cannot fit the generated lessons.
"""
from __future__ import annotations

import copy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b13481ce1294"
TASK_ID = "b13481ce1294"
VERSION = "3.0.0"
RULE_HASH = "d86f259d9d68"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Generate two equal panels separated by one full color-8 column.  For "
    "each aligned cell, the output keeps the source color when exactly one "
    "panel is nonzero and writes 0 when both or neither are nonzero.  Default "
    "draws alternate a canonical 4x9 input profile with a band-specific "
    "expanded profile, use exactly two or three panel colors, and include "
    "left-only, right-only, both-zero, same-color overlap, and different-color "
    "overlap witnesses in every scene."
)

INVARIANTS = [
    "all cells are integer ARC colors in 0..9",
    "exactly one full vertical color-8 separator is present",
    "the separator divides two nonempty equal-width panels",
    "color 8 appears only in the separator column",
    "ordinary draws contain left-only, right-only, overlap, and empty cells",
    "ordinary draws contain both same-color and different-color overlaps",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

BRANCH_PROFILES = ("xor_heavy", "balanced", "overlap_heavy")
PANEL_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "alternating canonical/band-expanded profile",
        "valid": "3..10",
    },
    "panel_w": {
        "type": "int",
        "default": "alternating canonical/band-expanded profile",
        "valid": "2..8",
    },
    "palette_size": {
        "type": "int",
        "default": "sample-index schedule over 2 and 3",
        "valid": "2..5",
    },
    "branch_profile": {
        "type": "str",
        "default": "sample-index cycle",
        "valid": "|".join(BRANCH_PROFILES),
    },
}

_ALLOWED_OVERRIDES = frozenset(AXES)
_BAND_ALT_SHAPES: dict[str | None, tuple[int, int]] = {
    None: (5, 4),
    "easy": (3, 3),
    "medium": (5, 4),
    "hard": (6, 5),
}
_PALETTE_SCHEDULE = (2, 3, 3, 2)


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in _BAND_ALT_SHAPES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "panel_w", "palette_size"):
        value = overrides.get(name)
        if value is not None and (type(value) is not int):
            raise TypeError(f"{name} must be an integer")
    profile = overrides.get("branch_profile")
    if profile is not None and not isinstance(profile, str):
        raise TypeError("branch_profile must be a string")


def _draw_exact_int(ctx, overrides: dict[str, Any], name: str,
                    default: int, lo: int, hi: int) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _draw_exact_choice(ctx, overrides: dict[str, Any], name: str,
                       default: str, options: tuple[str, ...]) -> str:
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _default_shape(sample_index: int, difficulty: str | None) -> tuple[int, int]:
    if sample_index % 2 == 0:
        return 4, 4
    return _BAND_ALT_SHAPES[difficulty]


def _branch_counts(cell_count: int, profile: str) -> tuple[int, int, int, int]:
    """Return left-only, right-only, overlap, empty counts.

    All domains have at least six aligned cells, so every returned tuple can
    include both directional XOR branches, two overlap cells (one same-color
    and one different-color), and at least one both-zero cell.
    """
    if cell_count < 6:
        raise ValueError("panel area must be at least 6")
    if profile == "xor_heavy":
        overlap = max(2, cell_count // 4)
        empty = max(1, cell_count // 6)
        xor_total = cell_count - overlap - empty
        if xor_total <= overlap:
            overlap = 2
            empty = 1
            xor_total = cell_count - 3
    elif profile == "balanced":
        overlap = max(2, cell_count // 3)
        while cell_count - 2 * overlap < 1:
            overlap -= 1
        xor_total = overlap
        empty = cell_count - xor_total - overlap
    elif profile == "overlap_heavy":
        xor_total = max(2, cell_count // 5)
        empty = max(1, cell_count // 6)
        overlap = cell_count - xor_total - empty
        if overlap <= xor_total:
            xor_total = 2
            empty = 1
            overlap = cell_count - 3
    else:  # validated by GenCtx, retained as a local defensive guard
        raise ValueError(f"unknown branch profile {profile!r}")

    left_only = (xor_total + 1) // 2
    right_only = xor_total // 2
    if min(left_only, right_only, overlap, empty) < 1 or overlap < 2:
        raise AssertionError("branch allocation lost a mandatory witness")
    return left_only, right_only, overlap, empty


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    default_h, default_pw = _default_shape(int(sample_index), difficulty)
    height = _draw_exact_int(ctx, overrides, "grid_h", default_h, 3, 10)
    panel_w = _draw_exact_int(ctx, overrides, "panel_w", default_pw, 2, 8)
    default_palette_size = _PALETTE_SCHEDULE[int(sample_index) % len(_PALETTE_SCHEDULE)]
    palette_size = _draw_exact_int(
        ctx, overrides, "palette_size", default_palette_size, 2, 5
    )
    default_profile = BRANCH_PROFILES[int(sample_index) % len(BRANCH_PROFILES)]
    branch_profile = _draw_exact_choice(
        ctx, overrides, "branch_profile", default_profile, BRANCH_PROFILES
    )

    layout_rng = ctx.draw_rng(
        f"layout|h={height}|pw={panel_w}|palette={palette_size}|profile={branch_profile}"
    )
    palette_rng = ctx.draw_rng(f"palette|size={palette_size}")
    palette = list(PANEL_COLORS)
    palette_rng.shuffle(palette)
    palette = palette[:palette_size]

    positions = [(row, col) for row in range(height) for col in range(panel_w)]
    layout_rng.shuffle(positions)
    n_left, n_right, n_overlap, _n_empty = _branch_counts(
        len(positions), branch_profile
    )
    cursor = 0
    left_only = positions[cursor:cursor + n_left]
    cursor += n_left
    right_only = positions[cursor:cursor + n_right]
    cursor += n_right
    overlaps = positions[cursor:cursor + n_overlap]

    grid = full_grid(height, panel_w * 2 + 1, 0)
    sep = panel_w
    for row in range(height):
        grid[row][sep] = 8

    # XOR-output cells deliberately begin with two different colors, so every
    # ordinary scene refutes a fixed-output-color shortcut by itself.
    xor_slots = [(pos, "left") for pos in left_only] + [
        (pos, "right") for pos in right_only
    ]
    for index, ((row, col), side) in enumerate(xor_slots):
        color = palette[index % palette_size]
        target_col = col if side == "left" else sep + 1 + col
        grid[row][target_col] = color

    # The first overlap is same-color; the second is different-color.  Assign
    # unused palette colors here first so `palette_size` is exactly observable
    # even at the smallest 3x2 panel area.
    same_color = palette[2] if palette_size >= 3 else palette[0]
    row, col = overlaps[0]
    grid[row][col] = same_color
    grid[row][sep + 1 + col] = same_color

    if palette_size >= 5:
        diff_left, diff_right = palette[3], palette[4]
    elif palette_size == 4:
        diff_left, diff_right = palette[3], palette[0]
    else:
        diff_left, diff_right = palette[0], palette[1]
    row, col = overlaps[1]
    grid[row][col] = diff_left
    grid[row][sep + 1 + col] = diff_right

    for index, (row, col) in enumerate(overlaps[2:]):
        left_color = palette[(index + 1) % palette_size]
        right_color = palette[(index + 2) % palette_size]
        grid[row][col] = left_color
        grid[row][sep + 1 + col] = right_color

    meta = {
        "grid_h": height,
        "panel_w": panel_w,
        "palette_size": palette_size,
        "branch_profile": branch_profile,
    }
    errors = self_check(grid, meta=meta)
    if errors:
        raise AssertionError("generated malformed panel-XOR scene: " + "; ".join(errors))
    teaching_errors = _teaching_errors(grid)
    if teaching_errors:
        raise AssertionError("generated rule-hiding panel-XOR scene: " + "; ".join(teaching_errors))
    return grid


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)):
        raise ValueError("grid must be a list or tuple")
    result: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            result.append([int(value) for value in row])
        elif isinstance(row, (list, tuple)):
            result.append(list(row))
        else:
            raise ValueError("grid rows must be lists, tuples, or digit strings")
    return result


def _analyze(grid: Any) -> dict[str, Any]:
    try:
        values = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}
    if not values or not values[0]:
        return {"errors": ["grid must be nonempty"]}
    width = len(values[0])
    if any(len(row) != width for row in values):
        return {"errors": ["grid must be rectangular"]}
    height = len(values)
    errors: list[str] = []
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in values for value in row
    ):
        errors.append("every cell must be an integer ARC color in 0..9")
        return {"errors": errors, "grid": values, "height": height, "width": width}

    separators = [
        col for col in range(width)
        if all(values[row][col] == 8 for row in range(height))
    ]
    if len(separators) != 1:
        errors.append(
            f"expected exactly one full color-8 separator column, found {len(separators)}"
        )
        return {
            "errors": errors,
            "grid": values,
            "height": height,
            "width": width,
            "separators": separators,
        }
    sep = separators[0]
    panel_w = sep
    right_w = width - sep - 1
    if panel_w < 1 or panel_w != right_w:
        errors.append(
            f"separator must divide equal nonempty panels, got widths {panel_w}/{right_w}"
        )
        return {
            "errors": errors,
            "grid": values,
            "height": height,
            "width": width,
            "separator": sep,
            "panel_w": panel_w,
        }
    stray_eights = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if col != sep and values[row][col] == 8
    ]
    if stray_eights:
        errors.append("color 8 may appear only in the full separator column")

    left = [row[:sep] for row in values]
    right = [row[sep + 1:] for row in values]
    branch_counts = {
        "left_only": 0,
        "right_only": 0,
        "overlap": 0,
        "empty": 0,
        "same_overlap": 0,
        "different_overlap": 0,
    }
    panel_colors: set[int] = set()
    output_colors: set[int] = set()
    for row in range(height):
        for col in range(panel_w):
            lv = left[row][col]
            rv = right[row][col]
            if lv not in (0, 8):
                panel_colors.add(lv)
            if rv not in (0, 8):
                panel_colors.add(rv)
            if lv != 0 and rv == 0:
                branch_counts["left_only"] += 1
                output_colors.add(lv)
            elif lv == 0 and rv != 0:
                branch_counts["right_only"] += 1
                output_colors.add(rv)
            elif lv != 0 and rv != 0:
                branch_counts["overlap"] += 1
                if lv == rv:
                    branch_counts["same_overlap"] += 1
                else:
                    branch_counts["different_overlap"] += 1
            else:
                branch_counts["empty"] += 1

    xor_total = branch_counts["left_only"] + branch_counts["right_only"]
    overlap = branch_counts["overlap"]
    if xor_total > overlap:
        branch_profile = "xor_heavy"
    elif xor_total == overlap:
        branch_profile = "balanced"
    else:
        branch_profile = "overlap_heavy"
    return {
        "errors": errors,
        "grid": values,
        "height": height,
        "width": width,
        "separator": sep,
        "panel_w": panel_w,
        "left": left,
        "right": right,
        "palette_size": len(panel_colors),
        "panel_colors": panel_colors,
        "output_colors": output_colors,
        "branch_counts": branch_counts,
        "branch_profile": branch_profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural input-grammar check; curriculum requirements live elsewhere."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    if not 3 <= analysis["height"] <= 10:
        errors.append("grid height must be in 3..10")
    if not 2 <= analysis["panel_w"] <= 8:
        errors.append("panel width must be in 2..8")
    if not isinstance(meta, dict):
        return errors
    requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
    observed = {
        "grid_h": analysis["height"],
        "panel_w": analysis["panel_w"],
        "palette_size": analysis["palette_size"],
        "branch_profile": analysis["branch_profile"],
    }
    for name, actual in observed.items():
        expected = requested.get(name)
        if expected is not None and expected != actual:
            errors.append(f"meta {name} requested {expected!r}, observed {actual!r}")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe axes: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "panel_w": analysis["panel_w"],
        "palette_size": analysis["palette_size"],
        "branch_profile": analysis["branch_profile"],
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    counts = analysis["branch_counts"]
    for branch in ("left_only", "right_only", "overlap", "empty"):
        if counts[branch] == 0:
            errors.append(f"missing {branch} rule branch")
    if not 2 <= analysis["palette_size"] <= 5:
        errors.append("canonical-like scenes use 2..5 panel colors")
    if len(analysis["output_colors"]) < 2:
        errors.append("XOR output must preserve at least two source colors")
    return errors


def _teaching_errors(grid) -> list[str]:
    analysis = _analyze(grid)
    errors = strict_canonical_like(grid)
    if errors:
        return errors
    counts = analysis["branch_counts"]
    if counts["same_overlap"] == 0:
        errors.append("missing same-color overlap witness")
    if counts["different_overlap"] == 0:
        errors.append("missing different-color overlap witness")
    return errors


def rule_mirror(grid) -> list[list[int]]:
    """Test-only Python mirror; the bundled Racket program remains authority."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid panel-XOR input: " + "; ".join(analysis["errors"]))
    left, right = analysis["left"], analysis["right"]
    output = full_grid(analysis["height"], analysis["panel_w"], 0)
    for row in range(analysis["height"]):
        for col in range(analysis["panel_w"]):
            lv, rv = left[row][col], right[row][col]
            if lv != 0 and rv == 0:
                output[row][col] = lv
            elif lv == 0 and rv != 0:
                output[row][col] = rv
    return output


def _rival_union_left_priority(grid):
    analysis = _analyze(grid)
    out = full_grid(analysis["height"], analysis["panel_w"], 0)
    for row in range(analysis["height"]):
        for col in range(analysis["panel_w"]):
            lv, rv = analysis["left"][row][col], analysis["right"][row][col]
            out[row][col] = lv if lv != 0 else rv
    return out


def _rival_cancel_equal_only(grid):
    analysis = _analyze(grid)
    out = full_grid(analysis["height"], analysis["panel_w"], 0)
    for row in range(analysis["height"]):
        for col in range(analysis["panel_w"]):
            lv, rv = analysis["left"][row][col], analysis["right"][row][col]
            if lv != 0 and rv != 0:
                out[row][col] = 0 if lv == rv else lv
            else:
                out[row][col] = lv if lv != 0 else rv
    return out


def _rival_left_only(grid):
    analysis = _analyze(grid)
    out = full_grid(analysis["height"], analysis["panel_w"], 0)
    for row in range(analysis["height"]):
        for col in range(analysis["panel_w"]):
            lv, rv = analysis["left"][row][col], analysis["right"][row][col]
            if lv != 0 and rv == 0:
                out[row][col] = lv
    return out


def _rival_right_only(grid):
    analysis = _analyze(grid)
    out = full_grid(analysis["height"], analysis["panel_w"], 0)
    for row in range(analysis["height"]):
        for col in range(analysis["panel_w"]):
            lv, rv = analysis["left"][row][col], analysis["right"][row][col]
            if lv == 0 and rv != 0:
                out[row][col] = rv
    return out


def _rival_fixed_color(grid):
    analysis = _analyze(grid)
    out = full_grid(analysis["height"], analysis["panel_w"], 0)
    for row in range(analysis["height"]):
        for col in range(analysis["panel_w"]):
            lv, rv = analysis["left"][row][col], analysis["right"][row][col]
            if (lv != 0) != (rv != 0):
                out[row][col] = 1
    return out


def _rival_fill_empty(grid):
    analysis = _analyze(grid)
    out = rule_mirror(grid)
    for row in range(analysis["height"]):
        for col in range(analysis["panel_w"]):
            if analysis["left"][row][col] == 0 and analysis["right"][row][col] == 0:
                out[row][col] = 8
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "union_left_priority": _rival_union_left_priority,
    "cancel_equal_only": _rival_cancel_equal_only,
    "left_only": _rival_left_only,
    "right_only": _rival_right_only,
    "fixed_color_mask": _rival_fixed_color,
    "fill_empty_with_separator": _rival_fill_empty,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _branch_witness(name: str):
    def predicate(grid) -> bool:
        analysis = _analyze(grid)
        return not analysis.get("errors") and analysis["branch_counts"][name] > 0
    return predicate


def _multicolor_output(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis.get("errors") and len(analysis["output_colors"]) >= 2


def _canonical_shape(grid) -> bool:
    analysis = _analyze(grid)
    return (
        not analysis.get("errors")
        and analysis["height"] == 4
        and analysis["panel_w"] == 4
        and analysis["palette_size"] in (2, 3)
    )


def _expanded_shape(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis.get("errors") and not _canonical_shape(grid)


SEMANTIC_WITNESSES = {
    "left_only_branch": _branch_witness("left_only"),
    "right_only_branch": _branch_witness("right_only"),
    "same_color_overlap": _branch_witness("same_overlap"),
    "different_color_overlap": _branch_witness("different_overlap"),
    "both_zero_branch": _branch_witness("empty"),
    "multicolor_xor_output": _multicolor_output,
}

WITNESS_RIVALS = {
    "left_only_branch": ["right_only"],
    "right_only_branch": ["left_only"],
    "same_color_overlap": ["union_left_priority"],
    "different_color_overlap": ["cancel_equal_only"],
    "multicolor_xor_output": ["fixed_color_mask"],
    "both_zero_branch": ["fill_empty_with_separator"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to eliminate every named plausible rival."""
    errors: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]

    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} is missing input/output")
            continue
        findings = strict_canonical_like(pair["input"])
        if findings:
            errors.append(f"demo {index} is outside the teaching grammar: {findings[:2]}")
            continue
        if rule_mirror(pair["input"]) != _coerce_grid(pair["output"]):
            errors.append(f"demo {index} output does not match panel XOR")
            continue
        valid_demos.append(pair)

    if len(valid_demos) == len(demos):
        for name, rival in LESSON_COMPETITORS.items():
            if all(rival(pair["input"]) == _coerce_grid(pair["output"])
                   for pair in valid_demos):
                errors.append(f"rival {name!r} survives every demonstration")
        if not any(_branch_witness("different_overlap")(pair["input"])
                   for pair in valid_demos):
            errors.append("demonstrations omit different-color overlap")

    if not isinstance(query, dict) or "input" not in query:
        errors.append("query is missing input")
    else:
        findings = strict_canonical_like(query["input"])
        if findings:
            errors.append(f"query is outside the teaching grammar: {findings[:2]}")
        if "output" in query and rule_mirror(query["input"]) != _coerce_grid(query["output"]):
            errors.append("query output does not match panel XOR")
    return errors


def mutation_fixtures() -> list[tuple[str, Any]]:
    """Targeted structural impostors for focused tests and review evidence."""
    valid = generate(20260727, 0, difficulty="medium")
    analysis = _analyze(valid)
    sep = analysis["separator"]
    fixtures: list[tuple[str, Any]] = []

    no_separator = copy.deepcopy(valid)
    for row in range(len(no_separator)):
        no_separator[row][sep] = 0
    fixtures.append(("missing separator", no_separator))

    second_separator = copy.deepcopy(valid)
    for row in range(len(second_separator)):
        second_separator[row][0] = 8
    fixtures.append(("second full separator", second_separator))

    stray_eight = copy.deepcopy(valid)
    stray_eight[0][0] = 8
    fixtures.append(("stray panel eight", stray_eight))

    bad_color = copy.deepcopy(valid)
    bad_color[0][0] = 10
    fixtures.append(("non-ARC color", bad_color))

    ragged = copy.deepcopy(valid)
    ragged[0] = ragged[0][:-1]
    fixtures.append(("ragged row", ragged))
    return fixtures
