"""Generator for ARC task 25ff71a9 / content hash 67a35830fe56.

The authoritative rule shifts the entire grid down by one row.  The old bottom
row is discarded and the new top row is background.  The curriculum cycles
through four visibly different row profiles so a four-demonstration lesson
shows both ordinary translation and the otherwise-canonical-compatible bottom
boundary case.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "67a35830fe56"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "6cea5d0ac450"

SUMMARY = (
    "Shift every input row down by exactly one position: output row 0 is all "
    "background 0, output row r is input row r-1, and the original bottom row "
    "is discarded. Generated lessons cycle through top-only, middle-only, "
    "multirow vertical, and explicit bottom-row-drop inputs."
)
INVARIANTS = [
    "rectangular 3..6 by 3..6 grid with background 0 and one foreground color",
    "at least one foreground cell lies above the bottom row",
    "four sequential samples cover top, middle, multirow, and bottom-drop cues",
    "bottom-row foreground is present in the bottom_drop profile and must vanish",
]

ROW_PROFILES = ("top_only", "middle_only", "vertical", "bottom_drop")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

AXES = {
    "grid_h": {
        "type": "int",
        "default": "3 every fourth sample; otherwise difficulty-banded 3..6",
        "valid": "3..6",
    },
    "grid_w": {
        "type": "int",
        "default": "3 every fourth sample; otherwise difficulty-banded 3..6",
        "valid": "3..6",
    },
    "fg_color": {"type": "color", "default": "rng non-zero", "valid": "1..9"},
    "row_profile": {
        "type": "str",
        "default": "cyclic by sample_index",
        "valid": "|".join(ROW_PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _draw_dim(ctx, label: str, sample_index: int, band: str, overrides: dict[str, Any]) -> int:
    """Draw one dimension while honoring the full declared override domain."""
    if label in overrides:
        return ctx.draw_int(label, 3, 6)
    if sample_index % 4 == 0:
        return ctx.draw_choice(label, [3])
    choices = {
        "easy": [3, 4],
        "medium": [3, 4, 5],
        "hard": [3, 5, 6],
    }[band]
    return ctx.draw_choice(label, choices)


def _draw_profile(ctx, sample_index: int, overrides: dict[str, Any]) -> str:
    if "row_profile" in overrides:
        return ctx.draw_choice("row_profile", list(ROW_PROFILES))
    return ctx.draw_choice("row_profile", [ROW_PROFILES[sample_index % len(ROW_PROFILES)]])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    h = _draw_dim(ctx, "grid_h", sample_index, band, overrides)
    w = _draw_dim(ctx, "grid_w", sample_index, band, overrides)
    if "fg_color" in overrides:
        fg = ctx.draw_color("fg_color", exclude={0})
    else:
        fg = ctx.draw_choice("fg_color", list(range(3, 10)))
    profile = _draw_profile(ctx, sample_index, overrides)
    rng = ctx.draw_rng("placement")
    grid = full_grid(h, w, 0)

    if profile == "top_only":
        count = 2
        for c in rng.sample(range(w), count):
            grid[0][c] = fg
    elif profile == "middle_only":
        row = rng.randint(1, h - 2)
        count = 2
        for c in rng.sample(range(w), count):
            grid[row][c] = fg
    elif profile == "vertical":
        col = rng.randrange(w)
        for row in range(h - 1):
            grid[row][col] = fg
    elif profile == "bottom_drop":
        top_count = 2
        bottom_count = 1
        for c in rng.sample(range(w), top_count):
            grid[0][c] = fg
        for c in rng.sample(range(w), bottom_count):
            grid[h - 1][c] = fg
    else:  # draw_choice validates overrides, so this is defensive only.
        raise ValueError(f"unknown row_profile: {profile!r}")

    return grid


def _shape(grid: Any) -> tuple[int, int, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return 0, 0, ["grid rows must be non-empty"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        errors.append("grid must be rectangular")
    if not (3 <= h <= 6 and 3 <= w <= 6):
        errors.append(f"grid dimensions must each be 3..6, got {h}x{w}")
    return h, w, errors


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    h, w, errors = _shape(grid)
    info: dict[str, Any] = {"grid_h": h, "grid_w": w}
    if errors:
        return info, errors

    flat = [value for row in grid for value in row]
    if any(isinstance(value, bool) or not isinstance(value, int) or not (0 <= value <= 9) for value in flat):
        errors.append("cells must be integer ARC colors 0..9")
        return info, errors
    colors = sorted(set(flat) - {0})
    if len(colors) != 1:
        errors.append(f"expected exactly one non-zero foreground color, got {colors}")
        return info, errors

    fg = colors[0]
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == fg}
    info.update({"fg_color": fg, "cells": cells})
    if not cells:
        errors.append("at least one foreground cell is required")
        return info, errors
    if all(r == h - 1 for r, _ in cells):
        errors.append("at least one foreground cell must lie above the bottom row")
        return info, errors

    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}
    canonical_cellsets = {
        frozenset({(0, 1), (0, 2), (1, 2)}),
        frozenset({(1, 0), (1, 1), (1, 2)}),
        frozenset({(0, 1), (1, 0), (1, 1)}),
        frozenset({(0, 0), (0, 1), (0, 2)}),
        frozenset({(1, 1)}),
        frozenset({(0, 0), (1, 0)}),
    }
    info["canonical_3x3"] = (
        h == 3 and w == 3 and fg in (1, 2)
        and frozenset(cells) in canonical_cellsets
    )

    profile: str | None = None
    if h - 1 in rows:
        top_cells = cells & {(0, c) for c in range(w)}
        bottom_cells = cells & {(h - 1, c) for c in range(w)}
        if rows == {0, h - 1} and len(top_cells) == 2 and len(bottom_cells) == 1:
            profile = "bottom_drop"
        else:
            errors.append("bottom-row lessons must use only top and bottom foreground rows")
    elif rows == {0} and len(cells) == 2:
        profile = "top_only"
    elif len(rows) == 1 and 0 not in rows and len(cells) == 2:
        profile = "middle_only"
    elif cols and len(cols) == 1 and rows == set(range(h - 1)):
        profile = "vertical"
    elif not info["canonical_3x3"]:
        errors.append("foreground does not match a declared teaching row profile")

    if profile is not None:
        info["row_profile"] = profile
    return info, errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if "row_profile" not in info:
        raise ValueError("grid is canonical-lawful but not one of the generated row profiles")
    return {name: info[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed or rule-hiding scenes while accepting all official inputs."""
    return _analyse(grid)[1]


def strict_canonical_like(grid: Any) -> list[str]:
    info, errors = _analyse(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if (info["grid_h"], info["grid_w"]) != (3, 3):
        reasons.append("canonical task uses a 3x3 grid")
    return reasons


def rule_mirror(grid: Any) -> list[list[int]]:
    h, w, errors = _shape(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return [[0] * w] + [list(row) for row in grid[: h - 1]]


def _profile_is(name: str):
    def predicate(grid: Any) -> bool:
        info, errors = _analyse(grid)
        return not errors and info.get("row_profile") == name

    return predicate


SEMANTIC_WITNESSES = {
    "top_row_translation": _profile_is("top_only"),
    "middle_row_translation": _profile_is("middle_only"),
    "multirow_translation": _profile_is("vertical"),
    "bottom_row_is_dropped": _profile_is("bottom_drop"),
}


def _rival_identity(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def _rival_clear_top_only(grid: Any) -> list[list[int]]:
    out = [list(row) for row in grid]
    out[0] = [0] * len(out[0])
    return out


def _rival_shift_down_wrap(grid: Any) -> list[list[int]]:
    return [list(grid[-1])] + [list(row) for row in grid[:-1]]


def _rival_copy_down(grid: Any) -> list[list[int]]:
    out = [list(row) for row in grid]
    for r in range(1, len(grid)):
        for c, value in enumerate(grid[r - 1]):
            if value != 0:
                out[r][c] = value
    return out


SEMANTIC_RIVALS = {
    "identity_no_shift": _rival_identity,
    "clear_top_without_shift": _rival_clear_top_only,
    "shift_down_with_wraparound": _rival_shift_down_wrap,
    "copy_foreground_down_without_erasing": _rival_copy_down,
}
WITNESS_RIVALS = {
    "top_row_translation": [
        "identity_no_shift",
        "clear_top_without_shift",
        "copy_foreground_down_without_erasing",
    ],
    "middle_row_translation": [
        "identity_no_shift",
        "clear_top_without_shift",
        "copy_foreground_down_without_erasing",
    ],
    "multirow_translation": [
        "identity_no_shift",
        "clear_top_without_shift",
        "copy_foreground_down_without_erasing",
    ],
    "bottom_row_is_dropped": list(SEMANTIC_RIVALS),
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "shift_down_with_wraparound": _rival_shift_down_wrap,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")

    profiles: set[str] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info, errors = _analyse(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        profile = info.get("row_profile")
        if profile is None:
            reasons.append(f"demo {index} is not a generated teaching profile")
        else:
            profiles.add(profile)
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output is not the one-row downward shift")

    missing = set(ROW_PROFILES) - profiles
    if missing:
        reasons.append(f"demonstrations miss row profiles: {sorted(missing)}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        _, query_errors = _analyse(query["input"])
        if query_errors:
            reasons.append(f"query malformed: {query_errors[0]}")

    return reasons


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    return ROW_PROFILES[sample_index % len(ROW_PROFILES)]


SCHEDULE_PROFILES = ROW_PROFILES
