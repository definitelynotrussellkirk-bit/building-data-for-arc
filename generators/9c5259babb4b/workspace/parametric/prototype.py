"""Matched-input parametric symmetry-precedence episodes for 9c5259babb4b.

The canonical setting checks top-bottom symmetry before left-right symmetry.
The alternate reverses only that precedence.  Inputs are sampled independently
of the hidden setting and retain the source task's 8-connected object discovery,
singleton removal, and symmetry classification.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]
TASK_ID = "9c5259babb4b"
PRECEDENCES = ("top_bottom_first", "left_right_first")
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4


def _load_generator():
    path = TASK_HOME / "generator.py"
    name = "_symmetry_precedence_base_" + hashlib.sha256(path.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load_generator()

_DEMO_SPECS = (
    {"profile": "precedence_both", "difficulty": "easy"},
    {"profile": "precedence_both", "difficulty": "medium", "touch_border": True},
    {"profile": "class_balanced", "difficulty": "easy"},
    {"profile": "dense_mixed", "difficulty": "medium"},
    {"profile": "precedence_both", "difficulty": "hard"},
    {"profile": "no_asymmetry", "difficulty": "hard"},
)
_QUERY_SPECS = (
    {"profile": "precedence_both", "difficulty": "easy"},
    {"profile": "precedence_both", "difficulty": "medium"},
    {"profile": "precedence_both", "difficulty": "hard", "touch_border": True},
    {"profile": "precedence_both", "difficulty": "hard", "exact_30": True, "min_foreground": 45},
)


def _literal_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a literal integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def validate_precedence(value: Any) -> str:
    if type(value) is not str or value not in PRECEDENCES:
        raise ValueError(f"precedence must be one of {PRECEDENCES}")
    return value


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"precedence"}:
        raise ValueError("settings must contain exactly precedence")
    return validate_precedence(settings["precedence"])


def program_for(precedence: Any) -> str:
    precedence = validate_precedence(precedence)
    return (HERE / f"{precedence}.rkt").read_text()


def _derive(seed: int, split: str, index: int, attempt: int) -> tuple[int, int]:
    payload = f"9c5259babb4b-precedence-v1:{seed}:{split}:{index}:{attempt}".encode()
    digest = hashlib.sha256(payload).digest()
    source_seed = int.from_bytes(digest[:8], "big") & (2**63 - 1)
    sample_index = int.from_bytes(digest[8:16], "big") & (2**63 - 1)
    return source_seed, sample_index


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _translate_to_border(grid: list[list[int]], *, side: str) -> list[list[int]]:
    background = BASE._mode(grid)
    occupied = [(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value != background]
    if not occupied:
        raise ValueError("cannot translate an empty foreground")
    if side == "top":
        dr, dc = -min(row for row, _ in occupied), 0
    elif side == "left":
        dr, dc = 0, -min(col for _, col in occupied)
    else:
        raise ValueError(f"unknown border side {side!r}")
    result = [[background] * len(grid[0]) for _ in grid]
    for row, col in occupied:
        result[row + dr][col + dc] = grid[row][col]
    return result


def _pad_to_30(grid: list[list[int]], *, seed: int, split: str, index: int) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    if height > 30 or width > 30:
        raise ValueError("cannot pad a grid larger than 30x30")
    background = BASE._mode(grid)
    digest = hashlib.sha256(f"pad:{seed}:{split}:{index}".encode()).digest()
    row0 = digest[0] % (31 - height)
    col0 = digest[1] % (31 - width)
    result = [[background] * 30 for _ in range(30)]
    for row, values in enumerate(grid):
        result[row0 + row][col0:col0 + width] = list(values)
    return result


def scene_summary(grid: list[list[int]]) -> dict[str, Any]:
    analysis = BASE._analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid symmetry scene: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    counts = Counter(obj["kind"] for obj in facts["kept"])
    background = facts["background"]
    foreground = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != background
    ]
    canonical = output_for(grid, "top_bottom_first")
    alternate = output_for(grid, "left_right_first")
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "background": background,
        "scene_profile": analysis["scene_profile"],
        "singleton_count": facts["singleton_count"],
        "kept_count": facts["kept_count"],
        "foreground_cells": len(foreground),
        "foreground_touches_border": any(
            row in (0, len(grid) - 1) or col in (0, len(grid[0]) - 1)
            for row, col in foreground
        ),
        "class_counts": {
            "top_bottom_only": counts["h"],
            "left_right_only": counts["v"],
            "asymmetric": counts["a"],
            "both": counts["both"],
        },
        "diagonal_asymmetric_count": sum(
            1 for obj in facts["kept"]
            if obj["kind"] == "a" and not BASE._connected4(obj["norm"])
        ),
        "setting_difference_cells": sum(
            first != second
            for first_row, second_row in zip(canonical, alternate)
            for first, second in zip(first_row, second_row)
        ),
    }


def output_for(grid: list[list[int]], precedence: Any) -> list[list[int]]:
    precedence = validate_precedence(precedence)
    analysis = BASE._analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid symmetry scene: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    output = [[facts["background"]] * len(grid[0]) for _ in grid]
    for obj in facts["kept"]:
        kind = obj["kind"]
        if precedence == "top_bottom_first":
            color = 1 if kind in {"h", "both"} else 3 if kind == "v" else 6
        else:
            color = 3 if kind in {"v", "both"} else 1 if kind == "h" else 6
        for row, col in obj["cells"]:
            output[row][col] = color
    return output


def _build_scene(seed: int, split: str, index: int, spec: dict[str, Any], forbidden: set[tuple[tuple[int, ...], ...]]):
    for attempt in range(256):
        source_seed, sample_index = _derive(seed, split, index, attempt)
        grid = BASE.generate(
            source_seed,
            sample_index,
            difficulty=spec["difficulty"],
            scene_profile=spec["profile"],
        )
        if spec.get("touch_border"):
            side = "top" if (source_seed + index) % 2 == 0 else "left"
            grid = _translate_to_border(grid, side=side)
        if spec.get("exact_30"):
            grid = _pad_to_30(grid, seed=seed, split=split, index=index)
        frozen = _freeze(grid)
        if frozen in forbidden:
            continue
        try:
            summary = scene_summary(grid)
        except ValueError:
            continue
        if summary["scene_profile"] != spec["profile"]:
            continue
        if spec.get("touch_border") and not summary["foreground_touches_border"]:
            continue
        if spec.get("exact_30") and (summary["height"], summary["width"]) != (30, 30):
            continue
        if summary["foreground_cells"] < spec.get("min_foreground", 0):
            continue
        return grid
    raise RuntimeError(f"could not construct {split} scene {index} for seed {seed}")


def build_episode(seed: Any, precedence: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _literal_int("seed", seed, 0, 2**63 - 1)
    precedence = validate_precedence(precedence)
    demos = _literal_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _literal_int("queries", queries, QUERY_COUNT, QUERY_COUNT)
    del queries

    used: set[tuple[tuple[int, ...], ...]] = set()
    train_inputs = []
    for index, spec in enumerate(_DEMO_SPECS[:demos]):
        grid = _build_scene(seed, "train", index, spec, used)
        used.add(_freeze(grid))
        train_inputs.append(grid)
    test_inputs = []
    for index, spec in enumerate(_QUERY_SPECS):
        grid = _build_scene(seed, "test", index, spec, used)
        used.add(_freeze(grid))
        test_inputs.append(grid)

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": copy.deepcopy(grid), "output": output_for(grid, precedence)}

    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {"precedence": precedence},
        "train": [pair(grid) for grid in train_inputs],
        "test": [pair(grid) for grid in test_inputs],
        "program_solution": program_for(precedence),
    }


def public_projection(episode: Any, query_index: Any) -> dict[str, Any]:
    if type(episode) is not dict or not isinstance(episode.get("train"), list) or not isinstance(episode.get("test"), list):
        raise ValueError("episode must contain train and test lists")
    query_index = _literal_int("query_index", query_index, 0, len(episode["test"]) - 1)
    train = []
    for pair in episode["train"]:
        if type(pair) is not dict or set(pair) < {"input", "output"}:
            raise ValueError("demonstration pairs need input and output")
        train.append({"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])})
    query = episode["test"][query_index]
    if type(query) is not dict or "input" not in query:
        raise ValueError("query pair needs input")
    return {"train": train, "test": [{"input": copy.deepcopy(query["input"])}]}


def episode_digest(episode: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(episode, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
