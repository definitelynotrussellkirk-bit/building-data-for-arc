"""Semantic generator for ARC task 22d1f016cb3d.

Every color-5 cell is classified from its four cardinal neighbors.  It becomes
2 when it has color 5 on both horizontal and both vertical sides, 1 when it
has neither an opposing horizontal pair nor an opposing vertical pair, and 4
otherwise.  Every non-5 cell is preserved exactly.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "22d1f016cb3d"
TASK_ID = "22d1f016cb3d"
VERSION = "3.0.0"
RULE_HASH = "2219db85ca5f"
SUMMARY = "Recolor each 5 from its opposing cardinal-neighbor pairs: interior=2, corner/end=1, and edge=4; preserve every non-5 cell."
INVARIANTS = [
    "only color-5 cells change",
    "a 5 with both horizontal and vertical opposing 5-neighbor pairs becomes 2",
    "a 5 with neither opposing pair becomes 1",
    "every other 5 becomes 4",
    "generated inputs reserve colors 1, 2, and 4 for the output",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3")
GENERAL_PROFILES = (
    "single_rectangle",
    "two_rectangles",
    "many_rectangles",
    "border_rectangles",
    "thin_rectangles",
    "hollow_frame",
    "punctured_rectangle",
    "orthogonal_shape",
    "mixed_shapes",
    "decoy_colors",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "three exact-public and ten generalized local-neighbor lessons",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = (
    "5555550000/5555550000/5555550000/5555550000/5555550000/0000000000/0000555555/0000555555/0000555555/0000555555",
    "0000000000/0000000000/0555500000/0555500000/0555500000/0555505555/0000005555/0000005555/0000005555/0000005555",
    "0555500000/0555500000/0555500000/0555500000/0555500000/0555500000/0000000000/0000555555/0000555555/0000555555",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 3 <= len(grid) <= 30 or not 3 <= width <= 30:
        return ["grid dimensions must be within 3..30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal ARC integers 0..9"]
    return []


def rule_mirror(grid):
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 5:
                continue
            horizontal = col > 0 and col + 1 < width and grid[row][col - 1] == grid[row][col + 1] == 5
            vertical = row > 0 and row + 1 < height and grid[row - 1][col] == grid[row + 1][col] == 5
            output[row][col] = 2 if horizontal and vertical else 1 if not horizontal and not vertical else 4
    return output


def _components(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(row, col) for row in range(height) for col in range(width) if grid[row][col] == 5}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue, cells = deque([start]), []
        while queue:
            row, col = queue.popleft()
            cells.append((row, col))
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(cells))
    return sorted(components, key=lambda cells: cells[0])


def _component_facts(cells, height, width):
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    box_h, box_w = bottom - top + 1, right - left + 1
    cell_set = set(cells)
    box = {(row, col) for row in range(top, bottom + 1) for col in range(left, right + 1)}
    perimeter = {
        (row, col)
        for row, col in box
        if row in {top, bottom} or col in {left, right}
    }
    missing = sorted(box - cell_set)
    return {
        "cells": cells,
        "size": len(cells),
        "bbox": (top, left, box_h, box_w),
        "solid": cell_set == box,
        "hollow": box_h >= 4 and box_w >= 4 and cell_set == perimeter,
        "punctured": len(missing) == 1 and top < missing[0][0] < bottom and left < missing[0][1] < right,
        "thin": box_h <= 2 or box_w <= 2,
        "touches_border": top == 0 or left == 0 or bottom == height - 1 or right == width - 1,
    }


def _profile_for(grid, facts):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    if facts["decoy_count"]:
        return "decoy_colors"
    components = facts["components"]
    irregular = [component for component in components if not component["solid"]]
    if len(components) >= 2 and irregular:
        return "mixed_shapes"
    if len(components) == 1 and irregular:
        component = components[0]
        if component["hollow"]:
            return "hollow_frame"
        if component["punctured"]:
            return "punctured_rectangle"
        return "orthogonal_shape"
    if not components or irregular:
        return None
    if any(component["thin"] for component in components):
        return "thin_rectangles"
    if any(component["touches_border"] for component in components):
        return "border_rectangles"
    if len(components) == 1:
        return "single_rectangle"
    if len(components) == 2:
        return "two_rectangles"
    return "many_rectangles" if 3 <= len(components) <= 5 else None


def _extract_facts(grid):
    height, width = len(grid), len(grid[0])
    components = [_component_facts(cells, height, width) for cells in _components(grid)]
    output = rule_mirror(grid)
    counts = {color: sum(value == color for row in output for value in row) for color in (1, 2, 4)}
    facts = {
        "height": height,
        "width": width,
        "components": components,
        "component_count": len(components),
        "decoy_count": sum(value not in {0, 5} for row in grid for value in row),
        "output_counts": counts,
        "output": output,
    }
    facts["scene_profile"] = _profile_for(grid, facts)
    return facts


def _profile_errors(facts):
    profile = facts["scene_profile"]
    components = facts["components"]
    errors = []
    if profile in PUBLIC_PROFILES:
        return errors
    if profile == "single_rectangle":
        if len(components) != 1 or min(components[0]["bbox"][2:]) < 3:
            errors.append("single_rectangle requires one solid rectangle with both sides at least 3")
    elif profile == "two_rectangles":
        if len(components) != 2 or any(min(component["bbox"][2:]) < 3 for component in components):
            errors.append("two_rectangles requires two solid rectangles with both sides at least 3")
    elif profile == "many_rectangles":
        if not 3 <= len(components) <= 5 or any(min(component["bbox"][2:]) < 3 for component in components):
            errors.append("many_rectangles requires three to five substantial solid rectangles")
    elif profile == "border_rectangles":
        if len(components) != 2 or any(min(component["bbox"][2:]) < 3 for component in components):
            errors.append("border_rectangles requires two substantial edge-touching rectangles")
    elif profile == "thin_rectangles":
        if len(components) != 1 or components[0]["size"] < 5 or max(components[0]["bbox"][2:]) < 5:
            errors.append("thin_rectangles requires one intentional length-five-or-more bar")
    elif profile == "hollow_frame":
        if len(components) != 1 or min(components[0]["bbox"][2:]) < 5:
            errors.append("hollow_frame requires one frame with both sides at least 5")
    elif profile == "punctured_rectangle":
        if len(components) != 1 or min(components[0]["bbox"][2:]) < 5:
            errors.append("punctured_rectangle requires one substantial block with one interior hole")
    elif profile == "orthogonal_shape":
        if len(components) != 1 or components[0]["size"] < 9 or min(components[0]["bbox"][2:]) < 5:
            errors.append("orthogonal_shape requires one substantial L, T, or plus lesson")
    elif profile == "mixed_shapes":
        if len(components) != 2 or not any(component["solid"] for component in components) or not any(not component["solid"] and component["size"] >= 9 for component in components):
            errors.append("mixed_shapes requires one solid rectangle and one substantial orthogonal shape")
    elif profile == "decoy_colors":
        if len(components) != 1 or not components[0]["solid"] or min(components[0]["bbox"][2:]) < 3 or not 1 <= facts["decoy_count"] <= 5:
            errors.append("decoy_colors requires one substantial solid rectangle and one to five decoys")
    return errors


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "facts": None, "scene_profile": None, "output": None}
    facts = _extract_facts(grid)
    if not facts["components"]:
        errors.append("input must contain color 5")
    if any(value in {1, 2, 4} for row in grid for value in row):
        errors.append("generated input must reserve output colors 1, 2, and 4")
    if facts["scene_profile"] not in SCENE_PROFILES:
        errors.append("grid does not match a declared scene profile")
    else:
        errors.extend(_profile_errors(facts))
    if not facts["output_counts"][1]:
        errors.append("scene must witness at least one corner/end classification")
    return {"errors": errors, "facts": facts, "scene_profile": facts["scene_profile"], "output": facts["output"]}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _size_range(difficulty):
    if difficulty == "easy":
        return (8, 12), (8, 12)
    if difficulty == "medium":
        return (10, 16), (10, 16)
    if difficulty == "hard":
        return (13, 21), (13, 21)
    return (9, 17), (9, 17)


def _blank(height, width):
    return [[0 for _ in range(width)] for _ in range(height)]


def _paint_rect(grid, top, left, height, width, color=5):
    for row in range(top, top + height):
        for col in range(left, left + width):
            grid[row][col] = color


def _interior_rectangle(grid, rng, *, low=3, high=8):
    height, width = len(grid), len(grid[0])
    rect_h = rng.randint(low, min(high, height - 2))
    rect_w = rng.randint(low, min(high, width - 2))
    top = rng.randint(1, height - rect_h - 1)
    left = rng.randint(1, width - rect_w - 1)
    _paint_rect(grid, top, left, rect_h, rect_w)


def _orthogonal_shape(grid, rng, *, top, left, box_h=6, box_w=6):
    kind = rng.choice(("l", "t", "plus"))
    if kind == "l":
        for row in range(top, top + box_h):
            grid[row][left] = 5
        for col in range(left, left + box_w):
            grid[top + box_h - 1][col] = 5
    elif kind == "t":
        for col in range(left, left + box_w):
            grid[top][col] = 5
        center = left + box_w // 2
        for row in range(top, top + box_h):
            grid[row][center] = 5
    else:
        center_row, center_col = top + box_h // 2, left + box_w // 2
        for col in range(left, left + box_w):
            grid[center_row][col] = 5
        for row in range(top, top + box_h):
            grid[row][center_col] = 5


def _general_scene(difficulty, profile, rng):
    (h_low, h_high), (w_low, w_high) = _size_range(difficulty)
    height, width = rng.randint(h_low, h_high), rng.randint(w_low, w_high)
    if profile in {"two_rectangles", "border_rectangles"}:
        height, width = max(height, 11), max(width, 11)
    elif profile in {"many_rectangles", "mixed_shapes"}:
        height, width = max(height, 14), max(width, 14)
    else:
        height, width = max(height, 9), max(width, 9)
    grid = _blank(height, width)

    if profile == "single_rectangle":
        _interior_rectangle(grid, rng)
    elif profile == "two_rectangles":
        first_h, first_w = rng.randint(3, 4), rng.randint(3, 4)
        second_h, second_w = rng.randint(3, 4), rng.randint(3, 4)
        _paint_rect(grid, 1, 1, first_h, first_w)
        _paint_rect(grid, height - second_h - 1, width - second_w - 1, second_h, second_w)
    elif profile == "many_rectangles":
        positions = ((1, 1), (1, width - 5), (height - 5, 1), (height - 5, width - 5))
        for top, left in positions[:rng.choice((3, 4))]:
            _paint_rect(grid, top, left, rng.choice((3, 4)), rng.choice((3, 4)))
    elif profile == "border_rectangles":
        _paint_rect(grid, 0, 1, rng.choice((3, 4)), 3)
        second_h = rng.choice((3, 4))
        _paint_rect(grid, height - second_h, width - 3, second_h, 3)
    elif profile == "thin_rectangles":
        if rng.choice((True, False)):
            rect_h, rect_w = rng.choice((1, 2)), rng.randint(5, min(8, width - 2))
        else:
            rect_h, rect_w = rng.randint(5, min(8, height - 2)), rng.choice((1, 2))
        top = rng.randint(1, height - rect_h - 1)
        left = rng.randint(1, width - rect_w - 1)
        _paint_rect(grid, top, left, rect_h, rect_w)
    elif profile == "hollow_frame":
        box_h, box_w = rng.randint(5, min(8, height - 2)), rng.randint(5, min(8, width - 2))
        top, left = rng.randint(1, height - box_h - 1), rng.randint(1, width - box_w - 1)
        for row in range(top, top + box_h):
            for col in range(left, left + box_w):
                if row in {top, top + box_h - 1} or col in {left, left + box_w - 1}:
                    grid[row][col] = 5
    elif profile == "punctured_rectangle":
        box_h, box_w = rng.randint(5, min(8, height - 2)), rng.randint(5, min(8, width - 2))
        top, left = rng.randint(1, height - box_h - 1), rng.randint(1, width - box_w - 1)
        _paint_rect(grid, top, left, box_h, box_w)
        grid[top + box_h // 2][left + box_w // 2] = 0
    elif profile == "orthogonal_shape":
        _orthogonal_shape(grid, rng, top=1, left=1)
    elif profile == "mixed_shapes":
        _paint_rect(grid, 1, 1, 4, 5)
        _orthogonal_shape(grid, rng, top=height - 7, left=width - 7)
    elif profile == "decoy_colors":
        _interior_rectangle(grid, rng)
        available = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == 0]
        rng.shuffle(available)
        for (row, col), color in zip(available, rng.sample([3, 6, 7, 8, 9], rng.randint(1, 5))):
            grid[row][col] = color
    else:
        raise ValueError(f"unknown scene_profile: {profile!r}")

    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError(f"invalid {profile}: {analysis['errors']} / {analysis['scene_profile']}")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES + GENERAL_PROFILES * 4)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(difficulty, profile, ctx.draw_rng("geometry"))
