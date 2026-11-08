"""Native matched-input family with an optional second-stage vertical flip."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]
GENERATOR_PATH = TASK_HOME / "generator.py"
CANONICAL_PATH = HERE / "canonical.rkt"
MODES = ("none", "flip_ud")
DIMS = (
    (12, 22, 4, 3),
    (15, 24, 5, 2),
    (18, 28, 6, 1),
    (22, 30, 5, 3),
    (30, 30, 10, 2),
)
TEXTURES = ("default", "warm", "cool", "varied")
QUERY_SCENE_INDICES = (104, 101, 102, 103)


def _load_base():
    name = "_arc_9e2802ee78bd_base_" + hashlib.sha256(str(GENERATOR_PATH).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load_base()


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _mode(value: Any) -> str:
    if type(value) is not str or value not in MODES:
        raise ValueError("post_transform must be 'none' or 'flip_ud'")
    return value


def _settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"post_transform"}:
        raise ValueError("settings must contain exactly post_transform")
    return _mode(settings["post_transform"])


def canonical_source() -> str:
    return CANONICAL_PATH.read_text(encoding="utf-8")


_FINAL_PASTE = "(t13-paste-all g trans 1 (+ sep 1))"


def _replace_final(expression: str) -> str:
    source = canonical_source()
    if source.count(_FINAL_PASTE) != 1:
        raise ValueError("canonical final paste changed or is ambiguous")
    return source.replace(_FINAL_PASTE, expression, 1)


def post_source(operation: str) -> str:
    expressions = {
        "none": _FINAL_PASTE,
        "flip_ud": "(t13-paste-all g (flip-ud trans) 1 (+ sep 1))",
        "flip_lr": "(t13-paste-all g (flip-lr trans) 1 (+ sep 1))",
        "rotate_cw": "(t13-paste-all g (rotate-cw trans) 1 (+ sep 1))",
    }
    if operation not in expressions:
        raise ValueError(f"unknown post operation: {operation}")
    return canonical_source() if operation == "none" else _replace_final(expressions[operation])


def program(settings: dict[str, Any]) -> str:
    return post_source(_settings(settings))


def counterfactual_program(settings: dict[str, Any], ablation: str) -> str:
    mode = _settings(settings)
    if ablation != "wrong_intermediate":
        raise ValueError("only wrong_intermediate is supported")
    expression = (
        "(t13-paste-all g (flip-ud src) 1 (+ sep 1))"
        if mode == "flip_ud"
        else "(t13-paste-all g src 1 (+ sep 1))"
    )
    return _replace_final(expression)


def rival_programs() -> dict[str, str]:
    return {
        "identity_source": _replace_final("(t13-paste-all g src 1 (+ sep 1))"),
        "flip_ud_source": _replace_final("(t13-paste-all g (flip-ud src) 1 (+ sep 1))"),
        "flip_lr_post": post_source("flip_lr"),
        "rotate_cw_post": post_source("rotate_cw"),
    }


def scene(seed: int, index: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, 2**31 - 1, "index")
    height, width, panel_w, marker = DIMS[index % len(DIMS)]
    texture = TEXTURES[(seed + index) % len(TEXTURES)]
    palette_size = 2 + ((seed * 3 + index) % 4)
    grid = BASE.generate(
        seed,
        index,
        difficulty=None,
        grid_h=height,
        grid_w=width,
        panel_h=height - 1,
        panel_w=panel_w,
        marker=marker,
        palette_size=palette_size,
        texture=texture,
        position_bias="left_panel",
    )
    if BASE.self_check(grid):
        raise AssertionError(BASE.self_check(grid))
    return grid


def transform_intermediate(grid: list[list[int]]) -> list[list[int]]:
    info = BASE._analyze(grid)
    return [list(row) for row in info["transformed"]]


def _paste_nonzero(
    grid: list[list[int]], panel: list[list[int]], top: int, left: int
) -> list[list[int]]:
    out = [list(row) for row in grid]
    for row, values in enumerate(panel):
        for col, value in enumerate(values):
            if value != 0 and 0 <= top + row < len(out) and 0 <= left + col < len(out[0]):
                out[top + row][left + col] = value
    return out


def transform(
    grid: list[list[int]],
    mode: str,
    *,
    wrong_intermediate: str | None = None,
) -> list[list[int]]:
    mode = _mode(mode)
    info = BASE._analyze(grid)
    if wrong_intermediate not in (None, "identity_source"):
        raise ValueError("wrong_intermediate must be None or 'identity_source'")
    intermediate = (
        [list(row) for row in info["panel"]]
        if wrong_intermediate == "identity_source"
        else [list(row) for row in info["transformed"]]
    )
    final_panel = BASE._flip_ud(intermediate) if mode == "flip_ud" else intermediate
    return _paste_nonzero(grid, final_panel, 1, info["separator"] + 1)


def intermediate_summary(grid: list[list[int]]) -> dict[str, Any]:
    info = BASE._analyze(grid)
    panel = transform_intermediate(grid)
    return {
        "marker": info["marker"],
        "source_shape": [info["panel_h"], info["panel_w"]],
        "transformed_shape": [len(panel), len(panel[0])],
        "transformed_panel": panel,
    }


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 2,
    queries: int = 4,
) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    mode = _settings(settings)
    train_inputs = [scene(seed, index) for index in range(demos)]
    test_inputs = [scene(seed, QUERY_SCENE_INDICES[index]) for index in range(queries)]
    return {
        "train": [{"input": grid, "output": transform(grid, mode)} for grid in train_inputs],
        "test": [{"input": grid, "output": transform(grid, mode)} for grid in test_inputs],
        "program_solution": program(settings),
    }


def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select an existing query; bool is forbidden")
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }
