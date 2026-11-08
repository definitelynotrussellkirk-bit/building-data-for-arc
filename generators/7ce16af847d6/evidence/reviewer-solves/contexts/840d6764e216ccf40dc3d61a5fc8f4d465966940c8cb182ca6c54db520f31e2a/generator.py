"""Curriculum generator for recoloring exact solid blue 3x3 components.

The selected Racket rule is unchanged.  Inputs stay at canonical scale and use
three scheduled scene profiles: ordinary canonical-like controls, shape-based
counterexamples, and a color counterexample.  Every three consecutive examples
therefore distinguish the exact conjunction ``blue + size 9 + bbox 3x3`` from
several plausible shortcuts.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import product
from typing import Any

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "7ce16af847d6"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "a7803abc6931"
SUMMARY = (
    "On a zero background, recolor only four-connected color-1 components that "
    "are exactly nine cells in a 3x3 bounding box. Canonical-scale scenes mix "
    "solid blue 3x3 targets with blue near-misses and two nonblue decorations. "
    "Scheduled counterexamples include a hollow blue 3x3, a nine-cell non-square, "
    "a 3x3-with-tail, and a nonblue solid 3x3."
)
INVARIANTS = [
    "11x11 or 12x12 rectangular integer grid with palette {0,1,d1,d2}; color 3 is output-only",
    "2..3 exact solid blue 3x3 targets, 2..3 blue non-target components, and exactly two differently colored decorations",
    "6..8 four-connected same-color components, each with bounding dimensions at most 4x4",
    "three consecutive default examples cover canonical, shape-counterexample, and color-counterexample profiles",
]

SCENE_PROFILES = (
    "canonical_mix",
    "shape_counterexamples",
    "color_counterexample",
)
SCHEDULE_PROFILES = SCENE_PROFILES
SCHEDULE_PERIOD = len(SCENE_PROFILES)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "three-profile consecutive-example schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()

# Shapes are normalized (row, column) offsets and are all four-connected.
_SOLID_3 = tuple(product(range(3), range(3)))
_RING_3 = tuple(
    (r, c) for r in range(3) for c in range(3)
    if r in (0, 2) or c in (0, 2)
)
_SIZE_NINE_NON_SQUARE = tuple(
    [(r, c) for r in range(2) for c in range(4)] + [(2, 0)]
)
_SOLID_3_WITH_TAIL = tuple(list(_SOLID_3) + [(1, 3)])
_CANONICAL_BLUE_NEAR_MISSES = (
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),  # 2x3 rectangle
    ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)),  # 3x2 rectangle
    ((0, 0), (0, 1), (1, 0), (1, 1)),                  # 2x2 square
    ((0, 0), (0, 1), (0, 2)),                          # horizontal line
    ((0, 0), (1, 0), (2, 0)),                          # vertical line
    ((0, 0), (1, 0), (2, 0), (2, 1)),                  # L tetromino
    ((0, 0), (0, 1), (1, 1), (1, 2)),                  # zig-zag tetromino
)
_DECOR_SHAPES = (
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0)),
    ((0, 0), (1, 0), (1, 1), (1, 2)),
)
_DECOR_PALETTE = (2, 4, 5, 6, 7, 8, 9)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if "scene_profile" in overrides:
        value = overrides["scene_profile"]
        if not isinstance(value, str) or value not in SCENE_PROFILES:
            raise ValueError(
                f"scene_profile override must be one of {SCENE_PROFILES}, got {value!r}"
            )


def schedule_profile(seed, sample_index, difficulty=None):
    """Every three consecutive sample indices cover all teaching profiles."""
    return SCENE_PROFILES[(int(seed) + int(sample_index)) % SCHEDULE_PERIOD]


def _shape_bounds(cells):
    return (
        max(r for r, _ in cells) + 1,
        max(c for _, c in cells) + 1,
    )


def _slots(side: int):
    # Three 3-or-4-cell regions with one guaranteed background row/column gap.
    spans = ((0, 3), (4, 3), (8, side - 8))
    return [
        (r0, c0, rh, cw)
        for r0, rh in spans
        for c0, cw in spans
    ]


def _assign_slots(items, side, rng):
    slots = _slots(side)
    candidates = {}
    for index, obj in enumerate(items):
        ph, pw = _shape_bounds(obj["cells"])
        candidates[index] = [
            slot_index
            for slot_index, (_r0, _c0, sh, sw) in enumerate(slots)
            if ph <= sh and pw <= sw
        ]
        rng.shuffle(candidates[index])
        if not candidates[index]:
            raise RuntimeError(f"no slot can fit {obj['name']} ({ph}x{pw})")

    # Constrained shapes first; deterministic backtracking guarantees a layout.
    order = sorted(
        range(len(items)),
        key=lambda index: (len(candidates[index]), -len(items[index]["cells"]), index),
    )
    assignment = {}

    def place(depth, used):
        if depth == len(order):
            return True
        index = order[depth]
        for slot_index in candidates[index]:
            if slot_index in used:
                continue
            assignment[index] = slot_index
            used.add(slot_index)
            if place(depth + 1, used):
                return True
            used.remove(slot_index)
            assignment.pop(index, None)
        return False

    if not place(0, set()):
        raise RuntimeError("constructive slot assignment unexpectedly failed")
    return slots, assignment


def _render(items, side, rng):
    grid = [[0 for _ in range(side)] for _ in range(side)]
    slots, assignment = _assign_slots(items, side, rng)
    for index, obj in enumerate(items):
        r0, c0, sh, sw = slots[assignment[index]]
        ph, pw = _shape_bounds(obj["cells"])
        r0 += rng.randrange(sh - ph + 1)
        c0 += rng.randrange(sw - pw + 1)
        for dr, dc in obj["cells"]:
            if grid[r0 + dr][c0 + dc] != 0:
                raise RuntimeError("constructive slot overlap")
            grid[r0 + dr][c0 + dc] = obj["color"]

    # D4 symmetry adds positional diversity without changing object predicates.
    symmetry = rng.randrange(8)
    if symmetry >= 4:
        grid = [row[::-1] for row in grid]
    for _ in range(symmetry % 4):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def _ordinary_objects(n_targets, decor_colors, rng, *, color_counterexample):
    items = [
        {"name": f"target_{index}", "color": 1, "cells": _SOLID_3}
        for index in range(n_targets)
    ]
    near_misses = rng.sample(list(_CANONICAL_BLUE_NEAR_MISSES), 3)
    items.extend(
        {"name": f"blue_near_miss_{index}", "color": 1, "cells": cells}
        for index, cells in enumerate(near_misses)
    )
    if color_counterexample:
        items.append({"name": "nonblue_exact_3x3", "color": decor_colors[0], "cells": _SOLID_3})
        items.append({"name": "decoration", "color": decor_colors[1], "cells": rng.choice(_DECOR_SHAPES)})
    else:
        shapes = rng.sample(list(_DECOR_SHAPES), 2)
        items.extend(
            {"name": f"decoration_{index}", "color": color, "cells": shape}
            for index, (color, shape) in enumerate(zip(decor_colors, shapes))
        )
    return items


def _profile_objects(profile, decor_colors, rng):
    if profile == "shape_counterexamples":
        return [
            {"name": "target_0", "color": 1, "cells": _SOLID_3},
            {"name": "target_1", "color": 1, "cells": _SOLID_3},
            {"name": "hollow_blue_3x3", "color": 1, "cells": _RING_3},
            {"name": "nine_cell_non_square", "color": 1, "cells": _SIZE_NINE_NON_SQUARE},
            {"name": "solid_3x3_with_tail", "color": 1, "cells": _SOLID_3_WITH_TAIL},
            {"name": "decoration_0", "color": decor_colors[0], "cells": rng.choice(_DECOR_SHAPES)},
            {"name": "decoration_1", "color": decor_colors[1], "cells": rng.choice(_DECOR_SHAPES)},
        ]
    n_targets = 2 + rng.randrange(2)
    return _ordinary_objects(
        n_targets,
        decor_colors,
        rng,
        color_counterexample=profile == "color_counterexample",
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    requested = overrides.get("scene_profile")
    scheduled = requested or schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", [scheduled])
    band_key = "default" if difficulty is None else str(difficulty)
    rng = ctx.draw_rng(f"layout_{profile}_{band_key}")
    side = 12 if profile == "shape_counterexamples" else 11 + rng.randrange(2)
    decor_colors = rng.sample(list(_DECOR_PALETTE), 2)
    items = _profile_objects(profile, decor_colors, rng)
    grid = _render(items, side, rng)

    observed = observe_overrides(grid)["scene_profile"]
    if observed != profile:
        raise RuntimeError(f"rendered profile {profile!r} observed as {observed!r}")
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"rendered profile {profile!r} failed self_check: {errors}")
    return grid


def _components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    parts = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        color = grid[start[0]][start[1]]
        cells = {start}
        todo = [start]
        while todo:
            r, c = todo.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    cells.add(point)
                    todo.append(point)
        parts.append({"color": color, "cells": cells})
    return parts


def _part_facts(part):
    cells = part["cells"]
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return {
        "color": part["color"],
        "size": len(cells),
        "height": max(rows) - min(rows) + 1,
        "width": max(cols) - min(cols) + 1,
    }


def _is_exact_blue_3x3(part):
    facts = _part_facts(part)
    return (
        facts["color"] == 1
        and facts["size"] == 9
        and facts["height"] == 3
        and facts["width"] == 3
    )


def _contains_solid_blue_3x3(grid, part):
    if part["color"] != 1:
        return False
    cells = part["cells"]
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return any(
        {(r + dr, c + dc) for dr in range(3) for dc in range(3)} <= cells
        for r in range(min(rows), max(rows) - 1)
        for c in range(min(cols), max(cols) - 1)
    )


def analyze_grid(grid):
    """Return structural facts; malformed grids report errors instead of raising."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["expected a nonempty rectangular grid"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["expected a nonempty rectangular grid"]}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["ragged grid"]}
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return {"errors": ["cells must be integer ARC colors 0..9, excluding booleans"]}

    parts = _components(grid)
    part_facts = [_part_facts(part) for part in parts]
    blue = [part for part in parts if part["color"] == 1]
    targets = [part for part in blue if _is_exact_blue_3x3(part)]
    decorations = [part for part in parts if part["color"] != 1]
    return {
        "errors": [],
        "height": len(grid),
        "width": width,
        "palette": {value for row in grid for value in row},
        "parts": parts,
        "part_facts": part_facts,
        "blue": blue,
        "targets": targets,
        "blue_distractors": [part for part in blue if not _is_exact_blue_3x3(part)],
        "decorations": decorations,
    }


def self_check(grid, *, difficulty=None, meta=None):
    facts = analyze_grid(grid)
    errors = list(facts["errors"])
    if errors:
        return errors
    if (facts["height"], facts["width"]) not in ((11, 11), (12, 12)):
        errors.append("canvas must be canonical-scale 11x11 or 12x12")
    palette = facts["palette"]
    if len(palette) != 4 or 0 not in palette or 1 not in palette or 3 in palette:
        errors.append("input palette must be exactly {0,1,d1,d2} with distinct non-3 decoration colors")
    if not 6 <= len(facts["parts"]) <= 8:
        errors.append("expected 6..8 same-color components")
    if not 2 <= len(facts["targets"]) <= 3:
        errors.append("expected 2..3 exact solid blue 3x3 targets")
    if not 2 <= len(facts["blue_distractors"]) <= 3:
        errors.append("expected 2..3 blue non-target components")
    if len(facts["decorations"]) != 2:
        errors.append("expected exactly two nonblue decoration components")
    elif len({part["color"] for part in facts["decorations"]}) != 2:
        errors.append("the two decorations must use distinct colors")
    for index, item in enumerate(facts["part_facts"]):
        if item["height"] > 4 or item["width"] > 4 or item["size"] > 12:
            errors.append(f"component {index} exceeds the documented 4x4 / 12-cell grammar")
        if item["color"] == 1 and not 3 <= item["size"] <= 12:
            errors.append(f"blue component {index} has unsupported size {item['size']}")
        if item["color"] != 1 and not 4 <= item["size"] <= 9:
            errors.append(f"decoration component {index} has unsupported size {item['size']}")
    return errors


def strict_canonical_like(grid):
    """The declared manifold includes every canonical input and every generated draw."""
    return self_check(grid)


def _has_hollow_blue_3x3(grid):
    return any(
        item["color"] == 1 and item["height"] == item["width"] == 3 and item["size"] < 9
        for item in analyze_grid(grid).get("part_facts", ())
    )


def _has_blue_nine_cell_non_square(grid):
    return any(
        item["color"] == 1 and item["size"] == 9 and (item["height"], item["width"]) != (3, 3)
        for item in analyze_grid(grid).get("part_facts", ())
    )


def _has_blue_contains_3x3_but_not_exact(grid):
    facts = analyze_grid(grid)
    return any(
        _contains_solid_blue_3x3(grid, part) and not _is_exact_blue_3x3(part)
        for part in facts.get("blue", ())
    )


def _has_nonblue_exact_3x3(grid):
    return any(
        item["color"] != 1 and (item["size"], item["height"], item["width"]) == (9, 3, 3)
        for item in analyze_grid(grid).get("part_facts", ())
    )


def _has_blue_non_target(grid):
    return bool(analyze_grid(grid).get("blue_distractors"))


def observe_overrides(grid):
    if _has_nonblue_exact_3x3(grid):
        profile = "color_counterexample"
    elif (
        _has_hollow_blue_3x3(grid)
        and _has_blue_nine_cell_non_square(grid)
        and _has_blue_contains_3x3_but_not_exact(grid)
    ):
        profile = "shape_counterexamples"
    else:
        profile = "canonical_mix"
    return {"scene_profile": profile}


def _paint_matching(grid, predicate):
    out = deepcopy(grid)
    for part in _components(grid):
        if predicate(grid, part):
            for r, c in part["cells"]:
                out[r][c] = 3
    return out


def rule_mirror(grid):
    """Independent Python cross-check; the canonical Racket source remains authority."""
    return _paint_matching(grid, lambda _grid, part: _is_exact_blue_3x3(part))


def _rival_blue_size_nine(grid):
    return _paint_matching(
        grid,
        lambda _grid, part: part["color"] == 1 and len(part["cells"]) == 9,
    )


def _rival_blue_bbox_3x3(grid):
    return _paint_matching(
        grid,
        lambda _grid, part: part["color"] == 1
        and (_part_facts(part)["height"], _part_facts(part)["width"]) == (3, 3),
    )


def _rival_contains_solid_3x3(grid):
    return _paint_matching(grid, _contains_solid_blue_3x3)


def _rival_any_color_exact_3x3(grid):
    return _paint_matching(
        grid,
        lambda _grid, part: (
            (_part_facts(part)["size"], _part_facts(part)["height"], _part_facts(part)["width"])
            == (9, 3, 3)
        ),
    )


def _rival_all_blue_components(grid):
    return _paint_matching(grid, lambda _grid, part: part["color"] == 1)


# Deliberately wrong candidate programs used only to test lesson identifiability.
SEMANTIC_RIVALS = {
    "blue_size_nine": _rival_blue_size_nine,
    "blue_bbox_3x3": _rival_blue_bbox_3x3,
    "contains_solid_3x3": _rival_contains_solid_3x3,
    "any_color_exact_3x3": _rival_any_color_exact_3x3,
    "all_blue_components": _rival_all_blue_components,
}
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in ("blue_size_nine", "blue_bbox_3x3", "any_color_exact_3x3")
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "hollow_blue_3x3": _has_hollow_blue_3x3,
    "blue_nine_cell_non_square": _has_blue_nine_cell_non_square,
    "blue_contains_3x3_but_not_exact": _has_blue_contains_3x3_but_not_exact,
    "nonblue_exact_3x3": _has_nonblue_exact_3x3,
    "blue_non_target": _has_blue_non_target,
}
WITNESS_RIVALS = {
    "hollow_blue_3x3": ["blue_bbox_3x3"],
    "blue_nine_cell_non_square": ["blue_size_nine"],
    "blue_contains_3x3_but_not_exact": ["contains_solid_3x3"],
    "nonblue_exact_3x3": ["any_color_exact_3x3"],
    "blue_non_target": ["all_blue_components"],
}


def lesson_identifiable(demos, query):
    """Check labels and eliminate the finite declared rival set using demos only."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    errors = []
    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            errors.append(f"demonstration {index} must contain input and output")
            continue
        grid = demo["input"]
        expected = rule_mirror(grid)
        if expected != demo["output"]:
            errors.append(f"demonstration {index} label disagrees with the rule")
        valid_demos.append(demo)
    if errors:
        return errors
    return [
        f"surviving declared rival: {name}"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(demo["input"]) == demo["output"] for demo in valid_demos)
    ]


def mutation_fixtures():
    """Named malformed cases for task-local and generic mutation audits."""
    base = generate(7011, 4, difficulty="medium", scene_profile="canonical_mix")
    yield "blank", [[0 for _ in row] for row in base]
    ragged = deepcopy(base)
    ragged[-1].pop()
    yield "ragged", ragged
    output_color = deepcopy(base)
    output_color[0][0] = 3
    yield "output_color_in_input", output_color
    missing_decor = deepcopy(base)
    decor = next(part for part in _components(missing_decor) if part["color"] != 1)
    for r, c in decor["cells"]:
        missing_decor[r][c] = 0
    yield "missing_decoration", missing_decor
    damaged_targets = deepcopy(base)
    for part in [part for part in _components(damaged_targets) if _is_exact_blue_3x3(part)]:
        r, c = min(part["cells"])
        damaged_targets[r][c] = 0
    yield "damaged_targets", damaged_targets
