"""Generator for c6fa0b0b24da: replace sparse cells by their solid bbox.

Lawful inputs contain two to seven cells of one nonzero color.  Their bounding
box spans at least three rows and columns but never covers the entire canvas.
The output is a fresh background grid with that complete bounding rectangle
filled in the input color.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c6fa0b0b24da"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "b0af10c78fff"

SUMMARY = (
    "Scatter two to seven cells of one nonzero color so their bounding box "
    "spans at least 3x3 without covering the whole canvas. Replace the sparse "
    "input by a solid rectangle filling that bounding box in the same color."
)

EXAMPLES_NEEDED = 4
EXPECTED_OUTPUT_CODOMAIN = 500_000
OUTPUT_CODOMAIN_BY_DIFFICULTY = {
    "easy": 100_000,
    "medium": 300_000,
    "hard": 500_000,
    None: 300_000,
}

# Disjoint palettes make the palette axis independently observable from a grid.
PALETTES = {
    "default": (1, 9),
    "warm": (2, 4, 6),
    "cool": (5, 8),
    "rainbow": (3, 7),
}
PALETTE_KINDS = tuple(PALETTES)
PALETTE_WITNESSES = {name: colors[0] for name, colors in PALETTES.items()}
DEGENERATE_TEXTURES = ("only_one_cell", "no_cells", "cells_aligned")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h": {
        "type": "int",
        "default": "6-8 easy / 8-12 medium / 11-16 hard",
        "valid": "6..16",
    },
    "grid_w": {
        "type": "int",
        "default": "7-9 easy / 10-13 medium / 12-18 hard",
        "valid": "7..18",
    },
    "palette_kind": {
        "type": "str",
        "default": "keyed draw",
        "valid": "|".join(PALETTE_KINDS),
    },
    "color": {
        "type": "int",
        "default": "keyed draw inside palette_kind",
        "valid": "1..9 (must belong to selected palette_kind)",
    },
    "num_cells": {
        "type": "int",
        "default": "2-3 easy / 2-5 medium / 4-7 hard",
        "valid": "2..7",
    },
    "texture": {
        "type": "str",
        "default": "optional alias for palette_kind",
        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
    },
}

INVARIANTS = [
    "the grid is rectangular, at most 30x30, and uses background 0",
    "all foreground cells have one exact nonzero ARC color",
    "two to seven foreground cells are present in ordinary generation",
    "the foreground bbox spans at least three rows and three columns",
    "the bbox is not the entire canvas, so the output retains background",
    "the output is a fresh solid bbox rectangle in the input color",
]

_ALLOWED_OVERRIDES = set(AXES)
_DIFFICULTIES = {None, "easy", "medium", "hard"}


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise TypeError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(sample_index, "sample_index", 0, 2**63 - 1)
    if difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "color", "num_cells"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise TypeError(f"{name} override must be an exact integer")
    if "palette_kind" in overrides and overrides["palette_kind"] is not None:
        if type(overrides["palette_kind"]) is not str:
            raise TypeError("palette_kind override must be a string")
        if overrides["palette_kind"] not in PALETTE_KINDS:
            raise ValueError(f"palette_kind must be one of {PALETTE_KINDS}")
    if "texture" in overrides and overrides["texture"] is not None:
        if type(overrides["texture"]) is not str:
            raise TypeError("texture override must be a string")
        if overrides["texture"] not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
            raise ValueError("unsupported texture override")


def _palette_for_color(color: int) -> str:
    matches = [name for name, colors in PALETTES.items() if color in colors]
    if len(matches) != 1:
        raise ValueError(f"color {color} does not identify one palette")
    return matches[0]


def _effective_overrides(overrides: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    values = dict(overrides)
    texture = values.pop("texture", None)
    if texture in DEGENERATE_TEXTURES:
        return values, texture
    if texture in PALETTE_KINDS:
        if values.get("palette_kind") not in (None, texture):
            raise ValueError("texture and palette_kind request different palettes")
        values["palette_kind"] = texture
    if values.get("color") is not None:
        color = _exact_int(values["color"], "color", 1, 9)
        implied = _palette_for_color(color)
        if values.get("palette_kind") not in (None, implied):
            raise ValueError("color does not belong to selected palette_kind")
        values["palette_kind"] = implied
    return values, None


def _difficulty_ranges(difficulty: str | None) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (6, 8), (7, 9), (2, 3)
    if difficulty == "hard":
        return (11, 16), (12, 18), (4, 7)
    return (8, 12), (10, 13), (2, 5)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, fresh lawful input grid."""
    _validate_call(seed, sample_index, difficulty, overrides)
    effective, degenerate = _effective_overrides(overrides)
    if degenerate is not None:
        return _draw_from_degenerate(degenerate)

    (h_lo, h_hi), (w_lo, w_hi), (n_lo, n_hi) = _difficulty_ranges(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int_strict("grid_h", h_lo, h_hi)
    width = ctx.draw_int_strict("grid_w", w_lo, w_hi)
    palette = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    color = ctx.draw_choice("color", PALETTES[palette])
    count = ctx.draw_int_strict("num_cells", n_lo, n_hi)

    rng = ctx.draw_rng("layout")
    row_span = rng.randint(3, height)
    col_span = rng.randint(3, width)
    if row_span == height and col_span == width:
        if height > 3 and rng.random() < 0.5:
            row_span -= 1
        elif width > 3:
            col_span -= 1
        else:  # unreachable for supported dimensions, retained as a loud guard
            raise RuntimeError("cannot retain a canvas margin")
    top = rng.randint(0, height - row_span)
    left = rng.randint(0, width - col_span)
    bottom = top + row_span - 1
    right = left + col_span - 1

    grid = full_grid(height, width, 0)
    points = {(top, left), (bottom, right)}
    candidates = [
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if (row, col) not in points
    ]
    rng.shuffle(candidates)
    points.update(candidates[: count - 2])
    for row, col in points:
        grid[row][col] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"internal generation defect: {errors}")
    return grid


def _coerce_grid(grid: Any) -> tuple[list[list[int]], list[str]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return [], ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return [], ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return [], ["grid dimensions must not exceed 30"]
    out: list[list[int]] = []
    for row in grid:
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            return [], ["grid values must be exact integer ARC colors 0..9"]
        out.append(list(row))
    return out, []


def _scene_facts(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    value, errors = _coerce_grid(grid)
    if errors:
        return None, errors
    cells = [(r, c, value[r][c]) for r in range(len(value)) for c in range(len(value[0])) if value[r][c]]
    if not cells:
        return None, ["no nonzero cells found"]
    colors = {v for _r, _c, v in cells}
    if len(colors) != 1:
        return None, ["foreground must use exactly one nonzero color"]
    rows = [r for r, _c, _v in cells]
    cols = [c for _r, c, _v in cells]
    top, bottom, left, right = min(rows), max(rows), min(cols), max(cols)
    return {
        "grid": value,
        "height": len(value),
        "width": len(value[0]),
        "color": next(iter(colors)),
        "cells": [(r, c) for r, c, _v in cells],
        "count": len(cells),
        "bbox": (top, bottom, left, right),
        "row_span": bottom - top + 1,
        "col_span": right - left + 1,
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Strict structural check for the canonical family."""
    facts, errors = _scene_facts(grid)
    if errors:
        return errors
    assert facts is not None
    if facts["count"] < 2:
        errors.append("need at least two foreground cells")
    if facts["row_span"] < 3:
        errors.append("bbox row span must be at least 3")
    if facts["col_span"] < 3:
        errors.append("bbox column span must be at least 3")
    if facts["row_span"] == facts["height"] and facts["col_span"] == facts["width"]:
        errors.append("bbox must not cover the whole canvas")
    if meta and isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        observed = observe_overrides(grid)
        for key, expected in meta["overrides"].items():
            if key == "texture" and expected in PALETTE_KINDS:
                key = "palette_kind"
            if key in observed and observed[key] != expected:
                errors.append(f"override {key} not observable")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    facts, errors = _scene_facts(grid)
    if errors:
        return {}
    assert facts is not None
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "palette_kind": _palette_for_color(facts["color"]),
        "color": facts["color"],
        "num_cells": facts["count"],
    }


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the exact canonical Racket rule."""
    facts, errors = _scene_facts(grid)
    if errors:
        raise ValueError("; ".join(errors))
    assert facts is not None
    top, bottom, left, right = facts["bbox"]
    output = full_grid(facts["height"], facts["width"], 0)
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            output[row][col] = facts["color"]
    return output


def _draw_from_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(8, 9, 0)
    if name == "only_one_cell":
        grid[3][4] = 5
    elif name == "cells_aligned":
        grid[3][1] = 4
        grid[3][7] = 4
    elif name != "no_cells":
        raise ValueError(f"unknown degenerate texture {name}")
    return grid
