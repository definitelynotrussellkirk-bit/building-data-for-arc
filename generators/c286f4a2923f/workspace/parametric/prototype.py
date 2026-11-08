"""Native parametric family for source-mask transfer and topology consumption.

The default is the exact selected canonical Racket source.  The alternative
first performs the same transfer, then fills every background pocket enclosed
by the transferred cyan mask with yellow.  Inputs are identical across settings.
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

TASK_ID = "c286f4a2923f"
VERSION = "1.0.0"
FINISHES = ("transfer_only", "fill_transferred_holes")
SETTINGS = tuple({"finish": finish} for finish in FINISHES)
DEFAULT = {"finish": "transfer_only"}
HERE = Path(__file__).resolve().parent
CANONICAL_PROGRAM_SHA256 = "496d98097154e7eef48c7e46f442ae964f540c5ba1f789e1bb5d7684f4ea43d4"


def _load_local(name: str, path: Path):
    module_name = f"_c286_parametric_{name}_{hashlib.sha256(path.read_bytes()).hexdigest()}"
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
            "settings must be exactly {'finish': 'transfer_only|fill_transferred_holes'}"
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
    if finish == "transfer_only":
        return canonical_source()
    return _source("fill_transferred_holes.rkt")


def counterfactual_program() -> str:
    return _source("skip_transfer.rkt")


def _border(height: int, width: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (r, c)
        for r in range(height)
        for c in range(width)
        if r in (0, height - 1) or c in (0, width - 1)
    )


def _lattice(size: int = 12) -> tuple[tuple[int, int], ...]:
    cuts = {0, 4, 8, size - 1}
    return tuple(
        (r, c)
        for r in range(size)
        for c in range(size)
        if r in cuts or c in cuts
    )


SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "tee": ((0, 1), (1, 0), (1, 1), (1, 2)),
    "ell": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "ring3": _border(3, 3),
    "frame5": _border(5, 5),
    "double_frame": tuple(sorted(set(_border(7, 11)) | {(r, 5) for r in range(7)})),
    "stair": ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3)),
    "lattice12": _lattice(12),
}

# The first three profiles always contain both no-hole and multi-hole examples,
# so three demonstrations distinguish the two finite settings for every seed.
_TRAIN = (
    {"shape": "ell", "grid": (9, 15), "extra": (1, 2), "gap": 2, "source_first": False},
    {"shape": "ring3", "grid": (10, 16), "extra": (2, 1), "gap": 2},
    {"shape": "double_frame", "grid": (12, 27), "extra": (1, 1), "gap": 1},
    {"shape": "ell", "grid": (11, 16), "extra": (2, 2), "gap": 2},
    {"shape": "frame5", "grid": (15, 22), "extra": (2, 2), "gap": 2},
    {"shape": "stair", "grid": (13, 20), "extra": (1, 2), "gap": 3},
)

_TEST = (
    {"shape": "frame5", "grid": (13, 21), "extra": (1, 2), "gap": 2},
    {"shape": "double_frame", "grid": (15, 28), "extra": (2, 1), "gap": 2},
    {"shape": "ring3", "grid": (8, 14), "extra": (0, 0), "gap": 1, "border": True},
    {"shape": "lattice12", "grid": (30, 30), "extra": (0, 0), "gap": 2},
)


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}/{VERSION}/{seed}/{split}/{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _shape_size(cells: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _flip(cells: tuple[tuple[int, int], ...], mode: int) -> tuple[tuple[int, int], ...]:
    height, width = _shape_size(cells)
    result = []
    for r, c in cells:
        rr = height - 1 - r if mode & 2 else r
        cc = width - 1 - c if mode & 1 else c
        result.append((rr, cc))
    return tuple(sorted(result))


def _construct(seed: int, split: str, index: int) -> list[list[int]]:
    specs = _TRAIN if split == "train" else _TEST
    spec = specs[index]
    rng = _rng(seed, split, index)
    height, width = spec["grid"]
    cells = _flip(SHAPES[spec["shape"]], rng.randrange(4))
    source_h, source_w = _shape_size(cells)
    extra_h, extra_w = spec["extra"]
    target_h, target_w = source_h + extra_h, source_w + extra_w
    gap = spec["gap"]
    border = bool(spec.get("border", False))
    margin = 0 if border else 1
    minimum = source_w + target_w + gap + 2 * margin
    if minimum > width or max(source_h, target_h) + 2 * margin > height:
        raise AssertionError(f"infeasible profile {split}/{index}")

    horizontal_slack = width - minimum
    before = rng.randint(0, horizontal_slack)
    after = horizontal_slack - before
    source_first = (
        bool(spec["source_first"])
        if "source_first" in spec
        else bool(rng.randrange(2))
    )
    if source_first:
        source_left = margin + before
        target_left = source_left + source_w + gap
    else:
        target_left = margin + before
        source_left = target_left + target_w + gap
    # Preserve the unused after slack explicitly in the feasibility assertion.
    assert max(source_left + source_w, target_left + target_w) + margin + after == width

    source_top = rng.randint(margin, height - margin - source_h)
    target_top = rng.randint(margin, height - margin - target_h)
    grid = [[0] * width for _ in range(height)]
    for dr, dc in cells:
        grid[source_top + dr][source_left + dc] = 2
    for r in range(target_top, target_top + target_h):
        for c in range(target_left, target_left + target_w):
            grid[r][c] = 3
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
        for split in ("train", "test")
        for grid in result[split]
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
