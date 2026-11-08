"""Semantic generator for ARC task f13d23b71bd4.

Extract monochrome 4-connected objects against literal background 7. Objects
of size four or more fall until their own bottom reaches the canvas bottom;
smaller objects stay. Repaint onto a fresh background in row-major object
order, so later objects win any landing collision.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "f13d23b71bd4"
TASK_ID = "f13d23b71bd4"
VERSION = "3.0.0"
RULE_HASH = "71a162d2019e"
SUMMARY = "Drop each monochrome 4-connected object of size at least four to the bottom on a fresh color-7 canvas."
INVARIANTS = [
    "literal color 7 is the background",
    "objects are monochrome 4-connected components",
    "object size three stays while size four falls",
    "a falling object's vertical shift is canvas-bottom minus its own bottom row",
    "object shape and color are preserved by translation",
    "the result starts as a fresh color-7 canvas",
    "objects are repainted in row-major discovery order so later landing collisions overwrite earlier ones",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "threshold_3_vs_4",
    "same_color_thresholds",
    "mixed_sizes_1_to_6",
    "different_colors_touch",
    "diagonal_same_color",
    "wide_fall",
    "tall_fall",
    "irregular_fall",
    "already_bottom_big",
    "landing_overlap_small_wins",
    "landing_overlap_later_big_wins",
    "many_colors",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and twelve observable size-gravity lessons",
        "valid": "public_1|public_2|public_3|public_4|threshold_3_vs_4|same_color_thresholds|mixed_sizes_1_to_6|different_colors_touch|diagonal_same_color|wide_fall|tall_fall|irregular_fall|already_bottom_big|landing_overlap_small_wins|landing_overlap_later_big_wins|many_colors",
    }
}

_PUBLIC_ROWS = {
    "public_1": "7777777/7667667/7767667/7777767/7777767/7777777/7777777",
    "public_2": "777777777777777/755777777555777/755777557555777/777757557555757/777777557777757/777777777777757/777777777777777/777777777777777/777777777777777/777777777777777/777777777777777/777777777777777/777777777777777/777777777777777/777777777777777",
    "public_3": "7777777777777777/7117777777777777/7117177777711117/7117177777717717/7117777777711117/7117777771777777/7777777771777777/7777777771777777/7777777177777777/7777771177777777/7777771177777777/7777777777777777/7777777777777777/7777777777777777/7777777777777777/7777777777777777",
    "public_4": "77777777777777/74474747447447/74474777447447/77774774447447/77777774447447/77777777777777/77777777777777/77777777777777/77777777777777/77777777777777/77777777777777/77777777777777/77777777777777/77777777777777",
}


def _decode(text):
    return [[int(value) for value in line] for line in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SHAPES = {
    1: ((0, 0),),
    2: ((0, 0), (0, 1)),
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (0, 1), (1, 0), (1, 1)),
    5: ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
}
_WIDE = tuple((0, col) for col in range(6))
_TALL = tuple((row, 0) for row in range(6))
_IRREGULAR = ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3))


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


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 7 or (row, col) in seen:
                continue
            color = grid[row][col]
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.pop(0)
                cells.append((current_row, current_col))
                for delta_row, delta_col in _NEIGHBORS:
                    next_row, next_col = current_row + delta_row, current_col + delta_col
                    if 0 <= next_row < height and 0 <= next_col < width and (next_row, next_col) not in seen and grid[next_row][next_col] == color:
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))
            row_values = [cell[0] for cell in cells]
            col_values = [cell[1] for cell in cells]
            bbox = (min(row_values), min(col_values), max(row_values), max(col_values))
            drop = height - 1 - bbox[2] if len(cells) >= 4 else 0
            target = {(cell_row + drop, cell_col) for cell_row, cell_col in cells}
            box_height, box_width = bbox[2] - bbox[0] + 1, bbox[3] - bbox[1] + 1
            if box_width >= 5 and box_width > box_height * 2:
                shape_kind = "wide"
            elif box_height >= 5 and box_height > box_width * 2:
                shape_kind = "tall"
            elif len(cells) < box_height * box_width:
                shape_kind = "irregular"
            else:
                shape_kind = "compact"
            result.append({
                "color": color,
                "cells": set(cells),
                "bbox": bbox,
                "size": len(cells),
                "drop": drop,
                "target": target,
                "shape_kind": shape_kind,
            })
    return result


def _rule_facts(grid):
    height, width = len(grid), len(grid[0])
    pieces = _components(grid)
    output = [[7] * width for _ in range(height)]
    landing_owners = {}
    for index, obj in enumerate(pieces):
        for row, col in obj["target"]:
            landing_owners.setdefault((row, col), []).append(index)
            output[row][col] = obj["color"]
    collisions = {cell: owners for cell, owners in landing_owners.items() if len(owners) > 1}
    touching = set()
    diagonal_same_color = set()
    for left in range(len(pieces)):
        for right in range(left + 1, len(pieces)):
            if any(abs(ar - br) + abs(ac - bc) == 1 for ar, ac in pieces[left]["cells"] for br, bc in pieces[right]["cells"]):
                touching.add((left, right))
            if pieces[left]["color"] == pieces[right]["color"] and any(abs(ar - br) == 1 and abs(ac - bc) == 1 for ar, ac in pieces[left]["cells"] for br, bc in pieces[right]["cells"]):
                diagonal_same_color.add((left, right))
    collision_pairs = {
        tuple(pair)
        for owners in collisions.values()
        for pair in ((owners[left], owners[right]) for left in range(len(owners)) for right in range(left + 1, len(owners)))
    }
    return {
        "objects": pieces,
        "output": output,
        "collisions": collisions,
        "collision_pairs": collision_pairs,
        "different_color_touching": {(left, right) for left, right in touching if pieces[left]["color"] != pieces[right]["color"]},
        "diagonal_same_color": diagonal_same_color,
        "changed": sum(a != b for line_a, line_b in zip(grid, output) for a, b in zip(line_a, line_b)),
    }


def rule_mirror(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _rule_facts(grid)["output"]


def _general_profile(facts):
    pieces = facts["objects"]
    sizes = sorted(obj["size"] for obj in pieces)
    if facts["collision_pairs"]:
        has_small = any(pieces[index]["size"] < 4 for pair in facts["collision_pairs"] for index in pair)
        return "landing_overlap_small_wins" if has_small else "landing_overlap_later_big_wins"
    if facts["different_color_touching"]:
        return "different_colors_touch"
    if facts["diagonal_same_color"]:
        return "diagonal_same_color"
    if any(obj["size"] >= 4 and obj["drop"] == 0 for obj in pieces) and any(obj["size"] >= 4 and obj["drop"] > 0 for obj in pieces):
        return "already_bottom_big"
    if len(pieces) == 6 and sizes == [1, 2, 3, 4, 5, 6]:
        return "mixed_sizes_1_to_6"
    if len(pieces) == 2 and sizes == [3, 4]:
        return "same_color_thresholds" if len({obj["color"] for obj in pieces}) == 1 else "threshold_3_vs_4"
    if len(pieces) == 2 and sum(obj["size"] < 4 for obj in pieces) == 1:
        big = next(obj for obj in pieces if obj["size"] >= 4)
        if big["shape_kind"] == "wide":
            return "wide_fall"
        if big["shape_kind"] == "tall":
            return "tall_fall"
        if big["shape_kind"] == "irregular":
            return "irregular_fall"
    if len(pieces) == 5 and len({obj["color"] for obj in pieces}) == 5:
        return "many_colors"
    return None


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    height, width = len(grid), len(grid[0])
    if height < 6 or width < 6:
        errors.append("both dimensions must be at least six")
    if sum(value == 7 for line in grid for value in line) <= height * width // 2:
        errors.append("literal background 7 must occupy a strict majority of the canvas")
    facts = _rule_facts(grid)
    pieces = facts["objects"]
    if not 2 <= len(pieces) <= 6:
        errors.append("training scenes require two to six monochrome objects")
    if any(not 1 <= obj["size"] <= 10 for obj in pieces):
        errors.append("calibrated object sizes are one through ten")
    if not any(obj["size"] >= 4 and obj["drop"] > 0 for obj in pieces):
        errors.append("at least one threshold object must visibly fall")
    if facts["changed"] < max(2, int(height * width * 0.01)):
        errors.append("gravity must make a material visible change")
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    profile = public
    if not errors and not public:
        profile = _general_profile(facts)
        if profile not in GENERAL_PROFILES:
            errors.append("scene does not match one declared size-gravity profile")
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


def _dimensions(difficulty, profile, rng):
    ranges = {
        None: ((10, 17), (10, 18)),
        "easy": ((7, 11), (7, 12)),
        "medium": ((11, 17), (11, 18)),
        "hard": ((15, 21), (15, 22)),
    }
    row_range, col_range = ranges[difficulty]
    height, width = rng.randint(*row_range), rng.randint(*col_range)
    if profile in ("mixed_sizes_1_to_6", "many_colors"):
        height, width = max(height, 13), max(width, 15)
    if profile.startswith("landing_overlap"):
        height, width = max(height, 10), max(width, 8)
    return height, width


def _place(grid, shape, color, rng, *, bottom=False, allow_touch=False):
    height, width = len(grid), len(grid[0])
    shape_height = max(row for row, _ in shape) + 1
    shape_width = max(col for _, col in shape) + 1
    row_values = [height - shape_height] if bottom else list(range(max(0, height - shape_height - 1)))
    origins = [(row, col) for row in row_values for col in range(width - shape_width + 1)]
    rng.shuffle(origins)
    for origin_row, origin_col in origins:
        cells = {(origin_row + row, origin_col + col) for row, col in shape}
        if any(grid[row][col] != 7 for row, col in cells):
            continue
        if not allow_touch and any(
            grid[next_row][next_col] != 7 and (next_row, next_col) not in cells
            for row, col in cells
            for delta_row, delta_col in _NEIGHBORS
            for next_row, next_col in ((row + delta_row, col + delta_col),)
            if 0 <= next_row < height and 0 <= next_col < width
        ):
            continue
        for row, col in cells:
            grid[row][col] = color
        return True
    return False


def _set_cells(grid, cells, color):
    if any(not (0 <= row < len(grid) and 0 <= col < len(grid[0])) or grid[row][col] != 7 for row, col in cells):
        return False
    for row, col in cells:
        grid[row][col] = color
    return True


def _general_scene(ctx, profile, rng):
    available_colors = [value for value in range(10) if value != 7]
    for _ in range(1000):
        height, width = _dimensions(ctx.difficulty, profile, rng)
        grid = [[7] * width for _ in range(height)]
        colors = rng.sample(available_colors, 7)
        success = True
        if profile in ("threshold_3_vs_4", "same_color_thresholds"):
            second_color = colors[0] if profile == "same_color_thresholds" else colors[1]
            success = _place(grid, _SHAPES[3], colors[0], rng) and _place(grid, _SHAPES[4], second_color, rng)
        elif profile == "mixed_sizes_1_to_6":
            for size in range(1, 7):
                success = success and _place(grid, _SHAPES[size], colors[0], rng)
        elif profile == "different_colors_touch":
            row, col = rng.randint(1, height - 5), rng.randint(1, width - 5)
            left = {(row, col), (row, col + 1), (row + 1, col), (row + 1, col + 1)}
            right = {(row, col + 2), (row + 1, col + 2), (row + 2, col + 2)}
            success = _set_cells(grid, left, colors[0]) and _set_cells(grid, right, colors[1])
        elif profile == "diagonal_same_color":
            row, col = rng.randint(1, height - 5), rng.randint(1, width - 5)
            success = _set_cells(grid, {(row, col), (row + 1, col + 1)}, colors[0])
            success = success and _place(grid, _SHAPES[4], colors[0], rng)
        elif profile in ("wide_fall", "tall_fall", "irregular_fall"):
            shape = {"wide_fall": _WIDE, "tall_fall": _TALL, "irregular_fall": _IRREGULAR}[profile]
            success = _place(grid, shape, colors[0], rng) and _place(grid, _SHAPES[2], colors[0], rng)
        elif profile == "already_bottom_big":
            success = _place(grid, _SHAPES[4], colors[0], rng, bottom=True)
            success = success and _place(grid, _SHAPES[5], colors[0], rng) and _place(grid, _SHAPES[2], colors[0], rng)
        elif profile == "landing_overlap_small_wins":
            col = rng.randint(1, width - 2)
            top = rng.randint(0, max(0, height - 9))
            big = {(top + offset, col) for offset in range(4)}
            small = {(height - 2, col)}
            success = _set_cells(grid, big, colors[0]) and _set_cells(grid, small, colors[1])
        elif profile == "landing_overlap_later_big_wins":
            col = rng.randint(1, width - 3)
            first = {(1, col), (1, col + 1), (2, col), (2, col + 1)}
            second = {(4, col), (4, col + 1), (5, col), (5, col + 1)}
            success = _set_cells(grid, first, colors[0]) and _set_cells(grid, second, colors[1])
        elif profile == "many_colors":
            for size in range(1, 6):
                success = success and _place(grid, _SHAPES[size], colors[size - 1], rng)
        if not success:
            continue
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
        return [line[:] for line in _PUBLIC_INPUTS[profile]]
    grid = _general_scene(ctx, profile, ctx.draw_rng("geometry"))
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError(f"internal profile drift: {profile} -> {analysis}")
    return grid
