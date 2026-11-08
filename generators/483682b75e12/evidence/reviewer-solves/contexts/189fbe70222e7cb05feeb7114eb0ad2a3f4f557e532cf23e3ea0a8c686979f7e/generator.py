"""Semantic generator for ARC task 483682b75e12.

Color 7 is background and color 8 is a fixed floor.  Every 4-connected
component made from all other colors moves upward by exactly its total number
of cells, retaining its shape and per-cell colors.  Source locations clear to
7 while the cyan floor remains fixed.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "483682b75e12"
TASK_ID = "483682b75e12"
VERSION = "3.0.0"
RULE_HASH = "a2a5ebf00ff5"
SUMMARY = "Shift every non-7/non-8 connected component upward by its total cell count while preserving the cyan floor and cell colors."
INVARIANTS = [
    "color 7 is the cleared background and the bottom row is a fixed color-8 floor",
    "4-connectivity groups all adjacent non-7/non-8 cells even when their colors differ",
    "each component moves upward by exactly its total number of cells",
    "component geometry and every cell color are preserved",
    "ordinary lessons avoid target collisions and out-of-bounds shifts",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "singleton",
    "horizontal_domino",
    "vertical_domino",
    "horizontal_triomino",
    "vertical_triomino",
    "ell_tetromino",
    "square_tetromino",
    "tee_pentomino",
    "horizontal_six",
    "multicolor_connected",
    "mixed_sizes",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and eleven recoverable component-motion lessons",
        "valid": "public_1|public_2|public_3|public_4|singleton|horizontal_domino|vertical_domino|horizontal_triomino|vertical_triomino|ell_tetromino|square_tetromino|tee_pentomino|horizontal_six|multicolor_connected|mixed_sizes",
    }
}

_PUBLIC_ROWS = (
    "77777777/77777777/77777777/77777777/77777777/79777777/99977222/88888888",
    "77777777/77777777/77777777/77777777/77797777/72797773/72797173/88888888",
    "77777777/77777777/77777777/77777777/77777774/11777374/11173374/88888888",
    "77777777/77777777/77777777/77777777/77777777/77777777/55555576/88888888",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}

_SHAPES = {
    "singleton": ((0, 0),),
    "horizontal_domino": ((0, 0), (0, 1)),
    "vertical_domino": ((0, 0), (1, 0)),
    "horizontal_triomino": ((0, 0), (0, 1), (0, 2)),
    "vertical_triomino": ((0, 0), (1, 0), (2, 0)),
    "ell_tetromino": ((0, 0), (1, 0), (1, 1), (1, 2)),
    "square_tetromino": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "tee_pentomino": ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    "horizontal_six": ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)),
}
_SHAPE_PROFILES = {tuple(sorted(cells)): profile for profile, cells in _SHAPES.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 7 <= len(grid) <= 30 or not 7 <= width <= 30:
        return ["input dimensions must be between 7 and 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid):
    height, width = len(grid), len(grid[0])
    foreground = {(row, col) for row in range(height) for col in range(width) if grid[row][col] not in (7, 8)}
    seen = set()
    components = []
    for start in sorted(foreground):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        cells = set()
        while stack:
            row, col = stack.pop()
            cells.add((row, col))
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = row + drow, col + dcol
                if neighbor in foreground and neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append(tuple(sorted(cells)))
    return tuple(components)


def _normalize(cells):
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _extract_facts(grid):
    height, width = len(grid), len(grid[0])
    components = []
    output = [[8 if grid[row][col] == 8 else 7 for col in range(width)] for row in range(height)]
    target_counts = Counter()
    for cells in _components(grid):
        size = len(cells)
        targets = tuple((row - size, col) for row, col in cells if row - size >= 0)
        for row, col in targets:
            target_counts[(row, col)] += 1
            output[row][col] = grid[row + size][col]
        components.append(
            {
                "cells": cells,
                "size": size,
                "colors": tuple(sorted({grid[row][col] for row, col in cells})),
                "normalized": _normalize(cells),
                "targets": targets,
                "clipped": len(targets) != size,
            }
        )
    return {
        "height": height,
        "width": width,
        "components": tuple(components),
        "sizes": tuple(component["size"] for component in components),
        "target_collisions": tuple(sorted(cell for cell, count in target_counts.items() if count > 1)),
        "target_on_cyan": tuple(sorted(cell for cell in target_counts if grid[cell[0]][cell[1]] == 8)),
        "output": output,
    }


def rule_mirror(grid):
    """Independent Python oracle for the canonical Racket transformation."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return [row[:] for row in _extract_facts(grid)["output"]]


def _profile_for(grid, facts):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    components = facts["components"]
    if len(components) >= 3 and len(set(facts["sizes"])) >= 3:
        return "mixed_sizes"
    if not components:
        return None
    if any(len(component["colors"]) > 1 for component in components):
        return "multicolor_connected"
    shapes = {component["normalized"] for component in components}
    return _SHAPE_PROFILES.get(next(iter(shapes))) if len(shapes) == 1 else None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "facts": None, "scene_profile": None, "output": None}
    facts = _extract_facts(grid)
    profile = _profile_for(grid, facts)
    public = profile in PUBLIC_PROFILES
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared component-motion profile")
    if any(value != 8 for value in grid[-1]):
        errors.append("bottom row must be a complete cyan floor")
    if not public and any(8 in row for row in grid[:-1]):
        errors.append("generalized lessons keep cyan only on the floor")
    if not facts["components"]:
        errors.append("at least one moving component is required")
    if not public and any(component["clipped"] for component in facts["components"]):
        errors.append("generalized component shifts must remain in bounds")
    if facts["target_collisions"]:
        errors.append("component targets must not collide")
    if facts["target_on_cyan"]:
        errors.append("component targets must not overwrite cyan")
    if facts["output"] == [list(row) for row in grid]:
        errors.append("generated lesson must visibly transform")
    if any(value != 8 for value in facts["output"][-1]):
        errors.append("output must preserve the complete cyan floor")
    facts["scene_profile"] = profile
    return {"errors": errors, "facts": facts, "scene_profile": profile, "output": facts["output"]}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _shape_dimensions(cells):
    return max(row for row, _ in cells) + 1, max(col for _, col in cells) + 1


def _dimensions(difficulty, minimum_height, minimum_width, rng):
    bands = {
        None: ((8, 13), (8, 16)),
        "easy": ((8, 10), (8, 11)),
        "medium": ((9, 12), (10, 16)),
        "hard": ((11, 14), (14, 20)),
    }
    (h0, h1), (w0, w1) = bands[difficulty]
    height_low, width_low = max(h0, minimum_height), max(w0, minimum_width)
    height_high = max(h1, height_low)
    width_high = max(width_low, min(max(w1, width_low), minimum_width + 2))
    return rng.randint(height_low, height_high), rng.randint(width_low, width_high)


def _paint_component(grid, cells, row0, col0, colors):
    for index, (row, col) in enumerate(cells):
        grid[row0 + row][col0 + col] = colors[index % len(colors)]


def _general_scene(difficulty, profile, rng, colors):
    if profile == "mixed_sizes":
        specs = (
            (_SHAPES["singleton"], (colors[0],)),
            (_SHAPES["horizontal_domino"], (colors[1],)),
            (_SHAPES["ell_tetromino"], (colors[2],)),
        )
    elif profile == "multicolor_connected":
        specs = (
            (_SHAPES["ell_tetromino"], (colors[0], colors[1], colors[0], colors[1])),
            (_SHAPES["ell_tetromino"], (colors[2], colors[3], colors[2], colors[3])),
        )
    else:
        repeats = 5 if profile == "singleton" else 3 if len(_SHAPES[profile]) == 2 else 2
        specs = tuple((_SHAPES[profile], (colors[index % len(colors)],)) for index in range(repeats))
    max_size = max(len(cells) for cells, _ in specs)
    max_shape_h = max(_shape_dimensions(cells)[0] for cells, _ in specs)
    required_width = sum(_shape_dimensions(cells)[1] for cells, _ in specs) + 2 * (len(specs) - 1) + 2
    height, width = _dimensions(difficulty, max_size + max_shape_h + 1, required_width, rng)
    grid = [[7 for _ in range(width)] for _ in range(height)]
    grid[-1] = [8 for _ in range(width)]
    cursor = 1
    for cells, component_colors in specs:
        shape_h, shape_w = _shape_dimensions(cells)
        lowest_row0 = height - shape_h - 1
        row0 = lowest_row0 - rng.randint(0, min(2, lowest_row0 - len(cells)))
        col0 = cursor
        _paint_component(grid, cells, row0, col0, component_colors)
        cursor += shape_w + 2
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError((profile, analysis["errors"], analysis["scene_profile"]))
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    weighted = PUBLIC_PROFILES * 2 + GENERAL_PROFILES * 5
    profile = ctx.draw_choice("scene_profile", weighted)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    colors = ctx.draw_distinct_colors("colors", n=4, exclude={0, 7, 8})
    return _general_scene(difficulty, profile, ctx.draw_rng("scene"), colors)
