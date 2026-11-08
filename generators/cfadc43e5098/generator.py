"""Semantic generator for ARC task cfadc43e5098 (source f3b10344).

Treat every non-background four-connected monochrome object by its bounding
box.  Two same-color boxes may be joined across a horizontal or vertical gap
when they overlap on the perpendicular axis and have the same midpoint on
that axis.  Fill the complete gap with cyan-8 across the *interior* of the
overlap.  Suppress a candidate bridge when a third same-color object's box
intersects the bridge rectangle.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import permutations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "cfadc43e5098"
TASK_ID = "cfadc43e5098"
VERSION = "3.0.0"
RULE_HASH = "b67b77ea3d2d"
SUMMARY = "Bridge midpoint-aligned same-color object boxes across their full gap and overlap interior, unless a third same-color box blocks the bridge."
INVARIANTS = [
    "calibrated inputs use a zero background and five through eleven solid rectangles",
    "calibrated rectangle areas stay within the official nine-through-forty-nine-cell range",
    "bridge endpoints must have the same literal color",
    "horizontal endpoints overlap in rows and have equal row-midpoint sums",
    "vertical endpoints overlap in columns and have equal column-midpoint sums",
    "the cyan-8 bridge spans the full facing-edge gap but excludes the overlap boundary",
    "a third same-color bounding box intersecting the bridge suppresses that candidate",
    "all input rectangles and all cells outside unblocked bridges are preserved",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 5))
GENERAL_PROFILES = (
    "horizontal_pair",
    "vertical_pair",
    "horizontal_chain",
    "vertical_chain",
    "dual_axis",
    "midpoint_decoy",
    "blocker_cross",
    "unequal_overlap",
)
# Interleave the four exact public families with shortcut-refuting general
# families.  Every cyclic four-pair window therefore contains at least two
# general pairs; holding out any one pair still leaves a teaching witness.
SCENE_PROFILES = (
    "public_1", "horizontal_pair",
    "public_2", "vertical_pair",
    "public_3", "horizontal_chain",
    "public_4", "vertical_chain",
    "dual_axis", "midpoint_decoy", "blocker_cross", "unequal_overlap",
)
LESSON_SCHEDULE_PERIOD = len(SCENE_PROFILES)
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four complete official families plus eight alignment/blocking contrasts",
        "valid": "public_1|public_2|public_3|public_4|horizontal_pair|vertical_pair|horizontal_chain|vertical_chain|dual_axis|midpoint_decoy|blocker_cross|unequal_overlap",
    }
}

OBJECT_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)

# Exact canonical inputs reconstructed losslessly from their solid rectangle
# bounding boxes.  public_1..3 are training examples; public_4 is the held-out
# test example and duplicated augmented row.
_PUBLIC_SPECS = {
    "public_1": (30, 30, (
        (2, 1, 4, 7, 9), (2, 15, 4, 18, 9), (2, 15, 14, 18, 17),
        (2, 21, 5, 24, 8), (6, 1, 14, 7, 18), (6, 1, 22, 7, 27),
        (6, 14, 22, 19, 27),
    )),
    "public_2": (30, 30, (
        (1, 4, 3, 10, 9), (1, 4, 20, 10, 24), (3, 14, 7, 19, 11),
        (3, 22, 7, 26, 11), (3, 22, 20, 26, 24),
    )),
    "public_3": (25, 30, (
        (4, 2, 4, 7, 10), (4, 2, 16, 7, 21), (4, 3, 24, 6, 26),
        (4, 12, 0, 14, 2), (4, 12, 5, 14, 9), (4, 17, 4, 19, 10),
        (6, 11, 16, 14, 21), (6, 11, 24, 14, 26), (6, 17, 16, 19, 21),
    )),
    "public_4": (30, 29, (
        (2, 26, 9, 28, 11), (2, 26, 14, 28, 16),
        (3, 10, 16, 14, 21), (3, 10, 24, 14, 27),
        (3, 19, 16, 23, 21), (3, 20, 24, 22, 26),
        (7, 1, 5, 5, 11), (7, 1, 16, 5, 21), (7, 2, 1, 4, 3),
        (7, 10, 6, 14, 10), (7, 19, 4, 23, 12),
    )),
}


def _grid_from_spec(spec):
    height, width, rectangles = spec
    grid = [[0] * width for _ in range(height)]
    for color, row1, col1, row2, col2 in rectangles:
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                grid[row][col] = color
    return grid


_PUBLIC_INPUTS = {profile: _grid_from_spec(spec) for profile, spec in _PUBLIC_SPECS.items()}
_PUBLIC_EXACT = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return ["input must contain one through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        return ["input must contain one through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _neighbors(cell):
    row, col = cell
    return ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))


def _components(grid):
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height) for col in range(width)
        if grid[row][col] != 0
    }
    components = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        stack, cells = [start], {start}
        while stack:
            cell = stack.pop()
            for neighbor in _neighbors(cell):
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        components.append({
            "color": color,
            "cells": frozenset(cells),
            "bbox": (min(rows), min(cols), max(rows), max(cols)),
        })
    return tuple(sorted(components, key=lambda obj: min(obj["cells"])))


def _intersects(first, second):
    ar1, ac1, ar2, ac2 = first
    br1, bc1, br2, bc2 = second
    return max(ar1, br1) <= min(ar2, br2) and max(ac1, bc1) <= min(ac2, bc2)


def _pair_geometry(first, second):
    ar1, ac1, ar2, ac2 = first["bbox"]
    br1, bc1, br2, bc2 = second["bbox"]
    row_start, row_end = max(ar1, br1), min(ar2, br2)
    col_start, col_end = max(ac1, bc1), min(ac2, bc2)
    row_overlap, col_overlap = row_start <= row_end, col_start <= col_end
    if row_overlap and not col_overlap and ar1 + ar2 == br1 + br2:
        gap1 = ac2 + 1 if ac2 < bc1 else bc2 + 1
        gap2 = bc1 - 1 if ac2 < bc1 else ac1 - 1
        bridge = (row_start + 1, gap1, row_end - 1, gap2)
        return ("horizontal", bridge) if bridge[0] <= bridge[2] and bridge[1] <= bridge[3] else None
    if col_overlap and not row_overlap and ac1 + ac2 == bc1 + bc2:
        gap1 = ar2 + 1 if ar2 < br1 else br2 + 1
        gap2 = br1 - 1 if ar2 < br1 else ar1 - 1
        bridge = (gap1, col_start + 1, gap2, col_end - 1)
        return ("vertical", bridge) if bridge[0] <= bridge[2] and bridge[1] <= bridge[3] else None
    return None


def _bridge_facts(grid):
    components = _components(grid)
    candidates, mismatches = [], []
    for first_index, first in enumerate(components):
        for second_index in range(first_index + 1, len(components)):
            second = components[second_index]
            if first["color"] != second["color"]:
                continue
            geometry = _pair_geometry(first, second)
            if geometry is None:
                ar1, ac1, ar2, ac2 = first["bbox"]
                br1, bc1, br2, bc2 = second["bbox"]
                row_overlap = max(ar1, br1) <= min(ar2, br2)
                col_overlap = max(ac1, bc1) <= min(ac2, bc2)
                horizontal_mismatch = row_overlap and not col_overlap and ar1 + ar2 != br1 + br2
                vertical_mismatch = col_overlap and not row_overlap and ac1 + ac2 != bc1 + bc2
                if horizontal_mismatch or vertical_mismatch:
                    area1 = (ar2 - ar1 + 1) * (ac2 - ac1 + 1)
                    area2 = (br2 - br1 + 1) * (bc2 - bc1 + 1)
                    mismatches.append({
                        "orientation": "horizontal" if horizontal_mismatch else "vertical",
                        "large": area1 >= 20 and area2 >= 20,
                        "objects": (first_index, second_index),
                    })
                continue
            orientation, bridge = geometry
            blocker_indices = tuple(
                index
                for index, obj in enumerate(components)
                if index not in (first_index, second_index)
                and obj["color"] == first["color"]
                and _intersects(obj["bbox"], bridge)
            )
            candidates.append({
                "orientation": orientation,
                "bridge": bridge,
                "objects": (first_index, second_index),
                "color": first["color"],
                "blockers": blocker_indices,
                "blocked": bool(blocker_indices),
                "unequal_boxes": first["bbox"] != second["bbox"] and (
                    (first["bbox"][2] - first["bbox"][0], first["bbox"][3] - first["bbox"][1])
                    != (second["bbox"][2] - second["bbox"][0], second["bbox"][3] - second["bbox"][1])
                ),
            })
    return {"components": components, "candidates": tuple(candidates), "mismatches": tuple(mismatches)}


def rule_mirror(grid):
    """Broad, input-pure mirror of the canonical bbox bridge rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    for candidate in _bridge_facts(grid)["candidates"]:
        if candidate["blocked"]:
            continue
        row1, col1, row2, col2 = candidate["bridge"]
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                output[row][col] = 8
    return output



def _any_color_blocker_rule(grid):
    """Plausible wrong rule: any intersecting third box blocks a bridge."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _bridge_facts(grid)
    output = [list(row) for row in grid]
    for candidate in facts["candidates"]:
        endpoints = set(candidate["objects"])
        blocked = any(
            index not in endpoints and _intersects(obj["bbox"], candidate["bridge"])
            for index, obj in enumerate(facts["components"])
        )
        if blocked:
            continue
        row1, col1, row2, col2 = candidate["bridge"]
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                output[row][col] = 8
    return output


def _has_different_color_obstacle_does_not_block(grid):
    """Whether canonical bridging crosses a differently colored object's box."""
    facts = _bridge_facts(grid)
    for candidate in facts["candidates"]:
        if candidate["blocked"]:
            continue
        endpoints = set(candidate["objects"])
        if any(
            index not in endpoints
            and obj["color"] != candidate["color"]
            and _intersects(obj["bbox"], candidate["bridge"])
            for index, obj in enumerate(facts["components"])
        ):
            return True
    return False


def _canonicalize_colors(grid):
    mapping, next_label, normalized = {0: 0}, 10, []
    for row in grid:
        result = []
        for value in row:
            if value not in mapping:
                mapping[value] = next_label
                next_label += 1
            result.append(mapping[value])
        normalized.append(tuple(result))
    return tuple(normalized)


def _rotate(grid):
    return tuple(
        tuple(grid[len(grid) - 1 - row][col] for row in range(len(grid)))
        for col in range(len(grid[0]))
    )


def _d4_grids(grid):
    variants, current = set(), tuple(map(tuple, grid))
    for _ in range(4):
        variants.add(current)
        variants.add(tuple(tuple(reversed(row)) for row in current))
        current = _rotate(current)
    return tuple(sorted(variants))


_PUBLIC_FAMILY_KEYS = {
    _canonicalize_colors(transformed): profile
    for profile, grid in _PUBLIC_INPUTS.items()
    for transformed in _d4_grids(grid)
}


def _public_family(grid):
    try:
        return _PUBLIC_FAMILY_KEYS.get(_canonicalize_colors(grid))
    except TypeError:
        return None


def _general_profile(facts):
    if len(facts["components"]) != 8:
        return None
    unblocked = [candidate for candidate in facts["candidates"] if not candidate["blocked"]]
    blocked = [candidate for candidate in facts["candidates"] if candidate["blocked"]]
    horizontal = sum(item["orientation"] == "horizontal" for item in unblocked)
    vertical = sum(item["orientation"] == "vertical" for item in unblocked)
    blocked_horizontal = sum(item["orientation"] == "horizontal" for item in blocked)
    blocked_vertical = sum(item["orientation"] == "vertical" for item in blocked)
    if horizontal == 2 and vertical == 0 and blocked_horizontal >= 1:
        return "horizontal_chain"
    if vertical == 2 and horizontal == 0 and blocked_vertical >= 1:
        return "vertical_chain"
    if horizontal == 1 and vertical == 1 and not blocked:
        return "dual_axis"
    if vertical == 1 and horizontal == 0 and blocked_horizontal >= 1:
        return "blocker_cross"
    if horizontal == 1 and vertical == 0 and not blocked:
        if any(item["unequal_boxes"] for item in unblocked):
            return "unequal_overlap"
        if any(item["large"] for item in facts["mismatches"]):
            return "midpoint_decoy"
        return "horizontal_pair"
    if vertical == 1 and horizontal == 0 and not blocked:
        return "vertical_pair"
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": {}, "output": None}
    height, width = len(grid), len(grid[0])
    if not 25 <= height <= 30 or not 25 <= width <= 30:
        errors.append("calibrated scenes must use canonical-scale 25..30 by 25..30 canvases")
    if any(value == 8 for row in grid for value in row):
        errors.append("cyan 8 is reserved for generated bridges and may not occur in calibrated inputs")
    facts = _bridge_facts(grid)
    components = facts["components"]
    colors = {obj["color"] for obj in components}
    if not 5 <= len(components) <= 11:
        errors.append("calibrated scenes require five through eleven input rectangles")
    if not 2 <= len(colors) <= 3:
        errors.append("calibrated scenes require two or three non-background object colors")
    for obj in components:
        row1, col1, row2, col2 = obj["bbox"]
        area = (row2 - row1 + 1) * (col2 - col1 + 1)
        if area != len(obj["cells"]):
            errors.append("every calibrated object must be a solid rectangle")
            break
        if not 9 <= area <= 49:
            errors.append("calibrated rectangle areas must contain nine through forty-nine cells")
            break
    output = rule_mirror(grid)
    changed = sum(
        before != after
        for before_row, after_row in zip(grid, output)
        for before, after in zip(before_row, after_row)
    )
    unblocked = tuple(candidate for candidate in facts["candidates"] if not candidate["blocked"])
    if not unblocked or changed < 20:
        errors.append("calibrated scenes require at least one unblocked bridge changing twenty or more cells")
    profile = _public_family(grid) or _general_profile(facts)
    if profile not in SCENE_PROFILES:
        errors.append("rectangle relationships do not match a declared semantic profile")
    details = dict(facts)
    details.update({
        "height": height,
        "width": width,
        "colors": tuple(sorted(colors)),
        "object_count": len(components),
        "unblocked": unblocked,
        "changed": changed,
        "blocked_count": sum(candidate["blocked"] for candidate in facts["candidates"]),
    })
    return {"errors": errors, "scene_profile": profile, "facts": details, "output": output}


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    profile = analysis["scene_profile"]
    return profile if profile in PUBLIC_PROFILES and not analysis["errors"] else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


def strict_canonical_like(grid):
    """Return reasons when a grid falls outside this generator's task manifold."""
    return self_check(grid)


SEMANTIC_WITNESSES = {
    "different_color_obstacle_does_not_block": _has_different_color_obstacle_does_not_block,
}
SEMANTIC_RIVALS = {"any_color_blocks": _any_color_blocker_rule}
WITNESS_RIVALS = {
    "different_color_obstacle_does_not_block": ["any_color_blocks"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


@lru_cache(maxsize=None)
def _replacement_orders(count):
    return tuple(permutations(OBJECT_COLORS, count))


def _embed_public(profile, variant_index):
    transforms = _d4_grids(_PUBLIC_INPUTS[profile])
    grid = transforms[variant_index % len(transforms)]
    source_colors = sorted({value for row in grid for value in row if value != 0})
    orders = _replacement_orders(len(source_colors))
    replacements = orders[(variant_index // len(transforms)) % len(orders)]
    mapping = dict(zip(source_colors, replacements))
    return [[0 if value == 0 else mapping[value] for value in row] for row in grid]


def _draw_rect(grid, rectangle):
    color, row1, col1, row2, col2 = rectangle
    for row in range(row1, row2 + 1):
        for col in range(col1, col2 + 1):
            if grid[row][col] != 0:
                return False
    for row in range(row1, row2 + 1):
        for col in range(col1, col2 + 1):
            grid[row][col] = color
    return True


def _base_core(profile, colors):
    first, second, third = colors
    if profile == "horizontal_pair":
        return [(first, 2, 2, 8, 7), (first, 2, 16, 8, 21)]
    if profile == "vertical_pair":
        return [(first, 2, 2, 7, 8), (first, 16, 2, 21, 8)]
    if profile == "horizontal_chain":
        return [(first, 2, 2, 8, 6), (first, 2, 11, 8, 15), (first, 2, 20, 8, 24)]
    if profile == "vertical_chain":
        return [(first, 2, 2, 6, 8), (first, 11, 2, 15, 8), (first, 20, 2, 24, 8)]
    if profile == "dual_axis":
        return [
            (first, 2, 2, 8, 7), (first, 2, 14, 8, 19),
            (second, 14, 23, 18, 28), (second, 24, 23, 28, 28),
        ]
    if profile == "midpoint_decoy":
        return [
            (first, 2, 2, 8, 7), (first, 2, 16, 8, 21),
            (second, 14, 2, 18, 6), (second, 15, 14, 21, 18),
        ]
    if profile == "blocker_cross":
        return [
            (first, 2, 2, 8, 6), (first, 2, 20, 8, 24), (first, 3, 11, 6, 14),
            (second, 14, 2, 18, 8), (second, 24, 2, 28, 8),
        ]
    if profile == "unequal_overlap":
        return [(first, 2, 2, 8, 7), (first, 3, 16, 7, 21)]
    raise ValueError(profile)


def _rect_separated(rectangle, existing):
    color, row1, col1, row2, col2 = rectangle
    for other in existing:
        other_color, or1, oc1, or2, oc2 = other
        if _intersects((row1, col1, row2, col2), (or1, oc1, or2, oc2)):
            return False
        if color == other_color and _intersects(
            (max(0, row1 - 1), max(0, col1 - 1), min(29, row2 + 1), min(29, col2 + 1)),
            (or1, oc1, or2, oc2),
        ):
            return False
    return True


def _random_general(profile, rng):
    color_count = 3 if profile in ("dual_axis", "midpoint_decoy", "blocker_cross") else 2
    colors = rng.sample(OBJECT_COLORS, color_count)
    core = _base_core(profile, colors + colors[: max(0, 3 - len(colors))])

    # Put a differently colored 3x3 rectangle inside one canonical bridge.
    # The intended rule overwrites it with cyan; the plausible shortcut
    # "any intersecting color blocks" leaves it untouched.  This makes every
    # general profile an explicit teaching witness without changing the rule.
    core_grid = [[0] * 30 for _ in range(30)]
    if not all(_draw_rect(core_grid, rectangle) for rectangle in core):
        raise AssertionError(f"invalid base core for {profile!r}")
    witness_candidates = [
        candidate for candidate in _bridge_facts(core_grid)["candidates"]
        if not candidate["blocked"]
    ]
    if not witness_candidates:
        raise AssertionError(f"base core for {profile!r} has no unblocked bridge")
    row1, col1, row2, col2 = witness_candidates[0]["bridge"]
    if row2 - row1 + 1 < 3 or col2 - col1 + 1 < 3:
        raise AssertionError(f"base bridge for {profile!r} cannot hold a 3x3 witness")
    obstacle_row = (row1 + row2 - 2) // 2
    obstacle_col = (col1 + col2 - 2) // 2
    witness = (colors[-1], obstacle_row, obstacle_col, obstacle_row + 2, obstacle_col + 2)
    core = list(core) + [witness]

    for _ in range(800):
        rectangles = list(core)
        while len(rectangles) < 8:
            height, width = rng.randint(3, 6), rng.randint(3, 6)
            row1, col1 = rng.randint(1, 29 - height), rng.randint(1, 29 - width)
            color = rng.choice(colors[1:] or colors)
            rectangle = (color, row1, col1, row1 + height - 1, col1 + width - 1)
            if _rect_separated(rectangle, rectangles):
                rectangles.append(rectangle)
        grid = [[0] * 30 for _ in range(30)]
        if not all(_draw_rect(grid, rectangle) for rectangle in rectangles):
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct bridge lesson {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band_index = {None: 0, "easy": 1, "medium": 2, "hard": 3}[difficulty]
    schedule_index = 12 * seed + sample_index + 6000 * band_index
    if overrides.get("scene_profile") is not None:
        profile = ctx.draw_choice("scene_profile", list(SCENE_PROFILES))
        variant_index = schedule_index
    else:
        profile = ctx.draw_choice("scene_profile", [SCENE_PROFILES[schedule_index % len(SCENE_PROFILES)]])
        variant_index = schedule_index // len(SCENE_PROFILES)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES and overrides.get("scene_profile") is not None:
        grid = [row[:] for row in _PUBLIC_INPUTS[profile]]
    elif profile in PUBLIC_PROFILES:
        grid = _embed_public(profile, variant_index)
    else:
        grid = _random_general(profile, ctx.draw_rng("scene"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid midpoint-bridge lesson: " + "; ".join(errors))
    return grid
