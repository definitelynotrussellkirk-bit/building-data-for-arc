"""Semantic generator for the contest-synthetic size-recolor family.

Enumerate every monochromatic nonzero 4-connected object.  Recolor the whole
object by its cell count: size 1 -> 1, 2 -> 2, 3 -> 3, 4 -> 4, and 5+ -> 6.
Input color is deliberately varied in the mixed-palette profile; only object
size determines the output color.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "7c7796f15a18"
TASK_ID = "7c7796f15a18"
VERSION = "2.0.0"
RULE_HASH = "760ae845bd82"
SUMMARY = "Recolor every nonzero 4-connected object by size: 1/2/3/4 cells to colors 1/2/3/4, and 5+ cells to 6."
INVARIANTS = [
    "background is black (0)",
    "objects are maximal monochromatic nonzero 4-connected components",
    "every returned lesson visibly contains size buckets 1, 2, 3, 4, and 5+",
    "the output preserves the grid and object geometry while replacing each object's entire color by its size bucket",
    "input color is irrelevant to the recolor decision",
]

SCENE_PROFILES = (
    "branch_complete",
    "mixed_palette",
    "same_color_separate",
    "diagonal_touch",
    "large_bucket",
    "sparse_extremes",
    "dense_contest",
)
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "balanced size-bucket, palette-invariance, connectivity, sparse, and dense scenes",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_INPUT_COLORS = (5, 7, 8, 9)


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 5 <= len(grid) <= 30:
        return ["input must have five through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 5 <= len(grid[0]) <= 30:
        return ["input must have five through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _components(grid):
    height, width = len(grid), len(grid[0])
    visited, result = set(), []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            start = start_row, start_col
            if color == 0 or start in visited:
                continue
            visited.add(start)
            cells, frontier = {start}, [start]
            while frontier:
                row, col = frontier.pop()
                for dr, dc in _CARDINAL:
                    neighbour = row + dr, col + dc
                    if (
                        0 <= neighbour[0] < height
                        and 0 <= neighbour[1] < width
                        and neighbour not in visited
                        and grid[neighbour[0]][neighbour[1]] == color
                    ):
                        visited.add(neighbour)
                        cells.add(neighbour)
                        frontier.append(neighbour)
            result.append({"color": color, "cells": frozenset(cells), "size": len(cells)})
    return tuple(result)


def _output_color(size):
    return size if size <= 4 else 6


def rule_mirror(grid):
    """Exact Python mirror of the authored contest-synthetic Racket rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    for component in _components(grid):
        color = _output_color(component["size"])
        for row, col in component["cells"]:
            output[row][col] = color
    return output


def _diagonal_contacts(components):
    contacts = 0
    for left_index, left in enumerate(components):
        for right in components[left_index + 1 :]:
            if left["color"] != right["color"]:
                continue
            if any(
                abs(row_a - row_b) == 1 and abs(col_a - col_b) == 1
                for row_a, col_a in left["cells"]
                for row_b, col_b in right["cells"]
            ):
                contacts += 1
    return contacts


def _profile_from_facts(facts):
    sizes = facts["sizes"]
    if facts["diagonal_contacts"]:
        return "diagonal_touch"
    if facts["input_color_count"] >= 3:
        return "mixed_palette"
    if len(sizes) >= 12:
        return "dense_contest"
    if sizes == (1, 2, 3, 4, 8):
        return "sparse_extremes"
    if set(range(1, 9)).issubset(sizes):
        return "large_bucket"
    if sizes == (1, 1, 2, 2, 3, 3, 4, 4, 5, 5):
        return "same_color_separate"
    if sizes == (1, 2, 3, 4, 5):
        return "branch_complete"
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    components = _components(grid)
    sizes = tuple(sorted(component["size"] for component in components))
    input_colors = frozenset(component["color"] for component in components)
    facts = {
        "height": len(grid),
        "width": len(grid[0]),
        "components": components,
        "object_count": len(components),
        "sizes": sizes,
        "size_counts": dict(sorted(Counter(sizes).items())),
        "input_colors": input_colors,
        "input_color_count": len(input_colors),
        "diagonal_contacts": _diagonal_contacts(components),
        "large_bucket_sizes": tuple(size for size in sizes if size >= 5),
    }
    if len(components) < 5:
        errors.append("at least five objects are required")
    if not input_colors or not input_colors <= set(_INPUT_COLORS):
        errors.append("input object colors must come from 5, 7, 8, and 9")
    missing = {1, 2, 3, 4} - set(sizes)
    if missing or not any(size >= 5 for size in sizes):
        errors.append("every returned lesson must witness size buckets 1, 2, 3, 4, and 5+")
    if any(size > 8 for size in sizes):
        errors.append("training objects must contain at most eight cells")
    profile = _profile_from_facts(facts)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared size-recolor profile")
    output = None if errors else rule_mirror(grid)
    if output == [list(row) for row in grid]:
        errors.append("size recoloring must change the scene")
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": output}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _random_polyomino(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        row, col = rng.choice(sorted(cells))
        dr, dc = rng.choice(_CARDINAL)
        cells.add((row + dr, col + dc))
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return {(row - row0, col - col0) for row, col in cells}


def _block_ring(blocked, cells):
    height, width = len(blocked), len(blocked[0])
    for row, col in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                neighbour = row + dr, col + dc
                if 0 <= neighbour[0] < height and 0 <= neighbour[1] < width:
                    blocked[neighbour[0]][neighbour[1]] = True


def _place_specs(height, width, specs, rng, *, diagonal=False):
    grid = [[0] * width for _ in range(height)]
    blocked = [[False] * width for _ in range(height)]
    remaining = list(specs)
    if diagonal:
        color = remaining[0][1]
        fixed = [({(1, 1)}, color), ({(2, 2), (2, 3)}, color)]
        remaining = remaining[2:]
        for cells, fixed_color in fixed:
            for row, col in cells:
                grid[row][col] = fixed_color
        _block_ring(blocked, set().union(*(cells for cells, _ in fixed)))
    remaining.sort(key=lambda item: -item[0])
    for size, color in remaining:
        placed = False
        for _ in range(500):
            shape = _random_polyomino(rng, size)
            shape_height = max(row for row, _ in shape) + 1
            shape_width = max(col for _, col in shape) + 1
            top = rng.randint(0, height - shape_height)
            left = rng.randint(0, width - shape_width)
            cells = {(top + row, left + col) for row, col in shape}
            if any(blocked[row][col] for row, col in cells):
                continue
            for row, col in cells:
                grid[row][col] = color
            _block_ring(blocked, cells)
            placed = True
            break
        if not placed:
            raise AssertionError("could not place isolated size-recolor objects")
    return grid


def _limits(difficulty):
    if difficulty == "easy":
        return (12, 16)
    if difficulty == "medium":
        return (17, 22)
    if difficulty == "hard":
        return (23, 30)
    return (15, 24)


def _profile_specs(profile, difficulty, rng):
    if profile == "branch_complete":
        color = rng.choice(_INPUT_COLORS)
        return [(size, color) for size in range(1, 6)]
    if profile == "same_color_separate":
        color = rng.choice(_INPUT_COLORS)
        return [(size, color) for size in range(1, 6) for _ in range(2)]
    if profile == "diagonal_touch":
        color = rng.choice(_INPUT_COLORS)
        return [(size, color) for size in range(1, 6)]
    if profile == "large_bucket":
        colors = rng.sample(_INPUT_COLORS, 2)
        return [(size, colors[size % 2]) for size in range(1, 9)]
    if profile == "sparse_extremes":
        color = rng.choice(_INPUT_COLORS)
        return [(size, color) for size in (1, 2, 3, 4, 8)]
    if profile == "mixed_palette":
        count = rng.randint(10, 14)
        colors = rng.sample(_INPUT_COLORS, 4)
        sizes = list(range(1, 9)) + [rng.randint(1, 8) for _ in range(count - 8)]
        return [(size, colors[index % 4]) for index, size in enumerate(sizes)]
    if profile == "dense_contest":
        if difficulty == "easy":
            count = rng.randint(12, 16)
        elif difficulty == "hard":
            count = rng.randint(26, 32)
        else:
            count = rng.randint(18, 24)
        colors = rng.sample(_INPUT_COLORS, 2)
        sizes = list(range(1, 7)) + [rng.randint(1, 8) for _ in range(count - 6)]
        return [(size, colors[index % 2]) for index, size in enumerate(sizes)]
    raise ValueError(f"unknown scene_profile: {profile!r}")


def _scene(profile, difficulty, rng):
    low, high = _limits(difficulty)
    for _ in range(80):
        height, width = rng.randint(low, high), rng.randint(low, high)
        if profile == "dense_contest" and difficulty == "hard":
            height, width = rng.randint(27, 30), rng.randint(27, 30)
        specs = _profile_specs(profile, difficulty, rng)
        try:
            grid = _place_specs(height, width, specs, rng, diagonal=profile == "diagonal_touch")
        except AssertionError:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct size-recolor profile {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
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
    prior = (
        ("branch_complete",) * 4
        + ("mixed_palette",) * 4
        + ("same_color_separate",) * 2
        + ("diagonal_touch",) * 2
        + ("large_bucket",) * 3
        + ("sparse_extremes",)
        + ("dense_contest",) * 4
    )
    profile = ctx.draw_choice("scene_profile", prior)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    grid = _scene(profile, difficulty, ctx.draw_rng("scene"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid size-recolor lesson: " + "; ".join(errors))
    return grid
