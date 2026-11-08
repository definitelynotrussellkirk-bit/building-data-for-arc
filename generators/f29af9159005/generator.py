"""Semantic generator for ARC task f29af9159005.

For each zero cell, paint 4 when at least one color-2 seed shares its row or
column and no color-1 blocker lies strictly between the seed and that cell.
Existing nonzero cells survive, only color 1 blocks, and visibility from any
seed is sufficient.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "f29af9159005"
TASK_ID = "f29af9159005"
VERSION = "3.0.0"
RULE_HASH = "21f0acd89113"
SUMMARY = "Paint zero cells visible orthogonally from any red seed unless a blue blocker lies strictly between."
INVARIANTS = [
    "literal zero is background, color 2 is a seed, and color 1 is the only blocker",
    "visibility is horizontal or vertical only",
    "the endpoints are excluded when testing blockers between seed and target",
    "a cell is painted when any aligned seed has clear line of sight",
    "existing nonzero cells survive and non-1 values do not block cells beyond them",
    "multiple seed crosses union on the same-size output",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3")
GENERAL_PROFILES = (
    "single_clear_cross",
    "off_axis_decoys",
    "clip_up_adjacent",
    "clip_down_distant",
    "clip_left_right",
    "clip_all_four",
    "aligned_two_seeds",
    "crossing_two_seeds",
    "two_seed_rescue",
    "seed_on_edge",
    "seed_in_corner",
    "non_one_transparent",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "three exact-public and twelve observable line-of-sight lessons",
        "valid": "public_1|public_2|public_3|single_clear_cross|off_axis_decoys|clip_up_adjacent|clip_down_distant|clip_left_right|clip_all_four|aligned_two_seeds|crossing_two_seeds|two_seed_rescue|seed_on_edge|seed_in_corner|non_one_transparent",
    }
}

_PUBLIC_ROWS = {
    "public_1": "0000000/0010000/0002000/0010000/0000000",
    "public_2": "000000000/000100000/000100000/010020010/000100000/000100000/000000000",
    "public_3": "0000000000/0000100000/0000100000/0000200000/1110000111/0000200000/0000100000/0000100000/0000000000",
}


def _decode(text):
    return [[int(value) for value in line] for line in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}
_DIRECTIONS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(line, (list, tuple)) or len(line) != width for line in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for line in grid for value in line):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _between_clear(grid, seed, target):
    seed_row, seed_col = seed
    target_row, target_col = target
    if seed_row == target_row:
        return all(grid[seed_row][col] != 1 for col in range(min(seed_col, target_col) + 1, max(seed_col, target_col)))
    if seed_col == target_col:
        return all(grid[row][seed_col] != 1 for row in range(min(seed_row, target_row) + 1, max(seed_row, target_row)))
    return False


def _rule_facts(grid):
    height, width = len(grid), len(grid[0])
    anchors = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == 2]
    blockers = {(row, col) for row in range(height) for col in range(width) if grid[row][col] == 1}
    other_nonzero = {(row, col): grid[row][col] for row in range(height) for col in range(width) if grid[row][col] not in (0, 1, 2)}
    output = [list(line) for line in grid]
    visible_from = {}
    blocked_from = {}
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                continue
            aligned = [seed for seed in anchors if seed[0] == row or seed[1] == col]
            visible = [seed for seed in aligned if _between_clear(grid, seed, (row, col))]
            blocked = [seed for seed in aligned if seed not in visible]
            if visible:
                output[row][col] = 4
                visible_from[(row, col)] = visible
            if blocked:
                blocked_from[(row, col)] = blocked
    directional_blockers = {}
    for seed in anchors:
        per_direction = {}
        for name, (delta_row, delta_col) in _DIRECTIONS.items():
            distances = []
            row, col, distance = seed[0] + delta_row, seed[1] + delta_col, 1
            while 0 <= row < height and 0 <= col < width:
                if grid[row][col] == 1:
                    distances.append(distance)
                row += delta_row
                col += delta_col
                distance += 1
            if distances:
                per_direction[name] = min(distances)
        directional_blockers[seed] = per_direction
    off_axis = {cell for cell in blockers if not any(cell[0] == seed[0] or cell[1] == seed[1] for seed in anchors)}
    rescue = {cell for cell in visible_from if cell in blocked_from}
    return {
        "seeds": anchors,
        "blockers": blockers,
        "other_nonzero": other_nonzero,
        "visible_from": visible_from,
        "blocked_from": blocked_from,
        "directional_blockers": directional_blockers,
        "off_axis_blockers": off_axis,
        "rescue_cells": rescue,
        "output": output,
        "changed": sum(a != b for line_a, line_b in zip(grid, output) for a, b in zip(line_a, line_b)),
    }


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _rule_facts(grid)["output"]


def _general_profile(facts, height, width):
    anchors = facts["seeds"]
    if facts["other_nonzero"]:
        return "non_one_transparent" if len(anchors) == 1 and len(facts["other_nonzero"]) == 1 else None
    if any(row in (0, height - 1) and col in (0, width - 1) for row, col in anchors):
        return "seed_in_corner" if len(anchors) == 1 and facts["blockers"] == facts["off_axis_blockers"] else None
    if any(row in (0, height - 1) or col in (0, width - 1) for row, col in anchors):
        return "seed_on_edge" if len(anchors) == 1 and facts["blockers"] == facts["off_axis_blockers"] else None
    if len(anchors) == 2:
        if facts["rescue_cells"]:
            return "two_seed_rescue"
        if anchors[0][0] == anchors[1][0] or anchors[0][1] == anchors[1][1]:
            return "aligned_two_seeds" if facts["blockers"] == facts["off_axis_blockers"] else None
        return "crossing_two_seeds" if facts["blockers"] == facts["off_axis_blockers"] else None
    if len(anchors) != 1:
        return None
    directions = facts["directional_blockers"][anchors[0]]
    names = set(directions)
    if not names:
        if facts["blockers"] != facts["off_axis_blockers"]:
            return None
        if len(facts["blockers"]) == 1:
            return "single_clear_cross"
        if 2 <= len(facts["blockers"]) <= 5:
            return "off_axis_decoys"
        return None
    if names == {"up"} and directions["up"] == 1:
        return "clip_up_adjacent"
    if names == {"down"} and directions["down"] >= 2:
        return "clip_down_distant"
    if names == {"left", "right"}:
        return "clip_left_right"
    if names == set(_DIRECTIONS):
        return "clip_all_four"
    return None


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    height, width = len(grid), len(grid[0])
    if height < 5 or width < 5:
        errors.append("both dimensions must be at least five")
    if sum(value == 0 for line in grid for value in line) <= height * width // 2:
        errors.append("literal background 0 must occupy a strict majority of the canvas")
    facts = _rule_facts(grid)
    if not 1 <= len(facts["seeds"]) <= 2:
        errors.append("training scenes require one or two color-2 seeds")
    if len(facts["blockers"]) > 10:
        errors.append("training scenes use at most the canonical maximum of ten color-1 blockers")
    if len(facts["other_nonzero"]) > 1:
        errors.append("only the transparent-obstacle lesson may add one other nonzero cell")
    if facts["changed"] < max(3, int(height * width * 0.02)):
        errors.append("line-of-sight painting must make a material visible change")
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    profile = public
    if not errors and not public:
        profile = _general_profile(facts, height, width)
        if profile not in GENERAL_PROFILES:
            errors.append("scene does not match one declared line-of-sight profile")
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


def _dimensions(difficulty, rng):
    ranges = {
        None: ((6, 10), (8, 13)),
        "easy": ((5, 7), (7, 10)),
        "medium": ((7, 10), (9, 13)),
        "hard": ((10, 15), (12, 18)),
    }
    row_range, col_range = ranges[difficulty]
    return rng.randint(*row_range), rng.randint(*col_range)


def _interior_seed(rng, height, width, *, margin=1):
    return rng.randint(margin, height - margin - 1), rng.randint(margin, width - margin - 1)


def _general_scene(ctx, profile, rng):
    for _ in range(500):
        height, width = _dimensions(ctx.difficulty, rng)
        grid = [[0] * width for _ in range(height)]
        if profile in ("clip_all_four", "clip_left_right"):
            seed_row, seed_col = _interior_seed(rng, height, width, margin=2)
        else:
            seed_row, seed_col = _interior_seed(rng, height, width)
        grid[seed_row][seed_col] = 2
        if profile in ("single_clear_cross", "off_axis_decoys"):
            candidates = [(row, col) for row in range(height) for col in range(width) if row != seed_row and col != seed_col]
            rng.shuffle(candidates)
            count = 1 if profile == "single_clear_cross" else rng.randint(2, min(5, len(candidates)))
            for row, col in candidates[:count]:
                grid[row][col] = 1
        elif profile == "clip_up_adjacent":
            grid[seed_row - 1][seed_col] = 1
        elif profile == "clip_down_distant":
            if height - seed_row - 1 < 2:
                continue
            distance = rng.randint(2, height - seed_row - 1)
            grid[seed_row + distance][seed_col] = 1
        elif profile == "clip_left_right":
            grid[seed_row][seed_col - rng.randint(1, seed_col)] = 1
            grid[seed_row][seed_col + rng.randint(1, width - seed_col - 1)] = 1
        elif profile == "clip_all_four":
            grid[seed_row - rng.randint(2, seed_row)][seed_col] = 1
            grid[seed_row + rng.randint(2, height - seed_row - 1)][seed_col] = 1
            grid[seed_row][seed_col - rng.randint(2, seed_col)] = 1
            grid[seed_row][seed_col + rng.randint(2, width - seed_col - 1)] = 1
        elif profile == "aligned_two_seeds":
            candidates = [(row, seed_col) for row in range(1, height - 1) if row != seed_row and abs(row - seed_row) >= 2]
            if not candidates:
                continue
            second = rng.choice(candidates)
            grid[second[0]][second[1]] = 2
        elif profile in ("crossing_two_seeds", "two_seed_rescue"):
            candidates = [(row, col) for row in range(1, height - 1) for col in range(1, width - 1) if row != seed_row and col != seed_col and abs(col - seed_col) >= (2 if profile == "two_seed_rescue" else 1)]
            if not candidates:
                continue
            second = rng.choice(candidates)
            grid[second[0]][second[1]] = 2
            if profile == "two_seed_rescue":
                step = 1 if second[1] > seed_col else -1
                grid[seed_row][seed_col + step] = 1
        elif profile == "seed_on_edge":
            grid[seed_row][seed_col] = 0
            side = rng.choice(("top", "bottom", "left", "right"))
            if side in ("top", "bottom"):
                seed_row, seed_col = (0 if side == "top" else height - 1), rng.randint(1, width - 2)
            else:
                seed_row, seed_col = rng.randint(1, height - 2), (0 if side == "left" else width - 1)
            grid[seed_row][seed_col] = 2
            decoys = [(row, col) for row in range(height) for col in range(width) if row != seed_row and col != seed_col]
            rng.shuffle(decoys)
            for row, col in decoys[: rng.randint(1, 3)]:
                grid[row][col] = 1
        elif profile == "seed_in_corner":
            grid[seed_row][seed_col] = 0
            seed_row, seed_col = rng.choice(((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)))
            grid[seed_row][seed_col] = 2
            decoys = [(row, col) for row in range(height) for col in range(width) if row != seed_row and col != seed_col]
            rng.shuffle(decoys)
            for row, col in decoys[: rng.randint(1, 3)]:
                grid[row][col] = 1
        elif profile == "non_one_transparent":
            direction = rng.choice(((0, 1), (1, 0)))
            if seed_row + direction[0] >= height or seed_col + direction[1] >= width:
                continue
            grid[seed_row + direction[0]][seed_col + direction[1]] = rng.choice((3, 4, 5, 6, 7, 8, 9))
        if profile in ("clip_up_adjacent", "clip_down_distant", "clip_left_right", "clip_all_four", "aligned_two_seeds", "crossing_two_seeds"):
            current_seeds = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == 2]
            decoys = [
                (row, col)
                for row in range(height)
                for col in range(width)
                if grid[row][col] == 0 and all(row != anchor_row and col != anchor_col for anchor_row, anchor_col in current_seeds)
            ]
            rng.shuffle(decoys)
            for row, col in decoys[: rng.randint(1, min(3, len(decoys)))]:
                grid[row][col] = 1
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
    if profile in PUBLIC_PROFILES:
        return [line[:] for line in _PUBLIC_INPUTS[profile]]
    grid = _general_scene(ctx, profile, ctx.draw_rng("geometry"))
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError(f"internal profile drift: {profile} -> {analysis}")
    return grid
