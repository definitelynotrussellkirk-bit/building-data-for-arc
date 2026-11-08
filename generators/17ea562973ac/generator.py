"""Generator for ARC task 17ea562973ac (Draw the Missing Box).

A lawful input contains two to eight cells of one nonzero color on a zero
background.  Their bounding box spans at least four rows and four columns.  The
output is a fresh zero grid with the bounding-box outline painted in that color.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "17ea562973ac"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "22bfb52d3f48"
SUMMARY = (
    "On a zero background, find all 2..8 cells of the single nonzero color. "
    "Compute their minimal bounding rectangle and return a fresh grid of the "
    "same size containing only that rectangle's one-cell outline in the same "
    "color. Interior source markers are cleared."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the grid is 6..12 rows by 7..14 columns",
    "there are exactly 2..8 nonzero cells, all in one color from 2..9",
    "the marker bounding box spans at least four rows and four columns",
    "the output uses a fresh zero grid and paints only the bounding-box border",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical/generalized size",
        "valid": "6..12",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical/generalized size",
        "valid": "7..14",
    },
    "color": {
        "type": "int",
        "default": "scheduled 2..9",
        "valid": "2..9",
    },
    "num_cells": {
        "type": "int",
        "default": "scheduled 2..8",
        "valid": "2..8",
    },
}

SCHEDULE_PROFILES = (
    "two_diagonal_tl_br",
    "interior_three",
    "two_diagonal_tr_bl",
    "distributed_interior",
)

# The first five exact dimensions are the five canonical input profiles.  The
# remaining profiles broaden scale while keeping a 50% canonical-scale prior.
_SIZE_PROFILES = (
    (7, 8),
    (8, 8),
    (6, 10),
    (9, 7),
    (8, 9),
    (10, 11),
    (11, 13),
    (12, 14),
    (6, 14),
    (12, 7),
)
_COLOR_SCHEDULE = (3, 6, 4, 2, 5, 7, 8, 9)
_BAND_OFFSETS = {"easy": 0, "medium": 2, "hard": 5}


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["rows must be non-empty sequences"]
    width = len(grid[0])
    converted: list[list[int]] = []
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            return None, ["grid must be rectangular"]
        clean: list[int] = []
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return None, ["cells must be integer ARC colors in 0..9"]
            clean.append(value)
        converted.append(clean)
    return converted, []


def _analyze(grid: Any) -> dict[str, Any]:
    converted, errors = _coerce_grid(grid)
    facts: dict[str, Any] = {"errors": errors}
    if converted is None:
        return facts

    h, w = len(converted), len(converted[0])
    facts.update({"grid": converted, "grid_h": h, "grid_w": w})
    if not 6 <= h <= 12:
        errors.append("grid height must be in 6..12")
    if not 7 <= w <= 14:
        errors.append("grid width must be in 7..14")

    cells = [
        (r, c, converted[r][c])
        for r in range(h)
        for c in range(w)
        if converted[r][c] != 0
    ]
    colors = {value for _, _, value in cells}
    if not 2 <= len(cells) <= 8:
        errors.append(f"expected 2..8 nonzero cells, got {len(cells)}")
    if len(colors) != 1:
        errors.append("all nonzero cells must share exactly one color")
    elif not 2 <= next(iter(colors)) <= 9:
        errors.append("the marker color must be in 2..9")

    if not cells:
        return facts
    rows = [r for r, _, _ in cells]
    cols = [c for _, c, _ in cells]
    bbox = (min(rows), min(cols), max(rows), max(cols))
    r1, c1, r2, c2 = bbox
    if r2 - r1 < 3 or c2 - c1 < 3:
        errors.append("marker bounding box must span at least four rows and four columns")

    facts.update(
        {
            "cells": tuple((r, c) for r, c, _ in cells),
            "color": next(iter(colors)) if len(colors) == 1 else None,
            "num_cells": len(cells),
            "bbox": bbox,
            "has_interior_marker": any(
                r1 < r < r2 and c1 < c < c2 for r, c, _ in cells
            ),
        }
    )
    if len(cells) >= 2:
        first = cells[:2]
        facts["first_two_bbox"] = (
            min(first[0][0], first[1][0]),
            min(first[0][1], first[1][1]),
            max(first[0][0], first[1][0]),
            max(first[0][1], first[1][1]),
        )
    else:
        facts["first_two_bbox"] = None
    return facts


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Return exact task-grammar violations without mutating ``grid``."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid: Any) -> list[str]:
    """Generated scenes intentionally remain inside the canonical rule family."""
    return self_check(grid)


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every public axis exactly from the emitted pixels."""
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "color": info["color"],
        "num_cells": info["num_cells"],
    }


def _frame_output(
    h: int,
    w: int,
    bbox: tuple[int, int, int, int],
    color: int,
) -> list[list[int]]:
    output = full_grid(h, w, 0)
    r1, c1, r2, c2 = bbox
    for c in range(c1, c2 + 1):
        output[r1][c] = color
        output[r2][c] = color
    for r in range(r1 + 1, r2):
        output[r][c1] = color
        output[r][c2] = color
    return output


def rule_mirror(grid: Any) -> list[list[int]]:
    """Independent-of-Racket diagnostic mirror of the selected rule."""
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return _frame_output(
        info["grid_h"], info["grid_w"], info["bbox"], info["color"]
    )


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if type(difficulty) is str and difficulty in _BAND_OFFSETS:
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _draw_scheduled_int(ctx: Any, label: str, scheduled: int, lo: int, hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, scheduled, scheduled)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    del seed
    _band(difficulty)
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_num_cells(sample_index: int) -> int:
    profile = int(sample_index) % 4
    if profile in (0, 2):
        return 2
    if profile == 1:
        return 3
    return 4 + ((int(sample_index) // 4) % 5)


def _base_cells(
    profile: int,
    num_cells: int,
    bbox: tuple[int, int, int, int],
) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = bbox
    tl, tr, bl, br = (r1, c1), (r1, c2), (r2, c1), (r2, c2)
    if num_cells == 2:
        return {tl, br} if profile in (0, 1) else {tr, bl}
    if profile == 1:
        return {tl, (r1 + 1, c1 + 1), br}
    if profile == 3:
        if num_cells == 3:
            return {tl, (r1 + 1, c1 + 1), br}
        return {
            (r1, c1 + 1),
            (r1 + 1, c1),
            (r1 + 1, c1 + 1),
            br,
        }
    if profile == 2:
        return {tr, bl, tl}
    return {tl, br, tr}


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    band = _band(difficulty)
    index = int(sample_index)
    size_index = (index + _BAND_OFFSETS[band]) % len(_SIZE_PROFILES)
    scheduled_h, scheduled_w = _SIZE_PROFILES[size_index]
    scheduled_color = _COLOR_SCHEDULE[(index + _BAND_OFFSETS[band]) % len(_COLOR_SCHEDULE)]
    scheduled_count = _scheduled_num_cells(index)

    ctx = gen_ctx(
        seed=seed,
        sample_index=index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    h = _draw_scheduled_int(ctx, "grid_h", scheduled_h, 6, 12)
    w = _draw_scheduled_int(ctx, "grid_w", scheduled_w, 7, 14)
    color = _draw_scheduled_int(ctx, "color", scheduled_color, 2, 9)
    num_cells = _draw_scheduled_int(ctx, "num_cells", scheduled_count, 2, 8)

    rng = ctx.draw_rng("layout")
    bbox_h = rng.randint(4, h)
    bbox_w = rng.randint(4, w)
    r1 = rng.randint(0, h - bbox_h)
    c1 = rng.randint(0, w - bbox_w)
    bbox = (r1, c1, r1 + bbox_h - 1, c1 + bbox_w - 1)
    profile = index % 4
    cells = _base_cells(profile, num_cells, bbox)

    r2, c2 = bbox[2], bbox[3]
    candidates = [
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if (r, c) not in cells
    ]
    rng.shuffle(candidates)
    for cell in candidates:
        if len(cells) >= num_cells:
            break
        cells.add(cell)
    if len(cells) != num_cells:
        raise AssertionError(f"could not place {num_cells} distinct markers")

    grid = full_grid(h, w, 0)
    for r, c in cells:
        grid[r][c] = color
    errors = self_check(grid)
    if errors:
        raise AssertionError("generator emitted invalid scene: " + "; ".join(errors))
    return grid


# ---------------------------------------------------------------------------
# Finite semantic rivals and witnesses.
# ---------------------------------------------------------------------------


def _valid_info(grid: Any) -> dict[str, Any]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return info


def _requires_three_markers(grid: Any) -> list[list[int]]:
    info = _valid_info(grid)
    if info["num_cells"] < 3:
        return deepcopy(info["grid"])
    return rule_mirror(grid)


def _retain_original_markers(grid: Any) -> list[list[int]]:
    info = _valid_info(grid)
    output = deepcopy(info["grid"])
    frame = rule_mirror(grid)
    for r, row in enumerate(frame):
        for c, value in enumerate(row):
            if value:
                output[r][c] = value
    return output


def _first_two_markers_only(grid: Any) -> list[list[int]]:
    info = _valid_info(grid)
    return _frame_output(
        info["grid_h"],
        info["grid_w"],
        info["first_two_bbox"],
        info["color"],
    )


def _safe_witness(grid: Any, key: str) -> bool:
    info = _analyze(grid)
    if info["errors"]:
        return False
    if key == "two_markers":
        return info["num_cells"] == 2
    if key == "interior_marker":
        return bool(info["has_interior_marker"])
    if key == "first_two_incomplete":
        return info["first_two_bbox"] != info["bbox"]
    return False


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "requires_three_markers": _requires_three_markers,
    "retain_original_markers": _retain_original_markers,
    "first_two_markers_only": _first_two_markers_only,
}
CANONICAL_SHORTCUTS = {
    "requires_three_markers": _requires_three_markers,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "two_marker_domain": lambda grid: _safe_witness(grid, "two_markers"),
    "interior_marker_is_cleared": lambda grid: _safe_witness(grid, "interior_marker"),
    "all_markers_define_bbox": lambda grid: _safe_witness(grid, "first_two_incomplete"),
}
WITNESS_RIVALS = {
    "two_marker_domain": ["requires_three_markers"],
    "interior_marker_is_cleared": ["retain_original_markers"],
    "all_markers_define_bbox": ["first_two_markers_only"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Reject a lesson when a declared wrong rule survives all demonstrations."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo:
            reasons.append(f"demo {index}: malformed episode")
            continue
        try:
            truth = rule_mirror(demo["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"demo {index}: input outside rule domain: {exc}")
            continue
        if demo.get("output") != truth:
            reasons.append(f"demo {index}: output disagrees with the bounding-box rule")
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query: malformed episode")
    else:
        try:
            query_truth = rule_mirror(query["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"query: input outside rule domain: {exc}")
            query_truth = None
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != query_truth:
                reasons.append(
                    f"competing rule {name!r} fits every demo but changes the query"
                )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Named invalid grids used by task-local and shared defect probes."""
    blank = full_grid(8, 9, 0)
    aligned = full_grid(8, 9, 0)
    aligned[2][1] = aligned[2][7] = 5
    mixed = generate(81, 1, grid_h=8, grid_w=9, color=5, num_cells=3)
    for r, row in enumerate(mixed):
        for c, value in enumerate(row):
            if value:
                mixed[r][c] = 7
                break
        else:
            continue
        break
    # Add a second color at a previously empty position.
    mixed[0][0] = 5 if mixed[0][0] == 0 else 6
    dense = full_grid(8, 9, 0)
    for r, c in ((1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (5, 6), (5, 7), (6, 7)):
        dense[r][c] = 4
    return [
        ("blank", blank),
        ("aligned", aligned),
        ("mixed_colors", mixed),
        ("too_many_markers", dense),
    ]
