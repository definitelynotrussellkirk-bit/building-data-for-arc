"""Semantic generator for ARC task e2eab62ba331.

Use the top-left cell as a selector color, find the first remote object of
that color, and return the original grid's tight bounding-box subgrid around
that object.  Other colors inside that box are therefore preserved.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "e2eab62ba331"
TASK_ID = "e2eab62ba331"
VERSION = "3.0.0"
RULE_HASH = "a06ec2fdb2eb"
SUMMARY = "Select the remote object matching the top-left color and return its original tight bounding-box subgrid."
INVARIANTS = [
    "the literal-zero background and a nonzero selector at (0,0) are present",
    "exactly one remote monochrome 4-connected object matches the selector color",
    "the selector's own component contains (0,0) and is excluded from selection",
    "the selected object's tight bounding box determines output dimensions",
    "the output is the original subgrid, preserving zeros and any other colors inside the box",
    "unselected objects outside the selected bounding box do not affect the output",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 6))
GENERAL_PROFILES = (
    "hollow_ring",
    "concave_c",
    "staircase",
    "irregular_polyomino",
    "extended_selector",
    "interior_distractor",
    "target_touches_edge",
    "many_distractors",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five exact-public and eight observable selector-crop lessons",
        "valid": "public_1|public_2|public_3|public_4|public_5|hollow_ring|concave_c|staircase|irregular_polyomino|extended_selector|interior_distractor|target_touches_edge|many_distractors",
    }
}

_COLORS = tuple(range(1, 10))
_PUBLIC_ROWS = {
    "public_1": "400000000/000000770/004000077/004000000/004400000/000000000/000002200/000002200/000000000",
    "public_2": "7000000000/0000000200/0333000200/0300000200/0300000000/0000007770/0000000700/0000000700/0000000000/0000000000",
    "public_3": "2000000000/0000000800/0022000800/0002200880/0000000000/0000006600/0000006600/0000006000/0000000000",
    "public_4": "800000000/022000000/000008000/000008880/000000080/000000000/044400000/040400000/044400000/000000000",
    "public_5": "60000000000/00000000000/00606003300/00606000330/00666000000/00000000000/00000000000/00090000000/00090000000/00099000000/00000000000",
}


def _decode(rows):
    return [[int(value) for value in row] for row in rows.split("/")]


_PUBLIC_INPUTS = {name: _decode(rows) for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append({"color": color, "cells": set(cells)})
    return components


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _normalized(cells):
    row0, col0, _, _ = _bbox(cells)
    return {(row - row0, col - col0) for row, col in cells}


def _holes(cells):
    row0, col0, row1, col1 = _bbox(cells)
    empty = {(row, col) for row in range(row0, row1 + 1) for col in range(col0, col1 + 1) if (row, col) not in cells}
    outside = set()
    stack = [cell for cell in empty if cell[0] in (row0, row1) or cell[1] in (col0, col1)]
    while stack:
        cell = stack.pop()
        if cell in outside or cell not in empty:
            continue
        outside.add(cell)
        row, col = cell
        stack.extend((row + dr, col + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
    return empty - outside


def _shape_kind(cells):
    normalized = _normalized(cells)
    row0, col0, row1, col1 = _bbox(normalized)
    height, width = row1 + 1, col1 + 1
    full = {(row, col) for row in range(height) for col in range(width)}
    if height == 1 and width >= 3 and normalized == full:
        return "horizontal_line"
    if width == 1 and height >= 3 and normalized == full:
        return "vertical_line"
    if height >= 2 and width >= 2 and normalized == full:
        return "solid_rectangle"
    border = {(row, col) for row in range(height) for col in range(width) if row in (0, height - 1) or col in (0, width - 1)}
    if height >= 3 and width >= 3 and normalized == border:
        return "hollow_ring"
    c_shape = {(row, 0) for row in range(height)} | {(0, col) for col in range(width)} | {(height - 1, col) for col in range(width)}
    if height >= 3 and width >= 3 and normalized == c_shape:
        return "concave_c"
    stair = {(index, index) for index in range(min(height, width))} | {(index, index + 1) for index in range(min(height, width)) if index + 1 < width}
    if height >= 3 and width == height + 1 and normalized == stair:
        return "staircase"
    return None


def _rule_facts(grid):
    components = _components(grid)
    target = grid[0][0]
    anchor = next((obj for obj in components if (0, 0) in obj["cells"]), None)
    choices = [obj for obj in components if obj["color"] == target and (0, 0) not in obj["cells"]]
    selected = choices[0] if choices else None
    if selected is None:
        output = [[0]]
        box = None
        interior_other = set()
    else:
        box = _bbox(selected["cells"])
        row0, col0, row1, col1 = box
        output = [list(row[col0:col1 + 1]) for row in grid[row0:row1 + 1]]
        interior_other = {
            (row, col)
            for row in range(row0, row1 + 1)
            for col in range(col0, col1 + 1)
            if grid[row][col] not in (0, target)
        }
    other_objects = [obj for obj in components if obj is not anchor and obj is not selected]
    return {
        "target": target,
        "objects": components,
        "anchor": anchor,
        "choices": choices,
        "selected": selected,
        "bbox": box,
        "output": output,
        "interior_other": interior_other,
        "other_objects": other_objects,
        "shape_kind": _shape_kind(selected["cells"]) if selected else None,
        "holes": _holes(selected["cells"]) if selected else set(),
    }


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _rule_facts(grid)["output"]


def _general_profile(facts, height, width):
    anchor_size = len(facts["anchor"]["cells"])
    if anchor_size > 1:
        return "extended_selector"
    if facts["interior_other"]:
        return "interior_distractor"
    row0, col0, row1, col1 = facts["bbox"]
    if row0 == 0 or col0 == 0 or row1 == height - 1 or col1 == width - 1:
        return "target_touches_edge"
    if len(facts["other_objects"]) >= 4:
        return "many_distractors"
    return facts["shape_kind"] or "irregular_polyomino"


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    height, width = len(grid), len(grid[0])
    if height < 6 or width < 6:
        errors.append("expected both dimensions to be at least six")
    if grid[0][0] == 0:
        errors.append("expected a nonzero selector at (0,0)")
    if not any(value == 0 for row in grid for value in row):
        errors.append("expected literal-zero background")
    facts = _rule_facts(grid) if not errors else None
    if facts is not None:
        if facts["anchor"] is None:
            errors.append("selector component must contain (0,0)")
        if len(facts["choices"]) != 1:
            errors.append(f"expected exactly one remote selector-colored object, found {len(facts['choices'])}")
        if not facts["other_objects"]:
            errors.append("expected at least one distractor object")
        if len({value for row in facts["output"] for value in row}) < 2:
            errors.append("selected crop must contain at least two cell values")
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    profile = public
    if not errors and not public:
        profile = _general_profile(facts, height, width)
        if profile not in GENERAL_PROFILES:
            errors.append("scene does not match a declared selector-crop profile")
    result.update({"facts": facts, "output": facts["output"] if facts else None, "scene_profile": profile, "errors": errors})
    return result


def self_check(grid, *, difficulty=None, meta=None):
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    requested = ((meta or {}).get("overrides") or {}).get("scene_profile")
    if requested and analysis["scene_profile"] != requested:
        errors.append(f"scene profile drifted from {requested} to {analysis['scene_profile']}")
    return errors


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _dimensions(difficulty, rng):
    ranges = {None: (10, 16), "easy": (8, 12), "medium": (10, 16), "hard": (14, 20)}
    low, high = ranges[difficulty]
    return rng.randint(low, high), rng.randint(low, high)


def _polyomino(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        row, col = rng.choice(tuple(cells))
        dr, dc = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
        cells.add((row + dr, col + dc))
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return {(row - min_row, col - min_col) for row, col in cells}


def _shape(profile, rng):
    if profile == "solid_rectangle":
        height, width = rng.randint(2, 4), rng.randint(2, 5)
        return {(row, col) for row in range(height) for col in range(width)}
    if profile == "horizontal_line":
        return {(0, col) for col in range(rng.randint(4, 8))}
    if profile == "vertical_line":
        return {(row, 0) for row in range(rng.randint(4, 8))}
    if profile in ("hollow_ring", "interior_distractor"):
        height = width = 5 if profile == "interior_distractor" else rng.randint(3, 5)
        return {(row, col) for row in range(height) for col in range(width) if row in (0, height - 1) or col in (0, width - 1)}
    if profile == "concave_c":
        height, width = rng.randint(3, 5), rng.randint(3, 5)
        return {(row, 0) for row in range(height)} | {(0, col) for col in range(width)} | {(height - 1, col) for col in range(width)}
    if profile == "staircase":
        size = rng.randint(3, 5)
        return {(index, index) for index in range(size)} | {(index, index + 1) for index in range(size)}
    return _polyomino(rng, rng.randint(6, 16))


def _can_place(grid, cells, row0, col0, *, allow_edge=False):
    height, width = len(grid), len(grid[0])
    absolute = {(row0 + row, col0 + col) for row, col in cells}
    if any(not (0 <= row < height and 0 <= col < width) for row, col in absolute):
        return False
    if not allow_edge and any(row in (0, height - 1) or col in (0, width - 1) for row, col in absolute):
        return False
    return all(
        grid[row + dr][col + dc] == 0
        for row, col in absolute
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if 0 <= row + dr < height and 0 <= col + dc < width
    )


def _place_random(grid, cells, color, rng, *, edge=None):
    height, width = len(grid), len(grid[0])
    shape_h = max(row for row, _ in cells) + 1
    shape_w = max(col for _, col in cells) + 1
    origins = [(row, col) for row in range(height - shape_h + 1) for col in range(width - shape_w + 1)]
    rng.shuffle(origins)
    if edge == "bottom":
        origins.sort(key=lambda origin: origin[0] != height - shape_h)
    for row0, col0 in origins:
        allow_edge = edge is not None
        if edge == "bottom" and row0 != height - shape_h:
            continue
        if _can_place(grid, cells, row0, col0, allow_edge=allow_edge):
            for row, col in cells:
                grid[row0 + row][col0 + col] = color
            return row0, col0
    return None


def _general_scene(ctx, profile):
    rng = ctx.draw_rng("geometry")
    for _ in range(300):
        height, width = _dimensions(ctx.difficulty, rng)
        grid = [[0] * width for _ in range(height)]
        colors = rng.sample(_COLORS, 6)
        target = colors[0]
        grid[0][0] = target
        if profile == "extended_selector":
            grid[0][1] = grid[1][0] = target
        shape = _shape(profile, rng)
        placed = _place_random(grid, shape, target, rng, edge="bottom" if profile == "target_touches_edge" else None)
        if placed is None:
            continue
        row0, col0 = placed
        if profile == "interior_distractor":
            grid[row0 + 2][col0 + 2] = colors[1]
        distractor_count = 4 if profile == "many_distractors" else rng.randint(1, 3)
        placed_count = 1 if profile == "interior_distractor" else 0
        for index in range(distractor_count - placed_count):
            cells = {(0, 0), (0, 1)} if rng.random() < 0.5 else {(0, 0), (1, 0), (1, 1)}
            if _place_random(grid, cells, colors[1 + index], rng) is not None:
                placed_count += 1
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct selector-crop lesson {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES + GENERAL_PROFILES * 3 + ("irregular_polyomino",) * 12)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    grid = _general_scene(ctx, profile)
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError(f"internal profile drift: {profile} -> {analysis}")
    return grid
