"""Generate answer-identifying hole-count packing lessons.

The authoritative rule extracts every isolated nonzero object, crops it to its
bounding box, counts enclosed zero regions inside that crop, and packs the
crops left-to-right.  Objects are ordered by increasing hole count; equal-hole
objects are ordered by decreasing painted area.  The canonical Racket rule
uses color as a final deterministic tie-break, but ordinary lessons avoid
otherwise-identical hole/area keys because the written task does not need that
extra convention.

Ordinary sample indices alternate the two public semantic profiles:
``distinct_holes`` demonstrates 0 < 1 < 2 holes, while ``area_tie`` contains
two one-hole rings and demonstrates that the larger ring comes first.  Every
layout deliberately scrambles input reading order, so fixed-position and
reading-order packing shortcuts do not survive.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "73d82a9cacf6"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "1d1a8e3f7274"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.45

SUMMARY = (
    "Extract each isolated nonzero object and crop it to its bounding box. "
    "Count enclosed zero regions inside each crop, sort by increasing hole "
    "count and then by decreasing painted area, and horizontally pack the "
    "crops with one black column between them. Exact remaining ties use color "
    "as the canonical oracle's deterministic fallback."
)

INVARIANTS = [
    "background is black (0)",
    "exactly three isolated 4-connected objects with distinct colors",
    "ordinary lessons alternate the canonical hole profiles (0,1,2) and (0,1,1)",
    "the (0,1,1) profile contains 4x4 and 3x3 rings, proving larger-area-first",
    "input reading order is deliberately different from output sort order",
]

SCENE_PROFILES = ("distinct_holes", "area_tie")
CANVAS_PROFILES = ("10x16", "10x17", "11x18", "11x19", "12x18")
SCHEDULE_PROFILES = SCENE_PROFILES
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_PROFILE_SCHEDULE = SCENE_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "alternating sample-index schedule",
        "valid": "distinct_holes|area_tie",
    },
    "canvas_profile": {
        "type": "str",
        "default": "rng over canonical canvas sizes",
        "valid": "10x16|10x17|11x18|11x19|12x18",
    },
}

BACKGROUND = 0
COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)
_NEIGHBORS_4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NEIGHBORS_8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

# Reading-order slot permutations, expressed as semantic-role indexes placed
# into top-left / top-right / bottom-center slots. Identity is excluded.
_LAYOUT_PERMUTATIONS = (
    (0, 2, 1),
    (1, 0, 2),
    (1, 2, 0),
    (2, 0, 1),
    (2, 1, 0),
)

# Public linked signatures:
# (height, width, palette size including background,
#  sorted (hole_count, painted_area, bbox_h, bbox_w)).
_CANONICAL_SIGNATURES = {
    (10, 16, 4, ((0, 4, 2, 2), (1, 8, 3, 3), (2, 13, 3, 5))),
    (11, 18, 4, ((0, 4, 2, 2), (1, 8, 3, 3), (1, 12, 4, 4))),
    (12, 18, 4, ((0, 4, 2, 2), (1, 8, 3, 3), (2, 13, 3, 5))),
    (10, 17, 4, ((0, 4, 2, 2), (1, 8, 3, 3), (1, 12, 4, 4))),
    (11, 19, 4, ((0, 4, 2, 2), (1, 8, 3, 3), (2, 13, 3, 5))),
}

Grid = list[list[int]]
Cell = tuple[int, int]
ObjectFacts = dict[str, Any]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input grid."""
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = "medium" if difficulty is None else difficulty
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    if overrides.get("scene_profile") is None:
        scheduled = _PROFILE_SCHEDULE[int(sample_index) % len(_PROFILE_SCHEDULE)]
        scene_profile = ctx.draw_choice("scene_profile", (scheduled,))
    else:
        scene_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    canvas_profile = ctx.draw_choice("canvas_profile", CANVAS_PROFILES)
    height, width = _parse_canvas_profile(canvas_profile)

    rng = ctx.draw_rng(f"layout:{scene_profile}:{canvas_profile}:{band}")
    colors = _role_colors(rng)
    shapes = _profile_shapes(scene_profile, colors)
    layout_options = (
        tuple(
            permutation
            for permutation in _LAYOUT_PERMUTATIONS
            if permutation.index(2) < permutation.index(1)
        )
        if scene_profile == "area_tie"
        else _LAYOUT_PERMUTATIONS
    )
    permutation = layout_options[
        (int(sample_index) + rng.randrange(len(layout_options)))
        % len(layout_options)
    ]
    grid = _paint_in_slots(height, width, shapes, permutation)

    analysis = _analyze(grid)
    if analysis["errors"]:
        raise AssertionError("constructed invalid scene: " + "; ".join(analysis["errors"]))
    if analysis["facts"]["reading_order"] == analysis["facts"]["sorted_order"]:
        raise AssertionError("constructed scene failed reading-order conflict")

    errors = self_check(
        grid,
        difficulty=band,
        meta={
            "scene_profile": scene_profile,
            "canvas_profile": canvas_profile,
            "overrides": dict(overrides),
        },
    )
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    return grid


def schedule_profile(seed, sample_index, difficulty=None):
    """Declare the ordinary alternating lesson schedule."""
    del seed, difficulty
    return _PROFILE_SCHEDULE[int(sample_index) % len(_PROFILE_SCHEDULE)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the full lawful input grammar and reject structural impostors."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    facts = analysis["facts"]
    profile = _classify_profile(facts)
    if profile is None:
        errors.append(
            "scene must match distinct_holes (0,1,2) or area_tie (0,1,1 with 4x4 before 3x3 rings)"
        )
        return errors

    if facts["object_count"] != 3:
        errors.append(f"expected exactly 3 objects, found {facts['object_count']}")
    if facts["palette_size"] != 4:
        errors.append(
            f"expected background plus 3 distinct object colors, found palette size {facts['palette_size']}"
        )
    if facts["touching_object_pairs"]:
        errors.append("objects must be separated by at least one black cell")
    if facts["output"] == grid:
        errors.append("packing transformation must not be an identity")

    requested_scene = None
    requested_canvas = None
    if isinstance(meta, dict):
        requested_scene = meta.get("scene_profile")
        requested_canvas = meta.get("canvas_profile")
        if isinstance(meta.get("overrides"), dict):
            requested_scene = meta["overrides"].get(
                "scene_profile", requested_scene
            )
            requested_canvas = meta["overrides"].get(
                "canvas_profile", requested_canvas
            )
    observed = observe_overrides(grid)
    if requested_scene is not None and observed.get("scene_profile") != requested_scene:
        errors.append(
            f"scene_profile requested {requested_scene!r}, observed {observed.get('scene_profile')!r}"
        )
    if requested_canvas is not None and observed.get("canvas_profile") != requested_canvas:
        errors.append(
            f"canvas_profile requested {requested_canvas!r}, observed {observed.get('canvas_profile')!r}"
        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return reasons when a grid is outside the exact public joint manifold."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    signature = _linked_signature(analysis["facts"])
    if signature not in _CANONICAL_SIGNATURES:
        return [f"joint canonical signature not observed: {signature!r}"]
    return []


def canonical_profile_signature(grid):
    """Expose the strict linked signature for review tooling."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    return _linked_signature(analysis["facts"])


def observe_overrides(grid) -> dict[str, str]:
    """Recover every exact declared axis from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    facts = analysis["facts"]
    profile = _classify_profile(facts)
    if profile is None:
        return {}
    return {
        "scene_profile": profile,
        "canvas_profile": f"{facts['height']}x{facts['width']}",
    }


def semantic_signature(grid) -> dict[str, Any]:
    """Return linked task observables used by the strict semantic census."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "scene_profile": _classify_profile(facts),
        "canvas_profile": f"{facts['height']}x{facts['width']}",
        "hole_histogram": dict(Counter(obj["holes"] for obj in facts["objects"])),
        "areas_by_holes": {
            str(holes): tuple(
                sorted(
                    (obj["area"] for obj in facts["objects"] if obj["holes"] == holes),
                    reverse=True,
                )
            )
            for holes in sorted({obj["holes"] for obj in facts["objects"]})
        },
        "input_order": tuple(facts["reading_order"]),
        "packed_order": tuple(facts["sorted_order"]),
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python test mirror; the canonical Racket rule remains authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return deepcopy(analysis["facts"]["output"])


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that leave named shortcut programs query-relevant."""
    reasons: list[str] = []
    demo_profiles: set[str] = set()
    for index, pair in enumerate(demos):
        pair_errors, profile = _validate_pair(pair)
        reasons.extend(f"demo {index}: {error}" for error in pair_errors)
        if profile is not None:
            demo_profiles.add(profile)
    query_errors, query_profile = _validate_pair(query)
    reasons.extend(f"query: {error}" for error in query_errors)
    if reasons:
        return reasons

    required = set(SCENE_PROFILES)
    if demo_profiles != required:
        reasons.append(
            f"demos must contain profiles {sorted(required)}, found {sorted(demo_profiles)}"
        )
    if query_profile not in required:
        reasons.append(f"query profile {query_profile!r} is unsupported")

    for name, competitor in LESSON_COMPETITORS.items():
        matches_demos = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if not matches_demos:
            continue
        rival_query = competitor(query["input"])
        if rival_query != query["output"]:
            reasons.append(
                f"competitor {name!r} fits every demo but disagrees on the query"
            )
    return reasons


def _validate_pair(pair) -> tuple[list[str], str | None]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return ["pair must contain input and output grids"], None
    analysis = _analyze(pair["input"])
    if analysis["errors"]:
        return list(analysis["errors"]), None
    profile = _classify_profile(analysis["facts"])
    errors: list[str] = []
    if profile is None:
        errors.append("input is outside the teaching grammar")
    if pair["output"] != analysis["facts"]["output"]:
        errors.append("output does not equal hole-count packing")
    return errors, profile


def _witness_profile(name: str) -> Callable[[Grid], bool]:
    def predicate(grid) -> bool:
        return observe_overrides(grid).get("scene_profile") == name

    return predicate


def _witness_reading_order_conflict(grid) -> bool:
    analysis = _analyze(grid)
    return (
        not analysis["errors"]
        and analysis["facts"]["reading_order"] != analysis["facts"]["sorted_order"]
    )


def _witness_area_tie(grid) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"] or _classify_profile(analysis["facts"]) != "area_tie":
        return False
    return _rival_hole_only(grid) != analysis["facts"]["output"]


SEMANTIC_WITNESSES = {
    "distinct_hole_order": _witness_profile("distinct_holes"),
    "larger_area_tiebreak": _witness_area_tie,
    "reading_order_conflict": _witness_reading_order_conflict,
}


def _rival_hole_only(grid: Grid) -> Grid:
    return _pack_with_key(grid, lambda obj: (obj["holes"], obj["reading_rank"]))


def _rival_area_ascending(grid: Grid) -> Grid:
    return _pack_with_key(
        grid, lambda obj: (obj["holes"], obj["area"], obj["color"])
    )


def _rival_reading_order(grid: Grid) -> Grid:
    return _pack_with_key(grid, lambda obj: (obj["reading_rank"],))


def _rival_color_order(grid: Grid) -> Grid:
    return _pack_with_key(grid, lambda obj: (obj["color"],))


SEMANTIC_RIVALS = {
    "hole_count_only": _rival_hole_only,
    "area_ascending": _rival_area_ascending,
    "reading_order": _rival_reading_order,
}
WITNESS_RIVALS = {
    "distinct_hole_order": ["reading_order"],
    "larger_area_tiebreak": ["hole_count_only", "area_ascending"],
    "reading_order_conflict": ["reading_order"],
}
LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "color_order": _rival_color_order,
}
# None of the named rivals fits all five labeled canonical pairs.  They remain
# lesson competitors above, but the stricter canonical-fit declaration is empty.
CANONICAL_SHORTCUTS: dict[str, Callable[[Grid], Grid]] = {}


def _role_colors(rng) -> list[int]:
    """Assign distinct colors so color-order never equals semantic order."""
    palette = sorted(rng.sample(COLORS, 3))
    permutations = _LAYOUT_PERMUTATIONS
    assignment = permutations[rng.randrange(len(permutations))]
    return [palette[index] for index in assignment]


def _parse_canvas_profile(profile: str) -> tuple[int, int]:
    height, width = profile.split("x", 1)
    return int(height), int(width)


def _profile_shapes(profile: str, colors: list[int]) -> list[ObjectFacts]:
    if profile == "distinct_holes":
        return [
            _shape_solid_2x2(colors[0]),
            _shape_ring(3, 3, colors[1]),
            _shape_double_ring_3x5(colors[2]),
        ]
    if profile == "area_tie":
        return [
            _shape_solid_2x2(colors[0]),
            _shape_ring(4, 4, colors[1]),
            _shape_ring(3, 3, colors[2]),
        ]
    raise ValueError(f"unknown scene profile {profile!r}")


def _shape_solid_2x2(color: int) -> ObjectFacts:
    cells = tuple((row, col) for row in range(2) for col in range(2))
    return {"color": color, "cells": cells, "height": 2, "width": 2}


def _shape_ring(height: int, width: int, color: int) -> ObjectFacts:
    cells = tuple(
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    )
    return {"color": color, "cells": cells, "height": height, "width": width}


def _shape_double_ring_3x5(color: int) -> ObjectFacts:
    holes = {(1, 1), (1, 3)}
    cells = tuple(
        (row, col)
        for row in range(3)
        for col in range(5)
        if (row, col) not in holes
    )
    return {"color": color, "cells": cells, "height": 3, "width": 5}


def _paint_in_slots(
    height: int,
    width: int,
    shapes: list[ObjectFacts],
    permutation: tuple[int, int, int],
) -> Grid:
    grid = full_grid(height, width, BACKGROUND)
    for slot_index, role_index in enumerate(permutation):
        shape = shapes[role_index]
        shape_h = shape["height"]
        shape_w = shape["width"]
        if slot_index == 0:
            top, left = 0, 0
        elif slot_index == 1:
            top, left = 0, width - shape_w
        else:
            top, left = height - shape_h, (width - shape_w) // 2
        for row, col in shape["cells"]:
            target_row, target_col = top + row, left + col
            if grid[target_row][target_col] != BACKGROUND:
                raise AssertionError("slot construction produced an overlap")
            grid[target_row][target_col] = shape["color"]
    return grid


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _basic_grid_errors(grid)
    if errors:
        return {"errors": errors, "facts": None}
    height = len(grid)
    width = len(grid[0])
    components = _objects(grid)
    if not components:
        return {"errors": ["grid contains no nonzero objects"], "facts": None}

    colors = [obj["color"] for obj in components]
    if len(set(colors)) != len(colors):
        errors.append("every disconnected object must use a distinct color")
    touching_pairs = _touching_object_pairs(components)
    reading_order = tuple(obj["reading_rank"] for obj in components)
    sorted_objects = sorted(
        components,
        key=lambda obj: (obj["holes"], -obj["area"], obj["color"]),
    )
    sorted_order = tuple(obj["reading_rank"] for obj in sorted_objects)
    output = _pack_objects(sorted_objects)
    facts = {
        "height": height,
        "width": width,
        "palette_size": len({value for row in grid for value in row}),
        "object_count": len(components),
        "objects": tuple(components),
        "touching_object_pairs": touching_pairs,
        "reading_order": reading_order,
        "sorted_order": sorted_order,
        "output": output,
    }
    return {"errors": errors, "facts": facts}


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list or tuple of rows"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["every grid row must be a list or tuple"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or not widths or 0 in widths:
        return ["grid must be rectangular and nonempty"]
    height = len(grid)
    width = next(iter(widths))
    errors: list[str] = []
    if (height, width) not in {
        _parse_canvas_profile(profile) for profile in CANVAS_PROFILES
    }:
        errors.append(f"canvas must use a canonical size, found {height}x{width}")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid cells must be integer ARC colors 0..9")
    if not any(value == BACKGROUND for row in grid for value in row):
        errors.append("black background color 0 must be present")
    return errors


def _objects(grid: Grid) -> list[ObjectFacts]:
    height = len(grid)
    width = len(grid[0])
    seen: set[Cell] = set()
    components: list[ObjectFacts] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == BACKGROUND or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for delta_row, delta_col in _NEIGHBORS_4:
                    next_row = current[0] + delta_row
                    next_col = current[1] + delta_col
                    next_cell = (next_row, next_col)
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and next_cell not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add(next_cell)
                        stack.append(next_cell)
            ordered = tuple(sorted(cells))
            top = min(r for r, _ in ordered)
            bottom = max(r for r, _ in ordered)
            left = min(c for _, c in ordered)
            right = max(c for _, c in ordered)
            crop = [
                [grid[r][c] for c in range(left, right + 1)]
                for r in range(top, bottom + 1)
            ]
            components.append(
                {
                    "color": color,
                    "cells": ordered,
                    "cell_set": frozenset(ordered),
                    "area": len(ordered),
                    "top": top,
                    "left": left,
                    "bottom": bottom,
                    "right": right,
                    "height": bottom - top + 1,
                    "width": right - left + 1,
                    "crop": crop,
                    "holes": _hole_count(crop),
                }
            )
    components.sort(key=lambda obj: (obj["top"], obj["left"]))
    for rank, obj in enumerate(components):
        obj["reading_rank"] = rank
    return components


def _hole_count(crop: Grid) -> int:
    height = len(crop)
    width = len(crop[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if crop[row][col] == BACKGROUND
    }
    holes = 0
    while remaining:
        start = next(iter(remaining))
        stack = [start]
        remaining.remove(start)
        touches_border = False
        while stack:
            row, col = stack.pop()
            if row in (0, height - 1) or col in (0, width - 1):
                touches_border = True
            for delta_row, delta_col in _NEIGHBORS_4:
                nxt = (row + delta_row, col + delta_col)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
        if not touches_border:
            holes += 1
    return holes


def _touching_object_pairs(components: list[ObjectFacts]) -> tuple[tuple[int, int], ...]:
    touching: list[tuple[int, int]] = []
    for first_index, first in enumerate(components):
        for second_index in range(first_index + 1, len(components)):
            second_cells = components[second_index]["cell_set"]
            if any(
                (row + delta_row, col + delta_col) in second_cells
                for row, col in first["cells"]
                for delta_row, delta_col in _NEIGHBORS_8
            ):
                touching.append((first_index, second_index))
    return tuple(touching)


def _pack_objects(components: list[ObjectFacts]) -> Grid:
    out_height = max(obj["height"] for obj in components)
    out_width = sum(obj["width"] for obj in components) + len(components) - 1
    output = full_grid(out_height, out_width, BACKGROUND)
    left = 0
    for obj in components:
        crop = obj["crop"]
        for row in range(len(crop)):
            for col in range(len(crop[0])):
                if crop[row][col] != BACKGROUND:
                    output[row][left + col] = crop[row][col]
        left += len(crop[0]) + 1
    return output


def _pack_with_key(grid: Grid, key) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _pack_objects(sorted(analysis["facts"]["objects"], key=key))


def _classify_profile(facts: dict[str, Any]) -> str | None:
    if facts["object_count"] != 3:
        return None
    rows = tuple(
        sorted(
            (obj["holes"], obj["area"], obj["height"], obj["width"])
            for obj in facts["objects"]
        )
    )
    if rows == ((0, 4, 2, 2), (1, 8, 3, 3), (2, 13, 3, 5)):
        return "distinct_holes"
    if rows == ((0, 4, 2, 2), (1, 8, 3, 3), (1, 12, 4, 4)):
        return "area_tie"
    return None


def _linked_signature(facts: dict[str, Any]) -> tuple[Any, ...]:
    return (
        facts["height"],
        facts["width"],
        facts["palette_size"],
        tuple(
            sorted(
                (obj["holes"], obj["area"], obj["height"], obj["width"])
                for obj in facts["objects"]
            )
        ),
    )
