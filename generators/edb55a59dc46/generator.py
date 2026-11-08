"""Semantic generator for ARC task edb55a59dc46.

Read the first two nonzero values in the top row as an ordered palette, find
the first color-9 seed in row-major order, and draw four rays from that seed.
Each ray starts at palette index zero, advances its phase at every coordinate,
and paints only cells that are currently zero.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "edb55a59dc46"
TASK_ID = "edb55a59dc46"
VERSION = "3.0.0"
RULE_HASH = "200170356545"
SUMMARY = "Cycle the top row's first two nonzero colors along four zero-only rays from the first color-9 seed."
INVARIANTS = [
    "the first two nonzero top-row values are distinct non-9 driving colors",
    "the first color-9 cell in row-major order is the ray seed",
    "each direction restarts palette phase at zero",
    "phase advances at every in-bounds coordinate, including occupied cells",
    "only cells that are zero in the evolving result are painted",
    "existing palette markers, seeds, obstacles, and distractors survive",
    "rays clip naturally at canvas boundaries and output size is unchanged",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = (
    "baseline_interior",
    "separated_header",
    "header_on_ray",
    "seed_near_top",
    "seed_on_edge",
    "seed_in_corner",
    "occupied_ray_steps",
    "third_header_ignored",
    "off_ray_distractors",
    "multiple_seeds_first",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five exact-public and ten observable ordered-ray lessons",
        "valid": "public_1|public_2|public_3|public_4|public_5|baseline_interior|separated_header|header_on_ray|seed_near_top|seed_on_edge|seed_in_corner|occupied_ray_steps|third_header_ignored|off_ray_distractors|multiple_seeds_first",
    }
}

_PUBLIC_ROWS = {
    "public_1": "028000000/000000000/000000000/000009000/000000000/000000000/000000000",
    "public_2": "03400000/00000000/00000000/00000000/00000000/00900000/00000000/00000000",
    "public_3": "0760000000/0000000000/0000000900/0000000000/0000000000/0000000000",
    "public_4": "0520000/0000000/0000000/0000000/0000000/0000000/0009000/0000000/0000000",
    "public_5": "04700000000/00000000000/00000000000/00000000000/00000000900/00000000000/00000000000/00000000000",
}


def _decode(text):
    return [[int(value) for value in line] for line in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}
_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


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


def _rule_facts(grid):
    height, width = len(grid), len(grid[0])
    header_cells = [(0, col, grid[0][col]) for col in range(width) if grid[0][col] != 0]
    seed_cells = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == 9]
    if len(header_cells) < 2:
        raise ValueError("top row must supply at least two nonzero palette values")
    if not seed_cells:
        raise ValueError("grid must contain a color-9 seed")
    driving_colors = (header_cells[0][2], header_cells[1][2])
    seed = seed_cells[0]
    output = [list(line) for line in grid]
    ray_steps = {}
    for direction_index, (delta_row, delta_col) in enumerate(_DIRECTIONS):
        row, col = seed[0] + delta_row, seed[1] + delta_col
        step = 0
        while 0 <= row < height and 0 <= col < width:
            ray_steps[(row, col)] = (direction_index, step)
            if output[row][col] == 0:
                output[row][col] = driving_colors[step % 2]
            row += delta_row
            col += delta_col
            step += 1
    header_coords = {(row, col) for row, col, _ in header_cells}
    all_seed_coords = set(seed_cells)
    obstacle_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0 and (row, col) not in header_coords and (row, col) not in all_seed_coords
    }
    ray_coords = set(ray_steps)
    return {
        "header_cells": header_cells,
        "driving_colors": driving_colors,
        "seed_cells": seed_cells,
        "seed": seed,
        "ray_steps": ray_steps,
        "header_on_ray": bool(header_coords & ray_coords),
        "obstacle_cells": obstacle_cells,
        "ray_obstacles": obstacle_cells & ray_coords,
        "off_ray_obstacles": obstacle_cells - ray_coords,
        "extents": (seed[0], height - seed[0] - 1, seed[1], width - seed[1] - 1),
        "output": output,
        "changed": sum(a != b for line_a, line_b in zip(grid, output) for a, b in zip(line_a, line_b)),
    }


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _rule_facts(grid)["output"]


def _general_profile(facts, height, width):
    header_cells = facts["header_cells"]
    seed_cells = facts["seed_cells"]
    seed_row, seed_col = facts["seed"]
    if len(header_cells) == 3:
        if len(seed_cells) == 1 and not facts["obstacle_cells"] and not facts["header_on_ray"]:
            return "third_header_ignored"
        return None
    if len(seed_cells) == 2:
        if len(header_cells) == 2 and not facts["obstacle_cells"] and not facts["header_on_ray"]:
            return "multiple_seeds_first"
        return None
    if facts["obstacle_cells"]:
        if len(facts["obstacle_cells"]) == 2 and facts["ray_obstacles"] == facts["obstacle_cells"] and not facts["header_on_ray"]:
            return "occupied_ray_steps"
        if 1 <= len(facts["obstacle_cells"]) <= 3 and facts["off_ray_obstacles"] == facts["obstacle_cells"] and not facts["header_on_ray"]:
            return "off_ray_distractors"
        return None
    if seed_row in (0, height - 1) and seed_col in (0, width - 1):
        return "seed_in_corner"
    if seed_row in (0, height - 1) or seed_col in (0, width - 1):
        return "seed_on_edge"
    if seed_row == 1:
        return "seed_near_top"
    if facts["header_on_ray"]:
        return "header_on_ray"
    header_cols = [col for _, col, _ in header_cells]
    if header_cols[1] - header_cols[0] > 1:
        return "separated_header"
    return "baseline_interior"


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    height, width = len(grid), len(grid[0])
    if height < 6 or width < 6:
        errors.append("both dimensions must be at least six")
    try:
        facts = _rule_facts(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return result
    header_cells = facts["header_cells"]
    if len(header_cells) not in (2, 3):
        errors.append("training scenes require two driving header cells and at most one ignored header cell")
    if len(header_cells) >= 2:
        driving = facts["driving_colors"]
        if 9 in driving or driving[0] == driving[1]:
            errors.append("the first two header values must be distinct non-9 colors")
    if len(header_cells) == 3 and (header_cells[2][2] == 9 or len({value for _, _, value in header_cells}) != 3):
        errors.append("the ignored third header value must be a distinct non-9 color")
    if len(facts["seed_cells"]) not in (1, 2):
        errors.append("training scenes require one or two color-9 cells")
    if facts["seed"][0] == 0:
        errors.append("the first color-9 seed must be below the header row")
    if any(grid[row][col] == 9 for row, col in facts["obstacle_cells"]):
        errors.append("additional color-9 cells must be classified as seeds")
    if facts["changed"] < max(4, int(height * width * 0.02)):
        errors.append("the four-ray transformation must make a material visible change")
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    profile = public
    if not errors and not public:
        profile = _general_profile(facts, height, width)
        if profile not in GENERAL_PROFILES:
            errors.append("scene does not match one declared ordered-ray profile")
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
        None: ((7, 13), (8, 16)),
        "easy": ((6, 10), (7, 13)),
        "medium": ((8, 13), (9, 16)),
        "hard": ((10, 15), (11, 18)),
    }
    row_range, col_range = ranges[difficulty]
    return rng.randint(*row_range), rng.randint(*col_range)


def _header_columns(rng, width, seed_col, profile):
    if profile == "header_on_ray":
        other = rng.choice([col for col in range(width) if col != seed_col])
        return sorted((seed_col, other))
    count = 3 if profile == "third_header_ignored" else 2
    allowed = [col for col in range(width) if col != seed_col]
    if profile == "separated_header":
        choices = [(left, right) for left in allowed for right in allowed if left < right and right - left >= 2]
        return list(rng.choice(choices))
    if count == 3:
        choices = [(a, b, c) for a in allowed for b in allowed for c in allowed if a < b < c]
        return list(rng.choice(choices))
    choices = [(col, col + 1) for col in range(width - 1) if col != seed_col and col + 1 != seed_col]
    return list(rng.choice(choices))


def _seed_position(rng, height, width, profile):
    if profile == "seed_near_top":
        return 1, rng.randint(1, width - 2)
    if profile == "seed_on_edge":
        side = rng.choice(("bottom", "left", "right"))
        if side == "bottom":
            return height - 1, rng.randint(1, width - 2)
        return rng.randint(2, height - 2), 0 if side == "left" else width - 1
    if profile == "seed_in_corner":
        return height - 1, rng.choice((0, width - 1))
    if profile == "occupied_ray_steps":
        return rng.randint(2, height - 4), rng.randint(2, width - 4)
    if profile == "multiple_seeds_first":
        return rng.randint(1, height - 4), rng.randint(1, width - 2)
    return rng.randint(2, height - 2), rng.randint(1, width - 2)


def _general_scene(ctx, profile, rng):
    for _ in range(500):
        height, width = _dimensions(ctx.difficulty, rng)
        seed_row, seed_col = _seed_position(rng, height, width, profile)
        header_cols = _header_columns(rng, width, seed_col, profile)
        color_pool = list(range(1, 9))
        chosen = rng.sample(color_pool, 5)
        grid = [[0] * width for _ in range(height)]
        for index, col in enumerate(header_cols):
            grid[0][col] = chosen[index]
        grid[seed_row][seed_col] = 9
        if profile == "occupied_ray_steps":
            grid[seed_row + 1][seed_col] = chosen[2]
            grid[seed_row][seed_col + 2] = chosen[3]
        elif profile == "off_ray_distractors":
            candidates = [
                (row, col)
                for row in range(1, height)
                for col in range(width)
                if row != seed_row and col != seed_col and grid[row][col] == 0
            ]
            rng.shuffle(candidates)
            for index, (row, col) in enumerate(candidates[: rng.randint(1, 3)]):
                grid[row][col] = chosen[2 + index % 3]
        elif profile == "multiple_seeds_first":
            candidates = [
                (row, col)
                for row in range(seed_row + 1, height)
                for col in range(width)
                if row != seed_row and col != seed_col
            ]
            second_seed = rng.choice(candidates)
            grid[second_seed[0]][second_seed[1]] = 9
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
