"""Generator for ``5949237e2737`` — Color Agreement Under Fold.

A full-height color-8 bar is the vertical fold axis.  For every nonzero cell on
the left, inspect the cell at the reflected position on the right.  A left cell
survives only when the reflected cell has the same nonzero color, and the
survivor is emitted at that reflected RIGHT-side position in a same-size output.
Mismatched, empty-mirror, and unrelated right-only cells are erased.

The five-profile schedule deliberately separates wrong-color mismatches, empty
mirrors, mixed mismatches, right-only distractors, and a same-row same-color
wrong-position decoy.  Two profiles reproduce the canonical shape/palette
envelopes.  Every declared axis is recoverable from the returned grid.
"""
from __future__ import annotations

import copy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5949237e2737"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "08326857fca3"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.35

SUMMARY = (
    "A zero-background odd-width grid has one centered full-height color-8 "
    "vertical fold bar. Compare each nonzero left cell with its reflected "
    "right-side cell. Emit a same-size zero grid containing only equal-color "
    "matches, painted at the reflected right-side positions. Wrong-color "
    "pairs, empty mirrors, and right-only distractors disappear. Five scheduled "
    "profiles expose those distinctions and refute occupancy, mirror-all, "
    "wrong-side, copy-right, global-color-presence, and row-local "
    "color-presence shortcuts."
)

INVARIANTS = [
    "the grid is rectangular with one centered full-height color-8 fold bar",
    "color 8 occurs only on the fold bar",
    "there is at least one equal-color mirrored pair and at least one mismatch or empty mirror",
    "at least two non-bar colors are present",
    "the output is same-size, zero-background, and contains only matching cells at right-side mirror positions",
]

SCENE_PROFILES = (
    "wrong_color_plain",
    "empty",
    "mixed",
    "right_only",
    "wrong_color_decoy",
)
SCHEDULE_PROFILES = SCENE_PROFILES
_ALLOWED_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES = ("no_bar", "no_pairs", "all_match")
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-profile schedule with two canonical 7-row anchors",
        "valid": "5..14",
        "doc": "full input-grid height",
    },
    "half_w": {
        "type": "int",
        "default": "five-profile schedule with canonical half-widths 5 and 6",
        "valid": "2..7",
        "doc": "number of columns on each side of the centered fold bar",
    },
    "left_cells": {
        "type": "int",
        "default": "scheduled 7..9",
        "valid": "7..9",
        "doc": "number of nonzero cells left of the fold bar",
    },
    "match_count": {
        "type": "int",
        "default": "scheduled 1..5",
        "valid": "1..5",
        "doc": "number of left cells whose exact mirror has the same color",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled 2..4",
        "valid": "2..4",
        "doc": "number of distinct nonzero, non-bar colors in the input",
    },
    "scene_profile": {
        "type": "str",
        "default": "five-sample cyclic curriculum",
        "valid": "|".join(SCENE_PROFILES),
        "doc": "observable mismatch/distractor profile",
    },
}


def _normalize_band(difficulty: Any) -> str:
    if difficulty in (None, "default", "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Expose the five-way deterministic curriculum schedule."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _scheduled_int(ctx, overrides: dict[str, Any], label: str, default: int, lo: int, hi: int) -> int:
    """Pin scheduled defaults while accepting the full declared override range."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return int(ctx.draw_choice(label, (default,)))


def _scheduled_choice(ctx, overrides: dict[str, Any], label: str, default: str, options: tuple[str, ...]) -> str:
    if label in overrides and overrides[label] is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (default,)))


def _profile_defaults(profile: str, band: str) -> tuple[int, int, int, int, int]:
    """Return grid_h, half_w, left_cells, match_count, palette_size."""
    if profile == "wrong_color_plain":
        # Exact canonical coarse profile: (h=7, w=11, total palette=5).
        return 7, 5, 7, 5, 3
    if profile == "empty":
        # Exact canonical coarse profile: (h=7, w=13, total palette=4).
        return 7, 6, 8, 4, 2
    if profile == "mixed":
        return {
            "easy": (6, 3, 7, 3, 3),
            "medium": (9, 4, 8, 4, 4),
            "hard": (13, 6, 9, 5, 4),
        }[band]
    if profile == "right_only":
        return {
            "easy": (5, 2, 7, 2, 2),
            "medium": (10, 5, 9, 3, 3),
            "hard": (14, 7, 9, 5, 4),
        }[band]
    if profile == "wrong_color_decoy":
        return {
            "easy": (7, 3, 8, 4, 4),
            "medium": (11, 5, 9, 2, 3),
            "hard": (12, 6, 9, 1, 4),
        }[band]
    raise ValueError(f"unknown scene profile: {profile!r}")


def _canonical_template_positions(
    profile: str,
    height: int,
    half: int,
    count: int,
    rng,
) -> list[tuple[int, int]] | None:
    templates = {
        "wrong_color_plain": (
            (1, 1), (1, 2), (2, 2), (3, 2), (3, 3), (5, 1), (5, 2),
        ),
        "empty": (
            (1, 1), (1, 2), (2, 2), (2, 3), (4, 2), (4, 3), (4, 4), (5, 3),
        ),
    }
    template = templates.get(profile)
    if template is None or len(template) != count:
        return None
    max_row = max(row for row, _ in template)
    max_col = max(col for _, col in template)
    if max_row >= height or max_col >= half:
        return None
    row_shift = rng.randint(0, height - max_row - 1)
    col_shift = rng.randint(0, half - max_col - 1)
    positions = [(row + row_shift, col + col_shift) for row, col in template]
    if rng.choice((False, True)):
        positions = [(row, half - 1 - col) for row, col in positions]
    return sorted(positions)


def _choose_left_positions(
    height: int,
    half: int,
    count: int,
    profile: str,
    rng,
) -> list[tuple[int, int]]:
    templated = _canonical_template_positions(profile, height, half, count, rng)
    if templated is not None:
        return templated

    candidates = [(row, col) for row in range(height) for col in range(half)]
    rng.shuffle(candidates)
    if profile != "wrong_color_decoy":
        return sorted(candidates[:count])

    # The decoy must refute a row-local shortcut, not merely global color
    # presence. Reserve two distinct columns on one row so one can be a true
    # match and the other a same-color wrong-position mismatch.
    decoy_row = rng.randrange(height)
    decoy_cols = rng.sample(range(half), 2)
    reserved = [(decoy_row, col) for col in decoy_cols]
    remaining = [position for position in candidates if position not in reserved]
    return sorted(reserved + remaining[: count - len(reserved)])


def _same_row_pair(positions: list[tuple[int, int]]) -> tuple[tuple[int, int], tuple[int, int]]:
    by_row: dict[int, list[tuple[int, int]]] = {}
    for position in sorted(positions):
        by_row.setdefault(position[0], []).append(position)
    for row_positions in by_row.values():
        if len(row_positions) >= 2:
            return row_positions[0], row_positions[1]
    raise ValueError("wrong_color_decoy requires two left positions on one row")


def _different_color(color: int, palette: tuple[int, ...], offset: int = 1) -> int:
    index = palette.index(color)
    return palette[(index + offset) % len(palette)]


def _paint_pairs(
    grid: list[list[int]],
    half: int,
    positions: list[tuple[int, int]],
    match_positions: set[tuple[int, int]],
    palette: tuple[int, ...],
    profile: str,
    *,
    decoy_pair: tuple[tuple[int, int], tuple[int, int]] | None = None,
) -> None:
    matches = sorted(match_positions)
    mismatches = sorted(set(positions) - match_positions)

    if profile == "wrong_color_plain":
        # A hidden mismatch color never appears anywhere on the right.  This
        # distinguishes exact mirrored equality from global color presence.
        hidden = palette[0]
        visible = palette[1:]
        for index, (row, col) in enumerate(sorted(positions)):
            mirror_col = 2 * half - col
            right_color = visible[index % len(visible)]
            if (row, col) in match_positions:
                grid[row][col] = right_color
                grid[row][mirror_col] = right_color
            else:
                grid[row][col] = hidden
                grid[row][mirror_col] = right_color
        return

    left_colors = {
        position: palette[index % len(palette)]
        for index, position in enumerate(sorted(positions))
    }

    if profile == "wrong_color_decoy":
        # Force one mismatched left color to occur at a different matching
        # right-side location. A global color-presence shortcut therefore keeps
        # it, while the true position-wise comparison erases it. Reserve those
        # two cells for palette[0], then cycle every other palette color over
        # the remaining >=5 left cells so palette_size stays exactly observable.
        if decoy_pair is None:
            raise ValueError("wrong_color_decoy requires an explicit same-row decoy pair")
        decoy_color = palette[0]
        decoy_match, decoy_mismatch = decoy_pair
        if decoy_match not in match_positions or decoy_mismatch in match_positions:
            raise ValueError("decoy pair must contain one match and one mismatch")
        left_colors = {decoy_match: decoy_color, decoy_mismatch: decoy_color}
        visible = palette[1:]
        remaining = [
            position
            for position in sorted(positions)
            if position not in (decoy_match, decoy_mismatch)
        ]
        for index, position in enumerate(remaining):
            left_colors[position] = visible[index % len(visible)]

    for index, (row, col) in enumerate(matches):
        color = left_colors[(row, col)]
        mirror_col = 2 * half - col
        grid[row][col] = color
        grid[row][mirror_col] = color

    for index, (row, col) in enumerate(mismatches):
        color = left_colors[(row, col)]
        mirror_col = 2 * half - col
        grid[row][col] = color
        if profile in ("empty", "right_only"):
            continue
        if profile == "mixed" and index % 2 == 0:
            continue
        grid[row][mirror_col] = _different_color(color, palette, 1 + (index % (len(palette) - 1)))


def _add_right_only_distractors(
    grid: list[list[int]],
    half: int,
    left_positions: set[tuple[int, int]],
    palette: tuple[int, ...],
    rng,
) -> None:
    available = [
        (row, col)
        for row in range(len(grid))
        for col in range(half)
        if (row, col) not in left_positions
    ]
    rng.shuffle(available)
    count = min(len(available), 1 + rng.randrange(min(3, len(available))))
    for index, (row, left_col) in enumerate(available[:count]):
        grid[row][2 * half - left_col] = palette[index % len(palette)]


def _draw_from_degenerate(name: str) -> list[list[int]]:
    height, half = 8, 4
    grid = full_grid(height, 2 * half + 1, 0)
    if name == "no_bar":
        grid[1][1] = 4
        grid[1][7] = 4
        grid[3][2] = 5
        grid[3][6] = 5
        return grid
    for row in range(height):
        grid[row][half] = 8
    if name == "no_pairs":
        grid[1][1] = 4
        grid[2][2] = 5
        grid[3][1] = 6
        return grid
    if name == "all_match":
        for row, col, color in ((1, 1, 4), (2, 2, 5), (3, 1, 6), (4, 3, 7)):
            grid[row][col] = color
            grid[row][2 * half - col] = color
        return grid
    raise ValueError(f"unknown degenerate fixture: {name!r}")


def _validate_grid(grid: Any) -> tuple[list[str], list[list[int]] | None]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list of rows"], None
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["rows must be nonempty lists"], None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"], None
    normalized = [list(row) for row in grid]
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
        return {"errors": errors, "grid": normalized, "bars": bars}
    half = bars[0]
    if width != 2 * half + 1:
        errors.append("fold bar must be the center column of an odd-width grid")
    extra_eights = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if normalized[row][col] == 8 and col != half
    ]
    if extra_eights:
        errors.append("color 8 may appear only on the fold bar")
    if errors:
        return {"errors": errors, "grid": normalized, "bar_col": half}

    matches: list[tuple[int, int, int]] = []
    wrong: list[tuple[int, int, int, int]] = []
    empty: list[tuple[int, int, int]] = []
    right_only: list[tuple[int, int, int]] = []
    left_cells: list[tuple[int, int, int]] = []
    for row in range(height):
        for col in range(half):
            value = normalized[row][col]
            mirror_col = 2 * half - col
            mirror = normalized[row][mirror_col]
            if value != 0:
                left_cells.append((row, col, value))
                if mirror == value:
                    matches.append((row, col, value))
                elif mirror == 0:
                    empty.append((row, col, value))
                else:
                    wrong.append((row, col, value, mirror))
            elif mirror != 0:
                right_only.append((row, mirror_col, mirror))

    palette = sorted(
        {
            value
            for row in normalized
            for value in row
            if value not in (0, 8)
        }
    )
    if not left_cells:
        errors.append("left half must contain nonzero comparison cells")
    if not matches:
        errors.append("need at least one matching mirrored pair")
    if not (wrong or empty):
        errors.append("need at least one wrong-color or empty mirrored pair")
    if len(palette) < 2:
        errors.append("need at least two non-bar colors")

    right_positions_by_color: dict[int, set[tuple[int, int]]] = {}
    for row in range(height):
        for col in range(half + 1, width):
            value = normalized[row][col]
            if value:
                right_positions_by_color.setdefault(value, set()).add((row, col))
    global_decoy = False
    row_color_decoy = False
    for row, col, value, _ in wrong:
        own_mirror = (row, 2 * half - col)
        other_positions = {
            position
            for position in right_positions_by_color.get(value, set())
            if position != own_mirror
        }
        if other_positions:
            global_decoy = True
        if any(other_row == row for other_row, _ in other_positions):
            row_color_decoy = True

    scene_profile: str | None = None
    if wrong and empty:
        scene_profile = "mixed"
    elif wrong:
        scene_profile = "wrong_color_decoy" if global_decoy else "wrong_color_plain"
    elif empty:
        scene_profile = "right_only" if right_only else "empty"

    return {
        "errors": errors,
        "grid": normalized,
        "grid_h": height,
        "grid_w": width,
        "bar_col": half,
        "half_w": half,
        "left": tuple(left_cells),
        "left_cells": len(left_cells),
        "matches": tuple(matches),
        "match_count": len(matches),
        "wrong": tuple(wrong),
        "empty": tuple(empty),
        "right_only": tuple(right_only),
        "right_only_count": len(right_only),
        "palette": tuple(palette),
        "palette_size": len(palette),
        "global_color_decoy": global_decoy,
        "row_color_decoy": row_color_decoy,
        "scene_profile": scene_profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority grammar and reject rule-hiding degeneracies."""
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
                if name not in AXES:
                    continue
                expected = int(requested) if AXES[name]["type"] == "int" else str(requested)
                if observed[name] != expected:
                    errors.append(f"requested {name}={expected!r}, observed {observed[name]!r}")
    return sorted(set(errors))


def strict_canonical_like(grid) -> list[str]:
    """Recognize the two canonical geometry/palette envelopes."""
    facts = _analysis(grid)
    reasons = list(facts.get("errors", []))
    if reasons:
        return reasons
    if facts["grid_h"] != 7:
        reasons.append(f"canonical height is 7, got {facts['grid_h']}")
    if facts["half_w"] not in (5, 6):
        reasons.append(f"canonical half-width is 5 or 6, got {facts['half_w']}")
    if facts["left_cells"] not in (7, 8):
        reasons.append(f"canonical examples have 7 or 8 left cells, got {facts['left_cells']}")
    expected_palette = {5: 3, 6: 2}.get(facts["half_w"])
    if expected_palette is not None and facts["palette_size"] != expected_palette:
        reasons.append(
            f"canonical half-width {facts['half_w']} uses {expected_palette} non-bar colors, "
            f"got {facts['palette_size']}"
        )
    if not 4 <= facts["match_count"] <= 6:
        reasons.append(f"canonical examples have 4..6 matching cells, got {facts['match_count']}")
    return reasons


def observe_overrides(grid) -> dict[str, int | str]:
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    if facts["scene_profile"] is None:
        raise ValueError("scene profile is not observable")
    return {
        "grid_h": facts["grid_h"],
        "half_w": facts["half_w"],
        "left_cells": facts["left_cells"],
        "match_count": facts["match_count"],
        "palette_size": facts["palette_size"],
        "scene_profile": facts["scene_profile"],
    }


def semantic_observables(grid) -> dict[str, Any]:
    facts = _analysis(grid)
    if facts.get("errors"):
        return {"errors": list(facts["errors"])}
    return {
        **observe_overrides(grid),
        "wrong_count": len(facts["wrong"]),
        "empty_count": len(facts["empty"]),
        "right_only_count": facts["right_only_count"],
        "global_color_decoy": facts["global_color_decoy"],
        "row_color_decoy": facts["row_color_decoy"],
    }


def rule_mirror(grid) -> list[list[int]]:
    """Input-pure Python audit mirror; canonical Racket remains authoritative."""
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = full_grid(facts["grid_h"], facts["grid_w"], 0)
    half = facts["half_w"]
    for row, col, value in facts["matches"]:
        output[row][2 * half - col] = value
    return output


def generate(seed, sample_index, *, difficulty=None, **overrides):
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

    band = _normalize_band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    scheduled_profile = schedule_profile(seed, sample_index, band)
    scene_profile = _scheduled_choice(
        ctx, overrides, "scene_profile", scheduled_profile, SCENE_PROFILES
    )
    defaults = _profile_defaults(scheduled_profile, band)
    grid_h = _scheduled_int(ctx, overrides, "grid_h", defaults[0], 5, 14)
    half_w = _scheduled_int(ctx, overrides, "half_w", defaults[1], 2, 7)
    left_cells = _scheduled_int(ctx, overrides, "left_cells", defaults[2], 7, 9)
    match_count = _scheduled_int(ctx, overrides, "match_count", defaults[3], 1, 5)
    palette_size = _scheduled_int(ctx, overrides, "palette_size", defaults[4], 2, 4)

    grid = full_grid(grid_h, 2 * half_w + 1, 0)
    for row in range(grid_h):
        grid[row][half_w] = 8

    layout_rng = ctx.draw_rng("left_layout")
    positions = _choose_left_positions(
        grid_h, half_w, left_cells, scene_profile, layout_rng
    )
    match_rng = ctx.draw_rng("match_selection")
    decoy_pair = None
    if scene_profile == "wrong_color_decoy":
        decoy_match, decoy_mismatch = _same_row_pair(positions)
        remaining = [
            position
            for position in positions
            if position not in (decoy_match, decoy_mismatch)
        ]
        match_positions = {decoy_match}
        match_positions.update(match_rng.sample(remaining, match_count - 1))
        decoy_pair = (decoy_match, decoy_mismatch)
    else:
        match_positions = set(match_rng.sample(positions, match_count))

    palette_rng = ctx.draw_rng("palette")
    palette_values = list(_ALLOWED_COLORS)
    palette_rng.shuffle(palette_values)
    palette = tuple(palette_values[:palette_size])
    _paint_pairs(
        grid,
        half_w,
        positions,
        match_positions,
        palette,
        scene_profile,
        decoy_pair=decoy_pair,
    )
    if scene_profile == "right_only":
        _add_right_only_distractors(
            grid,
            half_w,
            set(positions),
            palette,
            ctx.draw_rng("right_only_distractors"),
        )

    expected = {
        "grid_h": grid_h,
        "half_w": half_w,
        "left_cells": left_cells,
        "match_count": match_count,
        "palette_size": palette_size,
        "scene_profile": scene_profile,
    }
    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal construction error: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"internal construction mismatch: expected {expected}, observed {observed}")
    return copy.deepcopy(grid)


def _rival_occupancy(grid) -> list[list[int]]:
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = full_grid(facts["grid_h"], facts["grid_w"], 0)
    half = facts["half_w"]
    for row, col, _ in facts["left"]:
        mirror_col = 2 * half - col
        if facts["grid"][row][mirror_col] != 0:
            output[row][mirror_col] = facts["grid"][row][mirror_col]
    return output


def _rival_mirror_all_left(grid) -> list[list[int]]:
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = full_grid(facts["grid_h"], facts["grid_w"], 0)
    half = facts["half_w"]
    for row, col, value in facts["left"]:
        output[row][2 * half - col] = value
    return output


def _rival_left_side_output(grid) -> list[list[int]]:
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = full_grid(facts["grid_h"], facts["grid_w"], 0)
    for row, col, value in facts["matches"]:
        output[row][col] = value
    return output


def _rival_copy_right(grid) -> list[list[int]]:
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = full_grid(facts["grid_h"], facts["grid_w"], 0)
    half = facts["half_w"]
    for row in range(facts["grid_h"]):
        for col in range(half + 1, facts["grid_w"]):
            if facts["grid"][row][col] != 0:
                output[row][col] = facts["grid"][row][col]
    return output


def _rival_global_color_presence(grid) -> list[list[int]]:
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = full_grid(facts["grid_h"], facts["grid_w"], 0)
    half = facts["half_w"]
    right_colors = {
        facts["grid"][row][col]
        for row in range(facts["grid_h"])
        for col in range(half + 1, facts["grid_w"])
        if facts["grid"][row][col] != 0
    }
    for row, col, value in facts["left"]:
        if value in right_colors:
            output[row][2 * half - col] = value
    return output


def _rival_row_color_presence(grid) -> list[list[int]]:
    facts = _analysis(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    output = full_grid(facts["grid_h"], facts["grid_w"], 0)
    half = facts["half_w"]
    for row, col, value in facts["left"]:
        if value in facts["grid"][row][half + 1 :]:
            output[row][2 * half - col] = value
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "occupancy_only": _rival_occupancy,
    "mirror_all_left": _rival_mirror_all_left,
    "matching_cells_on_left": _rival_left_side_output,
    "copy_every_right_cell": _rival_copy_right,
    "global_color_presence": _rival_global_color_presence,
    "row_color_presence": _rival_row_color_presence,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _has_wrong_color(grid) -> bool:
    return bool(_analysis(grid).get("wrong"))


def _has_empty_mirror(grid) -> bool:
    return bool(_analysis(grid).get("empty"))


def _has_match(grid) -> bool:
    return bool(_analysis(grid).get("matches"))


def _has_right_only(grid) -> bool:
    return bool(_analysis(grid).get("right_only"))


def _has_global_decoy(grid) -> bool:
    return bool(_analysis(grid).get("global_color_decoy"))


def _has_row_color_decoy(grid) -> bool:
    return bool(_analysis(grid).get("row_color_decoy"))


SEMANTIC_WITNESSES = {
    "wrong_color_pair_is_erased": _has_wrong_color,
    "empty_mirror_is_erased": _has_empty_mirror,
    "matching_cell_moves_to_right": _has_match,
    "right_only_distractor_is_erased": _has_right_only,
    "same_color_elsewhere_is_not_a_match": _has_global_decoy,
    "same_row_color_elsewhere_is_not_a_match": _has_row_color_decoy,
}
WITNESS_RIVALS = {
    "wrong_color_pair_is_erased": ["occupancy_only"],
    "empty_mirror_is_erased": ["mirror_all_left"],
    "matching_cell_moves_to_right": ["matching_cells_on_left"],
    "right_only_distractor_is_erased": ["copy_every_right_cell"],
    "same_color_elsewhere_is_not_a_match": ["global_color_presence"],
    "same_row_color_elsewhere_is_not_a_match": ["row_color_presence"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a five-example lesson to kill every named shortcut."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    observed_profiles: set[str] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with exact mirrored color agreement")
            continue
        observed_profiles.add(observe_overrides(pair["input"])["scene_profile"])

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with exact mirrored color agreement")

    missing_profiles = sorted(set(SCENE_PROFILES) - observed_profiles)
    if missing_profiles:
        reasons.append(f"demonstrations omit scene profiles {missing_profiles}")

    for name, rival in LESSON_COMPETITORS.items():
        survives = True
        for pair in demos:
            try:
                if rival(pair["input"]) != pair["output"]:
                    survives = False
                    break
            except Exception:
                survives = False
                break
        if survives:
            reasons.append(f"rival rule {name!r} still fits every demonstration")
    return reasons


def mutation_fixtures():
    base = generate(
        73,
        2,
        difficulty="medium",
        grid_h=9,
        half_w=4,
        left_cells=8,
        match_count=4,
        palette_size=3,
        scene_profile="mixed",
    )
    half = observe_overrides(base)["half_w"]

    missing_bar = copy.deepcopy(base)
    for row in range(len(missing_bar)):
        missing_bar[row][half] = 0

    off_center_bar = copy.deepcopy(base)
    for row in range(len(off_center_bar)):
        off_center_bar[row][half] = 0
        off_center_bar[row][half - 1] = 8

    extra_eight = copy.deepcopy(base)
    extra_eight[0][0] = 8

    all_match = copy.deepcopy(base)
    for row in range(len(all_match)):
        for col in range(half):
            value = all_match[row][col]
            if value:
                all_match[row][2 * half - col] = value

    no_match = copy.deepcopy(base)
    palette = [1, 2, 3, 4, 5, 6, 7, 9]
    for row in range(len(no_match)):
        for col in range(half):
            value = no_match[row][col]
            if value and no_match[row][2 * half - col] == value:
                no_match[row][2 * half - col] = next(color for color in palette if color != value)

    invalid_color = copy.deepcopy(base)
    invalid_color[0][0] = 10

    ragged = copy.deepcopy(base)
    ragged[0] = ragged[0][:-1]

    return [
        ("missing_fold_bar", missing_bar),
        ("off_center_fold_bar", off_center_bar),
        ("extra_color_8_outside_bar", extra_eight),
        ("all_pairs_match_no_negative_contrast", all_match),
        ("no_matching_pair", no_match),
        ("invalid_arc_color", invalid_color),
        ("ragged_grid", ragged),
    ]
