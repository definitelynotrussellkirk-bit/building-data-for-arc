"""Native diagonal-projection family with a post-projection count relay.

``project_only`` is the exact canonical rule. ``component_count_relay`` first
constructs the canonical square, counts its same-color 8-connected components,
and uses that derived count as a 1-indexed selector into the source row's
nonzero cells. Only the selected source cell's projected diagonal is recolored
9. Python outputs are authoring claims; native qualification replays labels in
protected Racket.
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
from typing import Any, Iterable

TASK_ID = "82bce7d23c06"
VERSION = "projected-component-count-relay-v1"
FINISHES = ("project_only", "component_count_relay")
SETTINGS = tuple({"finish": value} for value in FINISHES)
DEFAULT_SETTINGS = {"finish": "project_only"}
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
CANONICAL_SHA256 = "21cafd5200143bfecf34d80aa39db3766b772103db913b2fe411888f4e3b8c46"
HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parents[1] / "generator.py"
SHORTCUTS = (
    "first_nonzero_diagonal",
    "last_nonzero_diagonal",
    "second_nonzero_diagonal",
    "third_nonzero_diagonal",
    "distinct_color_count",
    "binary_run_count",
    "source_color_run_count",
    "paint_all_target_color",
    "paint_whole_target_component",
)

# Symbols are remapped to distinct seed-dependent colors in 1..8. The first
# two demonstrations alone distinguish both settings and every declared rival.
_DEMO_PROFILES = (
    (("A", 0, "A", "B", "B"), "gap_merge_component_count_2"),
    (("A", "A", "B", 0, "A", "C"), "four_projected_components"),
    (("A", "B", "B", 0, "C", "D"), "four_components_distinct_target"),
    (("A", "A", 0, 0, "B", "B", 0), "two_wide_bands"),
    (("A", "A", "B", "C"), "dense_three_components"),
    ((0, "A", "A", 0, 0, "B", 0, 0, 0), "sparse_width_nine"),
)
_QUERY_PROFILES = (
    (("A", "B", "B", 0, "A"), "three_component_query"),
    (("A", "A", 0, "B", 0, "C", 0), "separated_query"),
    ((0, "A", "A", 0, 0, 0, "B", 0), "sparse_width_eight"),
    (("A", 0, "A", "B", "B", "C"), "exact_30x30_component_relay"),
)


def _load_generator():
    body = GENERATOR_PATH.read_bytes()
    name = "_parametric_82b_generator_" + hashlib.sha256(
        str(GENERATOR_PATH).encode() + body
    ).hexdigest()
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {GENERATOR_PATH}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        exec(compile(body, str(GENERATOR_PATH), "exec"), module.__dict__)
    return module


_GEN = _load_generator()


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _finish(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"finish"}:
        raise ValueError("settings must contain exactly finish")
    value = settings["finish"]
    if type(value) is not str or value not in FINISHES:
        raise ValueError(f"finish must be one of {FINISHES}")
    return value


def _source(name: str, expected_sha256: str | None = None) -> str:
    raw = (HERE / name).read_bytes()
    if not raw.strip():
        raise ValueError(f"empty Racket source: {name}")
    observed = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and observed != expected_sha256:
        raise ValueError(f"{name} drifted: {observed}")
    return raw.decode("utf-8")


@lru_cache(maxsize=1)
def canonical_source() -> str:
    return _source("canonical.rkt", CANONICAL_SHA256)


@lru_cache(maxsize=1)
def relay_source() -> str:
    return _source("component-count-relay.rkt")


def program(settings: Any) -> str:
    return canonical_source() if _finish(settings) == "project_only" else relay_source()


def counterfactual_program() -> str:
    return _source("wrong-nonzero-count.rkt")


def _validated_grid(grid: Any) -> list[list[int]]:
    errors = _GEN.self_check(grid)
    if errors:
        raise ValueError("invalid diagonal-projection input: " + "; ".join(errors))
    return [list(grid[0])]


def _project(grid: Any) -> list[list[int]]:
    return _GEN.rule_mirror(_validated_grid(grid))


def _objects8_same_color(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = cr + dr, cc + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            objects.append({"color": color, "cells": tuple(sorted(cells))})
    return objects


def _source_color_run_count(row: list[int]) -> int:
    return sum(
        value != 0 and (index == 0 or row[index - 1] != value)
        for index, value in enumerate(row)
    )


def _binary_run_count(row: list[int]) -> int:
    return sum(
        value != 0 and (index == 0 or row[index - 1] == 0)
        for index, value in enumerate(row)
    )


def _diagonal_cells(size: int, source_col: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (row, col)
        for row in range(size)
        for col in range(size)
        if col - (size - 1) + row == source_col
    )


def intermediate(grid: Any) -> dict[str, Any]:
    checked = _validated_grid(grid)
    row = checked[0]
    projected = _project(checked)
    components = _objects8_same_color(projected)
    source_cols = [index for index, value in enumerate(row) if value != 0]
    component_count = len(components)
    if not 1 <= component_count <= len(source_cols):
        raise ValueError(
            f"projected component count {component_count} cannot select among {len(source_cols)} nonzero cells"
        )
    target_col = source_cols[component_count - 1]
    size = len(projected)
    return {
        "projected_component_count": component_count,
        "projected_components": [
            {"color": obj["color"], "size": len(obj["cells"])} for obj in components
        ],
        "source_nonzero_cols": source_cols,
        "source_color_run_count": _source_color_run_count(row),
        "binary_run_count": _binary_run_count(row),
        "distinct_color_count": len(set(value for value in row if value != 0)),
        "target_nonzero_rank": component_count,
        "target_source_col": target_col,
        "target_diagonal_cells": [list(cell) for cell in _diagonal_cells(size, target_col)],
        "counterfactual_target_source_col": source_cols[-1],
        "output_size": size,
    }


def _paint_diagonal(projected: list[list[int]], source_col: int, color: int = 9) -> list[list[int]]:
    output = [row[:] for row in projected]
    for row, col in _diagonal_cells(len(output), source_col):
        output[row][col] = color
    return output


def solve(grid: Any, settings: Any) -> list[list[int]]:
    finish = _finish(settings)
    checked = _validated_grid(grid)
    projected = _project(checked)
    if finish == "project_only":
        return projected
    info = intermediate(checked)
    return _paint_diagonal(projected, info["target_source_col"])


def counterfactual_transform(grid: Any) -> list[list[int]]:
    checked = _validated_grid(grid)
    info = intermediate(checked)
    return _paint_diagonal(_project(checked), info["counterfactual_target_source_col"])


def _rank_to_col(row: list[int], rank: int) -> int:
    cols = [index for index, value in enumerate(row) if value != 0]
    rank = max(1, min(rank, len(cols)))
    return cols[rank - 1]


def _component_containing(
    components: list[dict[str, Any]], cells: set[tuple[int, int]]
) -> tuple[tuple[int, int], ...]:
    matches = [obj["cells"] for obj in components if cells.intersection(obj["cells"])]
    if len(matches) != 1:
        raise AssertionError(f"selected diagonal met {len(matches)} projected components")
    return matches[0]


def shortcut_solve(grid: Any, name: str) -> list[list[int]]:
    if name not in SHORTCUTS:
        raise ValueError(f"unknown shortcut {name!r}")
    checked = _validated_grid(grid)
    row = checked[0]
    projected = _project(checked)
    info = intermediate(checked)
    if name == "first_nonzero_diagonal":
        rank = 1
    elif name == "last_nonzero_diagonal":
        rank = len(info["source_nonzero_cols"])
    elif name == "second_nonzero_diagonal":
        rank = 2
    elif name == "third_nonzero_diagonal":
        rank = 3
    elif name == "distinct_color_count":
        rank = info["distinct_color_count"]
    elif name == "binary_run_count":
        rank = info["binary_run_count"]
    elif name == "source_color_run_count":
        rank = info["source_color_run_count"]
    else:
        rank = info["projected_component_count"]
    target_col = _rank_to_col(row, rank)
    if name == "paint_all_target_color":
        target_color = row[target_col]
        return [
            [9 if value == target_color else value for value in out_row]
            for out_row in projected
        ]
    if name == "paint_whole_target_component":
        selected = set(_diagonal_cells(len(projected), target_col))
        cells = _component_containing(_objects8_same_color(projected), selected)
        output = [out_row[:] for out_row in projected]
        for out_row, out_col in cells:
            output[out_row][out_col] = 9
        return output
    return _paint_diagonal(projected, target_col)


def _rng(seed: int, split: str, index: int) -> random.Random:
    material = f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _build_row(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    symbolic, _tag = profiles[index]
    rng = _rng(seed, split, index)
    symbols = sorted({value for value in symbolic if isinstance(value, str)})
    palette = list(range(1, 9))
    rng.shuffle(palette)
    mapping = dict(zip(symbols, palette[: len(symbols)], strict=True))
    values = [0 if value == 0 else mapping[value] for value in symbolic]
    if rng.randrange(2):
        values.reverse()
    grid = [values]
    errors = _GEN.self_check(grid)
    if errors:
        raise AssertionError({"profile": profiles[index], "errors": errors})
    info = intermediate(grid)
    if not 1 <= info["projected_component_count"] <= info["target_nonzero_rank"]:
        raise AssertionError("invalid relay selector")
    return grid


@lru_cache(maxsize=1024)
def _row_tuple(seed: int, split: str, index: int):
    return tuple(tuple(row) for row in _build_row(seed, split, index))


def _row(seed: int, split: str, index: int) -> list[list[int]]:
    return [list(row) for row in _row_tuple(seed, split, index)]


def sample_inputs(seed: Any, demos: Any = 3, queries: Any = 4) -> dict[str, list]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, *DEMO_LIMITS)
    queries = _integer("queries", queries, *QUERY_LIMITS)
    sampled = {
        "train": [_row(seed, "train", index) for index in range(demos)],
        "test": [_row(seed, "test", index) for index in range(queries)],
    }
    keys = [
        json.dumps(grid, separators=(",", ":"))
        for split in ("train", "test")
        for grid in sampled[split]
    ]
    if len(keys) != len(set(keys)):
        raise AssertionError("all generated inputs must be distinct")
    return sampled


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    finish = _finish(settings)
    sampled = sample_inputs(seed, demos, queries)
    chosen = {"finish": finish}
    return {
        "train": [
            {"input": deepcopy(grid), "output": solve(grid, chosen)}
            for grid in sampled["train"]
        ],
        "test": [
            {"input": deepcopy(grid), "output": solve(grid, chosen)}
            for grid in sampled["test"]
        ],
        "program_solution": program(chosen),
        "settings": chosen,
        "sampler": {
            "version": VERSION,
            "demo_profiles": [tag for _, tag in _DEMO_PROFILES[:demos]],
            "query_profiles": [tag for _, tag in _QUERY_PROFILES[:queries]],
        },
    }


def lesson_certificate(train_pairs: Any, settings: Any) -> dict[str, Any]:
    chosen = {"finish": _finish(settings)}
    if type(train_pairs) is not list or not train_pairs:
        raise ValueError("train_pairs must be a nonempty list")
    for pair in train_pairs:
        if type(pair) is not dict or "input" not in pair or "output" not in pair:
            raise ValueError("each demonstration needs input and output")
    survivors = [
        candidate
        for candidate in SETTINGS
        if all(solve(pair["input"], candidate) == pair["output"] for pair in train_pairs)
    ]
    shortcuts = [
        name
        for name in SHORTCUTS
        if all(shortcut_solve(pair["input"], name) == pair["output"] for pair in train_pairs)
    ]
    return {
        "settings": chosen,
        "demonstrations": len(train_pairs),
        "surviving_settings": survivors,
        "surviving_shortcuts": shortcuts,
        "query_outputs_used": False,
    }


def analyze(grid: Any) -> dict[str, Any]:
    checked = _validated_grid(grid)
    projected = _project(checked)
    info = intermediate(checked)
    occupied = [
        (row, col)
        for row, values in enumerate(projected)
        for col, value in enumerate(values)
        if value != 0
    ]
    sides = []
    if any(row == 0 for row, _ in occupied):
        sides.append("top")
    if any(row == len(projected) - 1 for row, _ in occupied):
        sides.append("bottom")
    if any(col == 0 for _, col in occupied):
        sides.append("left")
    if any(col == len(projected[0]) - 1 for _, col in occupied):
        sides.append("right")
    return {
        "input_shape": [1, len(checked[0])],
        "output_shape": [len(projected), len(projected[0])],
        "nonzero_count": len(info["source_nonzero_cols"]),
        "projected_nonzero_count": len(occupied),
        "projected_component_count": info["projected_component_count"],
        "source_color_run_count": info["source_color_run_count"],
        "binary_run_count": info["binary_run_count"],
        "distinct_color_count": info["distinct_color_count"],
        "target_nonzero_rank": info["target_nonzero_rank"],
        "target_source_col": info["target_source_col"],
        "boundary_sides": sorted(sides),
    }


def public_turn(episode: Any, query_index: Any) -> dict[str, Any]:
    if (
        type(episode) is not dict
        or type(episode.get("train")) is not list
        or type(episode.get("test")) is not list
    ):
        raise ValueError("episode must contain train and test lists")
    query_index = _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
