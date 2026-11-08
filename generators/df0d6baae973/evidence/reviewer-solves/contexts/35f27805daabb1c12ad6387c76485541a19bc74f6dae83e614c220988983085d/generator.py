"""Semantic generator for ARC task df0d6baae973.

Sort monochrome components by numeric color.  The output is their pairwise
area-winner matrix: off-diagonal cells contain the larger component's color,
while diagonal cells and equal-area comparisons contain zero.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "df0d6baae973"
TASK_ID = "df0d6baae973"
VERSION = "3.0.0"
RULE_HASH = "7ebd38f17678"
EXPECTED_OUTPUT_CODOMAIN = 80_000
SUMMARY = "Sort distinct-color components numerically and emit an area-winner matrix, using zero on the diagonal and for tied areas."
INVARIANTS = [
    "literal color 0 is background",
    "there are two to five monochrome 4-connected components",
    "component colors are distinct and determine output row/column order numerically",
    "component shapes and positions do not affect comparisons beyond their areas",
    "the output is an n by n symmetric matrix for n components",
    "diagonal output cells are zero",
    "off-diagonal unequal-area cells use the larger component's color",
    "off-diagonal equal-area cells are zero",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 6))
GENERAL_PROFILES = (
    "two_objects_unequal",
    "three_sizes_increasing",
    "three_sizes_decreasing",
    "tie_for_smaller",
    "tie_for_larger",
    "largest_middle_color",
    "smallest_middle_color",
    "singleton_component",
    "branched_polyominoes",
    "four_objects_mixed",
    "five_objects_mixed",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five exact-public and eleven observable color-order/area-comparison lessons",
        "valid": "public_1|public_2|public_3|public_4|public_5|two_objects_unequal|three_sizes_increasing|three_sizes_decreasing|tie_for_smaller|tie_for_larger|largest_middle_color|smallest_middle_color|singleton_component|branched_polyominoes|four_objects_mixed|five_objects_mixed",
    }
}

_PUBLIC_ROWS = {
    "public_1": "0000000000000/0202000000000/0222000060000/0020000066000/0000000006600/0040000000000/0044400000000/0000000000000/0000000000000/0000000000000",
    "public_2": "000000000000/000000007700/033000007700/003000000000/003300000000/000000055500/000000005000/000000005000/000000000000/000000000000",
    "public_3": "000000000000/022000000000/002200000000/000000000000/000000060600/000000066600/000800006000/000888000000/000000000000",
    "public_4": "0000000000000/0000000000000/0040000000000/0044000000000/0004400000000/0000909000000/0000999055500/0000090050000/0000000000000/0000000000000/0000000000000",
    "public_5": "0000000000000/0333000000000/0030000000000/0030000000000/0000000000000/0000000066000/0000000006000/0088000006600/0008000000000/0000000000000",
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
    facts = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            seen.add((row, col))
            queue = deque([(row, col)])
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            facts.append({"color": color, "cells": sorted(cells), "size": len(cells)})
    return sorted(facts, key=lambda fact: (fact["color"], fact["size"]))


def _has_two_by_two(cells):
    occupied = set(cells)
    return any({(row, col), (row + 1, col), (row, col + 1), (row + 1, col + 1)}.issubset(occupied) for row, col in occupied)


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _components(grid)
    output = []
    for row, first in enumerate(facts):
        values = []
        for col, second in enumerate(facts):
            if row == col or first["size"] == second["size"]:
                values.append(0)
            elif first["size"] > second["size"]:
                values.append(first["color"])
            else:
                values.append(second["color"])
        output.append(values)
    return output


def _general_profile(facts):
    count = len(facts)
    if count == 2:
        return "two_objects_unequal"
    if count == 4:
        return "four_objects_mixed"
    if count == 5:
        return "five_objects_mixed"
    sizes = [fact["size"] for fact in facts]
    if min(sizes) == 1:
        return "singleton_component"
    if any(_has_two_by_two(fact["cells"]) for fact in facts):
        return "branched_polyominoes"
    if sizes[0] < sizes[1] < sizes[2]:
        return "three_sizes_increasing"
    if sizes[0] > sizes[1] > sizes[2]:
        return "three_sizes_decreasing"
    ordered = sorted(sizes)
    if ordered[0] == ordered[1] < ordered[2]:
        return "tie_for_smaller"
    if ordered[0] < ordered[1] == ordered[2]:
        return "tie_for_larger"
    if sizes[1] == max(sizes) and len(set(sizes)) == 3:
        return "largest_middle_color"
    if sizes[1] == min(sizes) and len(set(sizes)) == 3:
        return "smallest_middle_color"
    return None


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    if all(value != 0 for row in grid for value in row):
        errors.append("expected literal zero background")
    facts = _components(grid)
    if not 2 <= len(facts) <= 5:
        errors.append("expected two to five comparison components")
    colors = [fact["color"] for fact in facts]
    if len(colors) != len(set(colors)):
        errors.append("component colors must be distinct")
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    profile = public
    if not errors and not public:
        profile = _general_profile(facts)
        if profile not in GENERAL_PROFILES:
            errors.append("scene does not match a declared comparison profile")
    output = rule_mirror(grid) if not errors else None
    result.update({
        "components": facts,
        "sizes": [fact["size"] for fact in facts],
        "colors": colors,
        "output": output,
        "scene_profile": profile,
        "errors": errors,
    })
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


def _size_signature(profile, difficulty, rng):
    high = {None: 8, "easy": 6, "medium": 8, "hard": 10}[difficulty]
    if profile == "two_objects_unequal":
        values = rng.sample(range(2, high + 1), 2)
        rng.shuffle(values)
        return values
    if profile == "four_objects_mixed":
        while True:
            values = [rng.randint(2, high) for _ in range(4)]
            if len(set(values)) >= 2:
                return values
    if profile == "five_objects_mixed":
        while True:
            values = [rng.randint(2, high) for _ in range(5)]
            if len(set(values)) >= 2:
                return values
    if profile == "singleton_component":
        pair = sorted(rng.sample(range(3, high + 1), 2))
        return [1, pair[0], pair[1]]
    if profile == "branched_polyominoes":
        values = sorted(rng.sample(range(4, high + 1), 3)) if high >= 6 else [4, 5, 6]
        return values
    three = sorted(rng.sample(range(2, high + 1), 3))
    low, middle, high_value = three
    if profile == "three_sizes_increasing":
        return three
    if profile == "three_sizes_decreasing":
        return list(reversed(three))
    if profile == "tie_for_smaller":
        return [low, low, high_value]
    if profile == "tie_for_larger":
        return [low, high_value, high_value]
    if profile == "largest_middle_color":
        return [middle, high_value, low]
    if profile == "smallest_middle_color":
        return [middle, low, high_value]
    raise ValueError(f"unsupported profile: {profile}")


def _path_shape(size, rng):
    if size == 1:
        return [(0, 0)]
    for _ in range(100):
        cells = [(0, 0)]
        occupied = {(0, 0)}
        while len(cells) < size:
            row, col = rng.choice(cells)
            dr, dc = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
            candidate = (row + dr, col + dc)
            if candidate in occupied:
                continue
            trial = occupied | {candidate}
            if _has_two_by_two(trial):
                continue
            occupied.add(candidate)
            cells.append(candidate)
        min_row = min(row for row, _ in cells)
        min_col = min(col for _, col in cells)
        return sorted((row - min_row, col - min_col) for row, col in cells)
    raise AssertionError("could not construct path polyomino")


def _branched_shape(size, rng):
    cells = {(0, 0), (0, 1), (1, 0), (1, 1)}
    while len(cells) < size:
        row, col = rng.choice(sorted(cells))
        dr, dc = rng.choice(((-1, 0), (1, 0), (0, -1), (0, 1)))
        cells.add((row + dr, col + dc))
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return sorted((row - min_row, col - min_col) for row, col in cells)


def _can_place(grid, shape, top, left):
    height, width = len(grid), len(grid[0])
    target = {(top + row, left + col) for row, col in shape}
    for row, col in target:
        if not (0 <= row < height and 0 <= col < width):
            return False
        if grid[row][col] != 0:
            return False
        for rr in range(row - 1, row + 2):
            for cc in range(col - 1, col + 2):
                if 0 <= rr < height and 0 <= cc < width and grid[rr][cc] != 0 and (rr, cc) not in target:
                    return False
    return True


def _general_scene(ctx, profile):
    rng = ctx.draw_rng("geometry")
    sizes = _size_signature(profile, ctx.difficulty, rng)
    count = len(sizes)
    colors = sorted(rng.sample(range(1, 10), count))
    bump = {None: 2, "easy": 0, "medium": 2, "hard": 4}[ctx.difficulty]
    height = 5 + 2 * count + bump + rng.randint(0, 2)
    width = 7 + 2 * count + bump + rng.randint(0, 2)
    for _ in range(120):
        grid = [[0] * width for _ in range(height)]
        success = True
        for index, (color, size) in enumerate(zip(colors, sizes)):
            shape = _branched_shape(size, rng) if profile == "branched_polyominoes" and index == 0 else _path_shape(size, rng)
            shape_h = max(row for row, _ in shape) + 1
            shape_w = max(col for _, col in shape) + 1
            placed = False
            for _ in range(200):
                top = rng.randint(0, height - shape_h)
                left = rng.randint(0, width - shape_w)
                if _can_place(grid, shape, top, left):
                    for row, col in shape:
                        grid[top + row][left + col] = color
                    placed = True
                    break
            if not placed:
                success = False
                break
        if success:
            return grid
    raise AssertionError("could not place comparison components")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES + GENERAL_PROFILES * 3)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    grid = _general_scene(ctx, profile)
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise AssertionError(f"internal invalid scene: {analysis['errors']}")
    if analysis["scene_profile"] != profile:
        raise AssertionError(f"profile drift: {profile} -> {analysis['scene_profile']}")
    return grid
