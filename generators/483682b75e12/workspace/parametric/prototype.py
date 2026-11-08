"""Matched-input parametric family for component-size motion.

The canonical setting moves each component upward by its own cell count.  The
alternative first computes the largest component size K in the current input,
then moves a component of size s upward by K - s + 1.  The latter is a genuine
global dependency: no component's displacement can be chosen before K is known.
"""
from __future__ import annotations

from collections import deque
import copy
import random
from typing import Callable


MODES = ("own_size", "complement_to_largest")
BACKGROUND = 7
FLOOR = 8
PALETTE = (0, 1, 2, 3, 4, 5, 6, 9)

SHAPES = {
    "s1": ((0, 0),),
    "h2": ((0, 0), (0, 1)),
    "v2": ((0, 0), (1, 0)),
    "l3": ((0, 0), (1, 0), (1, 1)),
    "h3": ((0, 0), (0, 1), (0, 2)),
    "v3": ((0, 0), (1, 0), (2, 0)),
    "sq4": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "l4": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "t5": ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    "h5": ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),
    "h6": ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)),
    "v6": ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)),
    "z6": ((0, 0), (0, 1), (0, 2), (1, 2), (1, 3), (1, 4)),
}

# Each component is (shape, row, col, multicolor).  There is deliberate spare
# vertical room for the seed-derived one-row jitter and both admitted rules.
DEMO_SCENES = (
    (12, 16, (("s1", 5, 1, False), ("h2", 7, 5, False), ("l4", 7, 11, True))),
    (14, 18, (("v2", 6, 1, True), ("l3", 8, 7, False), ("t5", 9, 13, True))),
    (15, 19, (("s1", 6, 2, False), ("h3", 8, 7, True), ("h6", 11, 12, False))),
    (16, 21, (("h2", 7, 1, False), ("sq4", 10, 7, True), ("z6", 12, 15, True))),
    (18, 23, (("s1", 7, 0, False), ("v2", 9, 4, False), ("l3", 11, 9, True), ("h5", 14, 16, False))),
    (20, 25, (("h2", 8, 1, True), ("l4", 11, 7, False), ("t5", 14, 14, True), ("v6", 12, 23, False))),
)

QUERY_SCENES = (
    (14, 20, (("s1", 6, 0, False), ("h2", 8, 4, True), ("l3", 9, 9, False), ("sq4", 10, 15, True))),
    (18, 24, (("v2", 7, 1, False), ("t5", 11, 8, True), ("h6", 15, 18, False))),
    (22, 27, (("s1", 6, 2, False), ("h3", 9, 7, True), ("l4", 13, 14, False), ("h5", 18, 22, True))),
    (30, 30, (
        ("s1", 6, 0, False), ("h2", 8, 3, True), ("v3", 10, 7, False),
        ("sq4", 13, 10, True), ("t5", 16, 15, True), ("h6", 21, 18, False),
        ("s1", 27, 29, False), ("v2", 24, 26, True), ("l3", 20, 1, False),
        ("l4", 24, 5, True), ("h5", 11, 24, False), ("v6", 21, 12, True),
    )),
)


def validate_mode(mode: object) -> str:
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"motion_mode must be one of {MODES}")
    return mode


def _validate_grid(grid):
    if type(grid) is not list or not 7 <= len(grid) <= 30 or type(grid[0]) is not list:
        raise ValueError("grid must have 7..30 rows")
    width = len(grid[0])
    if not 7 <= width <= 30:
        raise ValueError("grid must have 7..30 columns")
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be exact ARC integers")
    if any(value != FLOOR for value in grid[-1]):
        raise ValueError("bottom row must be a complete color-8 floor")
    if any(FLOOR in row for row in grid[:-1]):
        raise ValueError("color 8 is reserved for the floor")


def _components(grid, *, same_color=False):
    height, width = len(grid), len(grid[0])
    foreground = {(r, c) for r in range(height - 1) for c in range(width)
                  if grid[r][c] not in (BACKGROUND, FLOOR)}
    seen = set()
    result = []
    for start in sorted(foreground):
        if start in seen:
            continue
        color = grid[start[0]][start[1]]
        queue = deque([start])
        seen.add(start)
        cells = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) not in foreground or (nr, nc) in seen:
                    continue
                if same_color and grid[nr][nc] != color:
                    continue
                seen.add((nr, nc))
                queue.append((nr, nc))
        result.append(tuple(sorted(cells)))
    return tuple(result)


def scene_facts(grid):
    _validate_grid(grid)
    components = _components(grid)
    if not components:
        raise ValueError("at least one moving component is required")
    rows = [r for cells in components for r, _ in cells]
    cols = [c for cells in components for _, c in cells]
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "components": components,
        "sizes": tuple(len(cells) for cells in components),
        "max_size": max(map(len, components)),
        "occupied_rows": tuple(sorted(set(rows))),
        "occupied_cols": tuple(sorted(set(cols))),
    }


def _apply(grid, components, shifts, *, strict):
    height, width = len(grid), len(grid[0])
    output = [[FLOOR if grid[r][c] == FLOOR else BACKGROUND for c in range(width)]
              for r in range(height)]
    targets = set()
    for cells, shift in zip(components, shifts):
        if type(shift) is not int:
            raise ValueError("shift must be an integer")
        for r, c in cells:
            nr = r - shift
            if nr < 0 or nr >= height - 1:
                if strict:
                    raise ValueError("component shift leaves the admitted canvas")
                continue
            if strict and (nr, c) in targets:
                raise ValueError("component targets collide")
            targets.add((nr, c))
            output[nr][c] = grid[r][c]
    if strict and output == grid:
        raise ValueError("episode must visibly transform")
    return output


def transform(grid, mode):
    mode = validate_mode(mode)
    facts = scene_facts(grid)
    if mode == "own_size":
        shifts = list(facts["sizes"])
    else:
        largest = facts["max_size"]
        shifts = [largest - size + 1 for size in facts["sizes"]]
    return _apply(grid, facts["components"], shifts, strict=True)


def _rival(grid, name):
    facts = scene_facts(grid)
    components = facts["components"]
    sizes = facts["sizes"]
    largest = facts["max_size"]
    if name.startswith("fixed_"):
        shifts = [int(name.rsplit("_", 1)[1])] * len(components)
    elif name == "bbox_height":
        shifts = [max(r for r, _ in cells) - min(r for r, _ in cells) + 1 for cells in components]
    elif name == "bbox_width":
        shifts = [max(c for _, c in cells) - min(c for _, c in cells) + 1 for cells in components]
    elif name == "bbox_area":
        shifts = [(max(r for r, _ in cells) - min(r for r, _ in cells) + 1)
                  * (max(c for _, c in cells) - min(c for _, c in cells) + 1)
                  for cells in components]
    elif name == "largest_constant":
        shifts = [largest] * len(components)
    elif name == "complement_without_plus_one":
        shifts = [largest - size for size in sizes]
    elif name == "ascending_size_rank":
        ranks = {size: i + 1 for i, size in enumerate(sorted(set(sizes)))}
        shifts = [ranks[size] for size in sizes]
    elif name == "descending_size_rank":
        ranks = {size: i + 1 for i, size in enumerate(sorted(set(sizes), reverse=True))}
        shifts = [ranks[size] for size in sizes]
    elif name == "same_color_components":
        color_components = _components(grid, same_color=True)
        return _apply(grid, color_components, [len(cells) for cells in color_components], strict=False)
    else:
        raise ValueError(name)
    return _apply(grid, components, shifts, strict=False)


RIVAL_NAMES = (
    "fixed_1", "fixed_2", "fixed_3", "fixed_4", "bbox_height", "bbox_width",
    "bbox_area", "largest_constant", "complement_without_plus_one",
    "ascending_size_rank", "descending_size_rank", "same_color_components",
)


def _mix_seed(seed: int, slot: int, role: int) -> int:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an integer in 0..2^63-1")
    return (seed * 0x9E3779B185EBCA87 + slot * 0xD1B54A32D192ED03 + role) & ((1 << 64) - 1)


def _paint_scene(spec, seed, slot, role):
    height, width, components = spec
    rng = random.Random(_mix_seed(seed, slot, role))
    palette = rng.sample(PALETTE, 6)
    mirror = bool(rng.getrandbits(1))
    row_jitter = 0 if height == 30 else rng.choice((0, 0, 1))
    grid = [[BACKGROUND for _ in range(width)] for _ in range(height)]
    grid[-1] = [FLOOR for _ in range(width)]
    for index, (shape_name, row0, col0, multicolor) in enumerate(components):
        shape = SHAPES[shape_name]
        shape_width = max(c for _, c in shape) + 1
        if mirror:
            col0 = width - col0 - shape_width
        colors = (palette[index % len(palette)], palette[(index + 1) % len(palette)])
        for cell_index, (dr, dc) in enumerate(shape):
            color = colors[cell_index % 2] if multicolor else colors[0]
            grid[row0 + row_jitter + dr][col0 + dc] = color
    # Both settings must be total on every admitted input.
    transform(grid, "own_size")
    transform(grid, "complement_to_largest")
    return grid


def sample_inputs(seed, demos, queries):
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    train = [_paint_scene(DEMO_SCENES[i], seed, i, 0) for i in range(demos)]
    test = [_paint_scene(QUERY_SCENES[i], seed, i, 1) for i in range(queries)]
    frozen = [tuple(map(tuple, grid)) for grid in train + test]
    if len(frozen) != len(set(frozen)):
        raise AssertionError("episode inputs must be distinct")
    return train, test


def lesson_certificate(episode, selected_mode):
    selected_mode = validate_mode(selected_mode)
    train = episode["train"]
    test = episode["test"]
    setting_survivors = [mode for mode in MODES
                         if all(transform(pair["input"], mode) == pair["output"] for pair in train)]
    rival_survivors = [name for name in RIVAL_NAMES
                       if all(_rival(pair["input"], name) == pair["output"] for pair in train)]
    other = next(mode for mode in MODES if mode != selected_mode)
    query_disagreements = sum(transform(pair["input"], other) != pair["output"] for pair in test)
    return {
        "setting_survivors": setting_survivors,
        "rival_survivors": rival_survivors,
        "query_disagreements": query_disagreements,
        "rivals_checked": len(RIVAL_NAMES),
    }


def generate_episode(seed, mode, demos, queries, program_solution):
    mode = validate_mode(mode)
    train_inputs, test_inputs = sample_inputs(seed, demos, queries)
    episode = {
        "program_solution": program_solution,
        "train": [{"input": grid, "output": transform(grid, mode)} for grid in train_inputs],
        "test": [{"input": grid, "output": transform(grid, mode)} for grid in test_inputs],
    }
    certificate = lesson_certificate(episode, mode)
    if certificate["setting_survivors"] != [mode]:
        raise ValueError("demonstrations do not uniquely identify the selected setting")
    if certificate["rival_survivors"]:
        raise ValueError("declared teaching rival survived: " + ", ".join(certificate["rival_survivors"]))
    if certificate["query_disagreements"] != queries:
        raise ValueError("every query must distinguish the two admitted settings")
    return copy.deepcopy(episode)
