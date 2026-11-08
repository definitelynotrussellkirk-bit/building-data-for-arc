"""Native parametric family for rectangle borders and enclosure selection.

The default is the exact selected canonical Racket source. The alternative
first draws every colored rectangle border, then selects the frame with the
largest enclosed interior area and fills that interior with the frame's color.
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

TASK_ID = "1bfb2ef9ca71"
VERSION = "1.0.0"
FINISHES = ("borders_only", "fill_largest_interior")
SETTINGS = tuple({"finish": finish} for finish in FINISHES)
DEFAULT = {"finish": "borders_only"}
HERE = Path(__file__).resolve().parent
CANONICAL_PROGRAM_SHA256 = "a0ec8172be31e1dd1241771759a6a2703d297eeba88b3ddc019df4f0d49de9ea"


def _load_local(name: str, path: Path):
    module_name = f"_1bfb_parametric_{name}_{hashlib.sha256(path.read_bytes()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


O = _load_local("oracle", HERE / "oracle.py")


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _finish(settings: object) -> str:
    if (
        not isinstance(settings, dict)
        or set(settings) != {"finish"}
        or settings["finish"] not in FINISHES
    ):
        raise ValueError(
            "settings must be exactly {'finish': 'borders_only|fill_largest_interior'}"
        )
    return settings["finish"]


def _source(name: str) -> str:
    source = (HERE / name).read_text(encoding="utf-8")
    if not source.strip():
        raise ValueError(f"empty Racket source: {name}")
    return source


def canonical_source() -> str:
    source = _source("canonical.rkt")
    observed = hashlib.sha256(source.encode()).hexdigest()
    if observed != CANONICAL_PROGRAM_SHA256:
        raise ValueError(f"canonical source drift: {observed}")
    return source


def program(settings: object) -> str:
    finish = _finish(settings)
    if finish == "borders_only":
        return canonical_source()
    return _source("fill_largest_interior.rkt")


def counterfactual_program() -> str:
    return _source("skip_borders.rkt")


# Rectangle boxes are inclusive (top, left, bottom, right). The first profile
# deliberately makes the largest interior differ from the longest perimeter.
_TRAIN = (
    {"grid": (14, 20), "boxes": ((1, 1, 3, 13), (7, 12, 12, 17))},
    {"grid": (13, 18), "boxes": ((1, 1, 4, 7), (6, 1, 11, 4), (7, 10, 9, 14))},
    {"grid": (14, 20), "boxes": ((1, 1, 5, 7), (1, 11, 4, 18), (9, 6, 11, 11))},
    {"grid": (15, 21), "boxes": ((1, 1, 6, 5), (1, 10, 4, 18), (10, 2, 13, 8))},
    {"grid": (18, 24), "boxes": ((1, 1, 8, 7), (1, 13, 6, 22), (12, 4, 16, 12))},
    {"grid": (22, 27), "boxes": ((1, 1, 10, 8), (1, 14, 8, 25), (14, 2, 20, 11))},
)

_TEST = (
    {"grid": (10, 17), "boxes": ((0, 0, 4, 6), (5, 11, 9, 16))},
    {"grid": (16, 23), "boxes": ((1, 1, 7, 8), (1, 14, 5, 21), (10, 5, 14, 12))},
    {"grid": (20, 26), "boxes": ((1, 1, 9, 9), (1, 15, 7, 24), (13, 2, 18, 11))},
    {"grid": (30, 30), "boxes": ((1, 1, 12, 13), (1, 17, 9, 29), (17, 1, 29, 10), (18, 15, 29, 29))},
)


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}/{VERSION}/{seed}/{split}/{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _transform_box(
    box: tuple[int, int, int, int], height: int, width: int, mode: int
) -> tuple[int, int, int, int]:
    top, left, bottom, right = box
    if mode & 2:
        top, bottom = height - 1 - bottom, height - 1 - top
    if mode & 1:
        left, right = width - 1 - right, width - 1 - left
    return top, left, bottom, right


def _construct(seed: int, split: str, index: int) -> list[list[int]]:
    specs = _TRAIN if split == "train" else _TEST
    spec = specs[index]
    rng = _rng(seed, split, index)
    height, width = spec["grid"]
    mode = rng.randrange(4)
    boxes = [_transform_box(box, height, width, mode) for box in spec["boxes"]]
    colors = rng.sample(range(1, 10), len(boxes))
    grid = [[0] * width for _ in range(height)]
    for box_index, ((top, left, bottom, right), color) in enumerate(zip(boxes, colors)):
        orientation = (box_index + rng.randrange(2)) % 2
        endpoints = (
            ((top, left), (bottom, right))
            if orientation == 0
            else ((top, right), (bottom, left))
        )
        for r, c in endpoints:
            if grid[r][c] != 0:
                raise AssertionError("profile marker collision")
            grid[r][c] = color
    info = O.describe(grid, "borders_only")
    if not info["unique_largest_interior"]:
        raise AssertionError(f"profile {split}/{index} lacks a unique largest interior")
    return grid


@lru_cache(maxsize=1024)
def _scene_tuple(seed: int, split: str, index: int) -> tuple[tuple[int, ...], ...]:
    _integer(seed, 0, 2**63 - 1, "seed")
    limit = len(_TRAIN) if split == "train" else len(_TEST) if split == "test" else -1
    if limit < 0:
        raise ValueError("split must be train or test")
    _integer(index, 0, limit - 1, f"{split} index")
    return tuple(tuple(row) for row in _construct(seed, split, index))


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    return [list(row) for row in _scene_tuple(seed, split, index)]


def sample_inputs(seed: int, demos: int = 3, queries: int = 4) -> dict[str, list[list[list[int]]]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 3, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {
        "train": [_scene(seed, "train", i) for i in range(demos)],
        "test": [_scene(seed, "test", i) for i in range(queries)],
    }
    fingerprints = [
        json.dumps(grid, separators=(",", ":"))
        for split_name in ("train", "test")
        for grid in result[split_name]
    ]
    if len(fingerprints) != len(set(fingerprints)):
        raise AssertionError("all generated inputs must be distinct")
    return result


def solve(grid: list[list[int]], finish: str) -> list[list[int]]:
    return O.solve(grid, finish)


def generate(seed: int, settings: object, demos: int, queries: int) -> dict[str, object]:
    finish = _finish(settings)
    sampled = sample_inputs(seed, demos, queries)
    return {
        "train": [
            {"input": grid, "output": solve(grid, finish)} for grid in sampled["train"]
        ],
        "test": [
            {"input": grid, "output": solve(grid, finish)} for grid in sampled["test"]
        ],
        "program_solution": program(settings),
    }


def describe(grid: list[list[int]], settings: object) -> dict[str, object]:
    return O.describe(grid, _finish(settings))


def public_turn(episode: dict[str, object], query_index: int) -> dict[str, object]:
    tests = episode.get("test")
    if not isinstance(tests, list):
        raise ValueError("episode test split is missing")
    _integer(query_index, 0, len(tests) - 1, "query index")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(tests[query_index]["input"])}],
    }
