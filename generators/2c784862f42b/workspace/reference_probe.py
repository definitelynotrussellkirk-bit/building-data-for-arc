"""Independent oracle and reusable curriculum probe for 2c784862f42b.

The helpers deliberately reconstruct the public transform-code semantics rather
than importing production transformation functions.  Tests may point
``GENERATOR_UNDER_TEST`` at a retained candidate source.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

TASK_ID = "2c784862f42b"
TASK_HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or TASK_HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_2c784862f42b", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    root = find_root(__file__)
    return _canonical_pairs(TASK_ID, root=root)


def canonical_rule_source() -> str:
    root = find_root(__file__)
    ledger = root / "shared/data/canonical/puzzles.jsonl"
    if not ledger.is_file():
        ledger = root / "data/canonical/puzzles.jsonl"
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise KeyError(TASK_ID)


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _copy(grid):
    return [list(row) for row in grid]


def transform(panel, code: int):
    """Independent 5x5 implementation of the six published opcodes."""
    panel = _copy(panel)
    if code == 0:
        return panel
    if code == 1:  # clockwise
        return [list(row) for row in zip(*panel[::-1])]
    if code == 2:
        return [row[::-1] for row in panel[::-1]]
    if code == 3:  # counter-clockwise
        return [list(row) for row in zip(*panel)][::-1]
    if code == 4:
        return [row[::-1] for row in panel]
    if code == 5:
        return panel[::-1]
    raise ValueError(f"unknown transform code {code}")


def _recolor(panel, color: int):
    return [[color if value else 0 for value in row] for row in panel]


def _gallery(panels):
    out = []
    for row_index in range(5):
        row = []
        for index, panel in enumerate(panels):
            if index:
                row.append(0)
            row.extend(panel[row_index])
        out.append(row)
    return out


def intended_output(grid):
    current = _copy(grid[:5])
    codes = grid[5][:4]
    target = grid[5][4]
    panels = []
    for code in codes:
        current = transform(current, code)
        panels.append(_recolor(current, target))
    return _gallery(panels)


def independent_steps_output(grid):
    prototype = _copy(grid[:5])
    target = grid[5][4]
    return _gallery([_recolor(transform(prototype, code), target) for code in grid[5][:4]])


def swapped_quarter_turns_output(grid):
    remap = {1: 3, 3: 1}
    changed = _copy(grid)
    changed[5][:4] = [remap.get(code, code) for code in grid[5][:4]]
    return intended_output(changed)


def swapped_reflections_output(grid):
    remap = {4: 5, 5: 4}
    changed = _copy(grid)
    changed[5][:4] = [remap.get(code, code) for code in grid[5][:4]]
    return intended_output(changed)


def prototype_cells(grid):
    return {(r, c) for r in range(5) for c in range(5) if grid[r][c] != 0}


def connected(cells) -> bool:
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            point = (r + dr, c + dc)
            if point in cells and point not in seen:
                seen.add(point)
                stack.append(point)
    return seen == cells


def sequence_codes(grid):
    return tuple(grid[5][:4])


def rival_outputs(grid):
    return {
        "independent_steps": independent_steps_output(grid),
        "swap_quarter_turns": swapped_quarter_turns_output(grid),
        "swap_reflections": swapped_reflections_output(grid),
    }
