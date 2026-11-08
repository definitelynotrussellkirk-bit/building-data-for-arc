"""Semantic generator for ARC task 8b6a2892a064.

Every 4-connected non-orange component is a straight odd-length line (or a
singleton).  Rotate each line 90 degrees around its integer center, preserve
its color, and rebuild the rest of the canvas as orange 7.
"""
from __future__ import annotations

from collections import Counter
from puzzle_generators.base import gen_ctx

GENERATOR_ID = "8b6a2892a064"
TASK_ID = GENERATOR_ID
VERSION = "4.1.0"
# Validation/authoring repairs must preserve valid deterministic input draws.
SAMPLING_VERSION = "4.0.0"
RULE_HASH = "83a9329e575d"
SUMMARY = "Rotate each isolated straight odd-length component 90 degrees around its center on an orange canvas."
INVARIANTS = [
    "background is literal orange 7",
    "all foreground cells share one non-orange color",
    "each foreground component is a contiguous horizontal line, vertical line, or singleton",
    "line lengths are odd so their rotation centers are integral",
]

PUBLIC_PROFILES = (
    "public_train_1", "public_train_2", "public_train_3", "public_test_1",
)
GENERAL_BLUEPRINTS = {
    "two_mixed": (("h", 3), ("v", 5)),
    "three_mixed": (("s", 1), ("h", 3), ("v", 5)),
    "five_equal": (("h", 3), ("h", 3), ("h", 3), ("v", 3), ("v", 3)),
    "five_varied": (("s", 1), ("h", 5), ("v", 3), ("v", 3), ("v", 5)),
    "six_long": (("h", 5), ("h", 5), ("h", 5), ("v", 5), ("v", 5), ("v", 5)),
    "seven_varied": (("s", 1), ("h", 3), ("h", 3), ("h", 5), ("h", 5), ("v", 3), ("v", 7)),
    "eight_varied": (("s", 1), ("h", 3), ("h", 5), ("h", 7), ("h", 9), ("v", 3), ("v", 5), ("v", 7)),
    "ten_dense": (("s", 1), ("h", 3), ("h", 3), ("h", 3), ("h", 5), ("h", 5), ("h", 9), ("v", 3), ("v", 3), ("v", 5)),
}
GENERAL_PROFILES = tuple(GENERAL_BLUEPRINTS)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted exact-public and generalized line-blueprint lessons",
        "valid": "public_train_1|public_train_2|public_train_3|public_test_1|two_mixed|three_mixed|five_equal|five_varied|six_long|seven_varied|eight_varied|ten_dense",
    }
}

_PUBLIC_ROWS = {
    "public_train_1": (
        "757777777", "757775777", "757577777", "777577577", "777577577",
        "777777577", "555557577", "777777577", "777777777",
    ),
    "public_train_2": (
        "777777777", "772227277", "777777277", "772777277", "772777777",
        "772777777", "777772227", "722277777", "777777777",
    ),
    "public_train_3": (
        "77777777777", "77777777777", "78777888887", "78787777777",
        "78777787777", "77777787888", "77777787777", "77777787777",
        "88888787777", "77777787888", "77777787777",
    ),
    "public_test_1": (
        "7777777777777", "7777777777777", "9999977999997", "7777777777777",
        "7777777777999", "9999999997777", "7777777779777", "7777779779777",
        "7777977779777", "7777977777777", "9997977797777", "7777977797999",
        "7777977797777",
    ),
}
_PUBLIC_INPUTS = {
    name: [[int(value) for value in row] for row in rows]
    for name, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_SIGNATURES = {
    tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()
}


def _blueprint_signature(blueprint):
    return tuple(sorted(Counter(blueprint).items()))


_SIGNATURE_TO_PROFILE = {
    _blueprint_signature(blueprint): name
    for name, blueprint in GENERAL_BLUEPRINTS.items()
}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must be within 1..30"]
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["cells must be ARC colors"]
    return []


def _components(cells):
    remaining = set(cells)
    result = []
    while remaining:
        todo = [min(remaining)]
        component = set()
        while todo:
            cell = todo.pop()
            if cell not in remaining:
                continue
            remaining.remove(cell)
            component.add(cell)
            r, c = cell
            todo.extend(((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
        result.append(component)
    return sorted(result, key=lambda component: min(component))


def _component_descriptor(component):
    rows = sorted({r for r, _ in component})
    cols = sorted({c for _, c in component})
    if len(component) == 1:
        orientation = "s"
    elif len(rows) == 1 and cols == list(range(cols[0], cols[-1] + 1)):
        orientation = "h"
    elif len(cols) == 1 and rows == list(range(rows[0], rows[-1] + 1)):
        orientation = "v"
    else:
        return None
    return orientation, len(component), rows, cols


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    h, w = len(grid), len(grid[0])
    foreground_colors = {value for row in grid for value in row if value != 7}
    if len(foreground_colors) != 1:
        errors.append(f"expected exactly one foreground color, found {sorted(foreground_colors)}")
        return result
    color = next(iter(foreground_colors))
    foreground = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 7}
    components = _components(foreground)
    descriptors = []
    for component in components:
        descriptor = _component_descriptor(component)
        if descriptor is None:
            errors.append("every foreground component must be a contiguous straight line or singleton")
            return result
        orientation, length, rows, cols = descriptor
        if length % 2 == 0:
            errors.append("line components must have odd length")
        if any(grid[r][c] != color for r, c in component):
            errors.append("every foreground component must share one color")
        descriptors.append({
            "cells": component, "orientation": orientation, "length": length,
            "rows": rows, "cols": cols,
        })

    output = [[7] * w for _ in range(h)]
    for descriptor in descriptors:
        orientation, length = descriptor["orientation"], descriptor["length"]
        rows, cols = descriptor["rows"], descriptor["cols"]
        if orientation == "s":
            output[rows[0]][cols[0]] = color
        elif orientation == "h":
            center_r, center_c, half = rows[0], (cols[0] + cols[-1]) // 2, (length - 1) // 2
            for r in range(center_r - half, center_r + half + 1):
                if 0 <= r < h:
                    output[r][center_c] = color
        else:
            center_r, center_c, half = (rows[0] + rows[-1]) // 2, cols[0], (length - 1) // 2
            for c in range(center_c - half, center_c + half + 1):
                if 0 <= c < w:
                    output[center_r][c] = color

    signature = _blueprint_signature(
        tuple((descriptor["orientation"], descriptor["length"]) for descriptor in descriptors)
    )
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if profile is None and not errors:
        profile = _SIGNATURE_TO_PROFILE.get(signature)
    if profile not in SCENE_PROFILES:
        errors.append(f"component blueprint {signature!r} does not match a declared profile")
    result.update({
        "foreground_color": color,
        "components": components,
        "descriptors": descriptors,
        "component_count": len(components),
        "blueprint_signature": signature,
        "output": output,
        "scene_profile": profile,
        "errors": errors,
    })
    return result


def canonical_profile_signature(grid):
    analysis = _analysis(grid)
    profile = analysis.get("scene_profile")
    return profile if not analysis["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def rule_mirror(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["output"]]


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _line_cells(orientation, length, center_r, center_c):
    half = length // 2
    if orientation == "s":
        return {(center_r, center_c)}
    if orientation == "h":
        return {(center_r, center_c + offset) for offset in range(-half, half + 1)}
    return {(center_r + offset, center_c) for offset in range(-half, half + 1)}


def _isolated(candidate, occupied):
    for r, c in candidate:
        if (r, c) in occupied:
            return False
        if any(neighbor in occupied for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))):
            return False
    return True


def _general(rng, profile, band):
    blueprint = GENERAL_BLUEPRINTS[profile]
    max_length = max(length for _, length in blueprint)
    minimum = max(9, max_length + 2, 8 + (len(blueprint) + 1) // 2)
    offsets = {"easy": (0, 2), "medium": (2, 5), "hard": (5, 8)}[band]
    foreground_color = rng.choice((0, 1, 2, 3, 4, 5, 6, 8, 9))
    for _ in range(200):
        h = min(30, minimum + rng.randint(*offsets))
        w = min(30, minimum + rng.randint(*offsets))
        occupied = set()
        placements = []
        success = True
        specs = list(blueprint)
        rng.shuffle(specs)
        for orientation, length in specs:
            half = length // 2
            candidates = [
                (r, c) for r in range(half, h - half) for c in range(half, w - half)
            ]
            rng.shuffle(candidates)
            for center_r, center_c in candidates:
                cells = _line_cells(orientation, length, center_r, center_c)
                if _isolated(cells, occupied):
                    occupied.update(cells)
                    placements.append(cells)
                    break
            else:
                success = False
                break
        if success:
            grid = [[7] * w for _ in range(h)]
            for cells in placements:
                for r, c in cells:
                    grid[r][c] = foreground_color
            return grid
    raise ValueError(f"could not place isolated line blueprint {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer, excluding booleans")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer, excluding booleans")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed, sample_index=sample_index, version=SAMPLING_VERSION, task_id=TASK_ID,
        difficulty=band, overrides=overrides,
    )
    weighted = list(PUBLIC_PROFILES) + [profile for profile in GENERAL_PROFILES for _ in range(3)]
    profile = ctx.draw_choice("scene_profile", weighted)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general(ctx.draw_rng("layout"), profile, band)


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])


# Finite authoring checks. These rivals do not define or replace the Racket rule.
EXAMPLES_NEEDED = 3


def strict_canonical_like(grid):
    """The task domain is isolated, single-color, straight odd-length lines."""
    return self_check(grid)


def _partial_turn(grid, orientations=("h", "v"), min_length=1):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    height, width = len(grid), len(grid[0])
    output = [[7] * width for _ in range(height)]
    for descriptor in analysis["descriptors"]:
        orientation, length = descriptor["orientation"], descriptor["length"]
        cells = descriptor["cells"]
        if orientation in orientations and length >= min_length:
            rows, cols = descriptor["rows"], descriptor["cols"]
            cr, cc = (rows[0] + rows[-1]) // 2, (cols[0] + cols[-1]) // 2
            cells = {(cr + cc - c, cc + r - cr) for r, c in cells}
        for r, c in cells:
            if 0 <= r < height and 0 <= c < width:
                output[r][c] = analysis["foreground_color"]
    return output


def _identity(grid):
    return [list(row) for row in grid]


def _horizontal_only(grid):
    return _partial_turn(grid, ("h",))


def _vertical_only(grid):
    return _partial_turn(grid, ("v",))


def _skip_short_lines(grid):
    return _partial_turn(grid, min_length=5)


LESSON_COMPETITORS = {
    "identity": _identity,
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
    "skip_short_lines": _skip_short_lines,
}
SEMANTIC_RIVALS = LESSON_COMPETITORS


def _horizontal_turn_witness(grid):
    return rule_mirror(grid) != _vertical_only(grid)


def _vertical_turn_witness(grid):
    return rule_mirror(grid) != _horizontal_only(grid)


def _short_line_turn_witness(grid):
    return rule_mirror(grid) != _skip_short_lines(grid)


SEMANTIC_WITNESSES = {
    "horizontal_turn": _horizontal_turn_witness,
    "vertical_turn": _vertical_turn_witness,
    "short_line_turn": _short_line_turn_witness,
}
WITNESS_RIVALS = {
    "horizontal_turn": ["vertical_only"],
    "vertical_turn": ["horizontal_only"],
    "short_line_turn": ["skip_short_lines"],
}
