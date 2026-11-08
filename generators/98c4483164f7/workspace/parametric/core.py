"""Proposed rule variants for the 98c4483164f7 marker-ray family.

quarter_turns rotates each active diagonal clockwise in screen coordinates:
(dr, dc) -> (dc, -dr). stride projects at positive multiples of 1 or 2.
The full motif is always recolored and all four cells are ray origins.
No setting changes the canonical input grammar or the production generator.
Python is an independent authoring mirror; matching Racket is the authority.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
import importlib.util
from pathlib import Path
import sys

TASK_ID = "98c4483164f7"
HOME = Path(__file__).resolve().parent
PARAMETERS = {"quarter_turns": (0, 1, 2, 3), "stride": (1, 2)}


@dataclass(frozen=True)
class Params:
    quarter_turns: int = 0
    stride: int = 1


def normalize_params(params: Mapping | Params | None = None) -> Params:
    """Validate strict integer settings; omitted mapping fields use defaults.

    None and an empty mapping mean the canonical setting. Unknown fields,
    booleans, floats, null values and out-of-domain integers fail loudly.
    Params objects are validated here too; construction alone is not admission.
    """
    if params is None:
        result = Params()
    elif isinstance(params, Params):
        result = params
    elif isinstance(params, Mapping):
        unknown = set(params) - set(PARAMETERS)
        if unknown:
            raise ValueError(f"unknown parameter field(s): {sorted(map(str, unknown))}")
        result = Params(**params)
    else:
        raise TypeError("params must be a mapping, Params, or None")
    for name, allowed in PARAMETERS.items():
        value = getattr(result, name)
        if type(value) is not int:
            raise TypeError(f"{name} must be an exact integer, not bool or float")
        if value not in allowed:
            raise ValueError(f"{name} must be one of {allowed}, got {value!r}")
    return result


def params_dict(params: Mapping | Params | None = None) -> dict[str, int]:
    selected = normalize_params(params)
    return {"quarter_turns": selected.quarter_turns, "stride": selected.stride}


def enumerate_settings() -> list[dict[str, int]]:
    return [{"quarter_turns": turns, "stride": stride}
            for turns in PARAMETERS["quarter_turns"] for stride in PARAMETERS["stride"]]


def _parse_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 2 <= len(grid) <= 30:
        raise ValueError("grid must have 2..30 rows")
    if not isinstance(grid[0], (list, tuple)) or not 2 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 2..30 columns")
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integer ARC colors 0..9")
    cells = [(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0]
    if len(cells) != 4:
        raise ValueError("expected exactly four nonzero motif cells on background 0")
    top, left = min(r for r, _ in cells), min(c for _, c in cells)
    block = {(top + r, left + c) for r in (0, 1) for c in (0, 1)}
    if set(cells) != block:
        raise ValueError("the four nonzero cells must form one filled 2x2 motif")
    red = [(r, c) for r, c in cells if grid[r][c] == 2]
    payloads = {grid[r][c] for r, c in cells if grid[r][c] != 2}
    if not 1 <= len(red) <= 3 or len(payloads) != 1:
        raise ValueError("motif requires 1..3 red markers and one shared non-red payload color")
    return height, width, cells, red, top, left, next(iter(payloads))


def transform(grid, params: Mapping | Params | None = None) -> list[list[int]]:
    """Execute a parameterized Python mirror on any lawful canonical input."""
    selected = normalize_params(params)
    height, width, cells, red, top, left, payload = _parse_grid(grid)
    directions = []
    for row, col in red:
        dr, dc = (-1 if row == top else 1), (-1 if col == left else 1)
        for _ in range(selected.quarter_turns):
            dr, dc = dc, -dr
        directions.append((dr, dc))
    output = [list(row) for row in grid]
    for row, col in cells:
        output[row][col] = payload
    for row, col in cells:
        for dr, dc in directions:
            for distance in range(selected.stride, max(height, width), selected.stride):
                nr, nc = row + distance * dr, col + distance * dc
                if not (0 <= nr < height and 0 <= nc < width):
                    break
                output[nr][nc] = payload
    return output


def materialize_program(params: Mapping | Params | None = None) -> str:
    """Return exact canonical Racket by default, or a bounded projection edit."""
    selected = normalize_params(params)
    program = (HOME / "canonical.rkt").read_text(encoding="utf-8")
    row_token, col_token = "(* k (first dir))", "(* k (snd dir))"
    if program.count(row_token) != 1 or program.count(col_token) != 1:
        raise RuntimeError("canonical ray-coordinate patch anchors have drifted")
    if selected == Params():
        return program
    row_expr, col_expr = (
        ("(first dir)", "(snd dir)"),
        ("(snd dir)", "(- (first dir))"),
        ("(- (first dir))", "(- (snd dir))"),
        ("(- (snd dir))", "(first dir)"),
    )[selected.quarter_turns]
    # Distinct placeholders prevent a newly rotated expression from being
    # replaced again when it happens to equal the other original coordinate.
    program = program.replace(row_token, "__PARAMETRIC_ROW__")
    program = program.replace(col_token, "__PARAMETRIC_COL__")
    program = program.replace("__PARAMETRIC_ROW__", f"(* k {selected.stride} {row_expr})")
    return program.replace("__PARAMETRIC_COL__", f"(* k {selected.stride} {col_expr})")


@lru_cache(maxsize=1)
def canonical_generator():
    """Load this checkout's unchanged generator lazily, with no sibling imports."""
    root = next((p for p in HOME.parents if (p / "shared/runtime").is_dir()), None)
    if root is None:
        raise RuntimeError("cannot locate this checkout's shared/runtime")
    runtime = str(root / "shared/runtime")
    if runtime not in sys.path:
        sys.path.insert(0, runtime)
    path = root / "generators" / TASK_ID / "generator.py"
    name = "_parametric_canonical_98c4483164f7"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load canonical generator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sample_input(seed: int, index: int, *, grid_h=None, grid_w=None):
    """Delegate input sampling to the unchanged production generator.

    Seeds are exact integers; index is a nonnegative exact integer. Dimension
    overrides inherit the generator's exact integer 6..30 contract.
    """
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    if type(index) is not int:
        raise TypeError("index must be an exact integer")
    if index < 0:
        raise ValueError("index must be nonnegative")
    overrides = {}
    if grid_h is not None:
        overrides["grid_h"] = grid_h
    if grid_w is not None:
        overrides["grid_w"] = grid_w
    return canonical_generator().generate(seed, index, **overrides)
