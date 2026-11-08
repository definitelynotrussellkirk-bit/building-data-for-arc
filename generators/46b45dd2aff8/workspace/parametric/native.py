"""Native rectangle-selection family for ``46b45dd2aff8``.

``same_color`` is the byte-exact canonical program. ``nearest_aligned`` first
extracts all solid rectangles, then maps each isolated dot to the aligned
rectangle with the smallest background gap regardless of rectangle color.
The selected dot-to-rectangle records are the input-dependent intermediate
used by the shared flower/stem/cap renderer.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

TASK_ID = "46b45dd2aff8"
PARAMETER = "rectangle_policy"
SETTINGS = ("same_color", "nearest_aligned")
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1
_HOME = Path(__file__).resolve().parent
_TASK_HOME = _HOME.parents[1]
_PROGRAM_FILES = {
    "same_color": _HOME / "canonical.rkt",
    "nearest_aligned": _HOME / "nearest_aligned.rkt",
}

# sample_index, height, width, active colors, background. Every slot is a
# color-trap profile, so the first two demonstrations distinguish the settings.
_TRAIN_SPECS = (
    (2, 18, 20, 2, 3),
    (3, 20, 22, 3, 4),
    (5, 22, 24, 2, 8),
    (6, 24, 26, 3, 1),
    (7, 26, 28, 3, 5),
    (11, 27, 29, 3, 1),
)
_QUERY_SPECS = (
    (9, 18, 19, 2, 2),
    (10, 22, 23, 3, 6),
    (11, 27, 29, 3, 7),
    (13, 30, 30, 3, 9),
)


def _load_generator():
    name = "_46b45dd2aff8_source_generator"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    path = _TASK_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load 46b45dd2aff8 source generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_GEN = _load_generator()


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS!r}")
    return value


def program(settings: dict[str, Any]) -> str:
    return _PROGRAM_FILES[_validate_settings(settings)].read_text(encoding="utf-8")


def _scene_seed(seed: int, split: str, index: int) -> int:
    raw = f"{TASK_ID}|rectangle-policy-v1|{seed}|{split}|{index}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") & MAX_SEED


def _sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    specs = _TRAIN_SPECS if split == "train" else _QUERY_SPECS
    sample_index, height, width, n_colors, background = specs[index]
    grid = _GEN.generate(
        _scene_seed(seed, split, index),
        sample_index,
        difficulty="medium",
        grid_h=height,
        grid_w=width,
        n_colors=n_colors,
        background=background,
    )
    if _GEN.schedule_profile(0, sample_index, "medium") != "color_trap":
        raise RuntimeError("native curriculum must use color-trap profiles")
    errors = _GEN.self_check(grid)
    if errors:
        raise RuntimeError("source generator produced invalid scene: " + "; ".join(errors))
    if apply_rule(grid, "same_color") == apply_rule(grid, "nearest_aligned"):
        raise RuntimeError("color-trap scene does not distinguish rectangle policies")
    return grid


def _candidate_records(grid: list[list[int]], dot_color: int, dot: tuple[int, int]):
    _, rects, _ = _GEN._rects_and_dots(grid)
    rows = []
    for rectangle_color, bbox in sorted(rects.items()):
        relation = _GEN._dot_direction(dot, bbox)
        if relation is not None:
            direction, gap = relation
            rows.append((gap, bbox, rectangle_color, direction))
    return rows


def selection_records(grid: list[list[int]], policy: str) -> list[dict[str, Any]]:
    if policy not in SETTINGS:
        raise ValueError(f"policy must be one of {SETTINGS!r}")
    _, rects, dots = _GEN._rects_and_dots(grid)
    result: list[dict[str, Any]] = []
    for dot_color in sorted(dots):
        for dot in sorted(dots[dot_color]):
            if policy == "same_color":
                bbox = rects.get(dot_color)
                relation = _GEN._dot_direction(dot, bbox) if bbox is not None else None
                if relation is None:
                    continue
                direction, gap = relation
                rectangle_color = dot_color
            else:
                candidates = _candidate_records(grid, dot_color, dot)
                if not candidates:
                    continue
                gap, bbox, rectangle_color, direction = min(candidates)
            result.append(
                {
                    "dot_color": dot_color,
                    "dot": list(dot),
                    "rectangle_color": rectangle_color,
                    "rectangle_bbox": list(bbox),
                    "direction": direction,
                    "gap": gap,
                }
            )
    return result


def apply_rule(grid: list[list[int]], policy: str) -> list[list[int]]:
    out = deepcopy(grid)
    bg, _, _ = _GEN._rects_and_dots(grid)
    for record in selection_records(grid, policy):
        _GEN._transform_dot(
            out,
            bg,
            record["dot_color"],
            tuple(record["dot"]),
            tuple(record["rectangle_bbox"]),
        )
    return out


def generator_nearest_rule(grid: list[list[int]]) -> list[list[int]]:
    return _GEN._nearest_aligned_ignoring_color(grid)


def _identity(grid):
    return deepcopy(grid)


def _rival_functions() -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    return {
        "identity": _identity,
        "same_color": lambda grid: apply_rule(grid, "same_color"),
        "nearest_aligned": lambda grid: apply_rule(grid, "nearest_aligned"),
        "first_dot_same_color": _GEN._first_dot_per_color,
        "horizontal_same_color": _GEN._horizontal_only,
    }


def rival_outputs(grid: list[list[int]], chosen: str) -> dict[str, list[list[int]]]:
    if chosen not in SETTINGS:
        raise ValueError(f"chosen must be one of {SETTINGS!r}")
    return {
        name: function(grid)
        for name, function in _rival_functions().items()
        if name != chosen
    }


def surviving_rivals(train: list[dict[str, Any]], chosen: str) -> list[str]:
    if type(train) is not list or not train:
        raise ValueError("train must be a nonempty list")
    names = set(rival_outputs(train[0]["input"], chosen))
    return sorted(
        name
        for name in names
        if all(rival_outputs(pair["input"], chosen)[name] == pair["output"] for pair in train)
    )


def _pair(grid: list[list[int]], policy: str) -> dict[str, list[list[int]]]:
    return {"input": deepcopy(grid), "output": apply_rule(grid, policy)}


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    if type(queries) is not int:
        raise TypeError("queries must be an exact integer; bool is forbidden")
    if queries != QUERY_COUNT:
        raise ValueError(f"queries must be exactly {QUERY_COUNT}")
    policy = _validate_settings(settings)
    train = [_pair(_sample_input(seed, "train", i), policy) for i in range(demos)]
    test = [_pair(_sample_input(seed, "test", i), policy) for i in range(QUERY_COUNT)]
    encoded = [json.dumps(pair["input"], separators=(",", ":")) for pair in [*train, *test]]
    if len(encoded) != len(set(encoded)):
        raise RuntimeError("all demonstration and query inputs must be distinct")
    survivors = surviving_rivals(train, policy)
    if survivors:
        raise RuntimeError(f"visible demonstrations leave declared rivals alive: {survivors}")
    return {"train": train, "test": test, "program_solution": program(settings)}
