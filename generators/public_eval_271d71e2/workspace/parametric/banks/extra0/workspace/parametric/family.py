"""Moving-frame progress family for public ARC task 271d71e2."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import itertools
from functools import lru_cache
import json
import random

GENERATOR_ID = TASK_ID = "public_eval_271d71e2"
RULE_TASK_ID = 'ee_271d71e2'
VERSION = "1.0.0"
SUMMARY = "Move each framed progress panel toward its matching bar, capped by remaining gray cells, and advance its directional fill sweep."
INVARIANTS = [
    "background 6 contains complete black rectangular frames",
    "each frame has one attached red bar and one collinear same-span red target bar",
    "frame travel is capped by the count of gray interior cells",
    "each traveled cell converts one gray interior cell to orange",
]
AXES = {}
MODES = ("clockwise", "counterclockwise", "no_fill", "full_distance")
BG, FRAME, EMPTY, FILL, BAR = 6, 0, 5, 7, 9
SIDES = ("up", "right", "down", "left")


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(value: object) -> str:
    if type(value) is not str or value not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return value


def _grid(value: object) -> list[list[int]]:
    if type(value) is not list or not 3 <= len(value) <= 30:
        raise ValueError("grid height must be an exact list in 3..30")
    if type(value[0]) is not list or not 3 <= len(value[0]) <= 30:
        raise ValueError("grid width must be in 3..30")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width for row in value):
        raise ValueError("rectangular exact list rows required")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in value for cell in row):
        raise ValueError("exact integer ARC colors 0..9 required")
    return [row[:] for row in value]


def _find_frames(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    height, width = len(grid), len(grid[0])
    found = []
    for r0 in range(height):
        for c0 in range(width):
            if grid[r0][c0] != FRAME:
                continue
            if r0 and grid[r0 - 1][c0] == FRAME:
                continue
            if c0 and grid[r0][c0 - 1] == FRAME:
                continue
            c1 = c0
            while c1 + 1 < width and grid[r0][c1 + 1] == FRAME:
                c1 += 1
            r1 = r0
            while r1 + 1 < height and grid[r1 + 1][c0] == FRAME:
                r1 += 1
            if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
                continue
            valid = True
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    border = r in (r0, r1) or c in (c0, c1)
                    valid &= grid[r][c] == FRAME if border else grid[r][c] in (EMPTY, FILL)
            if valid:
                found.append((r0, c0, r1, c1))
    if not found:
        raise ValueError("at least one complete black frame required")
    return found


def _attached_line(side: str, box: tuple[int, int, int, int], height: int, width: int) -> list[tuple[int, int]]:
    r0, c0, r1, c1 = box
    if side == "up" and r0 > 0:
        return [(r0 - 1, c) for c in range(c0, c1 + 1)]
    if side == "down" and r1 + 1 < height:
        return [(r1 + 1, c) for c in range(c0, c1 + 1)]
    if side == "left" and c0 > 0:
        return [(r, c0 - 1) for r in range(r0, r1 + 1)]
    if side == "right" and c1 + 1 < width:
        return [(r, c1 + 1) for r in range(r0, r1 + 1)]
    return []


def _line_at(side: str, box: tuple[int, int, int, int], coordinate: int) -> list[tuple[int, int]]:
    r0, c0, r1, c1 = box
    if side in ("up", "down"):
        return [(coordinate, c) for c in range(c0, c1 + 1)]
    return [(r, coordinate) for r in range(r0, r1 + 1)]


def _sweep(box: tuple[int, int, int, int], side: str, mode: str) -> list[tuple[int, int]]:
    r0, c0, r1, c1 = box
    rows = list(range(r0 + 1, r1))
    columns = list(range(c0 + 1, c1))
    if side == "up":
        return [(r, c) for r in rows for c in (columns if mode != "counterclockwise" else columns[::-1])]
    if side == "down":
        return [(r, c) for r in rows[::-1] for c in (columns[::-1] if mode != "counterclockwise" else columns)]
    if side == "right":
        return [(r, c) for c in columns[::-1] for r in (rows if mode != "counterclockwise" else rows[::-1])]
    if side == "left":
        return [(r, c) for c in columns for r in (rows[::-1] if mode != "counterclockwise" else rows)]
    raise AssertionError(side)


def _record(grid: list[list[int]], box: tuple[int, int, int, int], mode: str) -> dict[str, object]:
    height, width = len(grid), len(grid[0])
    attached_sides = []
    for side in SIDES:
        cells = _attached_line(side, box, height, width)
        if cells and all(grid[r][c] == BAR for r, c in cells):
            attached_sides.append(side)
    if len(attached_sides) != 1:
        raise ValueError(f"frame must have exactly one attached bar, found {attached_sides}")
    side = attached_sides[0]
    r0, c0, r1, c1 = box
    if side == "up":
        attached_coordinate, candidates = r0 - 1, range(r0 - 2, -1, -1)
    elif side == "down":
        attached_coordinate, candidates = r1 + 1, range(r1 + 2, height)
    elif side == "left":
        attached_coordinate, candidates = c0 - 1, range(c0 - 2, -1, -1)
    else:
        attached_coordinate, candidates = c1 + 1, range(c1 + 2, width)
    targets = [coordinate for coordinate in candidates
               if all(grid[r][c] == BAR for r, c in _line_at(side, box, coordinate))]
    if not targets:
        raise ValueError("attached bar requires an outward collinear target bar")
    target_coordinate = targets[0]
    distance = abs(target_coordinate - attached_coordinate)
    gray_count = sum(grid[r][c] == EMPTY
                     for r in range(r0 + 1, r1) for c in range(c0 + 1, c1))
    actual_travel = distance if mode == "full_distance" else min(distance, gray_count)
    fill_count = 0 if mode == "no_fill" else actual_travel
    sweep_mode = "counterclockwise" if mode == "counterclockwise" else "clockwise"
    available = [(r, c) for r, c in _sweep(box, side, sweep_mode) if grid[r][c] == EMPTY]
    filled_cells = available[:fill_count]
    dr, dc = {
        "up": (-actual_travel, 0), "down": (actual_travel, 0),
        "left": (0, -actual_travel), "right": (0, actual_travel),
    }[side]
    return {
        "box": list(box), "side": side,
        "attached_coordinate": attached_coordinate, "target_coordinate": target_coordinate,
        "distance": distance, "gray_count": gray_count, "actual_travel": actual_travel,
        "translation": [dr, dc], "filled_cells": [list(p) for p in filled_cells],
        "attached_cells": [list(p) for p in _attached_line(side, box, height, width)],
    }


def analyze(grid: object, mode: str = "clockwise") -> dict[str, object]:
    selected_mode = _mode(mode)
    copied = _grid(grid)
    records = [_record(copied, box, selected_mode) for box in _find_frames(copied)]
    output = [row[:] for row in copied]
    # Clear all moving panels first so composition is independent of source order.
    for record in records:
        travel = record["actual_travel"]
        if not travel:
            continue
        r0, c0, r1, c1 = record["box"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                output[r][c] = BG
        for r, c in record["attached_cells"]:
            output[r][c] = BG
    for record in records:
        r0, c0, r1, c1 = record["box"]
        dr, dc = record["translation"]
        chosen = {tuple(p) for p in record["filled_cells"]}
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                value = FILL if (r, c) in chosen else copied[r][c]
                output[r + dr][c + dc] = value
        for r, c in record["attached_cells"]:
            output[r + dr][c + dc] = BAR
    return {"height": len(copied), "width": len(copied[0]), "mode": selected_mode,
            "objects": records, "output": output}


def solve(grid: object, mode: str = "clockwise") -> list[list[int]]:
    return analyze(grid, mode)["output"]


def self_check(grid: object) -> list[str]:
    try:
        normal = analyze(grid, "clockwise")
        alternate = analyze(grid, "counterclockwise")
        if normal["output"] == alternate["output"]:
            return ["clockwise and counterclockwise must differ on admitted generated inputs"]
        if not any(row["distance"] > min(row["distance"], row["gray_count"]) for row in normal["objects"]):
            return ["generated input must contain a progress-capped object"]
    except (TypeError, ValueError) as error:
        return [str(error)]
    return []


def _rng(seed: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"271d71e2/{seed}/{label}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _case_shape(profile: int) -> tuple[int, int, int]:
    if profile % 10 == 9:
        return 30, 30, 4
    shapes = [(12, 12, 2), (15, 18, 2), (18, 15, 3), (20, 20, 3),
              (22, 26, 3), (26, 22, 3), (24, 24, 3), (17, 17, 3)]
    return shapes[profile % len(shapes)]


def _shift_cells(cells: set[tuple[int, int]], dr: int, dc: int) -> set[tuple[int, int]]:
    return {(r + dr, c + dc) for r, c in cells}


def _pad(cells: set[tuple[int, int]], height: int, width: int) -> set[tuple[int, int]]:
    return {(rr, cc) for r, c in cells for rr in range(max(0, r - 1), min(height, r + 2))
            for cc in range(max(0, c - 1), min(width, c + 2))}


def _try_object(grid: list[list[int]], occupied: set[tuple[int, int]], rng: random.Random,
                role: str) -> set[tuple[int, int]] | None:
    height, width = len(grid), len(grid[0])
    outer_h, outer_w = rng.randint(4, 7), rng.randint(4, 7)
    r0 = rng.randint(1, height - outer_h - 1)
    c0 = rng.randint(1, width - outer_w - 1)
    r1, c1 = r0 + outer_h - 1, c0 + outer_w - 1
    feasible = []
    for side, maximum in (("up", r0 - 1), ("down", height - r1 - 2),
                          ("left", c0 - 1), ("right", width - c1 - 2)):
        if maximum >= 1:
            feasible.append((side, maximum))
    if not feasible:
        return None
    side, maximum = rng.choice(feasible)
    interior_count = (outer_h - 2) * (outer_w - 2)
    if role == "sweep":
        distance = rng.randint(1, min(maximum, 3, max(1, interior_count - 2)))
        gray_count = rng.randint(max(distance + 1, 2), interior_count)
    elif role == "cap":
        if min(maximum, 8) < 2:
            return None
        distance = rng.randint(2, min(maximum, 8))
        gray_count = rng.randint(1, min(distance - 1, interior_count - 1))
    else:
        distance = rng.randint(1, min(maximum, 6))
        gray_count = rng.randint(1, interior_count)
    box = (r0, c0, r1, c1)
    attached = set(_attached_line(side, box, height, width))
    attached_coordinate = {"up": r0 - 1, "down": r1 + 1, "left": c0 - 1, "right": c1 + 1}[side]
    target_coordinate = attached_coordinate + {"up": -distance, "down": distance, "left": -distance, "right": distance}[side]
    target = set(_line_at(side, box, target_coordinate))
    rectangle = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
    dr_unit, dc_unit = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}[side]
    corridor = set(target)
    for step in range(distance + 1):
        corridor |= _shift_cells(rectangle | attached, dr_unit * step, dc_unit * step)
    reserved = _pad(corridor, height, width)
    if reserved & occupied:
        return None
    for r, c in rectangle:
        border = r in (r0, r1) or c in (c0, c1)
        grid[r][c] = FRAME if border else EMPTY
    order = _sweep(box, side, "clockwise")
    filled_prefix = interior_count - gray_count
    for r, c in order[:filled_prefix]:
        grid[r][c] = FILL
    for r, c in attached | target:
        grid[r][c] = BAR
    return reserved


def _paint_fixed_object(grid: list[list[int]], box: tuple[int, int, int, int],
                        side: str, distance: int, gray_count: int) -> None:
    height, width = len(grid), len(grid[0])
    r0, c0, r1, c1 = box
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            grid[r][c] = FRAME if r in (r0, r1) or c in (c0, c1) else EMPTY
    order = _sweep(box, side, "clockwise")
    for r, c in order[:len(order) - gray_count]:
        grid[r][c] = FILL
    attached = _attached_line(side, box, height, width)
    coordinate = {"up": r0 - 1, "down": r1 + 1, "left": c0 - 1, "right": c1 + 1}[side]
    target_coordinate = coordinate + {"up": -distance, "down": distance, "left": -distance, "right": distance}[side]
    for r, c in attached + _line_at(side, box, target_coordinate):
        grid[r][c] = BAR


def _fallback_case(height: int, width: int, seed: int, profile: int) -> list[list[int]]:
    grid = [[BG] * width for _ in range(height)]
    variant = int.from_bytes(hashlib.sha256(f"fallback/{seed}/{profile}".encode()).digest()[:4], "big")
    left_shift = variant % max(1, min(3, width - 10))
    right_shift = (variant // 3) % max(1, min(3, width - 10))
    distance_a = 1
    gray_a = 4
    distance_b = 2 + ((variant // 17) % 2)
    gray_b = 1 + ((variant // 23) % (distance_b - 1))
    _paint_fixed_object(grid, (1, 1 + left_shift, 4, 4 + left_shift), "right", distance_a, gray_a)
    _paint_fixed_object(grid, (height - 5, width - 5 - right_shift, height - 2, width - 2 - right_shift),
                        "left", distance_b, gray_b)
    if self_check(grid):
        raise ValueError("fixed fallback violates the generated-input contract")
    return grid


def _build_case(seed: int, profile: int) -> list[list[int]]:
    rng = _rng(seed, f"profile-{profile}")
    height, width, object_count = _case_shape(profile)
    for _restart in range(20):
        grid = [[BG] * width for _ in range(height)]
        occupied: set[tuple[int, int]] = set()
        roles = ["sweep", "cap"] + ["mixed"] * (object_count - 2)
        success = True
        for role in roles:
            placed = None
            for _attempt in range(100):
                placed = _try_object(grid, occupied, rng, role)
                if placed is not None:
                    break
            if placed is None:
                success = False
                break
            occupied |= placed
        if success and self_check(grid) == []:
            return grid
    return _fallback_case(height, width, seed, profile)


@lru_cache(maxsize=128)
def _lesson_bank(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]], list[int]]:
    candidates = []
    seen = set()
    for index in range(80):
        grid = _build_case(seed + 1000003 * index, index)
        key = json.dumps(grid, separators=(",", ":"))
        if key not in seen:
            seen.add(key)
            candidates.append(grid)
        if len(candidates) >= 24:
            break
    if len(candidates) < 10:
        raise ValueError("not enough distinct constructive cases")
    teaching = None
    for a, b in itertools.combinations(range(len(candidates)), 2):
        pair = [candidates[a], candidates[b]]
        okay = True
        for target in ("clockwise", "counterclockwise"):
            wanted = [solve(g, target) for g in pair]
            survivors = [mode for mode in MODES if [solve(g, mode) for g in pair] == wanted]
            if survivors != [target]:
                okay = False
                break
        if okay:
            teaching = [a, b]
            break
    if teaching is None:
        raise ValueError("two-demo teaching search exhausted")
    remaining = [i for i in range(len(candidates)) if i not in teaching]
    rng = _rng(seed, "presentation")
    rng.shuffle(remaining)
    train_indices = teaching + remaining[:4]
    stress = next((i for i, g in enumerate(candidates) if len(g) == len(g[0]) == 30 and i not in train_indices), None)
    if stress is None:
        stress_grid = _build_case(seed + 90000091, 9)
        candidates.append(stress_grid)
        stress = len(candidates) - 1
    query_pool = [i for i in range(len(candidates)) if i not in train_indices and i != stress]
    rng.shuffle(query_pool)
    query_indices = [stress] + query_pool[:3]
    rng.shuffle(query_indices)
    return [deepcopy(candidates[i]) for i in train_indices], [deepcopy(candidates[i]) for i in query_indices], query_indices


def lesson_inputs(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    train, test, _order = _lesson_bank(seed)
    return train, test


def lesson_metadata(seed: int) -> dict[str, object]:
    train, test, order = _lesson_bank(seed)
    return {"source_seed": seed, "query_source_indices": order,
            "train_input_sha256": [hashlib.sha256(json.dumps(g, separators=(",", ":")).encode()).hexdigest() for g in train],
            "test_input_sha256": [hashlib.sha256(json.dumps(g, separators=(",", ":")).encode()).hexdigest() for g in test]}


def generate(seed: int = 0, sample_index: int = 0, difficulty: str = "medium", **kwargs: object) -> list[list[int]]:
    if kwargs:
        raise ValueError(f"unknown controls: {sorted(kwargs)}")
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(sample_index, 0, 2**31 - 1, "sample_index")
    if type(difficulty) is not str or difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")
    band = {"easy": 0, "medium": 1, "hard": 2}[difficulty]
    return _build_case(seed + 1000003 * sample_index + 9176 * band, sample_index + 11 * band)
