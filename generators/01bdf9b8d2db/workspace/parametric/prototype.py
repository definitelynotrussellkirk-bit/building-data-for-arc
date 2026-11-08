"""Parametric family for canonical chamber fill and a flooded-area selector.

The settings share the exact same input sampler. ``fill_all`` returns the exact
selected canonical Racket program. ``mark_smallest_total`` first performs that
chamber flood, counts the total flooded area of every seed color, then recolors
all cells of the least-total color to 9 (lowest color breaks an exact tie).
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

TASK_ID = "01bdf9b8d2db"
VERSION = "1.0.0"
FINISHES = ("fill_all", "mark_smallest_total")
SETTINGS = tuple({"finish": value} for value in FINISHES)
DEFAULT = {"finish": "fill_all"}
HERE = Path(__file__).resolve().parent
CANONICAL_PROGRAM_SHA256 = "e829e66a9c1a766749a02f8fec6de78f84cb5c13db3d8ad9e5e0647d7c2550ab"


def _load_local(name, path):
    module_name = f"_01bdf9b8d2db_{name}_{hashlib.sha256(path.read_bytes()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


O = _load_local("oracle", HERE / "oracle.py")


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _finish(settings):
    if (
        not isinstance(settings, dict)
        or set(settings) != {"finish"}
        or settings["finish"] not in FINISHES
    ):
        raise ValueError(
            "settings must be exactly {'finish': 'fill_all|mark_smallest_total'}"
        )
    return settings["finish"]


def _source(name):
    source = (HERE / name).read_text(encoding="utf-8")
    if not source.strip():
        raise ValueError(f"empty Racket source: {name}")
    return source


def canonical_source():
    source = _source("canonical.rkt")
    observed = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if observed != CANONICAL_PROGRAM_SHA256:
        raise ValueError(f"canonical source drift: {observed}")
    return source


def program(settings):
    finish = _finish(settings)
    if finish == "fill_all":
        return canonical_source()
    return _source("mark_smallest_total.rkt")


def counterfactual_program(name="seed_frequency"):
    if name != "seed_frequency":
        raise ValueError("only the source-bound seed_frequency counterfactual is retained")
    return _source("seed_frequency_counterfactual.rkt")


# Each group is ``(color, component-size-ranks)``. Components are ranked by
# (area, row-major first cell). The first two demonstrations intentionally teach
# different failure surfaces: repeated tiny chambers versus a second-smallest
# singleton whose smaller decoy color also owns the largest chamber.
_TRAIN = (
    {
        "shape": (12, 14), "v": (2, 5), "h": (3,), "gaps": (),
        "groups": ((8, (0, 1)), (1, (2,)), (2, (3,)), (3, (4, 5))),
        "tag": "repeated_tiny_total",
    },
    {
        "shape": (10, 13), "v": (3, 7), "h": (4,), "gaps": ((6, 3),),
        "groups": ((1, (0, 4)), (7, (1,)), (2, (2,)), (3, (3,))),
        "tag": "gap_and_second_smallest",
    },
    {
        "shape": (14, 16), "v": (3, 8, 12), "h": (5, 10),
        "gaps": ((2, 8), (8, 12)),
        "groups": ((8, (0, 1)), (1, (2, 9)), (2, (3, 4, 5, 6)),
                   (3, (7,)), (4, (8,))),
        "tag": "two_gates",
    },
    {
        "shape": (18, 20), "v": (4, 11, 15), "h": (6, 12),
        "gaps": ((9, 4), (3, 11)),
        "groups": ((7, (0,)), (1, (1, 2)), (2, (3, 4)),
                   (3, (5, 6, 7)), (4, (8, 9))),
        "tag": "large_merged_chambers",
    },
    {
        "shape": (22, 24), "v": (5, 13, 18), "h": (7, 15),
        "gaps": ((11, 5), (3, 13)),
        "groups": ((8, (0,)), (1, (1, 2)), (2, (3, 4)),
                   (3, (5, 6)), (4, (7,)), (6, (8,)), (7, (9,))),
        "tag": "seven_color_scale",
    },
    {
        "shape": (26, 28), "v": (4, 10, 19, 24), "h": (8, 17),
        "gaps": ((4, 10), (12, 19), (21, 24)),
        "groups": ((8, (0,)), (1, (1,)), (2, (2, 3)), (3, (4,)),
                   (4, (5,)), (6, (6,)), (7, (7, 8, 9, 10, 11))),
        "tag": "wide_multigate",
    },
)

_TEST = (
    {
        "shape": (13, 15), "v": (3, 9), "h": (4, 9), "gaps": ((6, 3),),
        "groups": ((8, (0, 1)), (1, (2, 6)), (2, (3, 7)),
                   (3, (4,)), (4, (5,))),
        "tag": "novel_repeat",
    },
    {
        "shape": (17, 19), "v": (4, 10, 15), "h": (6, 12),
        "gaps": ((3, 10), (9, 15)),
        "groups": ((7, (1,)), (1, (0, 9)), (2, (2,)), (3, (3,)),
                   (4, (4, 5, 6)), (6, (7,)), (8, (8,))),
        "tag": "novel_second_smallest",
    },
    {
        "shape": (24, 27), "v": (5, 13, 20), "h": (8, 16),
        "gaps": ((12, 5), (4, 13), (20, 20)),
        "groups": ((8, (0,)), (1, (1,)), (2, (2, 3)),
                   (3, (4, 5)), (4, (6,)), (6, (7,)), (7, (8,))),
        "tag": "large_novel",
    },
    {
        "shape": (30, 30), "v": (4, 11, 20, 25), "h": (7, 16, 24),
        "gaps": ((3, 11), (11, 20), (20, 4), (27, 25)),
        "groups": ((8, (0,)), (1, (1, 2)), (2, (3,)),
                   (3, (4, 5, 6, 7)), (4, (8,)), (6, (9,)),
                   (7, (10, 11, 12, 13, 14, 15))),
        "tag": "exact_30x30_stress",
    },
)


def _rng(seed, split, index):
    raw = f"{TASK_ID}/{VERSION}/{seed}/{split}/{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _wall_grid(spec):
    height, width = spec["shape"]
    grid = [[0] * width for _ in range(height)]
    for col in range(width):
        grid[0][col] = grid[-1][col] = 5
    for row in range(height):
        grid[row][0] = grid[row][-1] = 5
    for col in spec["v"]:
        for row in range(height):
            grid[row][col] = 5
    for row in spec["h"]:
        for col in range(width):
            grid[row][col] = 5
    for row, col in spec["gaps"]:
        if row in spec["h"] and col in spec["v"]:
            raise AssertionError("divider intersections cannot be opened")
        if grid[row][col] != 5:
            raise AssertionError("declared gap is not on a divider")
        grid[row][col] = 0
    return grid


def _transform(grid, code):
    if code == 0:
        return [row[:] for row in grid]
    if code == 1:
        return [list(reversed(row)) for row in grid]
    if code == 2:
        return list(reversed([row[:] for row in grid]))
    if code == 3:
        return [list(reversed(row)) for row in reversed(grid)]
    raise ValueError(code)


def _construct(seed, split, index):
    specs = _TRAIN if split == "train" else _TEST
    spec = specs[index]
    grid = _wall_grid(spec)
    ranked = sorted(O.regions(grid), key=lambda cells: (len(cells), cells[0]))
    covered = sorted(rank for _color, ranks in spec["groups"] for rank in ranks)
    if covered != list(range(len(ranked))):
        raise AssertionError(f"component grouping does not cover profile {split}/{index}")
    rng = _rng(seed, split, index)
    for color, ranks in spec["groups"]:
        for rank in ranks:
            row, col = rng.choice(ranked[rank])
            grid[row][col] = color
    grid = _transform(grid, rng.randrange(4))
    errors = O.validate_input(grid)
    if errors:
        raise AssertionError({"profile": spec["tag"], "errors": errors})
    return grid


@lru_cache(maxsize=512)
def _scene_tuple(seed, split, index):
    _integer(seed, 0, 2**63 - 1, "seed")
    if split == "train":
        _integer(index, 0, len(_TRAIN) - 1, "train index")
    elif split == "test":
        _integer(index, 0, len(_TEST) - 1, "test index")
    else:
        raise ValueError("split must be train or test")
    return tuple(tuple(row) for row in _construct(seed, split, index))


def _scene(seed, split, index):
    return [list(row) for row in _scene_tuple(seed, split, index)]


def sample_inputs(seed, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    value = {
        "train": [_scene(seed, "train", index) for index in range(demos)],
        "test": [_scene(seed, "test", index) for index in range(queries)],
    }
    keys = [
        json.dumps(grid, separators=(",", ":"))
        for split in ("train", "test")
        for grid in value[split]
    ]
    if len(keys) != len(set(keys)):
        raise AssertionError("all generated inputs must be distinct")
    return value


def generate(seed, settings, demos, queries):
    finish = _finish(settings)
    sampled = sample_inputs(seed, demos, queries)
    return {
        "train": [
            {"input": grid, "output": O.solve(grid, finish)}
            for grid in sampled["train"]
        ],
        "test": [
            {"input": grid, "output": O.solve(grid, finish)}
            for grid in sampled["test"]
        ],
        "program_solution": program(settings),
    }


def describe(grid, settings):
    finish = _finish(settings)
    info = O.intermediate(grid)
    return {
        "finish": finish,
        "shape": [len(grid), len(grid[0])],
        "chambers": len(info["chambers"]),
        "colors": len(info["filled_color_totals"]),
        "filled_color_totals": info["filled_color_totals"],
        "selected_color": info["selected_color"],
    }


def public_turn(episode, query_index):
    _integer(query_index, 0, len(episode["test"]) - 1, "query index")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
