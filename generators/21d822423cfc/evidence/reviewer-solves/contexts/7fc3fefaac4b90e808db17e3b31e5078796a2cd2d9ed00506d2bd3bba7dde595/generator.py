"""Semantic generator for ARC task 21d822423cfc.

Color 5 is an impermeable wall.  Every 4-connected component of non-5 cells
is a chamber.  If that chamber contains exactly one *distinct* seed color
from {1, 2, 3}, all of its zero cells are flooded with that color.  Multiple
copies of one seed agree; no seed or multiple distinct seed colors means no
fill.  Other nonzero colors are part of the chamber and remain unchanged.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "21d822423cfc"
TASK_ID = "21d822423cfc"
VERSION = "3.0.0"
RULE_HASH = "70caebbaa31c"
SUMMARY = "Flood zero cells in each non-5 chamber only when the chamber contains exactly one distinct seed color from 1, 2, or 3."
INVARIANTS = [
    "color 5 alone blocks 4-connected chamber traversal",
    "each chamber is decided independently",
    "zero distinct seed colors and two or more distinct seed colors leave a chamber unchanged",
    "multiple cells of one seed color still select that one color",
    "only zero cells are repainted; walls, seeds, and non-seed decoys remain unchanged",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 6))
GENERAL_PROFILES = (
    "four_all_seeded",
    "four_seed_blank",
    "four_seed_ambiguous",
    "six_mixed",
    "many_chambers",
    "horizontal_strips",
    "vertical_strips",
    "t_junction_chambers",
    "multiple_same_seed",
    "nonseed_decoys",
    "open_edge_chambers",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five exact-public and eleven generalized chamber-state lessons",
        "valid": "public_1|public_2|public_3|public_4|public_5|four_all_seeded|four_seed_blank|four_seed_ambiguous|six_mixed|many_chambers|horizontal_strips|vertical_strips|t_junction_chambers|multiple_same_seed|nonseed_decoys|open_edge_chambers",
    }
}

_PUBLIC_ROWS = (
    "55555555555/50050005005/50150205005/50050005005/50055555005/50050005005/50050305105/50050005005/55555555555",
    "555555555555/500050005005/502050305005/500050005005/500050005005/500055555005/500050005005/501050005025/500050005005/555555555555",
    "55555555555/51000502005/50000500005/55555555555/50000500005/50000500305/50000500005/55555555555/50000500005/50000500015/55555555555",
    "5555555555555/5030502005005/5000500005005/5000555555005/5000500005005/5010500005035/5000500005005/5000500005005/5555555555555",
    "5555555555555/5005000050005/5105002050005/5005000050005/5005000050005/5005000050005/5005555550005/5005003050105/5005000050005/5555555555555",
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
    if not 7 <= len(grid) <= 30 or not 7 <= width <= 30:
        return ["grid dimensions must be within 7..30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid):
    height, width = len(grid), len(grid[0])
    unseen = {(row, col) for row in range(height) for col in range(width) if grid[row][col] != 5}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = []
        while queue:
            row, col = queue.popleft()
            cells.append((row, col))
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(cells))
    return sorted(components, key=lambda cells: cells[0])


def _extract_facts(grid):
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    chambers = []
    for cells in _components(grid):
        values = [grid[row][col] for row, col in cells]
        seed_colors = sorted({value for value in values if 1 <= value <= 3})
        seed_cells = sum(1 <= value <= 3 for value in values)
        decoy_cells = sum(value not in {0, 1, 2, 3, 5} for value in values)
        changed = 0
        if len(seed_colors) == 1:
            color = seed_colors[0]
            for row, col in cells:
                if output[row][col] == 0:
                    output[row][col] = color
                    changed += 1
        state = "unique" if len(seed_colors) == 1 else "blank" if not seed_colors else "ambiguous"
        chambers.append({
            "cells": cells,
            "size": len(cells),
            "seed_colors": seed_colors,
            "seed_cells": seed_cells,
            "decoy_cells": decoy_cells,
            "state": state,
            "changed": changed,
        })
    outer_border = all(grid[0][col] == 5 and grid[height - 1][col] == 5 for col in range(width)) and all(grid[row][0] == 5 and grid[row][width - 1] == 5 for row in range(height))
    full_rows = [row for row in range(1, height - 1) if all(grid[row][col] == 5 for col in range(width))]
    full_cols = [col for col in range(1, width - 1) if all(grid[row][col] == 5 for row in range(height))]
    structural_walls = {
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if grid[row][col] == 5 and row not in full_rows and col not in full_cols
    }
    return {
        "height": height,
        "width": width,
        "chambers": chambers,
        "chamber_count": len(chambers),
        "states": [chamber["state"] for chamber in chambers],
        "outer_border": outer_border,
        "full_wall_rows": full_rows,
        "full_wall_cols": full_cols,
        "partial_wall_cells": len(structural_walls),
        "output": output,
        "changed": sum(chamber["changed"] for chamber in chambers),
    }


def _general_signature(facts):
    chambers = facts["chambers"]
    states = facts["states"]
    count = facts["chamber_count"]
    if not facts["outer_border"]:
        return "open_edge_chambers" if count >= 3 and "unique" in states else None
    if any(chamber["decoy_cells"] for chamber in chambers):
        return "nonseed_decoys" if "unique" in states else None
    if any(chamber["state"] == "unique" and chamber["seed_cells"] >= 2 for chamber in chambers):
        return "multiple_same_seed"
    if count >= 7:
        return "many_chambers" if "unique" in states and ("blank" in states or "ambiguous" in states) else None
    if facts["partial_wall_cells"]:
        return "t_junction_chambers" if 3 <= count <= 5 else None
    if facts["full_wall_rows"] and not facts["full_wall_cols"]:
        return "horizontal_strips" if 3 <= count <= 5 else None
    if facts["full_wall_cols"] and not facts["full_wall_rows"]:
        return "vertical_strips" if 3 <= count <= 5 else None
    if count == 6:
        return "six_mixed" if set(states) == {"unique", "blank", "ambiguous"} else None
    if count == 4:
        if states == ["unique"] * 4:
            return "four_all_seeded"
        if "unique" in states and "blank" in states and "ambiguous" not in states:
            return "four_seed_blank"
        if "unique" in states and "ambiguous" in states:
            return "four_seed_ambiguous"
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None}
    facts = _extract_facts(grid)
    if not 3 <= facts["chamber_count"] <= 9:
        errors.append(f"expected 3..9 non-5 chambers, got {facts['chamber_count']}")
    if facts["changed"] <= 0:
        errors.append("at least one unique-seed chamber must visibly fill")
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or _general_signature(facts)
    if profile is None:
        errors.append("scene does not match a declared semantic profile")
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": facts["output"]}


def rule_mirror(grid):
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _extract_facts(grid)["output"]


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _size_range(difficulty):
    if difficulty == "easy":
        return (9, 12), (11, 15)
    if difficulty == "medium":
        return (10, 15), (12, 18)
    if difficulty == "hard":
        return (13, 20), (15, 24)
    return (9, 17), (11, 20)


def _cut_positions(size, bands, rng):
    if bands <= 1:
        return []
    minimum = 2
    available = size - 2 - (bands - 1)
    if available < minimum * bands:
        raise ValueError("canvas too small for requested wall bands")
    lengths = [minimum] * bands
    for _ in range(available - minimum * bands):
        lengths[rng.randrange(bands)] += 1
    cuts, cursor = [], 1
    for length in lengths[:-1]:
        cursor += length
        cuts.append(cursor)
        cursor += 1
    return cuts


def _partition_grid(height, width, row_bands, col_bands, rng, *, outer=True):
    grid = [[0 for _ in range(width)] for _ in range(height)]
    row_cuts = _cut_positions(height, row_bands, rng)
    col_cuts = _cut_positions(width, col_bands, rng)
    if outer:
        for col in range(width):
            grid[0][col] = grid[height - 1][col] = 5
        for row in range(height):
            grid[row][0] = grid[row][width - 1] = 5
    for row in row_cuts:
        for col in range(width):
            grid[row][col] = 5
    for col in col_cuts:
        for row in range(height):
            grid[row][col] = 5
    return grid


def _t_junction_grid(height, width, rng):
    grid = _partition_grid(height, width, 1, 3, rng)
    cuts = [col for col in range(1, width - 1) if all(grid[row][col] == 5 for row in range(height))]
    split_row = rng.randint(3, height - 4)
    for col in range(cuts[0], cuts[1] + 1):
        grid[split_row][col] = 5
    return grid


def _merge_partition_chambers(grid, target_count, rng):
    """Open interior wall segments until a 3x3 partition has 7..9 chambers."""
    height, width = len(grid), len(grid[0])
    while len(_components(grid)) > target_count:
        full_rows = [row for row in range(1, height - 1) if all(grid[row][col] == 5 for col in range(width))]
        full_cols = [col for col in range(1, width - 1) if all(grid[row][col] == 5 for row in range(height))]
        row_bounds = [0] + full_rows + [height - 1]
        col_bounds = [0] + full_cols + [width - 1]
        segments = []
        for row in full_rows:
            for left, right in zip(col_bounds, col_bounds[1:]):
                cells = [(row, col) for col in range(left + 1, right)]
                if cells and all(grid[r][c] == 5 for r, c in cells):
                    segments.append(cells)
        for col in full_cols:
            for top, bottom in zip(row_bounds, row_bounds[1:]):
                cells = [(row, col) for row in range(top + 1, bottom)]
                if cells and all(grid[r][c] == 5 for r, c in cells):
                    segments.append(cells)
        before = len(_components(grid))
        rng.shuffle(segments)
        for cells in segments:
            trial = [row[:] for row in grid]
            for row, col in cells:
                trial[row][col] = 0
            if len(_components(trial)) == before - 1:
                grid = trial
                break
        else:
            raise AssertionError("could not open a chamber wall segment")
    return grid


def _paint_state(grid, cells, state, rng):
    candidates = list(cells)
    rng.shuffle(candidates)
    if state.startswith("seed"):
        color = int(state[-1]) if state[-1].isdigit() else rng.randint(1, 3)
        grid[candidates[0][0]][candidates[0][1]] = color
    elif state == "ambiguous":
        first, second = rng.sample([1, 2, 3], 2)
        grid[candidates[0][0]][candidates[0][1]] = first
        grid[candidates[1][0]][candidates[1][1]] = second
    elif state == "multiple":
        color = rng.randint(1, 3)
        for row, col in candidates[:rng.randint(2, min(4, len(candidates) - 1))]:
            grid[row][col] = color
    elif state == "decoy":
        grid[candidates[0][0]][candidates[0][1]] = rng.randint(1, 3)
        decoy_colors = rng.sample([4, 6, 7, 8, 9], rng.randint(1, 3))
        for (row, col), color in zip(candidates[1:], decoy_colors):
            grid[row][col] = color


def _states_for(profile, count, rng):
    seeds = ["seed1", "seed2", "seed3"]
    if profile == "four_all_seeded":
        states = [rng.choice(seeds) for _ in range(count)]
    elif profile == "four_seed_blank":
        states = ["seed1", "seed2", "blank", "blank"]
    elif profile == "four_seed_ambiguous":
        states = ["seed1", "seed3", "ambiguous", "blank"]
    elif profile in {"six_mixed", "many_chambers"}:
        pattern = ["seed1", "blank", "ambiguous", "seed2", "blank", "seed3"]
        states = [pattern[index % len(pattern)] for index in range(count)]
    elif profile in {"horizontal_strips", "vertical_strips", "t_junction_chambers", "open_edge_chambers"}:
        pattern = ["seed1", "blank", "ambiguous", "seed3"]
        states = [pattern[index % len(pattern)] for index in range(count)]
    elif profile == "multiple_same_seed":
        states = ["multiple"] + ["seed2" if index % 2 else "blank" for index in range(1, count)]
    elif profile == "nonseed_decoys":
        states = ["decoy"] + ["seed3" if index % 2 else "blank" for index in range(1, count)]
    else:
        raise ValueError(f"unknown profile: {profile}")
    rng.shuffle(states)
    return states


def _general_scene(ctx, profile, rng):
    (h_low, h_high), (w_low, w_high) = _size_range(ctx.difficulty)
    for _ in range(100):
        height, width = rng.randint(h_low, h_high), rng.randint(w_low, w_high)
        if profile in {"four_all_seeded", "four_seed_blank", "four_seed_ambiguous", "multiple_same_seed", "nonseed_decoys"}:
            grid = _partition_grid(height, width, 2, 2, rng)
        elif profile == "six_mixed":
            grid = _partition_grid(height, width, 2, 3, rng)
        elif profile == "many_chambers":
            grid = _partition_grid(max(height, 11), max(width, 11), 3, 3, rng)
            grid = _merge_partition_chambers(grid, rng.choice((7, 8, 9)), rng)
        elif profile == "horizontal_strips":
            height = max(height, 16)
            grid = _partition_grid(height, width, rng.choice((3, 4, 5)), 1, rng)
        elif profile == "vertical_strips":
            width = max(width, 16)
            grid = _partition_grid(height, width, 1, rng.choice((3, 4, 5)), rng)
        elif profile == "t_junction_chambers":
            grid = _t_junction_grid(height, width, rng)
        elif profile == "open_edge_chambers":
            width = max(width, 10)
            grid = _partition_grid(height, width, 1, rng.choice((3, 4)) if width >= 13 else 3, rng, outer=False)
        else:
            raise ValueError(f"unknown scene_profile: {profile!r}")
        components = _components(grid)
        states = _states_for(profile, len(components), rng)
        for cells, state in zip(components, states):
            _paint_state(grid, cells, state, rng)
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
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES + GENERAL_PROFILES * 4)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(ctx, profile, ctx.draw_rng("geometry"))
