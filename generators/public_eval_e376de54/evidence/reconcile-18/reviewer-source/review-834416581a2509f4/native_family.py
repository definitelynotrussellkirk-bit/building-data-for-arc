"""Normalize aligned parallel segments to a selected reference length."""
from __future__ import annotations
from collections import Counter
import copy
import hashlib
from pathlib import Path
import random

TASK_ID = "public_eval_e376de54"
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
PARAMETERS = {"target_mode": ["middle", "longest"]}
DEFAULT = {"target_mode": "middle"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}
assert CANONICAL.count("(define longest #f)") == 1
ALTERNATIVE = CANONICAL.replace("(define longest #f)", "(define longest #t)", 1)
DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


def _mode(settings: dict) -> str:
    if (type(settings) is not dict or set(settings) != {"target_mode"}
            or type(settings["target_mode"]) is not str
            or settings["target_mode"] not in PARAMETERS["target_mode"]):
        raise ValueError("settings must be exactly target_mode=middle or longest")
    return settings["target_mode"]


def program(settings: dict) -> str:
    return CANONICAL if _mode(settings) == "middle" else ALTERNATIVE


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
            or any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row)):
        raise ValueError("need an exact-integer rectangular ARC grid with axes 1..30")
    return [row[:] for row in grid]


def _unique_mode(values, label):
    ranked = Counter(values).most_common()
    if not ranked or (len(ranked) > 1 and ranked[0][1] == ranked[1][1]):
        raise ValueError(f"need a unique {label}")
    return ranked[0][0]


def _components(grid, background):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width)
              if grid[r][c] != background}
    result = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        stack = [start]
        unseen.remove(start)
        cells = set()
        while stack:
            r, c = stack.pop()
            cells.add((r, c))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    nxt = (r + dr, c + dc)
                    if nxt in unseen and grid[nxt[0]][nxt[1]] == color:
                        unseen.remove(nxt)
                        stack.append(nxt)
        result.append({"color": color, "cells": cells, "size": len(cells)})
    return result


def _line_direction(cells):
    cells = set(cells)
    for direction in DIRECTIONS:
        dr, dc = direction
        projection = lambda p: dr * p[0] + dc * p[1]
        start = min(cells, key=projection)
        expected = {(start[0] + i * dr, start[1] + i * dc) for i in range(len(cells))}
        if expected == cells:
            return direction
    raise ValueError("every object must be a contiguous one-cell-thick straight segment")


def plan(grid, target_mode="middle"):
    _mode({"target_mode": target_mode})
    grid = _grid(grid)
    height, width = len(grid), len(grid[0])
    background = _unique_mode([value for row in grid for value in row], "background mode")
    segments = _components(grid, background)
    if not 3 <= len(segments) <= 9 or len(segments) % 2 == 0:
        raise ValueError("need an odd count of 3..9 segments")
    directions = {_line_direction(segment["cells"]) for segment in segments}
    if len(directions) != 1:
        raise ValueError("all segments must be parallel")
    direction = next(iter(directions))
    dr, dc = direction

    def projection(point):
        return dr * point[0] + dc * point[1]

    def perpendicular(point):
        return -dc * point[0] + dr * point[1]

    for segment in segments:
        segment["min_end"] = min(segment["cells"], key=projection)
        segment["max_end"] = max(segment["cells"], key=projection)
    min_aligned = len({projection(segment["min_end"]) for segment in segments}) == 1
    max_aligned = len({projection(segment["max_end"]) for segment in segments}) == 1
    if min_aligned == max_aligned:
        raise ValueError("exactly one endpoint side must lie on a common perpendicular guide")
    anchor_side = "minimum" if min_aligned else "maximum"
    anchor_key = "min_end" if min_aligned else "max_end"
    ordered = sorted(segments, key=lambda segment: perpendicular(segment[anchor_key]))
    lengths = [segment["size"] for segment in ordered]
    target_length = (max(lengths) if target_mode == "longest"
                     else lengths[len(lengths) // 2])
    step = direction if min_aligned else (-dr, -dc)
    occupied = set()
    for segment in ordered:
        r0, c0 = segment[anchor_key]
        cells = {(r0 + i * step[0], c0 + i * step[1]) for i in range(target_length)}
        if any(not (0 <= r < height and 0 <= c < width) for r, c in cells):
            raise ValueError("normalized segment does not fit the canvas")
        if occupied & cells:
            raise ValueError("normalized segments must not overlap")
        occupied |= cells
        segment["output_cells"] = cells
    return {
        "grid": grid,
        "background": background,
        "segments": ordered,
        "direction": direction,
        "anchor_side": anchor_side,
        "lengths": lengths,
        "target_mode": target_mode,
        "target_length": target_length,
        "step": step,
    }


def solve(grid, target_mode="middle"):
    state = plan(grid, target_mode)
    output = [[state["background"] for _ in row] for row in state["grid"]]
    for segment in state["segments"]:
        for r, c in segment["output_cells"]:
            output[r][c] = segment["color"]
    return output


_PROFILES = (
    (16, 16, (1, 0), "minimum", (2, 5, 9)),
    (19, 21, (1, 1), "maximum", (2, 6, 4, 8, 5)),
    (18, 18, (1, 1), "minimum", (3, 5, 8)),
    (20, 20, (1, -1), "maximum", (4, 8, 6, 10, 7)),
    (22, 24, (1, 0), "maximum", (4, 12, 6, 9, 15, 10, 5)),
    (30, 30, (0, 1), "maximum", (5, 19, 7, 16, 9, 23, 11, 14, 6)),
    (17, 19, (0, 1), "minimum", (3, 7, 4, 11, 6)),
    (24, 24, (1, -1), "minimum", (3, 9, 5, 7, 11, 6, 8)),
    (26, 30, (1, 0), "minimum", (6, 18, 10, 22, 8)),
    (30, 30, (1, 1), "minimum", (12, 16, 13, 14, 17, 15, 11)),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _rng(seed, label):
    raw = hashlib.sha256(f"{TASK_ID}:{seed}:{label}".encode()).digest()
    return random.Random(int.from_bytes(raw[:16], "big"))


def _choose_anchors(height, width, direction, side, max_length, count):
    dr, dc = direction
    step = direction if side == "minimum" else (-dr, -dc)
    groups = {}
    for r in range(height):
        for c in range(width):
            end = (r + (max_length - 1) * step[0], c + (max_length - 1) * step[1])
            if not (0 <= end[0] < height and 0 <= end[1] < width):
                continue
            groups.setdefault(dr * r + dc * c, []).append((r, c))
    best = None
    for projection, points in groups.items():
        points.sort(key=lambda p: -dc * p[0] + dr * p[1])
        spaced = []
        for point in points:
            if not spaced or max(abs(point[0] - spaced[-1][0]), abs(point[1] - spaced[-1][1])) >= 2:
                spaced.append(point)
        if len(spaced) < count:
            continue
        score = (len(spaced), -abs(projection - (dr * (height - 1) + dc * (width - 1)) / 2))
        if best is None or score > best[0]:
            best = (score, spaced)
    if best is None:
        raise AssertionError("profile has no fitting aligned anchor set")
    candidates = best[1]
    if count == 1:
        return [candidates[len(candidates) // 2]]
    indices = [round(i * (len(candidates) - 1) / (count - 1)) for i in range(count)]
    anchors = [candidates[index] for index in indices]
    if len(set(anchors)) != count:
        raise AssertionError("anchor selection duplicated a position")
    return anchors


def _scene(profile_index, seed):
    height, width, direction, side, lengths0 = _PROFILES[profile_index]
    lengths = list(lengths0)
    count = len(lengths)
    anchors = _choose_anchors(height, width, direction, side, max(lengths), count)
    rng = _rng(seed, f"scene:{profile_index}")
    palette = list(range(10))
    rng.shuffle(palette)
    background = palette[0]
    available = palette[1:]
    colors = [available[i % len(available)] for i in range(count)]
    if count >= 5 and profile_index % 2 == 1:
        colors[-1] = colors[0]
    grid = [[background] * width for _ in range(height)]
    dr, dc = direction
    step = direction if side == "minimum" else (-dr, -dc)
    for anchor, length, color in zip(anchors, lengths, colors):
        for i in range(length):
            r = anchor[0] + i * step[0]
            c = anchor[1] + i * step[1]
            if grid[r][c] != background:
                raise AssertionError("profile segments overlap")
            grid[r][c] = color
    plan(grid, "middle")
    plan(grid, "longest")
    return grid


def input_bank(seed=0):
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    scenes = [_scene(index, seed) for index in range(len(_PROFILES))]
    demos = scenes[:6]
    queries = scenes[6:]
    _rng(seed, "query-order").shuffle(queries)
    return copy.deepcopy(demos), copy.deepcopy(queries)


def generate(seed=0, settings=None, demos=3, queries=4):
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, LIMITS["demos"][0], LIMITS["demos"][1], "demos")
    queries = _integer(queries, LIMITS["queries"][0], LIMITS["queries"][1], "queries")
    if settings is None:
        settings = {"target_mode": _rng(seed, "setting").choice(PARAMETERS["target_mode"])}
    target_mode = _mode(settings)
    demo_bank, query_bank = input_bank(seed)
    lesson = {
        "train": [{"input": grid, "output": solve(grid, target_mode)}
                  for grid in demo_bank[:demos]],
        "test": [{"input": grid, "output": solve(grid, target_mode)}
                 for grid in query_bank[:queries]],
        "program_solution": program({"target_mode": target_mode}),
    }
    return copy.deepcopy(lesson)
