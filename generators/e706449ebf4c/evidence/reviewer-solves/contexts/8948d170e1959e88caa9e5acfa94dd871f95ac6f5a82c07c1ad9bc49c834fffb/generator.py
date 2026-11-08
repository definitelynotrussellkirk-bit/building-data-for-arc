"""Semantic generator for ARC task e706449ebf4c.

Find 4-connected red components, measure each bounding-box bar length, and
paint cyan into zero cells whose doubled-coordinate Manhattan distance from
the doubled bounding-box center is at most that length. Existing red survives.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "e706449ebf4c"
TASK_ID = "e706449ebf4c"
VERSION = "3.0.0"
RULE_HASH = "665e4af22561"
SUMMARY = "Paint cyan doubled-coordinate Manhattan auras around red bars, using each bar's bounding-box length as the threshold."
INVARIANTS = [
    "the input uses only literal background 0 and red 2",
    "one to three separate 4-connected red components are present",
    "each generated component is a straight horizontal or vertical bar of length at least five",
    "bar length is the maximum inclusive bounding-box dimension",
    "distance is measured from the doubled bounding-box midpoint in doubled cell coordinates",
    "cyan 8 is painted only onto cells that are zero in the evolving result",
    "red bar cells survive even when another bar's aura reaches them",
    "auras may overlap or clip at the canvas boundary",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3")
GENERAL_PROFILES = (
    "single_vertical_odd",
    "single_vertical_even",
    "single_horizontal_odd",
    "single_horizontal_even",
    "two_parallel",
    "two_perpendicular",
    "three_mixed",
    "clipped_edge",
    "clipped_both_edges",
    "overlapping_auras",
    "aura_hits_other_bar",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "three exact-public and eleven observable aura lessons",
        "valid": "public_1|public_2|public_3|single_vertical_odd|single_vertical_even|single_horizontal_odd|single_horizontal_even|two_parallel|two_perpendicular|three_mixed|clipped_edge|clipped_both_edges|overlapping_auras|aura_hits_other_bar",
    }
}

_PUBLIC_ROWS = {
    "public_1": "000000000000000000000/000000000000000000000/000020000000000000000/000020000000000000000/000020000000000000000/000020000000000000000/000020000000000000000/000000000000000000000/000000000000000000000/000000000000000000000/000000000000000000000/000000000000000000000/000000000222222222000/000000000000000000000/000000000000000000000/000000000000000000000/000000000000000000000/000000000000000000000/000000000000000000000",
    "public_2": "0000000000000000000/0000000000000000000/0000000000000000000/0000000000000000000/0000000000000000000/0000000000000000000/0000000000000000000/0022222222222222000/0000000000000000000/0000000000000000000/0000000000000000000/0000000000000000000/0000000000000000000/0000000000000000000/0000000000000000000/0000000000000000000/0000000000000000000",
    "public_3": "0000000000000000000000/0000000000000000000000/0000000000000000000000/0000000000000000000000/0022222200000000000000/0000000000000000000000/0000000000000000000000/0000000000000000000000/0000000000000000000000/0000000000022222222220/0000000000000000000000/0000020000000000000000/0000020000000000000000/0000020000000000000000/0000020000000000000000/0000020000000000000000/0000020000000000000000/0000020000000000000000/0000000000000000000000/0000000000000000000000/0000000000000000000000",
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
    if any(isinstance(value, bool) or not isinstance(value, int) or value not in (0, 2) for row in grid for value in row):
        return ["input cells must be literal background 0 or red 2"]
    return []


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 2 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == 2 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _component_fact(grid, cells):
    height, width = len(grid), len(grid[0])
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    row0, row1, col0, col1 = min(rows), max(rows), min(cols), max(cols)
    length = max(row1 - row0 + 1, col1 - col0 + 1)
    center_row2, center_col2 = row0 + row1, col0 + col1
    field = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if abs(2 * row - center_row2) + abs(2 * col - center_col2) <= length
    }
    paintable = {cell for cell in field if grid[cell[0]][cell[1]] == 0}
    clipped_sides = set()
    for row in range(-length, height + length):
        for col in range(-length, width + length):
            if 0 <= row < height and 0 <= col < width:
                continue
            if abs(2 * row - center_row2) + abs(2 * col - center_col2) > length:
                continue
            if row < 0:
                clipped_sides.add("top")
            if row >= height:
                clipped_sides.add("bottom")
            if col < 0:
                clipped_sides.add("left")
            if col >= width:
                clipped_sides.add("right")
    orientation = "vertical" if row1 - row0 > col1 - col0 else "horizontal"
    return {
        "cells": cells,
        "bbox": (row0, col0, row1, col1),
        "length": length,
        "parity": "odd" if length % 2 else "even",
        "orientation": orientation,
        "field": field,
        "paintable": paintable,
        "clipped_sides": clipped_sides,
    }


def _rule_facts(grid):
    components = _components(grid)
    bars = [_component_fact(grid, cells) for cells in components]
    output = [list(row) for row in grid]
    for bar in bars:
        center_row2 = bar["bbox"][0] + bar["bbox"][2]
        center_col2 = bar["bbox"][1] + bar["bbox"][3]
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                distance2 = abs(2 * row - center_row2) + abs(2 * col - center_col2)
                if distance2 <= bar["length"] and output[row][col] == 0:
                    output[row][col] = 8
    hits = False
    for index, bar in enumerate(bars):
        other_cells = set().union(*(other["cells"] for j, other in enumerate(bars) if j != index)) if len(bars) > 1 else set()
        hits = hits or bool(bar["field"] & other_cells)
    overlaps = any(bars[i]["paintable"] & bars[j]["paintable"] for i in range(len(bars)) for j in range(i + 1, len(bars)))
    return {
        "bars": bars,
        "output": output,
        "aura_hits_other_bar": hits,
        "overlapping_auras": overlaps,
        "changed": sum(a != b for row_a, row_b in zip(grid, output) for a, b in zip(row_a, row_b)),
    }


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _rule_facts(grid)["output"]


def _general_profile(facts):
    bars = facts["bars"]
    if facts["aura_hits_other_bar"]:
        return "aura_hits_other_bar"
    if facts["overlapping_auras"]:
        return "overlapping_auras"
    if len(bars) == 1 and len(bars[0]["clipped_sides"]) >= 2:
        return "clipped_both_edges"
    if len(bars) == 1 and bars[0]["clipped_sides"]:
        return "clipped_edge"
    if len(bars) == 3:
        return "three_mixed"
    if len(bars) == 2:
        return "two_parallel" if bars[0]["orientation"] == bars[1]["orientation"] else "two_perpendicular"
    if len(bars) == 1:
        return f"single_{bars[0]['orientation']}_{bars[0]['parity']}"
    return None


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    height, width = len(grid), len(grid[0])
    if height < 6 or width < 6:
        errors.append("expected both dimensions to be at least six")
    facts = _rule_facts(grid)
    bars = facts["bars"]
    if not 1 <= len(bars) <= 3:
        errors.append(f"expected one to three red components, found {len(bars)}")
    for bar in bars:
        row0, col0, row1, col1 = bar["bbox"]
        straight = row0 == row1 or col0 == col1
        if not straight or len(bar["cells"]) != bar["length"]:
            errors.append("every generated red component must be a solid straight bar")
        if bar["length"] < 5:
            errors.append("every training bar must have canonical-supported length at least five")
    if facts["changed"] < max(1, int(height * width * 0.02)):
        errors.append("aura must visibly change at least two percent of the grid")
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    profile = public
    if not errors and not public:
        profile = _general_profile(facts)
        if profile not in GENERAL_PROFILES:
            errors.append("scene does not match a declared aura profile")
    result.update({"facts": facts, "output": facts["output"], "scene_profile": profile, "errors": errors})
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


def _dimensions(difficulty, rng, profile):
    if profile.startswith("single_"):
        # Keep the bands ordered while leaving enough independent choices of
        # canvas, bar length, and position that easy lessons do not collapse
        # into a small set of repeated grids.
        ranges = {None: (11, 21), "easy": (10, 18), "medium": (14, 24), "hard": (20, 30)}
    else:
        ranges = {None: (20, 25), "easy": (18, 22), "medium": (21, 26), "hard": (25, 30)}
    low, high = ranges[difficulty]
    return rng.randint(low, high), rng.randint(low, high)


def _paint_bar(grid, row, col, length, orientation):
    cells = [(row + index, col) if orientation == "vertical" else (row, col + index) for index in range(length)]
    if any(not (0 <= rr < len(grid) and 0 <= cc < len(grid[0])) or grid[rr][cc] != 0 for rr, cc in cells):
        return False
    if any(
        grid[nr][nc] == 2
        for rr, cc in cells
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        for nr, nc in ((rr + dr, cc + dc),)
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and (nr, nc) not in cells
    ):
        return False
    for rr, cc in cells:
        grid[rr][cc] = 2
    return True


def _length_for(rng, parity, limit):
    choices = [length for length in range(5, min(14, limit) + 1) if (length % 2 == 1) == (parity == "odd")]
    return rng.choice(choices)


def _random_bar(grid, rng, orientation, length, *, central=True):
    height, width = len(grid), len(grid[0])
    bar_h, bar_w = (length, 1) if orientation == "vertical" else (1, length)
    margin = (length + 1) // 2 if central else 0
    rows = list(range(margin, height - bar_h - margin + 1)) if central else list(range(height - bar_h + 1))
    cols = list(range(margin, width - bar_w - margin + 1)) if central else list(range(width - bar_w + 1))
    origins = [(row, col) for row in rows for col in cols]
    rng.shuffle(origins)
    return next(((row, col) for row, col in origins if _paint_bar(grid, row, col, length, orientation)), None)


def _single_scene(ctx, profile, rng):
    orientation = "vertical" if "vertical" in profile else "horizontal"
    parity = "odd" if profile.endswith("odd") else "even"
    for _ in range(500):
        height, width = _dimensions(ctx.difficulty, rng, profile)
        limit = (height if orientation == "vertical" else width) - 4
        if limit < (5 if parity == "odd" else 6):
            continue
        length = _length_for(rng, parity, limit)
        grid = [[0] * width for _ in range(height)]
        if _random_bar(grid, rng, orientation, length) is None:
            continue
        if _analysis(grid)["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct {profile}")


def _interaction_scene(ctx, profile, rng):
    for _ in range(1000):
        height, width = _dimensions(ctx.difficulty, rng, profile)
        if profile == "clipped_both_edges":
            length = rng.randint(8, 14)
            if rng.random() < 0.5:
                height = rng.randint(6, min(10, length))
                width = rng.randint(length + 3, min(30, length + 12))
                clipped_orientation = "horizontal"
            else:
                width = rng.randint(6, min(10, length))
                height = rng.randint(length + 3, min(30, length + 12))
                clipped_orientation = "vertical"
        grid = [[0] * width for _ in range(height)]
        if profile == "clipped_edge":
            orientation = rng.choice(("horizontal", "vertical"))
            limit = width if orientation == "horizontal" else height
            length = rng.randint(5, min(14, limit - 2))
            if orientation == "horizontal":
                row = rng.choice((0, height - 1))
                col = rng.randint(1, width - length - 1)
            else:
                row = rng.randint(1, height - length - 1)
                col = rng.choice((0, width - 1))
            _paint_bar(grid, row, col, length, orientation)
        elif profile == "clipped_both_edges":
            if clipped_orientation == "horizontal":
                _paint_bar(grid, rng.randint(1, height - 2), rng.randint(1, width - length - 1), length, "horizontal")
            else:
                _paint_bar(grid, rng.randint(1, height - length - 1), rng.randint(1, width - 2), length, "vertical")
        elif profile == "aura_hits_other_bar":
            orientation = rng.choice(("horizontal", "vertical"))
            limit = width if orientation == "horizontal" else height
            length = rng.randint(5, min(14, limit - 6))
            separation = rng.randint(2, max(2, length // 2))
            if orientation == "horizontal":
                row = rng.randint(2, height - separation - 3)
                col = rng.randint(2, width - length - 2)
                offset = rng.randint(-min(2, col - 1), min(2, width - length - col - 1))
                _paint_bar(grid, row, col, length, orientation)
                _paint_bar(grid, row + separation, col + offset, length, orientation)
            else:
                row = rng.randint(2, height - length - 2)
                col = rng.randint(2, width - separation - 3)
                offset = rng.randint(-min(2, row - 1), min(2, height - length - row - 1))
                _paint_bar(grid, row, col, length, orientation)
                _paint_bar(grid, row + offset, col + separation, length, orientation)
        elif profile == "overlapping_auras":
            orientation = rng.choice(("horizontal", "vertical"))
            limit = width if orientation == "horizontal" else height
            length = rng.randint(6, min(14, limit - 6))
            low = length // 2 + 1
            high = max(low, min(length - 1, (height if orientation == "horizontal" else width) - 5))
            separation = rng.randint(low, high)
            if orientation == "horizontal":
                row = rng.randint(2, height - separation - 3)
                col = rng.randint(2, width - length - 2)
                _paint_bar(grid, row, col, length, orientation)
                _paint_bar(grid, row + separation, col + rng.choice((-1, 0, 1)), length, orientation)
            else:
                row = rng.randint(2, height - length - 2)
                col = rng.randint(2, width - separation - 3)
                _paint_bar(grid, row, col, length, orientation)
                _paint_bar(grid, row + rng.choice((-1, 0, 1)), col + separation, length, orientation)
        else:
            orientations = {
                "two_parallel": ("horizontal", "horizontal"),
                "two_perpendicular": ("horizontal", "vertical"),
                "three_mixed": ("horizontal", "vertical", "horizontal"),
            }[profile]
            for orientation in orientations:
                parity = rng.choice(("odd", "even"))
                limit = (height if orientation == "vertical" else width) - 8
                length = _length_for(rng, parity, limit)
                if _random_bar(grid, rng, orientation, length) is None:
                    break
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct {profile}")


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
    rng = ctx.draw_rng("geometry")
    grid = _single_scene(ctx, profile, rng) if profile.startswith("single_") else _interaction_scene(ctx, profile, rng)
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError(f"internal profile drift: {profile} -> {analysis}")
    return grid
