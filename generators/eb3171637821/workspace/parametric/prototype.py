"""Parametric divider-lattice family for task ``eb3171637821``.

``solid_count`` is the exact canonical task: collapse every positive row band
and column band to one cell and color the resulting count rectangle uniformly
with the cell color.

``area_parity`` preserves the same segmentation but makes the measured
intermediate matter: each compressed cell receives the cell color only when
its source rectangle has odd area; even-area rectangles receive the divider
color.  The input distribution is shared between settings, so the labelled
examples—not hidden generator differences—identify the rule.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

from reviewer_support import canonical_path, find_root


TASK_ID = "eb3171637821"
PARAMETER_NAME = "encoding"
ENCODINGS = ("solid_count", "area_parity")
DEFAULT_ENCODING = "solid_count"
PROTOTYPE_VERSION = "divider-area-parity-v1"
HERE = Path(__file__).resolve().parent
CANONICAL_SHA256 = "da9f6ae6f31dc78a860e0b96f157a56ff75e6fd704c4804a9c392bff4663e2fc"

# (row sizes, row divider thickness, row boundary mode,
#  column sizes, column divider thickness, column boundary mode)
_DEMO_PROFILES = (
    ((1, 2, 3), 1, "none",  (1, 2, 3, 4), 2, "start"),
    ((2, 1, 4, 3), 2, "end", (3, 2, 1), 1, "none"),
    ((1, 5, 2, 3, 4), 1, "both", (2, 3, 5), 2, "start"),
    ((4, 1, 2), 2, "both", (1, 2, 4, 3, 5), 1, "end"),
    ((3, 2, 6, 1), 1, "start", (4, 1, 2, 5), 2, "both"),
    ((2, 7, 1, 4, 3), 2, "none", (1, 6, 2, 3), 1, "both"),
)
_QUERY_PROFILES = (
    ((1, 4, 2, 5), 1, "both", (2, 1, 3, 6), 2, "start"),
    ((6, 1, 3, 2, 4), 2, "end", (1, 5, 2, 4), 1, "none"),
    ((2, 3, 1, 6), 2, "start", (5, 2, 1, 3, 4), 1, "both"),
    # Exact 30x30 stress: 6x5 bands, 7 divider rows, 12 divider columns.
    ((1, 2, 3, 4, 5, 8), 1, "both", (1, 2, 3, 4, 8), 2, "both"),
)
_BOUNDARY_MODES = {"none", "start", "end", "both"}


def _canonical_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    root = find_root(__file__)
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    return rows


def canonical_program() -> str:
    programs = {row.get("program_solution") for row in _canonical_rows()}
    if len(programs) != 1 or not all(type(value) is str and value for value in programs):
        raise ValueError(f"{TASK_ID}: expected exactly one concrete canonical program")
    program = programs.pop()
    digest = hashlib.sha256(program.encode("utf-8")).hexdigest()
    if digest != CANONICAL_SHA256:
        raise ValueError(
            f"{TASK_ID}: canonical program changed ({digest}); refusing stale promotion"
        )
    return program


def validate_encoding(value: Any) -> str:
    if type(value) is not str or value not in ENCODINGS:
        raise ValueError(f"declared encoding must be one of {ENCODINGS}")
    return value


def rule_text(encoding: Any) -> str:
    selected = validate_encoding(encoding)
    if selected == DEFAULT_ENCODING:
        return canonical_program()
    path = HERE / "rules/area_parity.rkt"
    program = path.read_text(encoding="utf-8").rstrip("\n")
    if not program.startswith("(rule!") or "row-band-sizes" not in program:
        raise ValueError(f"invalid alternate rule source: {path}")
    return program


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be a nonnegative literal integer below 2**63")
    return seed


def _validate_count(value: Any, *, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be a literal integer in {minimum}..{maximum}")
    return value


def _validate_request(*, seed: Any, encoding: Any, demos: Any, queries: Any) -> str:
    _validate_seed(seed)
    selected = validate_encoding(encoding)
    _validate_count(demos, name="demos", minimum=2, maximum=6)
    _validate_count(queries, name="queries", minimum=1, maximum=4)
    return selected


def _seed_int(seed: int, split: str, index: int) -> int:
    payload = f"{PROTOTYPE_VERSION}:{seed}:{split}:{index}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest(), "big")


def _axis_mask(
    band_sizes: Iterable[int], divider_thickness: int, boundary_mode: str
) -> list[bool]:
    sizes = tuple(band_sizes)
    if not 2 <= len(sizes) <= 8 or any(type(size) is not int or size < 1 for size in sizes):
        raise ValueError("band sizes must contain 2..8 positive literal integers")
    if type(divider_thickness) is not int or divider_thickness not in (1, 2):
        raise ValueError("divider thickness must be 1 or 2")
    if boundary_mode not in _BOUNDARY_MODES:
        raise ValueError(f"unknown boundary mode: {boundary_mode}")
    mask: list[bool] = []
    if boundary_mode in {"start", "both"}:
        mask.extend([True] * divider_thickness)
    for index, size in enumerate(sizes):
        mask.extend([False] * size)
        if index + 1 < len(sizes):
            mask.extend([True] * divider_thickness)
    if boundary_mode in {"end", "both"}:
        mask.extend([True] * divider_thickness)
    return mask


def _permute_sizes(values: Iterable[int], rng: random.Random) -> tuple[int, ...]:
    values = list(values)
    # A cyclic rotation and optional reversal preserve the exact profile extent
    # while making seeds visibly different without changing the lesson family.
    offset = rng.randrange(len(values))
    values = values[offset:] + values[:offset]
    if rng.randrange(2):
        values.reverse()
    return tuple(values)


def build_input(seed: int, split: str, index: int) -> list[list[int]]:
    _validate_seed(seed)
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    if split not in {"train", "test"} or not 0 <= index < len(profiles):
        raise ValueError(f"unsupported {split!r} profile index {index}")
    row_sizes, row_thickness, row_mode, col_sizes, col_thickness, col_mode = profiles[index]
    rng = random.Random(_seed_int(seed, split, index))
    row_sizes = _permute_sizes(row_sizes, rng)
    col_sizes = _permute_sizes(col_sizes, rng)
    row_mask = _axis_mask(row_sizes, row_thickness, row_mode)
    col_mask = _axis_mask(col_sizes, col_thickness, col_mode)
    if len(row_mask) > 30 or len(col_mask) > 30:
        raise RuntimeError("profile exceeds ARC 30x30 limit")
    divider_color, cell_color = rng.sample(list(range(1, 10)), 2)
    return [
        [
            divider_color if row_mask[row] or col_mask[col] else cell_color
            for col in range(len(col_mask))
        ]
        for row in range(len(row_mask))
    ]


def _runs(indices: Iterable[int]) -> list[tuple[int, int]]:
    values = list(indices)
    if not values:
        return []
    result: list[tuple[int, int]] = []
    start = previous = values[0]
    for value in values[1:]:
        if value != previous + 1:
            result.append((start, previous))
            start = value
        previous = value
    result.append((start, previous))
    return result


def analyze_input(grid: Any) -> dict[str, Any]:
    if (
        type(grid) is not list
        or not grid
        or len(grid) > 30
        or type(grid[0]) is not list
        or not grid[0]
        or len(grid[0]) > 30
        or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
        or any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row)
    ):
        raise ValueError("expected a rectangular 1..30 ARC grid")
    height, width = len(grid), len(grid[0])
    colors = sorted({cell for row in grid for cell in row})
    if len(colors) != 2:
        raise ValueError("divider lattice requires exactly two colors")

    candidates: list[tuple[int, list[int], list[int]]] = []
    for color in colors:
        divider_rows = [row for row in range(height) if all(grid[row][col] == color for col in range(width))]
        divider_cols = [col for col in range(width) if all(grid[row][col] == color for row in range(height))]
        if not divider_rows or not divider_cols:
            continue
        divider_row_set, divider_col_set = set(divider_rows), set(divider_cols)
        if all(
            (grid[row][col] == color) == (row in divider_row_set or col in divider_col_set)
            for row in range(height)
            for col in range(width)
        ):
            candidates.append((color, divider_rows, divider_cols))
    if len(candidates) != 1:
        raise ValueError("could not identify a unique complete divider lattice")
    divider_color, divider_rows, divider_cols = candidates[0]
    cell_color = next(color for color in colors if color != divider_color)
    divider_row_set, divider_col_set = set(divider_rows), set(divider_cols)
    row_runs = _runs(row for row in range(height) if row not in divider_row_set)
    col_runs = _runs(col for col in range(width) if col not in divider_col_set)
    row_sizes = [end - start + 1 for start, end in row_runs]
    col_sizes = [end - start + 1 for start, end in col_runs]
    if not 2 <= len(row_sizes) <= 8 or not 2 <= len(col_sizes) <= 8:
        raise ValueError("divider lattice must contain 2..8 positive bands on each axis")
    return {
        "height": height,
        "width": width,
        "divider_color": divider_color,
        "cell_color": cell_color,
        "divider_rows": divider_rows,
        "divider_cols": divider_cols,
        "row_band_runs": [list(run) for run in row_runs],
        "col_band_runs": [list(run) for run in col_runs],
        "row_band_sizes": row_sizes,
        "col_band_sizes": col_sizes,
    }


def output_for(grid: Any, encoding: Any) -> list[list[int]]:
    selected = validate_encoding(encoding)
    info = analyze_input(grid)
    if selected == "solid_count":
        return [
            [info["cell_color"] for _ in info["col_band_sizes"]]
            for _ in info["row_band_sizes"]
        ]
    return [
        [
            info["cell_color"] if (row_size * col_size) % 2 else info["divider_color"]
            for col_size in info["col_band_sizes"]
        ]
        for row_size in info["row_band_sizes"]
    ]


def _shortcut_output(grid: Any, kind: str) -> list[list[int]]:
    info = analyze_input(grid)
    rows, cols = info["row_band_sizes"], info["col_band_sizes"]
    cell, divider = info["cell_color"], info["divider_color"]
    if kind == "always_cell":
        return [[cell for _ in cols] for _ in rows]
    if kind == "always_divider":
        return [[divider for _ in cols] for _ in rows]
    if kind == "row_parity_only":
        return [[cell if row % 2 else divider for _ in cols] for row in rows]
    if kind == "col_parity_only":
        return [[cell if col % 2 else divider for col in cols] for _ in rows]
    if kind == "sum_parity":
        return [[cell if (row + col) % 2 else divider for col in cols] for row in rows]
    if kind == "checkerboard":
        return [
            [cell if (r + c) % 2 else divider for c, _ in enumerate(cols)]
            for r, _ in enumerate(rows)
        ]
    raise ValueError(f"unknown shortcut: {kind}")


def shortcut_outputs(grid: Any, encoding: Any) -> dict[str, list[list[int]]]:
    selected = validate_encoding(encoding)
    if selected == "solid_count":
        return {
            "area_parity": output_for(grid, "area_parity"),
            "always_divider": _shortcut_output(grid, "always_divider"),
            "checkerboard": _shortcut_output(grid, "checkerboard"),
        }
    return {
        "solid_count": output_for(grid, "solid_count"),
        "always_divider": _shortcut_output(grid, "always_divider"),
        "row_parity_only": _shortcut_output(grid, "row_parity_only"),
        "col_parity_only": _shortcut_output(grid, "col_parity_only"),
        "sum_parity": _shortcut_output(grid, "sum_parity"),
        "checkerboard": _shortcut_output(grid, "checkerboard"),
    }


def assess_demos(demonstrations: list[dict[str, Any]], encoding: Any) -> dict[str, Any]:
    selected = validate_encoding(encoding)
    labels = [output_for(row["input"], selected) for row in demonstrations]
    declared = [
        candidate
        for candidate in ENCODINGS
        if all(
            output_for(row["input"], candidate) == label
            for row, label in zip(demonstrations, labels)
        )
    ]
    names = sorted(shortcut_outputs(demonstrations[0]["input"], selected))
    shortcuts = [
        name
        for name in names
        if all(
            shortcut_outputs(row["input"], selected)[name] == label
            for row, label in zip(demonstrations, labels)
        )
    ]
    return {
        "encoding": selected,
        "demonstrations": len(demonstrations),
        "declared_setting_survivors": declared,
        "shortcut_survivors": shortcuts,
        "tested_shortcuts": names,
    }


def select_inputs(seed: int, *, demos: int, queries: int) -> dict[str, list[dict[str, Any]]]:
    _validate_request(seed=seed, encoding=DEFAULT_ENCODING, demos=demos, queries=queries)
    selected = {
        "train": [{"input": build_input(seed, "train", index)} for index in range(demos)],
        "test": [{"input": build_input(seed, "test", index)} for index in range(queries)],
    }
    serialized = [
        json.dumps(row["input"], separators=(",", ":"))
        for split in ("train", "test")
        for row in selected[split]
    ]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("constructed episode contains duplicate inputs")
    return selected


def generate_episode(
    seed: Any, *, encoding: Any, demos: Any, queries: Any
) -> dict[str, Any]:
    selected_encoding = _validate_request(
        seed=seed, encoding=encoding, demos=demos, queries=queries
    )
    selected = select_inputs(seed, demos=demos, queries=queries)
    episode = {
        split: [
            {
                "input": copy.deepcopy(row["input"]),
                "output": output_for(row["input"], selected_encoding),
            }
            for row in selected[split]
        ]
        for split in ("train", "test")
    }
    episode["program_solution"] = rule_text(selected_encoding)
    return episode


def counterfactual_rule(kind: str) -> str:
    program = rule_text("area_parity")
    if kind == "wrong_intermediate":
        old = "(if (odd? (* (list-ref row-band-sizes r)\n                                      (list-ref col-band-sizes c)))"
        new = "(if (odd? (* 1 1))"
    elif kind == "row_only":
        old = "(if (odd? (* (list-ref row-band-sizes r)\n                                      (list-ref col-band-sizes c)))"
        new = "(if (odd? (list-ref row-band-sizes r))"
    else:
        raise ValueError(f"unknown counterfactual kind: {kind}")
    if program.count(old) != 1:
        raise ValueError(f"counterfactual rewrite point changed: {kind}")
    return program.replace(old, new)


def causal_case(grid: Any, kind: str = "wrong_intermediate") -> dict[str, Any]:
    actual = output_for(grid, "area_parity")
    if kind == "wrong_intermediate":
        counterfactual = _shortcut_output(grid, "always_cell")
    elif kind == "row_only":
        counterfactual = _shortcut_output(grid, "row_parity_only")
    else:
        raise ValueError(kind)
    if actual == counterfactual:
        raise RuntimeError(f"counterfactual {kind} did not change output")
    info = analyze_input(grid)
    return {
        "ablation": kind,
        "settings": {PARAMETER_NAME: "area_parity"},
        "program": rule_text("area_parity"),
        "counterfactual_program": counterfactual_rule(kind),
        "input": copy.deepcopy(grid),
        "intermediate_value": {
            "row_band_sizes": info["row_band_sizes"],
            "col_band_sizes": info["col_band_sizes"],
        },
        "output": actual,
        "counterfactual_output": counterfactual,
    }
