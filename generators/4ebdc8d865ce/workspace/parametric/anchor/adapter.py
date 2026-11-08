"""Matched-input lessons for isolated versus anchor-sized color-2 components.

The canonical setting is the task's exact selected Racket program.  The
alternative first measures the unique color-3 anchor component, then recolors
all color-2 components having that input-derived area.  Inputs are deliberately
shared across settings; only labels teach the episode-fixed rule.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import random


HERE = Path(__file__).resolve().parent
SELECTIONS = ("isolated_twos", "anchor_sized_twos")
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
EIGHT = CARDINAL + ((-1, -1), (-1, 1), (1, -1), (1, 1))
TRAIN_SHAPES = ((11, 13), (14, 16), (17, 19), (19, 22), (22, 25), (26, 28))
QUERY_SHAPES = ((12, 14), (20, 23), (30, 30), (24, 29))


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _selection(settings):
    if (type(settings) is not dict or set(settings) != {"selection"}
            or type(settings["selection"]) is not str
            or settings["selection"] not in SELECTIONS):
        raise ValueError(
            "settings must contain only selection='isolated_twos' or "
            "'anchor_sized_twos'"
        )
    return settings["selection"]


def program(settings):
    selection = _selection(settings)
    filename = "canonical.rkt" if selection == "isolated_twos" else "anchor_sized.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _grid(grid):
    if (type(grid) is not list or not 3 <= len(grid) <= 30
            or type(grid[0]) is not list or not 3 <= len(grid[0]) <= 30):
        raise ValueError("expected a rectangular 3..30 grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return grid


def components(grid, *, color=None, eight=False):
    """Return same-color connected components in row-major discovery order."""
    _grid(grid)
    deltas = EIGHT if eight else CARDINAL
    unseen = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (color is None or value == color)
    }
    found = []
    while unseen:
        origin = min(unseen)
        value = grid[origin[0]][origin[1]]
        unseen.remove(origin)
        cells = {origin}
        stack = [origin]
        while stack:
            r, c = stack.pop()
            for dr, dc in deltas:
                point = r + dr, c + dc
                if point in unseen and grid[point[0]][point[1]] == value:
                    unseen.remove(point)
                    cells.add(point)
                    stack.append(point)
        found.append({"color": value, "cells": tuple(sorted(cells))})
    return found


def _bbox_area(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def analyze(grid):
    objects = components(grid)
    anchors = [obj for obj in objects if obj["color"] == 3]
    if len(anchors) != 1:
        raise ValueError("expected exactly one cardinal color-3 anchor component")
    twos = [obj for obj in objects if obj["color"] == 2]
    fours = [obj for obj in objects if obj["color"] == 4]
    anchor_size = len(anchors[0]["cells"])
    two_sizes = [len(obj["cells"]) for obj in twos]
    color4_sizes = [len(obj["cells"]) for obj in fours]
    if not twos or 1 not in two_sizes or anchor_size not in two_sizes:
        raise ValueError("scene needs isolated and anchor-sized color-2 components")
    if color4_sizes.count(anchor_size) != 1:
        raise ValueError("scene needs one same-sized color-4 distractor")
    return {
        "objects": objects,
        "anchor": anchors[0],
        "anchor_size": anchor_size,
        "anchor_bbox_area": _bbox_area(anchors[0]["cells"]),
        "twos": twos,
        "two_sizes": two_sizes,
        "color4_sizes": color4_sizes,
    }


def _paint_components(grid, objects):
    out = copy.deepcopy(grid)
    for obj in objects:
        for r, c in obj["cells"]:
            out[r][c] = 1
    return out


def solve(grid, selection="isolated_twos"):
    if type(selection) is not str or selection not in SELECTIONS:
        raise ValueError("unknown selection")
    facts = analyze(grid)
    target = 1 if selection == "isolated_twos" else facts["anchor_size"]
    chosen = [obj for obj in facts["twos"] if len(obj["cells"]) == target]
    return _paint_components(grid, chosen)


def _seeded(seed, split, index):
    raw = f"4ebdc8d865ce-parametric-v1:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _bands(total):
    usable = total - 2
    lengths = [usable // 3 + int(i < usable % 3) for i in range(3)]
    result = []
    start = 0
    for length in lengths:
        result.append((start, length))
        start += length + 1
    return result


def _regions(height, width):
    return [
        (r, c, rh, cw)
        for r, rh in _bands(height)
        for c, cw in _bands(width)
    ]


def _small_shape(size, variant):
    shapes = {
        2: [((0, 0), (0, 1)), ((0, 0), (1, 0))],
        3: [((0, 0), (1, 0), (1, 1)), ((0, 0), (0, 1), (0, 2))],
        4: [((0, 1), (1, 0), (1, 1), (1, 2)), ((0, 0), (0, 1), (1, 0), (1, 1))],
        5: [((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
            ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2))],
        6: [((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1)),
            ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2))],
        7: [((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)),
            ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0))],
    }
    return shapes[size][variant % len(shapes[size])]


def _transform(cells, variant):
    points = list(cells)
    if variant & 1:
        points = [(r, -c) for r, c in points]
    for _ in range((variant // 2) % 4):
        points = [(c, -r) for r, c in points]
    min_r = min(r for r, _ in points)
    min_c = min(c for _, c in points)
    return tuple(sorted((r - min_r, c - min_c) for r, c in points))


def _place(grid, region, cells, color, *, align="random", rng=None):
    top, left, height, width = region
    cells = tuple(cells)
    shape_h = max(r for r, _ in cells) + 1
    shape_w = max(c for _, c in cells) + 1
    if shape_h > height or shape_w > width:
        raise ValueError("shape does not fit region")
    if align == "top_left":
        dr, dc = 0, 0
    elif align == "top_right":
        dr, dc = 0, width - shape_w
    elif align == "bottom_left":
        dr, dc = height - shape_h, 0
    elif align == "bottom_right":
        dr, dc = height - shape_h, width - shape_w
    else:
        if rng is None:
            raise ValueError("random placement needs rng")
        dr = rng.randint(0, height - shape_h)
        dc = rng.randint(0, width - shape_w)
    for r, c in cells:
        rr, cc = top + dr + r, left + dc + c
        if grid[rr][cc] != 0:
            raise ValueError("constructed components overlap")
        grid[rr][cc] = color


def _full_rectangle(region):
    _, _, height, width = region
    return tuple((r, c) for r in range(height) for c in range(width))


def _double_comb(region):
    _, _, height, width = region
    return tuple(
        (r, c)
        for r in range(height)
        for c in range(width)
        if r % 2 == 0 or c in (0, width - 1)
    )


def _diagonal_cluster(size, region):
    """Two 4-components, diagonally joined into one 8-component of `size`."""
    _, _, height, width = region
    if height < 3 or width < 3:
        raise ValueError("diagonal teaching slot too small")
    path = [(1, 1)]
    candidates = []
    for r in range(1, height):
        cols = range(1, width) if (r - 1) % 2 == 0 else range(width - 1, 0, -1)
        candidates.extend((r, c) for c in cols)
    for point in candidates:
        if point not in path:
            path.append(point)
    return ((0, 0),), tuple(path[: size - 1])


def _scene(height, width, anchor_size, rng, variant):
    if not 2 <= anchor_size <= 6:
        raise ValueError("anchor_size outside authored grammar")
    grid = [[0] * width for _ in range(height)]
    slots = _regions(height, width)

    def shape(size, salt):
        return _transform(_small_shape(size, variant + salt), variant + 3 * salt)

    _place(grid, slots[0], shape(anchor_size, 1), 3, align="top_left")
    _place(grid, slots[1], shape(anchor_size, 2), 2, align="random", rng=rng)
    _place(grid, slots[2], shape(anchor_size + 1, 3), 2, align="top_right")
    _place(grid, slots[3], ((0, 0),), 2, align="random", rng=rng)
    _place(grid, slots[4], shape(anchor_size, 4), 2, align="random", rng=rng)
    _place(grid, slots[5], shape(anchor_size, 5), 4, align="random", rng=rng)
    _place(grid, slots[6], _full_rectangle(slots[6]), 2, align="bottom_left")
    singleton, companion = _diagonal_cluster(anchor_size, slots[7])
    _place(grid, slots[7], singleton, 2, align="top_left")
    _place(grid, slots[7], companion, 2, align="top_left")
    _place(grid, slots[8], _double_comb(slots[8]), 2, align="bottom_right")
    analyze(grid)
    return grid


def _input(seed, split, index):
    if split == "train":
        height, width = TRAIN_SHAPES[index]
        anchor_size = 2 + ((seed + 2 * index) % 5)
        variant = index + seed % 7
    elif split == "test":
        height, width = QUERY_SHAPES[index]
        anchor_size = 2 + ((3 * seed + index + 1) % 5)
        variant = 11 + index + seed % 7
    else:
        raise ValueError("unknown split")
    return _scene(height, width, anchor_size, _seeded(seed, split, index), variant)


def sample_inputs(seed, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {
        "train": [_input(seed, "train", index) for index in range(demos)],
        "test": [_input(seed, "test", index) for index in range(queries)],
    }
    serialized = [
        repr(grid)
        for split in ("train", "test")
        for grid in result[split]
    ]
    if len(serialized) != len(set(serialized)):
        raise ValueError("authored episode inputs must be distinct")
    return result


def generate(seed, settings, demos, queries):
    selection = _selection(settings)
    sampled = sample_inputs(seed, demos=demos, queries=queries)
    episode = {
        "train": [],
        "test": [],
        "program_solution": program(settings),
        "seed": seed,
        "settings": copy.deepcopy(settings),
    }
    for split in ("train", "test"):
        episode[split] = [
            {"input": copy.deepcopy(grid), "output": solve(grid, selection)}
            for grid in sampled[split]
        ]
    return episode


def public_turn(episode, query_index=0):
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select an existing query")
    try:
        train = [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ]
        query = {"input": copy.deepcopy(episode["test"][query_index]["input"])}
    except (KeyError, TypeError) as error:
        raise ValueError("episode lacks private train/test pairs") from error
    return {"train": train, "test": [query]}
