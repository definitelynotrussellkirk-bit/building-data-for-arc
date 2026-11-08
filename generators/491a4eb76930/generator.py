"""Task-linked generator for ARC task 491a4eb76930 (source 692cd3b6).

Two disjoint 3x3 C-frames are made from color 2 around color-5 centers.
Each frame has one cardinal opening.  The Racket oracle extends each opening
one cell out, takes the rectangle bounded by those two exits, and paints the
lawful part of that rectangle color 4 while preserving both frames.  The
openings themselves also become color 4.

The openings are independent: parallel, perpendicular, mutually facing, and
mutually away relations are all part of the teaching distribution.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "491a4eb76930"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "c4ccdf332cee"

SUMMARY = (
    "On a zero background, place exactly two disjoint 3x3 C-frames. Each "
    "frame has seven color-2 cells around a color-5 center and one cardinal "
    "opening. Extend each opening one cell outward. The oracle paints color 4 "
    "through the lawful portion of the rectangle bounded by those two exit "
    "cells, excluding both 3x3 frame boxes and the half-strips behind either "
    "opening; it also paints the two opening cells color 4. The two openings "
    "may be parallel, perpendicular, facing, or pointing away."
)

INVARIANTS = [
    "the input palette is exactly {0, 2, 5}",
    "there are exactly two color-5 centers and fourteen color-2 frame cells",
    "each center owns one disjoint 3x3 C-frame with exactly one cardinal opening",
    "both one-cell-outward exits are in bounds",
    "the Racket transformation changes a nontrivial set of background/opening cells",
]

DIRECTIONS = ("up", "right", "down", "left")
RELATIONS = ("parallel", "perpendicular", "facing", "away")
VECTORS = {
    "up": (-1, 0),
    "right": (0, 1),
    "down": (1, 0),
    "left": (0, -1),
}
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}
PERPENDICULAR = {
    "up": ("left", "right"),
    "down": ("left", "right"),
    "left": ("up", "down"),
    "right": ("up", "down"),
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "keyed by difficulty with a 15x15 canonical-profile prior",
        "valid": "13..19",
    },
    "grid_w": {
        "type": "int",
        "default": "keyed by difficulty with a 15x15 canonical-profile prior",
        "valid": "13..19",
    },
    "opening_relation": {
        "type": "enum",
        "default": "four-way consecutive schedule",
        "valid": ["parallel", "perpendicular", "facing", "away"],
    },
}

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.98
_CANONICAL_PRIOR = 0.45
_BAND_RANGES = {
    "easy": ((13, 15), (13, 15)),
    "medium": ((14, 17), (14, 17)),
    "hard": ((16, 19), (16, 19)),
}
_MIN_CHANGED_FRAC = 0.10


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in _BAND_RANGES:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    return str(difficulty)


def _normalize_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    cleaned = {key: value for key, value in overrides.items() if value is not None}
    unknown = sorted(set(cleaned) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    return cleaned


def _draw_banded_int(ctx, overrides, label: str, lo: int, hi: int) -> int:
    if label in overrides:
        return int(ctx.draw_int(label, 13, 19))
    return int(ctx.draw_int(label, lo, hi))


def _draw_c(grid: list[list[int]], center: tuple[int, int], opening: str) -> None:
    cr, cc = center
    for row in range(cr - 1, cr + 2):
        for col in range(cc - 1, cc + 2):
            grid[row][col] = 5 if (row, col) == center else 2
    dr, dc = VECTORS[opening]
    grid[cr + dr][cc + dc] = 0


def _dot(vector: tuple[int, int], delta: tuple[int, int]) -> int:
    return vector[0] * delta[0] + vector[1] * delta[1]


def _infer_relation(
    first_center: tuple[int, int], first_direction: str,
    second_center: tuple[int, int], second_direction: str,
) -> str:
    if first_direction == second_direction:
        return "parallel"
    first_v = VECTORS[first_direction]
    second_v = VECTORS[second_direction]
    if _dot(first_v, second_v) == 0:
        return "perpendicular"
    delta = (
        second_center[0] - first_center[0],
        second_center[1] - first_center[1],
    )
    first_toward = _dot(first_v, delta)
    second_toward = _dot(second_v, (-delta[0], -delta[1]))
    if first_toward > 0 and second_toward > 0:
        return "facing"
    if first_toward < 0 and second_toward < 0:
        return "away"
    # With distinct rows/columns and opposite cardinal directions, the signs
    # are necessarily equal.  Keep this explicit for malformed external grids.
    return "opposed_mixed"


def _directions_for_relation(
    rng, relation: str,
    first_center: tuple[int, int], second_center: tuple[int, int],
) -> tuple[str, str]:
    if relation == "parallel":
        direction = rng.choice(DIRECTIONS)
        return direction, direction
    if relation == "perpendicular":
        first = rng.choice(DIRECTIONS)
        return first, rng.choice(PERPENDICULAR[first])

    use_horizontal = bool(rng.randrange(2))
    if use_horizontal:
        toward_first = "right" if first_center[1] < second_center[1] else "left"
    else:
        toward_first = "down" if first_center[0] < second_center[0] else "up"
    toward_second = OPPOSITE[toward_first]
    if relation == "facing":
        return toward_first, toward_second
    if relation == "away":
        return OPPOSITE[toward_first], OPPOSITE[toward_second]
    raise ValueError(f"unknown opening relation {relation!r}")


def _shape_facts(
    grid: list[list[int]], center: tuple[int, int]
) -> tuple[dict[str, Any] | None, list[str]]:
    h, w = len(grid), len(grid[0])
    cr, cc = center
    errors: list[str] = []
    if not (1 <= cr < h - 1 and 1 <= cc < w - 1):
        return None, [f"center {center} lacks a complete 3x3 neighborhood"]

    bbox = (cr - 1, cc - 1, cr + 1, cc + 1)
    non_twos = []
    frame_cells = set()
    for row in range(cr - 1, cr + 2):
        for col in range(cc - 1, cc + 2):
            if (row, col) == center:
                continue
            if grid[row][col] == 2:
                frame_cells.add((row, col))
            else:
                non_twos.append((row, col, grid[row][col]))
    if len(non_twos) != 1:
        errors.append(
            f"center {center} must have exactly one missing frame cell, found {len(non_twos)}"
        )
        return None, errors
    opening_r, opening_c, opening_value = non_twos[0]
    if opening_value != 0:
        errors.append(f"opening {(opening_r, opening_c)} must be background 0")
    dr, dc = opening_r - cr, opening_c - cc
    direction = next(
        (name for name, vector in VECTORS.items() if vector == (dr, dc)), None
    )
    if direction is None:
        errors.append(f"opening {(opening_r, opening_c)} must be cardinal")
        return None, errors
    exit_cell = (opening_r + dr, opening_c + dc)
    if not (0 <= exit_cell[0] < h and 0 <= exit_cell[1] < w):
        errors.append(f"exit {exit_cell} lies outside the grid")
    return {
        "center": center,
        "bbox": bbox,
        "opening": (opening_r, opening_c),
        "direction": direction,
        "exit": exit_cell,
        "frame_cells": frame_cells,
    }, errors


def _inside(box: tuple[int, int, int, int], row: int, col: int) -> bool:
    r1, c1, r2, c2 = box
    return r1 <= row <= r2 and c1 <= col <= c2


def _dead(shape: dict[str, Any], row: int, col: int) -> bool:
    r1, c1, r2, c2 = shape["bbox"]
    direction = shape["direction"]
    if direction == "right":
        return r1 <= row <= r2 and col < c1
    if direction == "left":
        return r1 <= row <= r2 and col > c2
    if direction == "up":
        return c1 <= col <= c2 and row > r2
    return c1 <= col <= c2 and row < r1


def _oracle_mirror(grid: list[list[int]], shapes: list[dict[str, Any]]) -> list[list[int]]:
    """Pure Python mirror of the pinned Racket oracle, for validation only."""
    out = [list(row) for row in grid]
    first, second = shapes
    r1 = min(first["exit"][0], second["exit"][0])
    r2 = max(first["exit"][0], second["exit"][0])
    c1 = min(first["exit"][1], second["exit"][1])
    c2 = max(first["exit"][1], second["exit"][1])
    for row in range(r1, r2 + 1):
        for col in range(c1, c2 + 1):
            if _inside(first["bbox"], row, col) or _inside(second["bbox"], row, col):
                continue
            if _dead(first, row, col) or _dead(second, row, col):
                continue
            out[row][col] = 4
    for shape in shapes:
        row, col = shape["opening"]
        out[row][col] = 4
    return out


def analyze_scene(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty row sequence"], "facts": None}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["rows must be nonempty sequences"], "facts": None}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "facts": None}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return {"errors": ["cells must be ARC color integers 0..9"], "facts": None}

    h, w = len(grid), width
    if not 13 <= h <= 19:
        errors.append(f"grid_h must be in 13..19, got {h}")
    if not 13 <= w <= 19:
        errors.append(f"grid_w must be in 13..19, got {w}")

    palette = {value for row in grid for value in row}
    if palette != {0, 2, 5}:
        errors.append(f"input palette must be exactly [0, 2, 5], got {sorted(palette)}")
    centers = sorted(
        (row, col)
        for row in range(h) for col in range(w)
        if grid[row][col] == 5
    )
    if len(centers) != 2:
        errors.append(f"expected exactly two color-5 centers, found {len(centers)}")
        return {"errors": errors, "facts": None}
    if sum(value == 2 for row in grid for value in row) != 14:
        errors.append("expected exactly fourteen color-2 frame cells")

    shapes: list[dict[str, Any]] = []
    for center in centers:
        shape, shape_errors = _shape_facts([list(row) for row in grid], center)
        errors.extend(shape_errors)
        if shape is not None:
            shapes.append(shape)
    if len(shapes) != 2:
        return {"errors": errors, "facts": None}

    boxes = []
    for shape in shapes:
        r1, c1, r2, c2 = shape["bbox"]
        boxes.append({(row, col) for row in range(r1, r2 + 1) for col in range(c1, c2 + 1)})
    if boxes[0] & boxes[1]:
        errors.append("the two 3x3 frame boxes must be disjoint")

    claimed_twos = shapes[0]["frame_cells"] | shapes[1]["frame_cells"]
    actual_twos = {
        (row, col)
        for row in range(h) for col in range(w)
        if grid[row][col] == 2
    }
    if claimed_twos != actual_twos:
        errors.append("every color-2 cell must belong to exactly one C-frame")

    if errors:
        return {"errors": errors, "facts": None}

    relation = _infer_relation(
        shapes[0]["center"], shapes[0]["direction"],
        shapes[1]["center"], shapes[1]["direction"],
    )
    if relation not in RELATIONS:
        errors.append(f"opening directions have unsupported relation {relation!r}")
        return {"errors": errors, "facts": None}

    output = _oracle_mirror([list(row) for row in grid], shapes)
    changed = [
        (row, col)
        for row in range(h) for col in range(w)
        if output[row][col] != grid[row][col]
    ]
    if len(changed) < 3:
        errors.append(f"oracle must change at least three cells, got {len(changed)}")

    facts = {
        "grid_h": h,
        "grid_w": w,
        "centers": centers,
        "shapes": shapes,
        "opening_relation": relation,
        "directions": tuple(shape["direction"] for shape in shapes),
        "output": output,
        "changed_cells": changed,
        "changed_count": len(changed),
        "changed_fraction": len(changed) / (h * w),
        "exit_row_span": abs(shapes[0]["exit"][0] - shapes[1]["exit"][0]),
        "exit_col_span": abs(shapes[0]["exit"][1] - shapes[1]["exit"][1]),
    }
    return {"errors": errors, "facts": facts}


def _draw_centers(rng, h: int, w: int) -> tuple[tuple[int, int], tuple[int, int]]:
    top_lo, top_hi = 2, max(2, h // 3)
    bottom_lo, bottom_hi = min(h - 3, max(top_hi + 4, (2 * h) // 3)), h - 3
    left_lo, left_hi = 2, max(2, w // 3)
    right_lo, right_hi = min(w - 3, max(left_hi + 4, (2 * w) // 3)), w - 3

    top = rng.randint(top_lo, top_hi)
    bottom = rng.randint(bottom_lo, bottom_hi)
    left = rng.randint(left_lo, left_hi)
    right = rng.randint(right_lo, right_hi)
    if rng.randrange(2):
        return (top, left), (bottom, right)
    return (top, right), (bottom, left)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = _normalize_overrides(overrides)
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    size_overridden = "grid_h" in overrides or "grid_w" in overrides
    canonical_profile = (
        not size_overridden
        and ctx.draw_rng(f"canonical_profile|{band}").random() < _CANONICAL_PRIOR
    )
    if canonical_profile:
        h = int(ctx.draw_int("grid_h", 15, 15))
        w = int(ctx.draw_int("grid_w", 15, 15))
    else:
        (h_lo, h_hi), (w_lo, w_hi) = _BAND_RANGES[band]
        h = _draw_banded_int(ctx, overrides, "grid_h", h_lo, h_hi)
        w = _draw_banded_int(ctx, overrides, "grid_w", w_lo, w_hi)

    if "opening_relation" in overrides:
        relation = str(ctx.draw_choice("opening_relation", RELATIONS))
    else:
        scheduled = RELATIONS[int(sample_index) % len(RELATIONS)]
        relation = str(ctx.draw_choice("opening_relation", (scheduled,)))

    for attempt in range(128):
        layout_rng = ctx.draw_rng(f"layout|{attempt}")
        first_center, second_center = _draw_centers(layout_rng, h, w)
        first_direction, second_direction = _directions_for_relation(
            layout_rng, relation, first_center, second_center
        )
        grid = full_grid(h, w, 0)
        _draw_c(grid, first_center, first_direction)
        _draw_c(grid, second_center, second_direction)
        analysis = analyze_scene(grid)
        if analysis["errors"]:
            continue
        facts = analysis["facts"]
        if facts["changed_fraction"] < _MIN_CHANGED_FRAC:
            continue
        if facts["exit_row_span"] < 2 or facts["exit_col_span"] < 2:
            continue
        if facts["opening_relation"] != relation:
            continue
        errors = self_check(
            grid,
            difficulty=difficulty,
            meta={"overrides": overrides},
        )
        if errors:
            raise AssertionError("constructed invalid C-frame scene: " + "; ".join(errors))
        return grid
    raise RuntimeError(
        f"failed to construct a lawful {h}x{w} {relation} C-frame scene"
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete two-C-frame teaching grammar, not just counts."""
    analysis = analyze_scene(grid)
    errors = list(analysis["errors"])
    if errors or analysis["facts"] is None:
        return errors
    facts = analysis["facts"]
    if facts["changed_fraction"] < _MIN_CHANGED_FRAC:
        errors.append(
            f"oracle changes only {facts['changed_fraction']:.1%}; need at least {_MIN_CHANGED_FRAC:.0%}"
        )
    requested = (meta or {}).get("overrides", {})
    for axis, expected in requested.items():
        observed = facts.get(axis)
        if observed != expected:
            errors.append(f"override {axis}={expected!r} observed as {observed!r}")
    return errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    analysis = analyze_scene(grid)
    if analysis["errors"] or analysis["facts"] is None:
        raise ValueError("cannot observe invalid scene: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {axis: facts[axis] for axis in AXES}


def strict_canonical_like(grid) -> list[str]:
    """Accept lawful task scenes with canonical colors, shapes, and rule strength."""
    analysis = analyze_scene(grid)
    if analysis["errors"] or analysis["facts"] is None:
        return list(analysis["errors"])
    facts = analysis["facts"]
    reasons = []
    if facts["changed_fraction"] < _MIN_CHANGED_FRAC:
        reasons.append("oracle transformation is too small to identify the corridor rule")
    if facts["exit_row_span"] < 2 or facts["exit_col_span"] < 2:
        reasons.append("the two exits must differ in both row and column")
    return reasons


def _witness_direction(direction: str) -> Callable[[Any], bool]:
    return lambda grid: (
        not analyze_scene(grid)["errors"]
        and direction in analyze_scene(grid)["facts"]["directions"]
    )


def _witness_relation(relation: str) -> Callable[[Any], bool]:
    return lambda grid: (
        not analyze_scene(grid)["errors"]
        and analyze_scene(grid)["facts"]["opening_relation"] == relation
    )


SEMANTIC_WITNESSES = {
    "opening_up": _witness_direction("up"),
    "opening_right": _witness_direction("right"),
    "opening_down": _witness_direction("down"),
    "opening_left": _witness_direction("left"),
    "relation_parallel": _witness_relation("parallel"),
    "relation_perpendicular": _witness_relation("perpendicular"),
    "relation_facing": _witness_relation("facing"),
    "relation_away": _witness_relation("away"),
    "two_dimensional_corridor": lambda grid: (
        not analyze_scene(grid)["errors"]
        and analyze_scene(grid)["facts"]["exit_row_span"] >= 4
        and analyze_scene(grid)["facts"]["exit_col_span"] >= 4
    ),
}


def _candidate_output(grid: list[list[int]], mode: str) -> list[list[int]]:
    analysis = analyze_scene(grid)
    if analysis["errors"] or analysis["facts"] is None:
        return [list(row) for row in grid]
    facts = analysis["facts"]
    shapes = facts["shapes"]
    if mode == "official":
        return deepcopy(facts["output"])
    if mode.startswith("relation_only:"):
        relation = mode.split(":", 1)[1]
        return deepcopy(facts["output"]) if facts["opening_relation"] == relation else [list(row) for row in grid]

    out = [list(row) for row in grid]
    if mode == "opening_rectangle":
        endpoints = [shape["opening"] for shape in shapes]
    elif mode == "center_rectangle":
        endpoints = [shape["center"] for shape in shapes]
    else:
        endpoints = [shape["exit"] for shape in shapes]
    r1, r2 = sorted((endpoints[0][0], endpoints[1][0]))
    c1, c2 = sorted((endpoints[0][1], endpoints[1][1]))
    for row in range(r1, r2 + 1):
        for col in range(c1, c2 + 1):
            if _inside(shapes[0]["bbox"], row, col) or _inside(shapes[1]["bbox"], row, col):
                continue
            if mode != "raw_exit_rectangle" and (
                _dead(shapes[0], row, col) or _dead(shapes[1], row, col)
            ):
                continue
            out[row][col] = 4
    for shape in shapes:
        row, col = shape["opening"]
        out[row][col] = 4
    return out


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a concrete corridor shortcut survives the demos."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        analysis = analyze_scene(pair.get("input"))
        label = "query" if index == len(demos) else f"demo {index}"
        if analysis["errors"] or analysis["facts"] is None:
            reasons.append(f"{label} input is outside the C-frame grammar")
            continue
        if pair.get("output") != analysis["facts"]["output"]:
            reasons.append(f"{label} output disagrees with the pinned corridor oracle")
    if reasons:
        return reasons

    candidates = [
        "opening_rectangle",
        "center_rectangle",
        "raw_exit_rectangle",
        *(f"relation_only:{relation}" for relation in RELATIONS),
    ]
    for candidate in candidates:
        survives = all(
            _candidate_output(pair["input"], candidate) == pair["output"]
            for pair in demos
        )
        if survives and _candidate_output(query["input"], candidate) != query["output"]:
            reasons.append(f"competing rule {candidate!r} survives every demonstration")
    return reasons


def mutation_fixtures():
    """Task-specific near-misses that self_check must reject."""
    base = generate(491, 17, difficulty="medium", opening_relation="perpendicular")
    analysis = analyze_scene(base)
    shapes = analysis["facts"]["shapes"]
    fixtures = []

    foreign = deepcopy(base)
    row, col = next(iter(shapes[0]["frame_cells"]))
    foreign[row][col] = 6
    fixtures.append(("foreign_color_replaces_frame_cell", foreign))

    missing_center = deepcopy(base)
    row, col = shapes[1]["center"]
    missing_center[row][col] = 0
    fixtures.append(("missing_second_center", missing_center))

    second_opening = deepcopy(base)
    row, col = next(iter(shapes[0]["frame_cells"]))
    second_opening[row][col] = 0
    fixtures.append(("two_openings_in_one_frame", second_opening))

    sealed = deepcopy(base)
    row, col = shapes[0]["opening"]
    sealed[row][col] = 2
    fixtures.append(("sealed_C_frame", sealed))

    stray = deepcopy(base)
    occupied = {
        cell for shape in shapes for cell in (
            shape["frame_cells"] | {shape["center"], shape["opening"]}
        )
    }
    row, col = next(
        (r, c)
        for r in range(len(stray)) for c in range(len(stray[0]))
        if (r, c) not in occupied and stray[r][c] == 0
    )
    stray[row][col] = 2
    fixtures.append(("stray_frame_color", stray))
    return fixtures
