"""Generator for easy_g06 — move every object cell one step toward a border marker.

The maroon (9) marker is a direction cue, not output content.  Its non-corner
border side selects one translation vector; every other non-zero cell moves by
exactly that vector and the marker disappears.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components

GENERATOR_ID = "e93047bc5081"
TASK_ID = "e93047bc5081"
VERSION = "3.0.0"
RULE_HASH = "604118ebde14"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "A single maroon(9) marker lies on one non-corner border cell. Its side "
    "selects up/down/left/right. Remove the marker and translate every other "
    "non-zero cell exactly one step toward that side, preserving all colors, "
    "shapes, and relative positions."
)

INVARIANTS = [
    "grid dimensions are 5..14 in both directions",
    "exactly one maroon(9) marker lies on a non-corner border cell",
    "one to three connected non-marker objects use distinct non-zero/non-9 colors",
    "every non-marker cell can move one step in the marker-selected direction",
    "ordinary lessons include all four directions and recurring multi-object counterexamples",
]

SIDES = ("top", "bottom", "left", "right")
SIDE_TO_DELTA = {
    "top": (-1, 0),
    "bottom": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "5..7 easy, 6..10 medium, 8..14 hard; 33% linked canonical schedule",
        "valid": "5..14",
        "doc": "Grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "5..8 easy, 6..11 medium, 8..14 hard; 33% linked canonical schedule",
        "valid": "5..14",
        "doc": "Grid width.",
    },
    "n_objs": {
        "type": "int",
        "default": "1..2 easy/medium, 1..3 hard; every four-sample lesson includes >=2",
        "valid": "1..3",
        "doc": "Number of connected non-marker colored objects.",
    },
    "marker_side": {
        "type": "str",
        "default": "sample_index cycles top,bottom,left,right",
        "valid": "top|bottom|left|right",
        "doc": "The border side containing the maroon direction marker.",
    },
}

# The four official inputs, reduced to task-relevant linked morphology.  Colors,
# exact cells, and marker coordinates may vary, but the tuple must stay intact.
_CANONICAL_SIGNATURES = frozenset(
    {
        (5, 6, 4, "top", 2, (1, 3)),
        (5, 5, 3, "bottom", 1, (3,)),
        (5, 6, 3, "left", 1, (3,)),
        (5, 6, 3, "right", 1, (3,)),
    }
)


def _banded_int(ctx, overrides, label, default_lo, default_hi, valid_lo, valid_hi):
    """Honor explicit boundaries across every difficulty band."""
    if overrides.get(label) is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _marker_side(grid) -> str | None:
    if not grid or not grid[0]:
        return None
    h, w = len(grid), len(grid[0])
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(markers) != 1:
        return None
    r, c = markers[0]
    if r == 0 and c not in (0, w - 1):
        return "top"
    if r == h - 1 and c not in (0, w - 1):
        return "bottom"
    if c == 0 and r not in (0, h - 1):
        return "left"
    if c == w - 1 and r not in (0, h - 1):
        return "right"
    return None


def _object_components(grid):
    return [comp for comp in components(grid) if comp["color"] != 9]


def _python_apply(grid):
    """Independent executable spelling of the selected Racket rule."""
    side = _marker_side(grid)
    if side is None:
        raise ValueError("grid does not contain one non-corner border marker")
    dr, dc = SIDE_TO_DELTA[side]
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 9):
                continue
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                raise ValueError("object cell would translate out of bounds")
            out[nr][nc] = value
    return out


def _profile_signature(grid):
    if not grid or not grid[0]:
        return None
    comps = _object_components(grid)
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
        _marker_side(grid),
        len(comps),
        tuple(sorted(len(comp["cells"]) for comp in comps)),
    )


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return [f"self_check: {reason}" for reason in reasons]
    signature = _profile_signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        return [f"linked canonical signature mismatch: {signature!r}"]
    return []


def observe_overrides(grid) -> dict[str, object]:
    """Recover every exact public axis from the returned grid itself."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_objs": len(_object_components(grid)) if grid and grid[0] else 0,
        "marker_side": _marker_side(grid),
    }


def _safe_region(h: int, w: int, side: str) -> list[tuple[int, int]]:
    """Interior cells at least two steps from the selected border.

    This makes every ordinary lesson refute the rival rule "slide until the
    border" while still matching every official input profile.
    """
    rows = range(1, h - 1)
    cols = range(1, w - 1)
    if side == "top":
        rows = range(2, h - 1)
    elif side == "bottom":
        rows = range(1, h - 2)
    elif side == "left":
        cols = range(2, w - 1)
    elif side == "right":
        cols = range(1, w - 2)
    return [(r, c) for r in rows for c in cols]


def _connected_growth(
    rng,
    region: set[tuple[int, int]],
    anchors: list[tuple[int, int]],
    sizes: list[int],
) -> list[set[tuple[int, int]]] | None:
    """Grow exact-size connected objects while preserving every anchor."""
    grown_shapes = [{anchor} for anchor in anchors]
    occupied = set(anchors)
    reserved = set(anchors)
    for index, target in enumerate(sizes):
        while len(grown_shapes[index]) < target:
            frontier = []
            for r, c in sorted(grown_shapes[index]):
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    cell = (r + dr, c + dc)
                    if (
                        cell in region
                        and cell not in occupied
                        and (cell not in reserved or cell == anchors[index])
                    ):
                        frontier.append(cell)
            if not frontier:
                return None
            cell = rng.choice(sorted(set(frontier)))
            grown_shapes[index].add(cell)
            occupied.add(cell)
    return grown_shapes


def _allocate_sizes(rng, n_objs: int, total_cells: int) -> list[int]:
    sizes = [1] * n_objs
    for _ in range(total_cells - n_objs):
        sizes[rng.randrange(n_objs)] += 1
    rng.shuffle(sizes)
    return sizes


def _place_objects(
    rng,
    h: int,
    w: int,
    side: str,
    sizes: list[int],
) -> list[set[tuple[int, int]]]:
    region_list = _safe_region(h, w, side)
    region = set(region_list)
    if sum(sizes) > len(region):
        raise ValueError(
            f"requested {sum(sizes)} object cells but only {len(region)} safe cells exist"
        )
    for _ in range(160):
        anchors = rng.sample(region_list, len(sizes))
        grown_shapes = _connected_growth(rng, region, anchors, sizes)
        if grown_shapes is None:
            continue
        # Keep each same-colored object connected and each color in one component.
        if all(len(cells) == target for cells, target in zip(grown_shapes, sizes)):
            return grown_shapes
    raise ValueError("could not place exact connected object layout")


def _choose_marker(rng, h: int, w: int, side: str, object_cells):
    if side in ("top", "bottom"):
        candidates = list(range(1, w - 1))
        # Prefer a marker column that is not shared by every object cell; this
        # refutes per-cell diagonal motion toward the marker coordinate.
        useful = [c for c in candidates if any(oc != c for _r, oc in object_cells)]
        c = rng.choice(useful or candidates)
        return (0 if side == "top" else h - 1, c)
    candidates = list(range(1, h - 1))
    useful = [r for r in candidates if any(orow != r for orow, _c in object_cells)]
    r = rng.choice(useful or candidates)
    return (r, 0 if side == "left" else w - 1)


def _canonical_sizes(side: str) -> tuple[int, int, list[int]]:
    if side == "top":
        return 5, 6, [3, 1]
    if side == "bottom":
        return 5, 5, [3]
    return 5, 6, [3]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")
    band = difficulty or "medium"
    scheduled_side = SIDES[sample_index % len(SIDES)]
    if overrides.get("marker_side") is not None:
        side = ctx.draw_choice("marker_side", SIDES)
    else:
        side = ctx.draw_choice("marker_side", (scheduled_side,))

    has_override = any(value is not None for value in overrides.values())
    canonical_slot = not has_override and sample_index % 3 == 0

    if canonical_slot:
        h0, w0, sizes = _canonical_sizes(side)
        h = ctx.draw_int("grid_h", h0, h0)
        w = ctx.draw_int("grid_w", w0, w0)
        n_objs = ctx.draw_int("n_objs", len(sizes), len(sizes))
    else:
        if band == "easy":
            h_lo, h_hi, w_lo, w_hi = 5, 7, 5, 8
            n_lo, n_hi, total_lo, total_hi = 1, 2, 3, 6
        elif band == "hard":
            h_lo, h_hi, w_lo, w_hi = 8, 14, 8, 14
            n_lo, n_hi, total_lo, total_hi = 1, 3, 6, 12
        else:
            h_lo, h_hi, w_lo, w_hi = 6, 10, 6, 11
            n_lo, n_hi, total_lo, total_hi = 1, 2, 4, 9

        h = _banded_int(ctx, overrides, "grid_h", h_lo, h_hi, 5, 14)
        w = _banded_int(ctx, overrides, "grid_w", w_lo, w_hi, 5, 14)
        if overrides.get("n_objs") is not None:
            n_objs = ctx.draw_int("n_objs", 1, 3)
        elif sample_index % 4 == 0:
            # Every consecutive four-demo lesson contains a multi-object case.
            n_objs = ctx.draw_int("n_objs", 2, min(3, n_hi))
        else:
            n_objs = ctx.draw_int("n_objs", n_lo, n_hi)

        capacity = len(_safe_region(h, w, side))
        total_lo = max(n_objs, min(total_lo, capacity))
        total_hi = max(total_lo, min(total_hi, capacity))
        total_cells = ctx.draw_int("total_object_cells", total_lo, total_hi)
        sizes = _allocate_sizes(rng, n_objs, total_cells)

    colors = ctx.draw_distinct_colors(
        "object_colors", n=n_objs, exclude={0, 9}
    )
    placed_shapes = _place_objects(rng, h, w, side, sizes)
    grid = full_grid(h, w, 0)
    for color, cells in zip(colors, placed_shapes):
        for r, c in cells:
            grid[r][c] = color
    all_object_cells = [cell for cells in placed_shapes for cell in cells]
    mr, mc = _choose_marker(rng, h, w, side, all_object_cells)
    grid[mr][mc] = 9
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed direction cues and any input the rule cannot shift."""
    del difficulty, meta
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]

    errors = []
    if not (5 <= h <= 14 and 5 <= w <= 14):
        errors.append(f"dims {h}x{w} outside 5..14")
    bad_values = sorted(
        {value for row in grid for value in row if not isinstance(value, int) or not 0 <= value <= 9},
        key=repr,
    )
    if bad_values:
        errors.append(f"grid contains invalid ARC values: {bad_values!r}")

    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(markers) != 1:
        errors.append(f"expected exactly one color-9 marker, found {len(markers)}")
    side = _marker_side(grid)
    if len(markers) == 1 and side is None:
        errors.append("color-9 marker must occupy one non-corner border cell")

    comps = _object_components(grid)
    if not (1 <= len(comps) <= 3):
        errors.append(f"expected 1-3 non-marker objects, found {len(comps)}")
    colors = [comp["color"] for comp in comps]
    if len(set(colors)) != len(colors):
        errors.append("each non-marker object must use a distinct color")
    if any(color in (0, 9) for color in colors):
        errors.append("non-marker objects may not use colors 0 or 9")

    object_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not object_cells:
        errors.append("expected at least one non-marker object cell")
    if side is not None:
        dr, dc = SIDE_TO_DELTA[side]
        for r, c in object_cells:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w):
                errors.append(
                    f"object cell {(r, c)} moves out of bounds toward {side}"
                )
                break
    return errors


def _shift_subset(grid, selected_cells: Iterable[tuple[int, int]]):
    side = _marker_side(grid)
    if side is None:
        return full_grid(len(grid), len(grid[0]), 0)
    selected = set(selected_cells)
    dr, dc = SIDE_TO_DELTA[side]
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 9) and (r, c) in selected:
                nr, nc = r + dr, c + dc
                if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]):
                    out[nr][nc] = value
    return out


def _rival_largest_only(grid):
    comps = _object_components(grid)
    if not comps:
        return full_grid(len(grid), len(grid[0]), 0)
    largest = max(comps, key=lambda comp: (len(comp["cells"]), -comp["bbox"][0], -comp["bbox"][1]))
    return _shift_subset(grid, largest["cells"])


def _rival_fixed_up(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 9) and r > 0:
                out[r - 1][c] = value
    return out


def _rival_until_border(grid):
    side = _marker_side(grid)
    if side is None:
        return full_grid(len(grid), len(grid[0]), 0)
    cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if side == "top":
        steps = min(r for r, _c, _v in cells)
    elif side == "bottom":
        steps = min(len(grid) - 1 - r for r, _c, _v in cells)
    elif side == "left":
        steps = min(c for _r, c, _v in cells)
    else:
        steps = min(len(grid[0]) - 1 - c for _r, c, _v in cells)
    dr, dc = SIDE_TO_DELTA[side]
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, c, value in cells:
        out[r + steps * dr][c + steps * dc] = value
    return out


def _rival_toward_marker_coordinate(grid):
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    out = full_grid(len(grid), len(grid[0]), 0)
    if len(markers) != 1:
        return out
    mr, mc = markers[0]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 9):
                continue
            dr = 0 if r == mr else (1 if mr > r else -1)
            dc = 0 if c == mc else (1 if mc > c else -1)
            nr, nc = r + dr, c + dc
            if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]):
                out[nr][nc] = value
    return out


def _witness_side(name):
    return lambda grid: _marker_side(grid) == name


def _witness_multi_object(grid):
    return len(_object_components(grid)) >= 2


def _witness_singleton_distractor(grid):
    sizes = sorted(len(comp["cells"]) for comp in _object_components(grid))
    return len(sizes) >= 2 and sizes[0] == 1 and sizes[-1] >= 3


def _witness_coordinate_misalignment(grid):
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(markers) != 1:
        return False
    mr, mc = markers[0]
    side = _marker_side(grid)
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if side in ("top", "bottom"):
        return any(c != mc for _r, c in cells)
    if side in ("left", "right"):
        return any(r != mr for r, _c in cells)
    return False


def _witness_more_than_one_step(grid):
    side = _marker_side(grid)
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not cells or side is None:
        return False
    if side == "top":
        return min(r for r, _c in cells) >= 2
    if side == "bottom":
        return max(r for r, _c in cells) <= len(grid) - 3
    if side == "left":
        return min(c for _r, c in cells) >= 2
    return max(c for _r, c in cells) <= len(grid[0]) - 3


SEMANTIC_WITNESSES = {
    "top_direction": _witness_side("top"),
    "bottom_direction": _witness_side("bottom"),
    "left_direction": _witness_side("left"),
    "right_direction": _witness_side("right"),
    "multiple_objects_move": _witness_multi_object,
    "singleton_plus_larger_object": _witness_singleton_distractor,
    "marker_coordinate_is_not_target": _witness_coordinate_misalignment,
    "one_step_not_slide_to_border": _witness_more_than_one_step,
}

SEMANTIC_RIVALS = {
    "largest_object_only": _rival_largest_only,
    "fixed_up_direction": _rival_fixed_up,
    "slide_until_border": _rival_until_border,
    "step_toward_marker_coordinate": _rival_toward_marker_coordinate,
}

WITNESS_RIVALS = {
    "top_direction": ["slide_until_border"],
    "bottom_direction": ["fixed_up_direction"],
    "left_direction": ["fixed_up_direction"],
    "right_direction": ["fixed_up_direction"],
    "multiple_objects_move": ["largest_object_only"],
    "singleton_plus_larger_object": ["largest_object_only"],
    "marker_coordinate_is_not_target": ["step_toward_marker_coordinate"],
    "one_step_not_slide_to_border": ["slide_until_border"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "largest_object_only": _rival_largest_only,
    "slide_until_border": _rival_until_border,
    "step_toward_marker_coordinate": _rival_toward_marker_coordinate,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Every four consecutive demonstrations pin direction and displacement."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons = []
    sides = set()
    demo_inputs = []
    for index, pair in enumerate(demos):
        grid = pair.get("input")
        output = pair.get("output")
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = _python_apply(grid)
        if output != expected:
            reasons.append(f"demo {index} output disagrees with one-step side translation")
        sides.add(_marker_side(grid))
        demo_inputs.append(grid)
    if sides != set(SIDES):
        reasons.append(f"demos cover marker sides {sorted(sides)!r}, not all four")
    if not any(_witness_multi_object(grid) for grid in demo_inputs):
        reasons.append("demos omit a case where every one of multiple objects moves")
    if not any(_python_apply(grid) != _rival_largest_only(grid) for grid in demo_inputs):
        reasons.append("largest-object-only rival survives every demo")
    if not any(_python_apply(grid) != _rival_until_border(grid) for grid in demo_inputs):
        reasons.append("slide-until-border rival survives every demo")
    if not any(
        _python_apply(grid) != _rival_toward_marker_coordinate(grid)
        for grid in demo_inputs
    ):
        reasons.append("marker-coordinate motion rival survives every demo")

    q_grid = query.get("input")
    q_output = query.get("output")
    q_errors = self_check(q_grid)
    if q_errors:
        reasons.append(f"query malformed: {q_errors[0]}")
    elif q_output != _python_apply(q_grid):
        reasons.append("query answer disagrees with one-step side translation")
    return reasons


def mutation_fixtures():
    """Task-semantic near misses that self_check must reject."""
    no_marker = full_grid(5, 6, 0)
    no_marker[2][2] = 4
    no_marker[2][3] = 4
    no_marker[3][2] = 4

    corner_marker = [row[:] for row in no_marker]
    corner_marker[0][0] = 9

    interior_marker = [row[:] for row in no_marker]
    interior_marker[1][1] = 9

    marker_only = full_grid(5, 6, 0)
    marker_only[0][2] = 9

    two_markers = [row[:] for row in no_marker]
    two_markers[0][2] = 9
    two_markers[4][3] = 9

    out_of_bounds = full_grid(5, 6, 0)
    out_of_bounds[0][2] = 9
    out_of_bounds[0][4] = 4

    return [
        ("missing_direction_marker", no_marker),
        ("corner_marker_ambiguous_side", corner_marker),
        ("interior_marker_no_side", interior_marker),
        ("marker_without_object", marker_only),
        ("two_direction_markers", two_markers),
        ("object_moves_out_of_bounds", out_of_bounds),
    ]
