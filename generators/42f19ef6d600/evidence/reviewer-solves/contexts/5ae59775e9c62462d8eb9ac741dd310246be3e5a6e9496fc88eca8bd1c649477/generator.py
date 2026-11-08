"""Semantic generator for ARC task 42f19ef6d600.

Find same-color 4-connected objects against background 7.  Objects with a
square bounding box of side at least two are marked in color 2.  Solid square
objects receive complete exterior side strips; non-solid square objects
receive the eight axial cells just outside their four bbox corners.  Marks
outside the canvas or on non-background input cells are skipped.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "42f19ef6d600"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "07ef8e3cc031"
SUMMARY = "Mark solid-square exterior sides or non-solid-square axial corners with 2 on background 7."

INVARIANTS = [
    "background is color 7 and input contains no color 2",
    "same-color 4-connected objects are analyzed independently",
    "only objects with square bbox side at least two are marked",
    "solid squares receive four exterior side strips",
    "non-solid squares receive eight axial corner-adjacent marks",
    "out-of-bounds or originally non-background mark positions are skipped",
]

PUBLIC_PROFILES = ("public_train_1", "public_train_2", "public_train_3", "public_test_1")
GENERAL_PROFILES = (
    "solid_square", "hollow_square", "irregular_square", "mixed_solid_hollow",
    "three_squares", "four_squares", "size_two_solid", "size_six_hollow", "edge_clipped",
    "nonsquare_decoys", "same_color_nested", "blocked_marks",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "uniform rng over four linked public and twelve generalized semantic lessons",
        "valid": "|".join(SCENE_PROFILES),
    }
}


_PUBLIC_MASKS = {
    "public_train_1": (
        "7777777777", "7aaaa777a7", "7a77a77a77", "7a77a77777", "7aaaa77777",
        "7777777777", "7777777777", "77a77aaaa7", "7a777aaaa7", "7777777777",
    ),
    "public_train_2": (
        "7777777777", "7777777777", "77aaa77a77", "77a7a77a77", "77aaa77a77",
        "7777777777", "7777777777", "77aaa77777", "7777777777", "7777777777",
    ),
    "public_train_3": (
        "7777777777", "7aaaaaaaa7", "7a777777a7", "7a777777a7", "7a77aa77a7",
        "7a77aa77a7", "7a777777a7", "7a777777a7", "7aaaaaaaa7", "7777777777",
    ),
    "public_test_1": (
        "7777777777", "7aaa77aa77", "7a7a77aa77", "7aaa777777", "7777777777",
        "77777aaa77", "7aa77a7a77", "7aa77aaa77", "7777777777", "7aaaaaaaa7",
    ),
}
_PUBLIC_SIGNATURES = {mask: profile for profile, mask in _PUBLIC_MASKS.items()}
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _blank(height, width):
    return [[7 for _ in range(width)] for _ in range(height)]


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty grid"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["empty grid"], 0, 0
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"], height, width
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be integer ARC colors 0..9"], height, width
    return [], height, width


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 7 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for dr, dc in _DIRS:
                    nr, nc = current_row + dr, current_col + dc
                    if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells.sort()
            r1, c1 = min(r for r, _ in cells), min(c for _, c in cells)
            r2, c2 = max(r for r, _ in cells), max(c for _, c in cells)
            obj_height, obj_width = r2 - r1 + 1, c2 - c1 + 1
            components.append({
                "color": color, "cells": tuple(cells), "size": len(cells),
                "r1": r1, "c1": c1, "r2": r2, "c2": c2,
                "height": obj_height, "width": obj_width,
                "solid": len(cells) == obj_height * obj_width,
                "qualifies": obj_height == obj_width and obj_height >= 2,
            })
    return components


def _candidate_marks(obj):
    r1, c1, r2, c2 = obj["r1"], obj["c1"], obj["r2"], obj["c2"]
    if obj["solid"]:
        return tuple(
            [(r1 - 1, col) for col in range(c1, c2 + 1)]
            + [(r2 + 1, col) for col in range(c1, c2 + 1)]
            + [(row, c1 - 1) for row in range(r1, r2 + 1)]
            + [(row, c2 + 1) for row in range(r1, r2 + 1)]
        )
    return (
        (r1 - 1, c1), (r1 - 1, c2), (r2 + 1, c1), (r2 + 1, c2),
        (r1, c1 - 1), (r2, c1 - 1), (r1, c2 + 1), (r2, c2 + 1),
    )


def _semantic_signature(grid):
    roles = {}
    names = iter("abcdefg")
    rendered = []
    for row in grid:
        values = []
        for value in row:
            if value in (2, 7):
                values.append(str(value))
            else:
                if value not in roles:
                    roles[value] = next(names)
                values.append(roles[value])
        rendered.append("".join(values))
    return tuple(rendered)


def _bbox_contains(outer, inner):
    return outer["r1"] < inner["r1"] and outer["c1"] < inner["c1"] and outer["r2"] > inner["r2"] and outer["c2"] > inner["c2"]


def _analysis(grid):
    errors, height, width = _validate_grid(grid)
    result = {"errors": errors, "height": height, "width": width, "scene_profile": None}
    if errors:
        return result
    if any(value == 2 for row in grid for value in row):
        errors.append("input color 2 is reserved for output marks")
    components = _components(grid)
    squares = [obj for obj in components if obj["qualifies"]]
    ignored = [obj for obj in components if not obj["qualifies"]]
    if not squares:
        errors.append("at least one qualifying square-bbox object is required")
    if len(squares) > 4:
        errors.append(f"expected at most four qualifying squares, got {len(squares)}")
    if errors:
        result.update({"objects": components, "squares": squares, "ignored": ignored})
        return result

    output = [list(row) for row in grid]
    eligible_marks, clipped_marks, blocked_marks = set(), set(), set()
    marks_by_object = []
    for obj in components:
        candidates = _candidate_marks(obj) if obj["qualifies"] else ()
        marks_by_object.append(tuple(candidates))
        for row, col in candidates:
            if not (0 <= row < height and 0 <= col < width):
                clipped_marks.add((row, col))
            elif grid[row][col] != 7:
                blocked_marks.add((row, col))
            else:
                eligible_marks.add((row, col))
                output[row][col] = 2
    nested = any(_bbox_contains(left, right) or _bbox_contains(right, left) for i, left in enumerate(squares) for right in squares[i + 1:])
    profile = _PUBLIC_SIGNATURES.get(_semantic_signature(grid))
    if profile is None:
        if clipped_marks:
            profile = "edge_clipped" if len(squares) == 1 and squares[0]["height"] == 4 and not squares[0]["solid"] else "unsupported_clipped_scene"
        elif blocked_marks:
            profile = "blocked_marks"
        elif nested:
            profile = "same_color_nested"
        elif ignored:
            profile = "nonsquare_decoys"
        elif len(squares) == 1 and squares[0]["height"] == 2 and squares[0]["solid"]:
            profile = "size_two_solid"
        elif len(squares) == 1 and squares[0]["height"] == 6 and not squares[0]["solid"]:
            profile = "size_six_hollow"
        elif len(squares) == 4:
            profile = "four_squares"
        elif len(squares) == 3:
            profile = "three_squares"
        elif len(squares) == 2 and {obj["solid"] for obj in squares} == {True, False}:
            profile = "mixed_solid_hollow"
        elif len(squares) == 1 and squares[0]["solid"]:
            profile = "solid_square"
        elif len(squares) == 1 and squares[0]["size"] == 2 * squares[0]["height"] - 1:
            profile = "irregular_square"
        elif len(squares) == 1 and not squares[0]["solid"]:
            profile = "hollow_square"
    if profile not in SCENE_PROFILES:
        errors.append(f"unrecognized square-marking lesson {profile!r}")
    if not eligible_marks:
        errors.append("lesson must produce at least one eligible color-2 mark")
    result.update({
        "errors": errors, "objects": components, "squares": squares, "ignored": ignored,
        "marks_by_object": tuple(marks_by_object), "eligible_marks": eligible_marks,
        "clipped_marks": clipped_marks, "blocked_marks": blocked_marks,
        "nested": nested, "output": output, "scene_profile": profile,
    })
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid)
    profile = info.get("scene_profile")
    return profile if not info["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["output"]]


def _grid_from_public(profile, colors):
    return [[7 if role == "7" else colors[ord(role) - ord("a")] for role in row] for row in _PUBLIC_MASKS[profile]]


def _paint_solid(grid, top, left, size, color):
    for row in range(top, top + size):
        for col in range(left, left + size):
            grid[row][col] = color


def _paint_frame(grid, top, left, size, color):
    for offset in range(size):
        grid[top][left + offset] = color
        grid[top + size - 1][left + offset] = color
        grid[top + offset][left] = color
        grid[top + offset][left + size - 1] = color


def _dimensions(rng, difficulty):
    if difficulty == "easy":
        return rng.randint(10, 14), rng.randint(10, 15)
    if difficulty == "hard":
        return rng.randint(21, 25), rng.randint(22, 26)
    return rng.randint(17, 20), rng.randint(18, 21)


def _general_grid(rng, difficulty, profile, colors):
    height, width = _dimensions(rng, difficulty)
    if profile in ("mixed_solid_hollow", "three_squares", "four_squares", "same_color_nested"):
        height, width = max(height, 14), max(width, 15)
    grid = _blank(height, width)
    if profile == "solid_square":
        _paint_solid(grid, 3, 3, 4, colors[0])
    elif profile == "hollow_square":
        _paint_frame(grid, 3, 3, 4, colors[0])
    elif profile == "irregular_square":
        for offset in range(4):
            grid[3][3 + offset] = colors[0]
            grid[3 + offset][3] = colors[0]
    elif profile == "mixed_solid_hollow":
        _paint_solid(grid, 2, 2, 3, colors[0])
        _paint_frame(grid, height - 6, width - 6, 4, colors[1])
    elif profile == "three_squares":
        _paint_solid(grid, 2, 2, 2, colors[0])
        _paint_frame(grid, 2, width - 5, 3, colors[0])
        _paint_solid(grid, height - 6, 3, 4, colors[0])
    elif profile == "four_squares":
        _paint_solid(grid, 2, 2, 2, colors[0])
        _paint_solid(grid, 2, width - 5, 3, colors[0])
        _paint_frame(grid, height - 6, 2, 4, colors[0])
        _paint_solid(grid, height - 5, width - 5, 3, colors[0])
    elif profile == "size_two_solid":
        _paint_solid(grid, 3, 3, 2, colors[0])
    elif profile == "size_six_hollow":
        _paint_frame(grid, 3, 3, 6, colors[0])
    elif profile == "edge_clipped":
        _paint_frame(grid, 0, 0, 4, colors[0])
    elif profile == "nonsquare_decoys":
        _paint_solid(grid, 2, 2, 3, colors[0])
        for col in range(width - 6, width - 2):
            grid[height - 3][col] = colors[1]
    elif profile == "same_color_nested":
        _paint_frame(grid, 2, 2, 8, colors[0])
        _paint_solid(grid, 5, 5, 2, colors[0])
    elif profile == "blocked_marks":
        _paint_frame(grid, 3, 3, 4, colors[0])
        grid[2][3] = colors[1]
        grid[3][2] = colors[1]
    else:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile != "edge_clipped":
        occupied = [(row, col, grid[row][col]) for row in range(height) for col in range(width) if grid[row][col] != 7]
        min_row, max_row = min(row for row, _, _ in occupied), max(row for row, _, _ in occupied)
        min_col, max_col = min(col for _, col, _ in occupied), max(col for _, col, _ in occupied)
        dr = rng.randint(1 - min_row, height - 2 - max_row)
        dc = rng.randint(1 - min_col, width - 2 - max_col)
        if dr or dc:
            grid = _blank(height, width)
            for row, col, color in occupied:
                grid[row + dr][col + dc] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    context = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = context.draw_choice("scene_profile", list(SCENE_PROFILES))
    colors = tuple(context.draw_distinct_colors("object_colors", n=6, exclude={2, 7}))
    rng = context.draw_rng("scene")
    if profile in PUBLIC_PROFILES:
        public_palette = (0, 1, 3, 4, 5, 6, 8, 9)
        public_color = public_palette[(seed + 2 * PUBLIC_PROFILES.index(profile)) % len(public_palette)]
        grid = _grid_from_public(profile, (public_color,))
    else:
        grid = _general_grid(rng, difficulty, profile, colors)
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile} -> {observed}")
    return [row[:] for row in grid]


def self_check(grid, *, difficulty=None, meta=None):
    info = _analysis(grid)
    errors = list(info["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - {"scene_profile"}
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        requested = overrides.get("scene_profile")
        if requested not in SCENE_PROFILES:
            errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and info["scene_profile"] != requested:
            errors.append(f"requested scene_profile {requested}, observed {info['scene_profile']}")
    return errors
