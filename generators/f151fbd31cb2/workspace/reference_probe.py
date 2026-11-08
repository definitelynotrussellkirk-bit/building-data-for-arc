"""Independent reviewer oracle and rival probes for f151fbd31cb2.

This module deliberately does not import implementation helpers from generator.py.
It is copied with task-local tests so future reviewers can replay the semantic
claims against canonical data and the real Racket authority.
"""
from __future__ import annotations

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
import sys
import types
from pathlib import Path
from typing import Iterable

TASK_ID = "f151fbd31cb2"
HOME = Path(__file__).resolve().parents[1]

_L_SHAPES = {
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
}
_PLUS = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = spec_from_file_location("reviewed_f151fbd31cb2", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    from reviewer_support import canonical_pairs as load_pairs, find_root

    return load_pairs(TASK_ID, root=find_root(__file__))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(row for row, _ in cells)
    c0 = min(col for _, col in cells)
    return tuple(sorted((row - r0, col - c0) for row, col in cells))


def _green_components(grid) -> list[tuple[tuple[int, int], ...]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 3
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            row, col = stack.pop()
            for dr, dc in _CARDINAL:
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        components.append(tuple(sorted(cells)))
    return components


def analyze(grid) -> dict:
    shape_hits = {
        color: [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        for color in (1, 4)
    }
    color_hits = {
        color: [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        for color in (2, 6, 8)
    }
    shape_keys = [color for color, cells in shape_hits.items() if len(cells) == 1]
    color_keys = [color for color, cells in color_hits.items() if len(cells) == 1]
    if len(shape_keys) != 1 or len(color_keys) != 1:
        raise ValueError("grid does not contain exactly one shape key and one color key")

    records = []
    for cells in _green_components(grid):
        normalized = _normalize(cells)
        if normalized in _L_SHAPES:
            family = "L"
        elif normalized == _PLUS:
            family = "PLUS"
        else:
            family = "OTHER"
        records.append({"cells": cells, "family": family, "size": len(cells)})
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "shape_key": shape_keys[0],
        "color_key": color_keys[0],
        "records": records,
        "n_l": sum(record["family"] == "L" for record in records),
        "n_plus": sum(record["family"] == "PLUS" for record in records),
    }


def observed(grid) -> dict:
    facts = analyze(grid)
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "shape_key": facts["shape_key"],
        "color_key": facts["color_key"],
        "n_l": facts["n_l"],
        "n_plus": facts["n_plus"],
    }


def _paint_family(grid, family: str) -> list[list[int]]:
    facts = analyze(grid)
    out = deepcopy(grid)
    for record in facts["records"]:
        if record["family"] == family:
            for row, col in record["cells"]:
                out[row][col] = facts["color_key"]
    return out


def rule_output(grid) -> list[list[int]]:
    facts = analyze(grid)
    selected = "L" if facts["shape_key"] == 1 else "PLUS"
    return _paint_family(grid, selected)


def majority_objects_rival(grid) -> list[list[int]]:
    """Ignore the shape key; recolor the more numerous family (L on ties)."""
    facts = analyze(grid)
    selected = "PLUS" if facts["n_plus"] > facts["n_l"] else "L"
    return _paint_family(grid, selected)


def larger_total_area_rival(grid) -> list[list[int]]:
    """Ignore the shape key; recolor the family occupying more green cells."""
    facts = analyze(grid)
    l_area = sum(record["size"] for record in facts["records"] if record["family"] == "L")
    plus_area = sum(record["size"] for record in facts["records"] if record["family"] == "PLUS")
    selected = "PLUS" if plus_area > l_area else "L"
    return _paint_family(grid, selected)


def _packet_rule_source() -> str:
    """Load the immutable task authority from this review packet's source tree."""
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
    """Expose the packet's relocated parser under the runtime's expected name."""
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


def racket_outputs(grids):
    """Apply the real packet Racket rule without importing a generator bundle."""
    from puzzle_generators import runner

    _install_packet_comment_parser()
    callable_text = runner.wrap_rule(_packet_rule_source())
    bridge, fn_name = runner._open_bridge_with_rule(callable_text)
    try:
        return [runner._apply_rule(bridge, fn_name, deepcopy(grid)) for grid in grids]
    finally:
        bridge.shutdown()
