"""Matched-input parametric family for e942ce41cbf5.

The canonical setting preserves the selected rule exactly. The alternate keeps
union and XOR controls canonical, while control 4 chooses the smaller of
intersection and XOR after the red mask has been transformed. The transformed
mask is an input-dependent intermediate needed to choose control 4's final set
operation.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import random
from typing import Iterable

HERE = Path(__file__).resolve().parent
POLICIES = ("canonical", "rank_control4")
PROGRAMS = {
    "canonical": (HERE / "canonical.rkt").read_text(encoding="utf-8"),
    "rank_control4": (HERE / "rank_control4.rkt").read_text(encoding="utf-8"),
}
OP_CONTROLS = (3, 4, 6)
TRANSFORM_CONTROLS = (7, 8, 9)

_DEMO_SPECS = (
    {"relation": "xor_smaller", "op": 4, "transform": 8, "causal": True},
    {"relation": "intersection_smaller", "op": 4, "transform": 9, "distinguish_transform": True},
    {"relation": "xor_smaller", "op": 6, "transform": 7},
    {"relation": "intersection_smaller", "op": 3, "transform": 8},
    {"relation": "xor_smaller", "op": 4, "transform": 9},
    {"relation": "intersection_smaller", "op": 6, "transform": 7},
)
_QUERY_SPECS = (
    {"relation": "xor_smaller", "op": 4, "transform": 8, "causal": True},
    {"relation": "intersection_smaller", "op": 4, "transform": 9},
    {"relation": "xor_smaller", "op": 6, "transform": 7},
    {"relation": "xor_smaller", "op": 4, "transform": 9, "causal": True, "large": True},
)


def _integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def policy(settings) -> str:
    if type(settings) is not dict or set(settings) != {"operation_policy"}:
        raise ValueError("settings must contain exactly operation_policy")
    value = settings["operation_policy"]
    if type(value) is not str or value not in POLICIES:
        raise ValueError(f"operation_policy must be one of {POLICIES!r}")
    return value


def program(settings) -> str:
    return PROGRAMS[policy(settings)]


def _norm(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = tuple((int(r), int(c)) for r, c in cells)
    if not cells:
        return frozenset()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _rot_cw(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = _norm(cells)
    height = max(r for r, _ in cells) + 1
    return _norm((c, height - 1 - r) for r, c in cells)


def _flip(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = _norm(cells)
    cmax = max(c for _, c in cells)
    return _norm((r, cmax - c) for r, c in cells)


def _transform(cells: Iterable[tuple[int, int]], control: int) -> frozenset[tuple[int, int]]:
    if control == 7:
        return _norm(cells)
    if control == 8:
        return _rot_cw(cells)
    if control == 9:
        return _flip(cells)
    raise ValueError(f"unknown transform control {control!r}")


def _inverse_transform(cells: Iterable[tuple[int, int]], control: int) -> frozenset[tuple[int, int]]:
    if control in (7, 9):
        return _transform(cells, control)
    result = _norm(cells)
    for _ in range(3):
        result = _rot_cw(result)
    return result


def _combine(a: frozenset[tuple[int, int]], b: frozenset[tuple[int, int]], op: int):
    if op == 3:
        return a | b
    if op == 4:
        return a & b
    if op == 6:
        return a ^ b
    raise ValueError(f"unknown operation control {op!r}")


def _relation(a: frozenset[tuple[int, int]], b: frozenset[tuple[int, int]]) -> str:
    intersection = len(a & b)
    xor = len(a ^ b)
    if intersection < xor:
        return "intersection_smaller"
    if intersection > xor:
        return "xor_smaller"
    return "tie"


def _ranked_op(a: frozenset[tuple[int, int]], b: frozenset[tuple[int, int]], control: int) -> int:
    if control in (3, 6):
        return control
    if control == 4:
        return 4 if len(a & b) <= len(a ^ b) else 6
    raise ValueError(f"unknown operation control {control!r}")


def _render(cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    cells = _norm(cells)
    if not cells:
        return [[0]]
    height = max(r for r, _ in cells) + 1
    width = max(c for _, c in cells) + 1
    out = [[0 for _ in range(width)] for _ in range(height)]
    for r, c in cells:
        out[r][c] = 8
    return out


def _parse(grid) -> tuple[frozenset[tuple[int, int]], frozenset[tuple[int, int]], int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be nonempty")
    width = len(grid[0])
    if len(grid) > 30 or width > 30 or any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular and at most 30x30")
    positions = {value: [] for value in range(10)}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError("grid cells must be exact integer colors")
            positions[value].append((r, c))
    ops = [value for value in OP_CONTROLS if positions[value]]
    transforms = [value for value in TRANSFORM_CONTROLS if positions[value]]
    if len(ops) != 1 or len(transforms) != 1 or not positions[1] or not positions[2]:
        raise ValueError("grid needs two masks and one control from each dictionary")
    return _norm(positions[1]), _norm(positions[2]), ops[0], transforms[0]


def solve(grid, selected_policy: str) -> list[list[int]]:
    if selected_policy not in POLICIES:
        raise ValueError(f"unknown policy {selected_policy!r}")
    blue, red_raw, op, transform = _parse(grid)
    red = _transform(red_raw, transform)
    actual_op = op if selected_policy == "canonical" else _ranked_op(blue, red, op)
    return _render(_combine(blue, red, actual_op))


def solve_ranked_with_pretransform_intermediate(grid) -> list[list[int]]:
    """Counterfactual: rank operations before applying the transform."""
    blue, red_raw, op, transform = _parse(grid)
    chosen = _ranked_op(blue, red_raw, op)
    red = _transform(red_raw, transform)
    return _render(_combine(blue, red, chosen))


def describe_case(grid) -> dict[str, object]:
    blue, red_raw, op, transform = _parse(grid)
    red = _transform(red_raw, transform)
    return {
        "operation_control": op,
        "transform_control": transform,
        "blue_cells": len(blue),
        "red_cells": len(red),
        "pre_transform_intersection": len(blue & red_raw),
        "pre_transform_xor": len(blue ^ red_raw),
        "pre_transform_relation": _relation(blue, red_raw),
        "post_transform_intersection": len(blue & red),
        "post_transform_xor": len(blue ^ red),
        "post_transform_relation": _relation(blue, red),
        "ranked_operation": _ranked_op(blue, red, op),
        "wrong_pretransform_operation": _ranked_op(blue, red_raw, op),
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"e942ce41cbf5:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _grow(rng: random.Random, height: int, width: int, size: int):
    cells = {(rng.randrange(height), rng.randrange(width))}
    while len(cells) < size:
        frontier = set()
        for r, c in cells:
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nxt[0] < height and 0 <= nxt[1] < width and nxt not in cells:
                    frontier.add(nxt)
        if not frontier:
            break
        cells.add(rng.choice(sorted(frontier)))
    return _norm(cells)


def _bbox_shape(cells) -> tuple[int, int]:
    cells = _norm(cells)
    return (max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1)


def _solid(cells) -> bool:
    cells = _norm(cells)
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    return len(cells) == h * w


def _draw_pair(rng: random.Random, spec: dict[str, object]):
    large = bool(spec.get("large"))
    transform = int(spec["transform"])
    relation = str(spec["relation"])
    causal = bool(spec.get("causal"))
    if large:
        # Constructive stress case: a left-heavy 24x11 connected mask and a
        # nearly identical post-flip target.  The raw (unflipped) red mask is
        # right-heavy, so pre-transform ranking is the opposite of the correct
        # post-transform ranking without any rejection search.
        box_h, box_w = 24, 11
        blue = {(r, c) for r in range(box_h) for c in range(6)}
        blue.update((0, c) for c in range(box_w))
        target = set(blue)
        remove_start = rng.randint(10, 17)
        add_start = rng.randint(1, 11)
        target.difference_update((r, 5) for r in range(remove_start, min(box_h, remove_start + 6)))
        target.update((r, 6) for r in range(add_start, min(box_h, add_start + 6)))
        return _norm(blue), _inverse_transform(_norm(target), transform)
    box_h, box_w = rng.choice(((5, 6), (6, 6), (6, 7), (7, 6)))
    area = box_h * box_w
    if relation == "xor_smaller":
        low, high = max(8, int(area * 0.42)), max(10, int(area * 0.68))
    else:
        low, high = max(6, int(area * 0.22)), max(8, int(area * 0.48))
    for _ in range(12000):
        blue = _grow(rng, box_h, box_w, rng.randint(low, high))
        red_target = _grow(rng, box_h, box_w, rng.randint(low, high))
        red_raw = _inverse_transform(red_target, transform)
        red = _transform(red_raw, transform)
        if _relation(blue, red) != relation:
            continue
        if causal and _relation(blue, red_raw) == relation:
            continue
        if not (blue & red and blue - red and red - blue):
            continue
        outputs = [_norm(_combine(blue, red, op)) for op in OP_CONTROLS]
        if len(set(outputs)) != 3 or any(not value or _solid(value) for value in outputs):
            continue
        if causal and _ranked_op(blue, red, int(spec["op"])) == _ranked_op(blue, red_raw, int(spec["op"])):
            continue
        if spec.get("distinguish_transform"):
            intended = _norm(_combine(blue, red, int(spec["op"])))
            wrong_results = [
                _norm(_combine(blue, _transform(red_raw, candidate), int(spec["op"])))
                for candidate in TRANSFORM_CONTROLS
                if candidate != transform
            ]
            if any(result == intended for result in wrong_results):
                continue
        return blue, red_raw
    raise ValueError(f"could not construct case for {spec!r}")


def _place(blue, red_raw, op: int, transform: int, *, large: bool) -> list[list[int]]:
    bh = max(r for r, _ in blue) + 1
    bw = max(c for _, c in blue) + 1
    rh = max(r for r, _ in red_raw) + 1
    rw = max(c for _, c in red_raw) + 1
    if large:
        height = width = 30
        blue_top, blue_left = 0, 1
        red_top, red_left = height - rh - 1, width - rw - 1
    else:
        height = max(12, max(bh, rh) + 4)
        width = max(14, bw + rw + 5)
        blue_top, blue_left = 1, 1
        red_top, red_left = 2, width - rw - 1
    if red_left <= blue_left + bw:
        raise ValueError("source mask panels overlap")
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for r, c in blue:
        grid[blue_top + r][blue_left + c] = 1
    for r, c in red_raw:
        grid[red_top + r][red_left + c] = 2
    grid[-1][0] = op
    grid[-1][-1] = transform
    return grid


def _pair(seed: int, split: str, index: int, selected_policy: str) -> dict[str, list[list[int]]]:
    spec = (_DEMO_SPECS if split == "demo" else _QUERY_SPECS)[index]
    rng = _rng(seed, split, index)
    blue, red_raw = _draw_pair(rng, spec)
    grid = _place(blue, red_raw, int(spec["op"]), int(spec["transform"]), large=bool(spec.get("large")))
    return {"input": grid, "output": solve(grid, selected_policy)}


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    selected_policy = policy(settings)
    return {
        "train": [_pair(seed, "demo", index, selected_policy) for index in range(demos)],
        "test": [_pair(seed, "query", index, selected_policy) for index in range(queries)],
        "program_solution": PROGRAMS[selected_policy],
    }


def public_turn(episode, query_index=0):
    if type(query_index) is not int or query_index < 0:
        raise ValueError("query_index must be a nonnegative integer")
    if not isinstance(episode, dict) or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    if query_index >= len(episode["test"]):
        raise ValueError("query_index is outside the retained queries")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
