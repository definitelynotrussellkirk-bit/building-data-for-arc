"""Native depth-order parametric family for ARC task 97f17772dd96.

The input grammar is shared across settings: two or three strictly nested blue
rectangular frames. ``outer_to_inner`` is the exact canonical authority and
paints positive nesting depth ``d`` with ``d + 1``. ``inner_to_outer`` first
measures the input-dependent maximum nesting depth ``M`` and paints depth ``d``
with ``M - d + 2``. Frame cells remain blue and exterior cells remain black.
"""
from __future__ import annotations

from copy import deepcopy
from functools import cache
import hashlib
import random
from pathlib import Path
from typing import Any

from reviewer_support import find_root, load_selected_generator

TASK_ID = "97f17772dd96"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)

Grid = list[list[int]]
DEPTH_ORDERS = ("outer_to_inner", "inner_to_outer")
DEFAULT_DEPTH_ORDER = "outer_to_inner"
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4

_DEMO_PROFILES = (
    {"h": 12, "w": 12, "n_frames": 2, "offset": False},
    {"h": 13, "w": 15, "n_frames": 3, "offset": True},
    {"h": 15, "w": 12, "n_frames": 3, "offset": False},
    {"h": 18, "w": 20, "n_frames": 2, "offset": True},
    {"h": 24, "w": 24, "n_frames": 3, "offset": True},
    {"h": 28, "w": 30, "n_frames": 2, "offset": False},
)
_QUERY_PROFILES = (
    {"h": 14, "w": 17, "n_frames": 2, "offset": True},
    {"h": 18, "w": 23, "n_frames": 3, "offset": False},
    {"h": 24, "w": 27, "n_frames": 2, "offset": False},
    {"h": 30, "w": 30, "n_frames": 3, "offset": True},
)


@cache
def _generator():
    return load_selected_generator(TASK_ID, root=ROOT)[0]


def _validate_depth_order(order: Any) -> str:
    if type(order) is not str:
        raise TypeError("depth_order must be an exact string")
    if order not in DEPTH_ORDERS:
        raise ValueError(f"unknown depth_order: {order!r}")
    return order


def canonical_program() -> str:
    source = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    if not source:
        raise ValueError("canonical.rkt is empty")
    return source


def program_for(order: str) -> str:
    order = _validate_depth_order(order)
    path = HERE / ("canonical.rkt" if order == DEFAULT_DEPTH_ORDER else "inner-to-outer.rkt")
    source = path.read_text(encoding="utf-8")
    if not source:
        raise ValueError(f"{path.name} is empty")
    return source


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_count(value: Any, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be in {minimum}..{maximum}")
    return value


def depth_facts(grid: Grid) -> dict[str, Any]:
    analysis = _generator().analyze_grid(grid)
    errors = analysis.get("errors", [])
    if errors:
        raise ValueError("invalid nested-frame input: " + "; ".join(errors))
    frames = [tuple(box) for box in analysis["frames"]]
    return {
        "height": analysis["height"],
        "width": analysis["width"],
        "frames": frames,
        "max_depth": len(frames),
        "offset": bool(analysis["asymmetry_force"]),
        "insets": [tuple(inset) for inset in analysis["insets"]],
    }


def _apply_with_max_depth(grid: Grid, max_depth: int, *, reverse: bool) -> Grid:
    facts = depth_facts(grid)
    if type(max_depth) is not int or not 1 <= max_depth <= 8:
        raise ValueError("max_depth must be an exact integer in 1..8")
    frames = facts["frames"]
    output = [list(row) for row in grid]
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 1:
                continue
            depth = sum(
                top < row < bottom and left < col < right
                for top, left, bottom, right in frames
            )
            if depth == 0:
                output[row][col] = 0
            elif reverse:
                output[row][col] = max_depth - depth + 2
            else:
                output[row][col] = depth + 1
    return output


def apply_order(grid: Grid, order: str) -> Grid:
    order = _validate_depth_order(order)
    facts = depth_facts(grid)
    return _apply_with_max_depth(
        grid,
        facts["max_depth"],
        reverse=order == "inner_to_outer",
    )


def apply_inner_to_outer_with_max_depth(grid: Grid, max_depth: int) -> Grid:
    """Audit helper for a wrong input-derived maximum-depth intermediate."""
    return _apply_with_max_depth(grid, max_depth, reverse=True)


def _rng(seed: int, split: str, slot: int) -> random.Random:
    material = f"{TASK_ID}|depth-order-v1|{seed}|{split}|{slot}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _make_input(seed: int, split: str, slot: int, profile: dict[str, Any]) -> Grid:
    generator = _generator()
    height = profile["h"]
    width = profile["w"]
    n_frames = profile["n_frames"]
    offset = profile["offset"]
    boxes = generator._layout_boxes(height, width, n_frames, offset, _rng(seed, split, slot))
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for box in boxes:
        generator._outline(grid, box)
    facts = depth_facts(grid)
    expected = {
        "height": height,
        "width": width,
        "max_depth": n_frames,
        "offset": offset,
    }
    observed = {key: facts[key] for key in expected}
    if observed != expected:
        raise AssertionError(f"constructed profile {expected!r} observed as {observed!r}")
    if apply_order(grid, "outer_to_inner") == apply_order(grid, "inner_to_outer"):
        raise AssertionError("profile does not distinguish depth order")
    return grid


def episode_inputs(seed: int, demos: int, queries: int) -> list[Grid]:
    seed = _validate_seed(seed)
    demos = _validate_count(demos, "demos", MIN_DEMOS, MAX_DEMOS)
    queries = _validate_count(queries, "queries", MIN_QUERIES, MAX_QUERIES)
    demo_inputs = [
        _make_input(seed, "demo", slot, _DEMO_PROFILES[slot])
        for slot in range(demos)
    ]
    query_inputs = [
        _make_input(seed, "query", slot, _QUERY_PROFILES[slot])
        for slot in range(queries)
    ]
    inputs = demo_inputs + query_inputs
    frozen = {tuple(tuple(row) for row in grid) for grid in inputs}
    if len(frozen) != len(inputs):
        raise AssertionError("episode inputs must be distinct")
    return inputs


def generate_episode(seed: int, depth_order: str, demos: int, queries: int) -> dict[str, Any]:
    depth_order = _validate_depth_order(depth_order)
    inputs = episode_inputs(seed, demos, queries)
    return {
        "train": [
            {"input": grid, "output": apply_order(grid, depth_order)}
            for grid in inputs[:demos]
        ],
        "test": [
            {"input": grid, "output": apply_order(grid, depth_order)}
            for grid in inputs[demos:]
        ],
        "program_solution": program_for(depth_order),
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    """Project one visible turn without settings, code, answers, or count hints."""
    if type(query_index) is not int:
        raise TypeError("query_index must be an exact integer")
    if not isinstance(episode, dict):
        raise TypeError("episode must be a dictionary")
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode needs train and test lists")
    if not 0 <= query_index < len(test):
        raise IndexError("query_index is outside the private query list")
    visible_train = []
    for pair in train:
        if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
            raise ValueError("every demonstration needs input and output")
        visible_train.append(
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
        )
    query = test[query_index]
    if not isinstance(query, dict) or "input" not in query:
        raise ValueError("query needs an input")
    return {"train": visible_train, "test": [{"input": deepcopy(query["input"])}]}
