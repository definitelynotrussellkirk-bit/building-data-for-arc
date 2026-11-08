"""Uniform-row sequence to concentric-layer family for public task 45a5af55."""
from __future__ import annotations

import copy
import hashlib
import random
from functools import lru_cache

TASK_ID = "public_eval_45a5af55"
VERSION = "1.0.0"
SETTINGS = ("outside_in", "inside_out")
DEPENDENCY = {
    "step_a": "Read the uniform row colors and discard the final duplicate center-evidence row.",
    "intermediate": "An input-dependent ordered sequence of layer colors whose length fixes the output side.",
    "step_b": "Color each output cell by its minimum distance to an edge, consuming that sequence outside-in or in the declared reverse order.",
    "why_b_depends_on_a": "Both output size and every ring color come from the extracted row sequence; input width and absolute coordinates carry no layer information.",
}


def _validate_grid(grid):
    if (
        type(grid) is not list
        or not 2 <= len(grid) <= 16
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(value) is not int or not 0 <= value <= 9 for value in row)
            for row in grid
        )
    ):
        raise ValueError("Expected a rectangular 2..16 by 1..30 exact-integer ARC grid")
    colors = []
    for row in grid:
        if len(set(row)) != 1:
            raise ValueError("Every input row must be uniform")
        colors.append(row[0])
    if colors[-1] != colors[-2]:
        raise ValueError("The final row must duplicate the center-layer color")
    return colors


def analyze(grid):
    colors = _validate_grid(grid)
    return {
        "row_colors": colors,
        "layers": colors[:-1],
        "layer_count": len(colors) - 1,
        "output_side": 2 * (len(colors) - 1),
    }


def solve(grid, layer_order="outside_in"):
    if layer_order not in SETTINGS:
        raise ValueError("Unknown layer order")
    info = analyze(grid)
    layers = info["layers"] if layer_order == "outside_in" else list(reversed(info["layers"]))
    side = info["output_side"]
    return [
        [layers[min(r, c, side - 1 - r, side - 1 - c)] for c in range(side)]
        for r in range(side)
    ]


def _rng(seed, index):
    raw = hashlib.sha256(f"45a5af55-v1:{seed}:{index}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


@lru_cache(maxsize=4096)
def _sample_frozen(seed, index):
    if type(seed) is not int or seed < 0 or type(index) is not int or index < 0:
        raise ValueError("seed and index must be nonnegative exact integers")
    rng = _rng(seed, index)
    layer_count = 15 if index % 10 == 9 else 4 + index % 10
    width = 1 + rng.randrange(30)
    palette = list(range(10))
    rng.shuffle(palette)
    active = palette[: 3 + rng.randrange(4)]

    # Mix runs and changes, then force distinct endpoints so the two declared
    # settings are identifiable from every demonstration independently.
    layers = [active[0]]
    for position in range(1, layer_count - 1):
        if position % 4 == 1 and rng.random() < 0.65:
            layers.append(layers[-1])
        else:
            choices = [color for color in active if color != layers[-1]]
            layers.append(rng.choice(choices))
    layers.append(active[1] if active[1] != layers[0] else active[2])
    colors = layers + [layers[-1]]
    grid = tuple(tuple(color for _ in range(width)) for color in colors)
    if len(solve([list(row) for row in grid], "outside_in")) > 30:
        raise RuntimeError("Constructed scene exceeds ARC bounds")
    return grid


def sample(seed, split, index):
    if split not in ("train", "test"):
        raise ValueError("Unknown split")
    source_index = index if split == "train" else 6 + index
    return [list(row) for row in _sample_frozen(seed, source_index)]


def public_views(episode, *, presentation_seed, limit=4):
    if type(presentation_seed) is not int or type(limit) is not int or not 1 <= limit <= 4:
        raise ValueError("Invalid presentation request")
    if type(episode) is not dict or type(episode.get("test")) is not list or len(episode["test"]) != 4:
        raise ValueError("Shuffle the complete four-query bank before selecting a prefix")
    order = list(range(4))
    random.Random(presentation_seed).shuffle(order)
    train = [
        {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
        for pair in episode["train"]
    ]
    return [
        {"train": copy.deepcopy(train), "test": [{"input": copy.deepcopy(episode["test"][index]["input"])}]}
        for index in order[:limit]
    ]
