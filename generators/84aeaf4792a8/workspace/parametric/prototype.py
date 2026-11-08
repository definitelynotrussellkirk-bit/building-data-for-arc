"""Native rotation-vs-dihedral parametric family for ARC task 84aeaf4792a8.

The source task extracts monochromatic components, canonicalizes their shapes
under translation and quarter-turn rotations, and renders the resulting
pairwise equivalence matrix.  This family varies only the transformation group:

* ``rotation`` is the byte-exact selected canonical rule.
* ``dihedral`` additionally treats reflected shapes as equivalent.

Inputs are setting-neutral.  The first two demonstrations contain chiral pairs,
rotation matches, coarse-statistic distractors, repeated colors and multiple
independent matching families, so the visible lesson distinguishes both settings
and rejects a bounded set of common shortcuts.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import public_challenge_bytes

TASK_ID = "84aeaf4792a8"
POLICIES = ("rotation", "dihedral")
PROGRAM_FILES = {
    "rotation": HERE / "canonical.rkt",
    "dihedral": HERE / "dihedral.rkt",
}
_DIR4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _load_adjacent(name: str, filename: str):
    path = HERE / filename
    module = sys.modules.get(name)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_RIVALS = _load_adjacent("_arcp_84aeaf4792a8_rivals", "rivals.py")
RIVAL_NAMES = _RIVALS.MODEL_NAMES


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _policy(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"equivalence_policy"}:
        raise ValueError("settings must contain exactly equivalence_policy")
    value = settings["equivalence_policy"]
    if type(value) is not str or value not in POLICIES:
        raise ValueError("equivalence_policy must be rotation or dihedral")
    return value


def program(settings: dict[str, Any]) -> str:
    return PROGRAM_FILES[_policy(settings)].read_text(encoding="utf-8")


def counterfactual_bbox_program() -> str:
    return (HERE / "counterfactual_bbox.rkt").read_text(encoding="utf-8")


def _norm(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("shape must contain cells")
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _turn(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _norm((c, -r) for r, c in cells)


def _turns(cells: Iterable[tuple[int, int]], count: int) -> tuple[tuple[int, int], ...]:
    current = _norm(cells)
    for _ in range(count % 4):
        current = _turn(current)
    return current


def _mirror(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _norm((r, -c) for r, c in cells)


def _scaled(cells: Iterable[tuple[int, int]], factor: int) -> tuple[tuple[int, int], ...]:
    cells = _norm(cells)
    return tuple(sorted(
        (factor * r + dr, factor * c + dc)
        for r, c in cells
        for dr in range(factor)
        for dc in range(factor)
    ))


def _orbit_key(cells: Iterable[tuple[int, int]], policy: str):
    policy = _policy({"equivalence_policy": policy})
    current = _norm(cells)
    values = []
    for _ in range(4):
        values.append(current)
        current = _turn(current)
    if policy == "dihedral":
        current = _mirror(cells)
        for _ in range(4):
            values.append(current)
            current = _turn(current)
    return min(values)


SHAPES = {
    "L4": _norm(((0, 0), (1, 0), (2, 0), (2, 1))),
    "S4": _norm(((0, 1), (0, 2), (1, 0), (1, 1))),
    "F5": _norm(((0, 1), (0, 2), (1, 0), (1, 1), (2, 1))),
    "P5": _norm(((0, 0), (0, 1), (1, 0), (1, 1), (2, 0))),
    "N5": _norm(((0, 0), (1, 0), (1, 1), (2, 1), (3, 1))),
    "T5": _norm(((0, 0), (0, 1), (0, 2), (1, 1), (2, 1))),
    "U5": _norm(((0, 0), (0, 2), (1, 0), (1, 1), (1, 2))),
    "PLUS5": _norm(((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))),
    "W5": _norm(((0, 0), (1, 0), (1, 1), (2, 1), (2, 2))),
    "Z5": _norm(((0, 0), (0, 1), (1, 1), (2, 1), (2, 2))),
}

# (family, reflected, quarter_turn_offset)
DEMO_PROFILES = (
    (16, 18, (("L4", False, 0), ("S4", False, 1), ("L4", True, 0),
              ("T5", False, 0), ("L4", False, 1), ("T5", False, 1)), 1, False),
    (17, 21, (("F5", False, 0), ("U5", False, 0), ("F5", True, 2),
              ("U5", False, 1), ("F5", False, 1)), 1, False),
    (15, 19, (("S4", False, 0), ("S4", True, 0),
              ("P5", False, 0), ("P5", False, 2)), 1, False),
    (20, 23, (("N5", False, 0), ("N5", True, 0), ("W5", False, 0),
              ("W5", False, 1), ("L4", False, 0), ("L4", False, 3)), 1, False),
    (13, 17, (("F5", False, 0), ("F5", True, 0), ("F5", False, 3)), 1, False),
    (22, 25, (("P5", False, 0), ("P5", True, 0), ("T5", False, 0),
              ("T5", False, 1), ("PLUS5", False, 0)), 1, False),
)

QUERY_PROFILES = (
    (14, 16, (("L4", False, 0), ("L4", True, 0),
              ("S4", False, 0), ("S4", False, 1)), 1, True),
    (18, 20, (("F5", False, 0), ("F5", True, 0), ("U5", False, 0),
              ("U5", False, 1), ("PLUS5", False, 0)), 1, True),
    (24, 27, (("N5", False, 0), ("N5", True, 0), ("N5", False, 2),
              ("T5", False, 0), ("T5", False, 1), ("W5", False, 0)), 1, True),
    (30, 30, (("P5", False, 0), ("P5", True, 0), ("P5", False, 1),
              ("S4", False, 0), ("S4", True, 0), ("PLUS5", False, 0)), 2, True),
)


def _validate_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("expected a nonempty grid")
    width = len(grid[0])
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    if any(type(row) is not list or len(row) != width or
           any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact ARC integer colors")
    return grid


def extract_components(grid: Any) -> list[dict[str, Any]]:
    grid = _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    result = []
    while remaining:
        seed = min(remaining)
        color = grid[seed[0]][seed[1]]
        remaining.remove(seed)
        queue = deque([seed])
        cells = []
        while queue:
            point = queue.popleft()
            cells.append(point)
            r, c = point
            for dr, dc in _DIR4:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        top = min(r for r, _ in cells)
        left = min(c for _, c in cells)
        bottom = max(r for r, _ in cells)
        right = max(c for _, c in cells)
        result.append({
            "color": color,
            "cells": tuple(sorted(cells)),
            "normalized": _norm(cells),
            "bbox": (top, left, bottom, right),
            "shape": (bottom - top + 1, right - left + 1),
        })
    return sorted(result, key=lambda obj: obj["bbox"][:2])


def _matrix(keys: list[Any]) -> list[list[int]]:
    return [[5 if row == col else 8 if keys[row] == keys[col] else 0
             for col in range(len(keys))] for row in range(len(keys))]


def analyze(grid: Any, policy: str) -> dict[str, Any]:
    policy = _policy({"equivalence_policy": policy})
    components = extract_components(grid)
    orbit_keys = [_orbit_key(obj["normalized"], policy) for obj in components]
    return {
        "components": deepcopy(components),
        "orbit_keys": orbit_keys,
        "matrix": _matrix(orbit_keys),
    }


def solve(grid: Any, policy: str) -> list[list[int]]:
    return analyze(grid, policy)["matrix"]


def solve_bbox_only(grid: Any) -> list[list[int]]:
    components = extract_components(grid)
    keys = [(len(obj["cells"]), obj["shape"]) for obj in components]
    return _matrix(keys)


def _derived_rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"{TASK_ID}:equivalence-policy-v1:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _slot_positions(height: int, width: int, shapes, boundary: bool, rng: random.Random):
    count = len(shapes)
    if count == 3:
        cells = ((0, 0), (0, 2), (1, 1))
    elif count == 4:
        cells = ((0, 0), (0, 2), (1, 0), (1, 2))
    elif count == 5:
        cells = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2))
    elif count == 6:
        cells = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2))
    else:
        raise ValueError("profiles require 3..6 objects")
    positions = []
    for index, ((band_r, band_c), shape) in enumerate(zip(cells, shapes)):
        shape_h = max(r for r, _ in shape) + 1
        shape_w = max(c for _, c in shape) + 1
        r0, r1 = band_r * (height // 2), (band_r + 1) * (height // 2) if band_r == 0 else height
        c0, c1 = band_c * (width // 3), (band_c + 1) * (width // 3) if band_c < 2 else width
        room_h, room_w = r1 - r0, c1 - c0
        if shape_h > room_h or shape_w > room_w:
            raise RuntimeError("shape does not fit assigned slot")
        if boundary:
            row = r0 if band_r == 0 else r1 - shape_h
            col = c0 if band_c == 0 else c1 - shape_w if band_c == 2 else c0 + (room_w - shape_w) // 2
        else:
            row_low, row_high = r0 + 1, r1 - shape_h - 1
            col_low, col_high = c0 + 1, c1 - shape_w - 1
            row = row_low if row_high < row_low else rng.randint(row_low, row_high)
            col = col_low if col_high < col_low else rng.randint(col_low, col_high)
        positions.append((row, col))
    return positions


def _scene(seed: int, split: str, index: int, profile) -> list[list[int]]:
    height, width, role_specs, scale, boundary = profile
    rng = _derived_rng(seed, split, index)
    global_turn = rng.randrange(4)
    shapes = []
    for family, reflected, turn_offset in role_specs:
        shape = SHAPES[family]
        if reflected:
            shape = _mirror(shape)
        shape = _turns(shape, global_turn + turn_offset)
        shapes.append(_scaled(shape, scale))
    positions = _slot_positions(height, width, shapes, boundary, rng)

    group_patterns = {
        3: (0, 0, 1),
        4: (0, 0, 1, 2),
        5: (0, 0, 1, 2, 2),
        6: (0, 0, 1, 2, 3, 2),
    }
    groups = group_patterns[len(shapes)]
    palette = rng.sample(range(1, 10), len(set(groups)))
    colors = [palette[group] for group in groups]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for shape, (top, left), color in zip(shapes, positions, colors):
        for r, c in shape:
            if grid[top + r][left + c] != 0:
                raise RuntimeError("profile placement collision")
            grid[top + r][left + c] = color

    components = extract_components(grid)
    if len(components) != len(shapes):
        raise RuntimeError("profile components merged or split")
    # At least one same-color nonmatch and one different-color match teach that
    # color is irrelevant.  The first profile also preserves equal area/bbox
    # distractors under its shared global turn.
    return grid


def _validate_request(seed: int, settings: Any, demos: int, queries: int) -> str:
    _exact_int(seed, 0, 2**63 - 1, "seed")
    _exact_int(demos, 2, 6, "demos")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")
    return _policy(settings)


def inputs(seed: int, demos: int = 3, queries: int = 4):
    _exact_int(seed, 0, 2**63 - 1, "seed")
    _exact_int(demos, 2, 6, "demos")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")
    train = [_scene(seed, "train", index, DEMO_PROFILES[index]) for index in range(demos)]
    test = [_scene(seed, "test", index, QUERY_PROFILES[index]) for index in range(4)]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in train + test]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("episode inputs must be distinct")
    return train, test


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    policy = _validate_request(seed, settings, demos, queries)
    train_inputs, test_inputs = inputs(seed, demos, queries)
    def pairs(grids):
        return [{"input": deepcopy(grid), "output": solve(grid, policy)} for grid in grids]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {"equivalence_policy": policy},
        "train": pairs(train_inputs),
        "test": pairs(test_inputs),
        "program_solution": program({"equivalence_policy": policy}),
    }


def public_query_turns(episode: dict[str, Any]) -> list[dict[str, Any]]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train and test lists")
    if not episode["train"] or len(episode["test"]) != 4:
        raise ValueError("episode must contain demonstrations and four queries")
    return [json.loads(public_challenge_bytes({"train": episode["train"], "test": [pair]}))
            for pair in episode["test"]]


def lesson_certificate(episode: dict[str, Any]) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("settings")) is not dict:
        raise ValueError("episode lacks settings")
    chosen = _policy(episode["settings"])
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode lacks train/test pairs")
    survivors = []
    rejection = {}
    query_disagreements = {}
    for model in RIVAL_NAMES:
        mismatches = [index for index, pair in enumerate(train)
                      if _RIVALS.predict(pair["input"], model) != pair["output"]]
        rejection[model] = mismatches
        if not mismatches:
            survivors.append(model)
        query_disagreements[model] = [index for index, pair in enumerate(test)
                                      if _RIVALS.predict(pair["input"], model) != pair["output"]]
    harmful = [model for model in survivors if model != chosen and query_disagreements[model]]
    return {
        "chosen": chosen,
        "declared_survivors": [model for model in POLICIES if model in survivors],
        "all_survivors": survivors,
        "harmful_rival_survivors": harmful,
        "rejected_by_demonstration": rejection,
        "query_disagreements": query_disagreements,
        "scope": "Finite named rivals only; not universal uniqueness.",
    }
