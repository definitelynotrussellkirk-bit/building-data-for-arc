"""Parametric shape-equivalence family for ``c782972f840b``.

The canonical setting compares object shapes up to rotation.  The alternate
setting additionally identifies reflections.  Inputs are shared across settings
and deliberately contain a chiral mirror pair plus independent color/shape
relations, including dense boundary-touching 30x30 stress.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "c782972f840b"
POLICIES = ("rotation", "dihedral")
DEFAULT_SETTINGS = {"equivalence_policy": "rotation"}
HERE = Path(__file__).resolve().parent

# height, width, scale, object count
_DEMO_PROFILES = (
    (12, 14, 1, 4),
    (13, 15, 1, 4),
    (14, 17, 1, 5),
    (16, 18, 1, 6),
    (18, 20, 2, 4),
    (22, 24, 2, 6),
)
_QUERY_PROFILES = (
    (16, 18, 1, 4),
    (20, 22, 2, 4),
    (24, 27, 2, 6),
    (30, 30, 3, 6),
)

_S = ((0, 1), (0, 2), (1, 0), (1, 1))
_Z = ((0, 0), (0, 1), (1, 1), (1, 2))
_T = ((0, 0), (0, 1), (0, 2), (1, 1))
_L = ((0, 0), (1, 0), (2, 0), (2, 1))


def _load_selected():
    path = HERE.parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("_c782_selected_for_parametric", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_SELECTED = _load_selected()


def _literal_int(name: str, value: object, lower: int, upper: int) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be a literal integer in {lower}..{upper}")
    return value


def normalize_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"equivalence_policy"}:
        raise ValueError("settings must contain exactly equivalence_policy")
    policy = settings["equivalence_policy"]
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError(f"equivalence_policy must be one of {POLICIES!r}")
    return {"equivalence_policy": policy}


@lru_cache(maxsize=1)
def canonical_program() -> str:
    return (HERE / "canonical.rkt").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def dihedral_program() -> str:
    return (HERE / "dihedral.rkt").read_text(encoding="utf-8")


def program(settings: object) -> str:
    policy = normalize_settings(settings)["equivalence_policy"]
    return canonical_program() if policy == "rotation" else dihedral_program()


def validate_input(value: object) -> list[list[int]]:
    if type(value) is not list or not 1 <= len(value) <= 30:
        raise ValueError("grid height must be 1..30")
    if not value or type(value[0]) is not list or not 1 <= len(value[0]) <= 30:
        raise ValueError("grid width must be 1..30")
    width = len(value[0])
    grid: list[list[int]] = []
    for row in value:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError("grid cells must be literal integers in 0..9")
        grid.append(row[:])
    items = _SELECTED._components(grid)
    if not 4 <= len(items) <= 6:
        raise ValueError("relation grammar requires 4..6 nonzero objects")
    if any(item["color"] is None for item in items):
        raise ValueError("every object must be monochrome")
    if any(item["color"] == 0 for item in items):
        raise ValueError("objects must be nonzero")
    return grid


def _policy_key(item: dict[str, Any], policy: str):
    if policy == "rotation":
        return item["rotation"]
    if policy == "dihedral":
        return item["dihedral"]
    if policy == "oriented":
        return item["oriented"]
    if policy == "bbox":
        r0, c0, r1, c1 = item["bbox"]
        return (r1 - r0 + 1, c1 - c0 + 1)
    if policy == "area":
        return len(item["cells"])
    raise ValueError(f"unknown equivalence policy {policy!r}")


def _class_ids(items: list[dict[str, Any]], policy: str) -> list[int]:
    seen: dict[Any, int] = {}
    result: list[int] = []
    for item in items:
        key = _policy_key(item, policy)
        if key not in seen:
            seen[key] = len(seen)
        result.append(seen[key])
    return result


def _render_from_classes(items: list[dict[str, Any]], class_ids: list[int]) -> list[list[int]]:
    size = len(items)
    out = [[0 for _ in range(size)] for _ in range(size)]
    for r in range(size):
        for c in range(size):
            if r == c:
                out[r][c] = 9
            else:
                same_shape = class_ids[r] == class_ids[c]
                same_color = items[r]["color"] == items[c]["color"]
                out[r][c] = (
                    6 if same_shape and same_color
                    else 4 if same_shape
                    else 2 if same_color
                    else 0
                )
    return out


def transform(value: object, policy: object) -> list[list[int]]:
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError(f"equivalence policy must be one of {POLICIES!r}")
    grid = validate_input(value)
    items = _SELECTED._components(grid)
    return _render_from_classes(items, _class_ids(items, policy))


def _normalize(shape):
    return _SELECTED._normalize_shape(shape)


def _rotate(shape, turns: int):
    return _SELECTED._rotate_n(shape, turns)


def _scale(shape, factor: int):
    cells = []
    for row, col in shape:
        for dr in range(factor):
            for dc in range(factor):
                cells.append((row * factor + dr, col * factor + dc))
    return _normalize(cells)


def _shape_size(shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _rng(seed: int, split: str, slot: int) -> random.Random:
    digest = hashlib.sha256(
        f"c782-equivalence-v1:{seed}:{split}:{slot}".encode()
    ).digest()
    return random.Random(digest)


def _anchors(height: int, width: int, shapes) -> list[tuple[int, int]]:
    n = len(shapes)
    if n <= 4:
        slots = (("top", "left"), ("top", "right"), ("bottom", "left"), ("bottom", "right"))
    else:
        slots = (
            ("top", "left"), ("top", "center"), ("top", "right"),
            ("bottom", "left"), ("bottom", "center"), ("bottom", "right"),
        )
    result = []
    for shape, (vertical, horizontal) in zip(shapes, slots[:n], strict=True):
        h, w = _shape_size(shape)
        row = 0 if vertical == "top" else height - h
        if horizontal == "left":
            col = 0
        elif horizontal == "right":
            col = width - w
        else:
            col = (width - w) // 2
        result.append((row, col))
    return result


def _build_input(seed: int, split: str, slot: int, profile: tuple[int, int, int, int]) -> list[list[int]]:
    height, width, scale, count = profile
    rng = _rng(seed, split, slot)
    shared_turn = rng.randrange(4)
    l_turn = rng.randrange(4)
    shapes = [
        _scale(_rotate(_S, shared_turn), scale),
        _scale(_rotate(_Z, shared_turn), scale),
        _scale(_rotate(_S, shared_turn + 1), scale),
        _scale(_rotate(_T, rng.randrange(4)), scale),
        _scale(_rotate(_L, l_turn), scale),
        _scale(_rotate(_L, l_turn + 1), scale),
    ][:count]
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], 3)
    colors = [palette[0], palette[0], palette[1], palette[1], palette[2], palette[2]][:count]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    occupied: set[tuple[int, int]] = set()
    for shape, color, (row0, col0) in zip(shapes, colors, _anchors(height, width, shapes), strict=True):
        cells = {(row0 + r, col0 + c) for r, c in shape}
        if any(not (0 <= r < height and 0 <= c < width) for r, c in cells):
            raise ValueError("profile does not fit its objects")
        if occupied & cells:
            raise ValueError("profile overlaps objects")
        if any((r + dr, c + dc) in occupied for r, c in cells for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
            raise ValueError("profile joins neighboring objects")
        for r, c in cells:
            grid[r][c] = color
        occupied.update(cells)
    validate_input(grid)
    items = _SELECTED._components(grid)
    if _class_ids(items, "dihedral")[0] != _class_ids(items, "dihedral")[1]:
        raise AssertionError("first two objects must be a dihedral-only mirror pair")
    if _class_ids(items, "rotation")[0] == _class_ids(items, "rotation")[1]:
        raise AssertionError("mirror pair must remain distinct under rotations")
    return grid


def _schedule(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demos = [_build_input(seed, "demo", i, profile) for i, profile in enumerate(_DEMO_PROFILES)]
    queries = [_build_input(seed, "query", i, profile) for i, profile in enumerate(_QUERY_PROFILES)]
    frozen = [json.dumps(grid, separators=(",", ":")) for grid in demos + queries]
    if len(frozen) != len(set(frozen)):
        raise ValueError("parametric schedule produced duplicate inputs")
    return demos, queries


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, object]:
    checked_seed = _literal_int("seed", seed, 0, 2**63 - 1)
    checked_demos = _literal_int("demos", demos, 2, 6)
    checked_queries = _literal_int("queries", queries, 1, 4)
    policy = normalize_settings(settings)["equivalence_policy"]
    demo_inputs, query_inputs = _schedule(checked_seed)

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": deepcopy(grid), "output": transform(grid, policy)}

    train = [pair(grid) for grid in demo_inputs[:checked_demos]]
    test = [pair(grid) for grid in query_inputs[:checked_queries]]
    if setting_survivors(train) != [policy]:
        raise ValueError("demonstrations do not uniquely identify equivalence_policy")
    return {"train": train, "test": test, "program_solution": program({"equivalence_policy": policy})}


def setting_survivors(demonstrations: object) -> list[str]:
    if type(demonstrations) is not list or not demonstrations:
        raise ValueError("demonstrations must be a nonempty list")
    return [
        policy for policy in POLICIES
        if all(transform(pair["input"], policy) == pair["output"] for pair in demonstrations)
    ]


def _rival_transform(value: object, name: str) -> list[list[int]]:
    grid = validate_input(value)
    items = _SELECTED._components(grid)
    if name in {"oriented", "bbox", "area"}:
        return _render_from_classes(items, _class_ids(items, name))
    n = len(items)
    if name == "color_only":
        classes = list(range(n))
        out = _render_from_classes(items, classes)
        return out
    if name == "all_same_shape":
        return _render_from_classes(items, [0] * n)
    if name == "shape_only_rotation":
        classes = _class_ids(items, "rotation")
        return [[9 if r == c else 4 if classes[r] == classes[c] else 0 for c in range(n)] for r in range(n)]
    if name == "shape_only_dihedral":
        classes = _class_ids(items, "dihedral")
        return [[9 if r == c else 4 if classes[r] == classes[c] else 0 for c in range(n)] for r in range(n)]
    if name == "identity_matrix":
        return [[9 if r == c else 0 for c in range(n)] for r in range(n)]
    raise ValueError(f"unknown rival {name!r}")


RIVALS = (
    "oriented",
    "bbox",
    "area",
    "color_only",
    "all_same_shape",
    "shape_only_rotation",
    "shape_only_dihedral",
    "identity_matrix",
)


def rival_survivors(demonstrations: object, *, selected_policy: str) -> list[str]:
    if selected_policy not in POLICIES:
        raise ValueError("unknown selected policy")
    return [
        name for name in RIVALS
        if all(_rival_transform(pair["input"], name) == pair["output"] for pair in demonstrations)
    ]


def dependency(value: object, policy: object) -> dict[str, object]:
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError("unknown policy")
    grid = validate_input(value)
    items = _SELECTED._components(grid)
    class_ids = _class_ids(items, policy)
    return {
        "step_a": "extract bbox-ordered objects and canonicalize each binary crop under the selected transformation group",
        "intermediate": "the ordered vector of input-dependent shape-orbit class IDs",
        "class_ids": class_ids,
        "colors": [item["color"] for item in items],
        "step_b": "render every matrix cell from equality of the class IDs together with object-color equality",
        "final": _render_from_classes(items, class_ids),
    }
