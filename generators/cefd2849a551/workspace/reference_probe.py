"""Independent review oracle and replay helpers for ``cefd2849a551``.

Nothing here imports geometry helpers from the selected generator.  Task-local
regression tests and future reviewers can therefore compare the implementation,
canonical examples, and real Racket authority against a separately written
4-neighbour-boundary oracle.
"""
from __future__ import annotations

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import sys
import types
from typing import Iterable, Sequence

TASK_ID = "cefd2849a551"
HOME = Path(__file__).resolve().parents[1]
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
EIGHT = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if dr or dc
)
Grid = list[list[int]]
Cell = tuple[int, int]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(
        path or os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")
    ).resolve()
    spec = spec_from_file_location("reviewed_cefd2849a551", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    from reviewer_support import canonical_pairs as load_pairs, find_root

    return load_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def object_facts(grid: Sequence[Sequence[int]]) -> tuple[int, set[Cell]]:
    colors = {
        int(value)
        for row in grid
        for value in row
        if int(value) != 0
    }
    if len(colors) != 1:
        raise ValueError(f"expected one foreground color, got {sorted(colors)}")
    color = next(iter(colors))
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if int(value) == color
    }
    return color, cells


def boundary_output(
    grid: Sequence[Sequence[int]],
    *,
    neighborhood: Iterable[tuple[int, int]] = CARDINAL,
) -> Grid:
    color, cells = object_facts(grid)
    height, width = len(grid), len(grid[0])
    boundary = {
        (row, col)
        for row, col in cells
        if any((row + dr, col + dc) not in cells for dr, dc in neighborhood)
    }
    return [
        [color if (row, col) in boundary else 0 for col in range(width)]
        for row in range(height)
    ]


def identity_rival(grid: Sequence[Sequence[int]]) -> Grid:
    return [list(row) for row in grid]


def eight_neighbor_rival(grid: Sequence[Sequence[int]]) -> Grid:
    return boundary_output(grid, neighborhood=EIGHT)


def bbox_perimeter_rival(grid: Sequence[Sequence[int]]) -> Grid:
    color, cells = object_facts(grid)
    height, width = len(grid), len(grid[0])
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return [
        [
            color
            if top <= row <= bottom
            and left <= col <= right
            and (row in (top, bottom) or col in (left, right))
            else 0
            for col in range(width)
        ]
        for row in range(height)
    ]


def observed_shape(grid: Sequence[Sequence[int]]) -> str:
    _color, cells = object_facts(grid)
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    missing = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if (row, col) not in cells
    }
    if not missing:
        return "rect"
    if len(missing) == 1:
        return "step"
    components = 0
    remaining = set(missing)
    while remaining:
        components += 1
        stack = [remaining.pop()]
        while stack:
            row, col = stack.pop()
            for dr, dc in CARDINAL:
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return "L" if components == 1 else "T" if components == 2 else "other"


def observed_palette(grid: Sequence[Sequence[int]]) -> str:
    color, _cells = object_facts(grid)
    groups = {
        "default": {4},
        "warm": {2, 3},
        "cool": {1, 8},
        "varied": {6, 7, 9},
    }
    for name, values in groups.items():
        if color in values:
            return name
    return "unknown"


def observed(grid: Sequence[Sequence[int]]) -> dict[str, int | str]:
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "shape_kind": observed_shape(grid),
        "palette_kind": observed_palette(grid),
    }


def _packet_rule_source() -> str:
    repo_root = HOME.parents[1]
    solutions = repo_root / "shared" / "data" / "base" / "solutions"
    for path in sorted(solutions.rglob("*.json")):
        try:
            record = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if record.get("task_id") != TASK_ID:
            continue
        target = record.get("racket_target") or {}
        if target.get("needs_conversion"):
            continue
        source = (target.get("target_code") or target.get("raw_code") or "").strip()
        if source:
            return source
    raise FileNotFoundError(f"packet contains no executable Racket authority for {TASK_ID}")


def _install_packet_comment_parser() -> None:
    if "scripts.comment_solutions" in sys.modules:
        return
    tools = HOME.parents[1] / "shared" / "tools"
    package = sys.modules.setdefault("scripts", types.ModuleType("scripts"))
    package.__path__ = [str(tools)]
    spec = spec_from_file_location(
        "scripts.comment_solutions", tools / "comment_solutions.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load packet Racket parser")
    module = module_from_spec(spec)
    sys.modules["scripts.comment_solutions"] = module
    spec.loader.exec_module(module)


def racket_outputs(grids: Iterable[Sequence[Sequence[int]]]) -> list[Grid]:
    """Apply the packet's selected Racket rule without importing the generator."""
    from puzzle_generators import runner

    _install_packet_comment_parser()
    callable_text = runner.wrap_rule(_packet_rule_source())
    bridge, function_name = runner._open_bridge_with_rule(callable_text)
    try:
        return [
            runner._apply_rule(bridge, function_name, deepcopy(grid))
            for grid in grids
        ]
    finally:
        bridge.shutdown()
