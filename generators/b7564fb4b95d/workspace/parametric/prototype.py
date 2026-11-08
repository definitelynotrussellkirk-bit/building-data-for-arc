"""Matched-input transform-order family for b7564fb4b95d.

The canonical setting applies the corner command to the selected source and
stamps the result.  The alternate first applies that command, then horizontally
reflects the command result before stamping.  The protected counterfactual
reflects the source before applying the command, exposing the non-commuting
order dependency on 90° and 270° commands.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

TASK_ID = "b7564fb4b95d"
VERSION = "command-reflection-order-v1"
PARAMETER = "transform_order"
MODES = ("command_only", "command_then_reflect")
DEFAULT_SETTINGS = {PARAMETER: MODES[0]}
_DIR = Path(__file__).resolve().parent
_PROGRAM_FILES = {
    MODES[0]: "canonical.rkt",
    MODES[1]: "command-then-reflect.rkt",
}
_DEMO_SPECS = (
    (11, 14, 1, 2),
    (15, 18, 2, 4),
    (18, 20, 3, 2),
    (20, 22, 2, 4),
    (24, 26, 3, 2),
    (27, 28, 3, 4),
)
_QUERY_SPECS = (
    (14, 16, 1, 4),
    (19, 23, 2, 2),
    (25, 27, 3, 4),
    (30, 30, 3, 2),
)


def _load_base():
    path = _DIR.parents[1] / "generator.py"
    body = path.read_bytes()
    name = "_arc_b7564fb4b95d_base_" + hashlib.sha256(str(path).encode() + body).hexdigest()
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load adjacent production generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


_BASE = _load_base()


def _exact_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in MODES:
        raise ValueError(f"{PARAMETER} must be one of {MODES}")
    return value


def program(settings: dict[str, Any]) -> str:
    return (_DIR / _PROGRAM_FILES[_mode(settings)]).read_bytes().decode("utf-8")


def counterfactual_program() -> str:
    return (_DIR / "reflect-then-command-counterfactual.rkt").read_bytes().decode("utf-8")


def _reflect_horizontal(cells):
    points = _BASE._normalize(cells)
    width = max(col for _, col in points) + 1
    return _BASE._normalize((row, width - 1 - col) for row, col in points)


def transform_intermediate(grid: list[list[int]]) -> dict[str, Any]:
    facts = _BASE.scene_facts(grid)
    source = _BASE._normalize(facts["source"])
    after_command = _BASE.transform_cells(source, facts["command_code"])
    after_command_reflect = _reflect_horizontal(after_command)
    reflected_source = _reflect_horizontal(source)
    wrong_order = _BASE.transform_cells(reflected_source, facts["command_code"])
    return {
        "command_code": facts["command_code"],
        "normalized_source": [list(point) for point in source],
        "after_command": [list(point) for point in after_command],
        "after_command_then_reflect": [list(point) for point in after_command_reflect],
        "after_reflect_then_command": [list(point) for point in wrong_order],
    }


def _render(grid: list[list[int]], template) -> list[list[int]]:
    facts = _BASE.scene_facts(grid)
    output = _BASE.full_grid(facts["grid_h"], facts["grid_w"], 0)
    for frame in facts["frames"]:
        for row, col in frame["cells"]:
            output[row][col] = frame["color"]
        _BASE._center_stamp(output, tuple(template), frame)
    return output


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    mode = _mode(settings)
    value = transform_intermediate(grid)
    if mode == MODES[0]:
        template = value["after_command"]
    else:
        template = value["after_command_then_reflect"]
    return _render(grid, tuple(tuple(point) for point in template))


def counterfactual_transform(grid: list[list[int]]) -> list[list[int]]:
    value = transform_intermediate(grid)
    return _render(
        grid,
        tuple(tuple(point) for point in value["after_reflect_then_command"]),
    )


def _identity_transform(grid):
    value = transform_intermediate(grid)
    return _render(grid, tuple(tuple(point) for point in value["normalized_source"]))


def _reflect_only_transform(grid):
    value = transform_intermediate(grid)
    source = tuple(tuple(point) for point in value["normalized_source"])
    return _render(grid, _reflect_horizontal(source))


def _vertical_reflect_after_command(grid):
    value = transform_intermediate(grid)
    points = tuple(tuple(point) for point in value["after_command"])
    height = max(row for row, _ in points) + 1
    reflected = _BASE._normalize((height - 1 - row, col) for row, col in points)
    return _render(grid, reflected)


def _frames_only(grid):
    facts = _BASE.scene_facts(grid)
    output = _BASE.full_grid(facts["grid_h"], facts["grid_w"], 0)
    for frame in facts["frames"]:
        for row, col in frame["cells"]:
            output[row][col] = frame["color"]
    return output


SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "ignore_all_transforms": _identity_transform,
    "reflect_source_only": _reflect_only_transform,
    "reflect_before_command": counterfactual_transform,
    "vertical_reflect_after_command": _vertical_reflect_after_command,
    "frames_only": _frames_only,
}


def _input(seed: int, private_index: int, spec: tuple[int, int, int, int]) -> list[list[int]]:
    height, width, frames, command = spec
    # Select a lawful asymmetric scene on which both settings and every declared
    # shortcut are observably distinct.  This is a bounded constructive teaching
    # filter, not a query-label check: it depends only on candidate input geometry.
    for attempt in range(64):
        candidate_index = private_index * 64 + attempt
        grid = _BASE.generate(
            seed,
            candidate_index,
            grid_h=height,
            grid_w=width,
            n_frames=frames,
            command_code=command,
        )
        outputs = [transform(grid, {PARAMETER: mode}) for mode in MODES]
        if outputs[0] == outputs[1]:
            continue
        if all(rival(grid) != output for rival in SHORTCUTS.values() for output in outputs):
            return grid
    raise RuntimeError(f"could not construct a distinguishing scene for private index {private_index}")


def _pair(seed: int, private_index: int, spec, settings):
    grid = _input(seed, private_index, spec)
    return {"input": grid, "output": transform(grid, settings)}


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    if type(seed) is not int:
        raise ValueError("seed must be an exact integer")
    _mode(settings)
    demo_count = _exact_int("demos", demos, 2, 6)
    query_count = _exact_int("queries", queries, 1, 4)
    train = [
        _pair(seed, index, _DEMO_SPECS[index], settings)
        for index in range(demo_count)
    ]
    test = [
        _pair(seed, 100 + index, _QUERY_SPECS[index], settings)
        for index in range(query_count)
    ]
    return {
        "train": train,
        "test": test,
        "program_solution": program(settings),
    }


def lesson_certificate(demos: list[dict[str, Any]], settings: dict[str, Any]) -> dict[str, Any]:
    requested = _mode(settings)
    surviving_settings = []
    for mode in MODES:
        candidate = {PARAMETER: mode}
        if all(transform(pair["input"], candidate) == pair["output"] for pair in demos):
            surviving_settings.append(candidate)
    surviving_shortcuts = [
        name
        for name, rival in SHORTCUTS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
    ]
    return {
        "requested_setting": {PARAMETER: requested},
        "surviving_settings": surviving_settings,
        "surviving_shortcuts": surviving_shortcuts,
        "query_outputs_used": False,
        "demonstration_count": len(demos),
    }


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    facts = _BASE.scene_facts(grid)
    frame_cells = [cell for frame in facts["frames"] for cell in frame["cells"]]
    occupied = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    return {
        "height": facts["grid_h"],
        "width": facts["grid_w"],
        "frame_count": len(facts["frames"]),
        "frame_cell_count": len(frame_cells),
        "source_size": facts["source_size"],
        "command_code": facts["command_code"],
        "occupied_row_span": max(row for row, _ in occupied) - min(row for row, _ in occupied),
        "occupied_col_span": max(col for _, col in occupied) - min(col for _, col in occupied),
    }
