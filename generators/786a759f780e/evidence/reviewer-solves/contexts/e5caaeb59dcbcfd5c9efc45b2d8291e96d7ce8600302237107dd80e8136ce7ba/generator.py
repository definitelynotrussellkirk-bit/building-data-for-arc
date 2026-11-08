"""Generate answer-identifying lessons for the hole-sorted component strip.

The authoritative rule finds 4-connected components of *all* nonzero cells,
so colors may mix inside one object.  Each component is cropped to its bounding
box, its enclosed zero regions are counted, and crops are packed left-to-right
with one black separator column.  Ordering is by increasing hole count, then
increasing painted area, then the component's first row-major color.

Three scheduled profiles make every lesson teach the full ordering chain:
``canonical_holes`` anchors the public 0/1/2-hole morphology,
``hole_priority`` makes hole count disagree with area-only sorting, and
``tie_chain`` exposes both area-ascending and color tie-break behavior.  Every
ordinary scene also contains a mixed-color component so per-color extraction is
an executable counterexample rather than an untested prose warning.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "786a759f780e"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "71abd31a186f"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "Find every 4-connected nonzero component, even when a component mixes "
    "colors. Crop each component, count enclosed black regions inside its "
    "bounding box, sort by increasing hole count, increasing painted area, "
    "and finally the first row-major component color, then pack the crops "
    "left-to-right with one black separator column."
)

INVARIANTS = [
    "background is black (0) and every ordinary input uses exactly three foreground colors",
    "components are separated by at least one black cell but may mix colors internally",
    "canonical_holes realizes 0-, 1-, and 2-hole public morphologies",
    "hole_priority makes area-only sorting disagree with hole-first sorting",
    "tie_chain proves increasing area and the final color tie-break",
    "input reading order is deliberately different from output order",
]

SCENE_PROFILES = ("canonical_holes", "hole_priority", "tie_chain")
CANVAS_PROFILES = ("11x20", "12x20")
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_SCHEDULE = SCENE_PROFILES
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "three-residue sample-index schedule",
        "valid": "canonical_holes|hole_priority|tie_chain",
    },
    "canvas_profile": {
        "type": "str",
        "default": "deterministic choice over canonical canvas sizes",
        "valid": "11x20|12x20",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, str]] = []

BACKGROUND = 0
COLORS = tuple(range(1, 10))
_NEIGHBORS_4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NEIGHBORS_8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

# Role indexes placed in top-left / top-right / bottom-center reading slots.
# Identity is excluded so reading-order packing is always visibly wrong.
_LAYOUT_PERMUTATIONS = (
    (0, 2, 1),
    (1, 0, 2),
    (1, 2, 0),
    (2, 0, 1),
    (2, 1, 0),
)
# For the equal-area small rings in tie_chain, role 1 (high color) must appear
# before role 0 (low color) in the input so omitting the color tie-break fails.
_TIE_LAYOUT_PERMUTATIONS = tuple(
    permutation
    for permutation in _LAYOUT_PERMUTATIONS
    if permutation.index(1) < permutation.index(0)
)

# Exact linked public signatures:
# (height, width, palette size including background,
#  sorted (holes, painted area, bbox height, bbox width)).
_CANONICAL_SIGNATURES = {
    (11, 20, 4, ((0, 4, 3, 2), (1, 8, 3, 3), (2, 23, 5, 7))),
    (12, 20, 4, ((0, 4, 3, 2), (1, 8, 3, 3), (2, 23, 5, 7))),
    (11, 20, 4, ((1, 8, 3, 3), (2, 26, 7, 7))),
    (12, 20, 4, ((1, 8, 3, 3), (2, 27, 8, 7))),
}

Grid = list[list[int]]
Cell = tuple[int, int]
ObjectFacts = dict[str, Any]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input grid with observable exact axes."""
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name, legal in (
        ("scene_profile", SCENE_PROFILES),
        ("canvas_profile", CANVAS_PROFILES),
    ):
        value = overrides.get(name)
        if value is not None and value not in legal:
            raise ValueError(f"{name} must be one of {legal}, not {value!r}")

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
        scheduled = schedule_profile(seed, sample_index, difficulty=band)
        scene_profile = ctx.draw_choice("scene_profile", (scheduled,))
    else:
        scene_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    canvas_profile = ctx.draw_choice("canvas_profile", CANVAS_PROFILES)
    height, width = _parse_canvas_profile(canvas_profile)

    rng = ctx.draw_rng(f"scene:{scene_profile}:{canvas_profile}:{band}")
    role_colors = _role_colors(scene_profile, rng)
    shapes = _profile_shapes(scene_profile, role_colors)

    # Reflection is nuisance variation. Recoloring happens afterwards so the
    # first row-major cell remains the declared primary/key color.
    reflect_code = rng.randrange(4)
    shapes = [_reflect(shape, reflect_code) for shape in shapes]
    mixed_role = rng.randrange(len(shapes))
    secondary_choices = [
        color for index, color in enumerate(role_colors) if index != mixed_role
    ]
    shapes[mixed_role] = _mix_last_cell(
        shapes[mixed_role], rng.choice(secondary_choices)
    )

    layouts = (
        _TIE_LAYOUT_PERMUTATIONS
        if scene_profile == "tie_chain"
        else _LAYOUT_PERMUTATIONS
    )
    permutation = layouts[
        (int(sample_index) + rng.randrange(len(layouts))) % len(layouts)
    ]
    grid = _paint_in_slots(height, width, shapes, permutation)

    analysis = _analyze(grid)
    if analysis["errors"]:
        raise AssertionError("constructed invalid scene: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    if facts["reading_order"] == facts["sorted_order"]:
        raise AssertionError("constructed scene failed reading-order conflict")
    if not any(len(obj["colors"]) > 1 for obj in facts["objects"]):
        raise AssertionError("constructed scene lacks a mixed-color component")

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
    """Declare the C/H/T cycle used by all ordinary lesson windows."""
    del seed, difficulty
    return _PROFILE_SCHEDULE[int(sample_index) % len(_PROFILE_SCHEDULE)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the linked teaching grammar and reject structural impostors."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    facts = analysis["facts"]
    profile = _classify_profile(facts)
    if profile is None:
        return [
            "scene must match canonical_holes, hole_priority, or tie_chain linked morphology"
        ]

    if facts["palette_size"] != 4:
        errors.append(
            "expected black plus exactly three foreground colors, "
            f"found palette size {facts['palette_size']}"
        )
    if profile != "canonical_holes" and facts["object_count"] != 3:
        errors.append(f"{profile} requires exactly 3 components")
    if profile == "canonical_holes" and facts["object_count"] not in (2, 3):
        errors.append("canonical_holes requires 2 or 3 components")
    if facts["touching_object_pairs"]:
        errors.append("components must be separated by at least one black cell")
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
            f"scene_profile requested {requested_scene!r}, "
            f"observed {observed.get('scene_profile')!r}"
        )
    if requested_canvas is not None and observed.get("canvas_profile") != requested_canvas:
        errors.append(
            f"canvas_profile requested {requested_canvas!r}, "
            f"observed {observed.get('canvas_profile')!r}"
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
    """Expose the strict linked signature for source-bound review tooling."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    return _linked_signature(analysis["facts"])


def observe_overrides(grid) -> dict[str, str]:
    """Recover every exact declared axis from returned pixels."""
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
    """Return linked task observables for semantic and curriculum censuses."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    holes = sorted({obj["holes"] for obj in facts["objects"]})
    return {
        "scene_profile": _classify_profile(facts),
        "canvas_profile": f"{facts['height']}x{facts['width']}",
        "hole_histogram": dict(Counter(obj["holes"] for obj in facts["objects"])),
        "areas_by_holes": {
            str(hole_count): tuple(
                sorted(
                    obj["area"]
                    for obj in facts["objects"]
                    if obj["holes"] == hole_count
                )
            )
            for hole_count in holes
        },
        "mixed_component_count": sum(
            len(obj["colors"]) > 1 for obj in facts["objects"]
        ),
        "input_order": tuple(facts["reading_order"]),
        "packed_order": tuple(facts["sorted_order"]),
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def rule_mirror(grid: Grid) -> Grid:
    """Pure-Python test mirror; the selected Racket program is authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return deepcopy(analysis["facts"]["output"])


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that leave any declared plausible program query-relevant."""
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
            f"demos must contain profiles {sorted(required)}, "
            f"found {sorted(demo_profiles)}"
        )
    if query_profile not in required:
        reasons.append(f"query profile {query_profile!r} is unsupported")

    for name, competitor in LESSON_COMPETITORS.items():
        if not all(competitor(pair["input"]) == pair["output"] for pair in demos):
            continue
        if competitor(query["input"]) != query["output"]:
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
        errors.append("output does not equal hole-sorted component packing")
    return errors, profile


def _parse_canvas_profile(profile: str) -> tuple[int, int]:
    height, width = profile.split("x", 1)
    return int(height), int(width)


def _role_colors(profile: str, rng) -> list[int]:
    """Choose distinct keys whose numeric order is not the semantic order."""
    low, middle, high = sorted(rng.sample(COLORS, 3))
    if profile == "tie_chain":
        # Desired order is low-small, high-small, middle-large; color-only puts
        # the middle-large object before the high-small object.
        return [low, high, middle]
    # Desired order is role 0,1,2; color-only instead yields role 1,2,0.
    return [high, low, middle]


def _profile_shapes(profile: str, colors: list[int]) -> list[Grid]:
    if profile == "canonical_holes":
        return [
            _paint_mask(((1, 0), (1, 1), (0, 1)), colors[0]),
            _ring(3, 3, colors[1]),
            _canonical_double_chamber(colors[2]),
        ]
    if profile == "hole_priority":
        return [
            [[colors[0]] * 4 for _ in range(3)],
            _ring(3, 3, colors[1]),
            _double_ring_3x5(colors[2]),
        ]
    if profile == "tie_chain":
        return [
            _ring(3, 3, colors[0]),
            _ring(3, 3, colors[1]),
            _ring(4, 4, colors[2]),
        ]
    raise ValueError(f"unknown scene profile {profile!r}")


def _paint_mask(mask: tuple[tuple[int, ...], ...], color: int) -> Grid:
    return [[color if value else 0 for value in row] for row in mask]


def _ring(height: int, width: int, color: int) -> Grid:
    return [
        [
            color
            if row in (0, height - 1) or col in (0, width - 1)
            else 0
            for col in range(width)
        ]
        for row in range(height)
    ]


def _double_ring_3x5(color: int) -> Grid:
    holes = {(1, 1), (1, 3)}
    return [
        [0 if (row, col) in holes else color for col in range(5)]
        for row in range(3)
    ]


def _canonical_double_chamber(color: int) -> Grid:
    return [
        [color] * 7,
        [color, 0, 0, color, 0, 0, color],
        [color, 0, 0, color, 0, 0, color],
        [color, 0, 0, color, 0, 0, color],
        [color] * 7,
    ]


def _reflect(shape: Grid, code: int) -> Grid:
    result = [row[:] for row in shape]
    if code & 1:
        result = [row[::-1] for row in result]
    if code & 2:
        result = result[::-1]
    return result


def _mix_last_cell(shape: Grid, secondary_color: int) -> Grid:
    result = [row[:] for row in shape]
    cells = [
        (row, col)
        for row, values in enumerate(result)
        for col, value in enumerate(values)
        if value != BACKGROUND
    ]
    if len(cells) < 2:
        raise ValueError("cannot mix color into a one-cell shape")
    row, col = max(cells)
    result[row][col] = secondary_color
    return result


def _paint_in_slots(
    height: int,
    width: int,
    shapes: list[Grid],
    permutation: tuple[int, int, int],
) -> Grid:
    grid = full_grid(height, width, BACKGROUND)
    for slot_index, role_index in enumerate(permutation):
        shape = shapes[role_index]
        shape_h, shape_w = len(shape), len(shape[0])
        if slot_index == 0:
            top, left = 0, 0
        elif slot_index == 1:
            top, left = 0, width - shape_w
        else:
            top, left = height - shape_h, (width - shape_w) // 2
        for row, values in enumerate(shape):
            for col, value in enumerate(values):
                if value == BACKGROUND:
                    continue
                target = (top + row, left + col)
                if grid[target[0]][target[1]] != BACKGROUND:
                    raise AssertionError("slot construction produced an overlap")
                grid[target[0]][target[1]] = value
    return grid


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _basic_grid_errors(grid)
    if errors:
        return {"errors": errors, "facts": None}
    height, width = len(grid), len(grid[0])
    components = _objects_nonzero(grid)
    if not components:
        return {"errors": ["grid contains no nonzero components"], "facts": None}
    touching_pairs = _touching_object_pairs(components)
    sorted_objects = sorted(
        components,
        key=lambda obj: (obj["holes"], obj["area"], obj["color"]),
    )
    facts = {
        "height": height,
        "width": width,
        "palette_size": len({value for row in grid for value in row}),
        "object_count": len(components),
        "objects": tuple(components),
        "touching_object_pairs": touching_pairs,
        "reading_order": tuple(obj["reading_rank"] for obj in components),
        "sorted_order": tuple(obj["reading_rank"] for obj in sorted_objects),
        "output": _pack_objects(sorted_objects),
    }
    return {"errors": [], "facts": facts}


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list or tuple of rows"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["every grid row must be a list or tuple"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or not widths or 0 in widths:
        return ["grid must be rectangular and nonempty"]
    height, width = len(grid), next(iter(widths))
    errors: list[str] = []
    if (height, width) not in {
        _parse_canvas_profile(profile) for profile in CANVAS_PROFILES
    }:
        errors.append(f"canvas must be 11x20 or 12x20, found {height}x{width}")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid cells must be literal integer ARC colors 0..9")
    if not any(value == BACKGROUND for row in grid for value in row):
        errors.append("black background color 0 must be present")
    return errors


def _objects_nonzero(grid: Grid) -> list[ObjectFacts]:
    """Match the Racket authority: connectivity ignores foreground color."""
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[ObjectFacts] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == BACKGROUND or (row, col) in seen:
                continue
            key_color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in _NEIGHBORS_4:
                    nr, nc = current[0] + dr, current[1] + dc
                    nxt = (nr, nc)
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and nxt not in seen
                        and grid[nr][nc] != BACKGROUND
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(_object_facts(grid, cells, key_color))
    components.sort(key=lambda obj: (obj["top"], obj["left"]))
    for rank, obj in enumerate(components):
        obj["reading_rank"] = rank
    return components


def _objects_same_color(grid: Grid) -> list[ObjectFacts]:
    """Plausible wrong extractor: split disconnected objects by exact color."""
    height, width = len(grid), len(grid[0])
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
                for dr, dc in _NEIGHBORS_4:
                    nr, nc = current[0] + dr, current[1] + dc
                    nxt = (nr, nc)
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and nxt not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(_object_facts(grid, cells, color, component_only=True))
    components.sort(key=lambda obj: (obj["top"], obj["left"]))
    for rank, obj in enumerate(components):
        obj["reading_rank"] = rank
    return components


def _object_facts(
    grid: Grid,
    cells: list[Cell],
    key_color: int,
    *,
    component_only: bool = False,
) -> ObjectFacts:
    ordered = tuple(sorted(cells))
    top = min(row for row, _ in ordered)
    bottom = max(row for row, _ in ordered)
    left = min(col for _, col in ordered)
    right = max(col for _, col in ordered)
    if component_only:
        cell_set = set(ordered)
        crop = [
            [
                grid[row][col] if (row, col) in cell_set else BACKGROUND
                for col in range(left, right + 1)
            ]
            for row in range(top, bottom + 1)
        ]
    else:
        crop = [
            [grid[row][col] for col in range(left, right + 1)]
            for row in range(top, bottom + 1)
        ]
    return {
        "color": key_color,
        "colors": tuple(sorted({grid[row][col] for row, col in ordered})),
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


def _hole_count(crop: Grid) -> int:
    height, width = len(crop), len(crop[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if crop[row][col] == BACKGROUND
    }
    holes = 0
    while remaining:
        start = min(remaining)
        stack = [start]
        remaining.remove(start)
        touches_border = False
        while stack:
            row, col = stack.pop()
            if row in (0, height - 1) or col in (0, width - 1):
                touches_border = True
            for dr, dc in _NEIGHBORS_4:
                nxt = (row + dr, col + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
        if not touches_border:
            holes += 1
    return holes


def _touching_object_pairs(
    components: list[ObjectFacts],
) -> tuple[tuple[int, int], ...]:
    touching: list[tuple[int, int]] = []
    for first_index, first in enumerate(components):
        for second_index in range(first_index + 1, len(components)):
            second_cells = components[second_index]["cell_set"]
            if any(
                (row + dr, col + dc) in second_cells
                for row, col in first["cells"]
                for dr, dc in _NEIGHBORS_8
            ):
                touching.append((first_index, second_index))
    return tuple(touching)


def _pack_objects(components: list[ObjectFacts]) -> Grid:
    if not components:
        raise ValueError("cannot pack an empty object list")
    out_height = max(obj["height"] for obj in components)
    out_width = sum(obj["width"] for obj in components) + len(components) - 1
    output = full_grid(out_height, out_width, BACKGROUND)
    left = 0
    for obj in components:
        for row, values in enumerate(obj["crop"]):
            for col, value in enumerate(values):
                if value != BACKGROUND:
                    output[row][left + col] = value
        left += obj["width"] + 1
    return output


def _pack_with_key(grid: Grid, key) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _pack_objects(sorted(analysis["facts"]["objects"], key=key))


def _classify_profile(facts: dict[str, Any]) -> str | None:
    rows = tuple(
        sorted(
            (obj["holes"], obj["area"], obj["height"], obj["width"])
            for obj in facts["objects"]
        )
    )
    if rows in {
        ((0, 4, 3, 2), (1, 8, 3, 3), (2, 23, 5, 7)),
        ((1, 8, 3, 3), (2, 26, 7, 7)),
        ((1, 8, 3, 3), (2, 27, 8, 7)),
    }:
        return "canonical_holes"
    if rows == ((0, 12, 3, 4), (1, 8, 3, 3), (2, 13, 3, 5)):
        return "hole_priority"
    if rows == ((1, 8, 3, 3), (1, 8, 3, 3), (1, 12, 4, 4)):
        return "tie_chain"
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


# --- Executable rival programs and their witnesses -----------------------


def _rival_area_only(grid: Grid) -> Grid:
    return _pack_with_key(grid, lambda obj: (obj["area"], obj["color"]))


def _rival_hole_only(grid: Grid) -> Grid:
    return _pack_with_key(grid, lambda obj: (obj["holes"], obj["reading_rank"]))


def _rival_area_descending(grid: Grid) -> Grid:
    return _pack_with_key(
        grid, lambda obj: (obj["holes"], -obj["area"], obj["color"])
    )


def _rival_no_color_tiebreak(grid: Grid) -> Grid:
    return _pack_with_key(
        grid, lambda obj: (obj["holes"], obj["area"], obj["reading_rank"])
    )


def _rival_reading_order(grid: Grid) -> Grid:
    return _pack_with_key(grid, lambda obj: (obj["reading_rank"],))


def _rival_color_order(grid: Grid) -> Grid:
    return _pack_with_key(grid, lambda obj: (obj["color"],))


def _rival_same_color_components(grid: Grid) -> Grid:
    components = _objects_same_color(grid)
    return _pack_objects(
        sorted(components, key=lambda obj: (obj["holes"], obj["area"], obj["color"]))
    )


def _witness_profile(profile: str) -> Callable[[Grid], bool]:
    def predicate(grid: Grid) -> bool:
        return observe_overrides(grid).get("scene_profile") == profile

    return predicate


def _witness_rival(profile: str, rival: Callable[[Grid], Grid]) -> Callable[[Grid], bool]:
    def predicate(grid: Grid) -> bool:
        return (
            observe_overrides(grid).get("scene_profile") == profile
            and rival(grid) != rule_mirror(grid)
        )

    return predicate


def _witness_reading_order(grid: Grid) -> bool:
    analysis = _analyze(grid)
    return (
        not analysis["errors"]
        and analysis["facts"]["reading_order"] != analysis["facts"]["sorted_order"]
        and _rival_reading_order(grid) != analysis["facts"]["output"]
    )


def _witness_multicolor(grid: Grid) -> bool:
    analysis = _analyze(grid)
    return (
        not analysis["errors"]
        and any(len(obj["colors"]) > 1 for obj in analysis["facts"]["objects"])
        and _rival_same_color_components(grid) != analysis["facts"]["output"]
    )


SEMANTIC_RIVALS = {
    "area_only": _rival_area_only,
    "hole_count_only": _rival_hole_only,
    "area_descending": _rival_area_descending,
    "no_color_tiebreak": _rival_no_color_tiebreak,
    "reading_order": _rival_reading_order,
    "color_order": _rival_color_order,
    "same_color_components": _rival_same_color_components,
}
SEMANTIC_WITNESSES = {
    "canonical_hole_chain": _witness_profile("canonical_holes"),
    "hole_priority_over_area": _witness_rival("hole_priority", _rival_area_only),
    "area_ascending_tiebreak": _witness_rival("tie_chain", _rival_area_descending),
    "color_tiebreak": _witness_rival("tie_chain", _rival_no_color_tiebreak),
    "reading_order_conflict": _witness_reading_order,
    "multicolor_component": _witness_multicolor,
}
WITNESS_RIVALS = {
    "canonical_hole_chain": ["color_order"],
    "hole_priority_over_area": ["area_only"],
    "area_ascending_tiebreak": ["hole_count_only", "area_descending"],
    "color_tiebreak": ["no_color_tiebreak"],
    "reading_order_conflict": ["reading_order"],
    "multicolor_component": ["same_color_components"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# All five programs below fit every public pair; ordinary profiles provide
# explicit counterexamples so a training lesson cannot inherit that ambiguity.
CANONICAL_SHORTCUTS = {
    "area_only": _rival_area_only,
    "hole_count_only": _rival_hole_only,
    "area_descending": _rival_area_descending,
    "no_color_tiebreak": _rival_no_color_tiebreak,
    "color_order": _rival_color_order,
}
