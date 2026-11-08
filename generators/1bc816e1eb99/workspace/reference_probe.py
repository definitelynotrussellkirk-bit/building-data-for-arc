"""Independent geometry/oracle helpers for generator 1bc816e1eb99.

This file intentionally does not import implementation helpers from generator.py.
It can be used by task-local tests and by the source-bound curriculum probe.
"""
from __future__ import annotations

from collections import deque
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

TASK_ID = "1bc816e1eb99"
HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

DIR4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def load_generator(path: str | Path | None = None):
    candidate = Path(path) if path else HOME / "generator.py"
    candidate = candidate.resolve()
    spec = importlib.util.spec_from_file_location(
        f"candidate_{TASK_ID}_{abs(hash(str(candidate)))}", candidate
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {candidate}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_record() -> dict:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def canonical_pairs() -> list[dict]:
    record = canonical_record()
    pairs: list[dict] = []
    for split in ("train", "test"):
        value = record[split]
        rows = value if isinstance(value, list) else [value]
        pairs.extend(pair for pair in rows if isinstance(pair, dict) and "output" in pair)
    return pairs


def _validate_grid(grid) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty sequence")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be non-empty sequences")
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise ValueError("grid must be rectangular")
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                raise ValueError("cells must be literal ARC integers 0..9")
    return len(grid), width


def components(grid, color: int = 4) -> list[set[tuple[int, int]]]:
    h, w = _validate_grid(grid)
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        comp = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in DIR4:
                p = (r + dr, c + dc)
                if p in unseen:
                    unseen.remove(p)
                    comp.add(p)
                    stack.append(p)
        result.append(comp)
    return result


def hole_count(cells: Iterable[tuple[int, int]]) -> int:
    cells = set(cells)
    if not cells:
        return 0
    min_r = min(r for r, _ in cells)
    max_r = max(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    max_c = max(c for _, c in cells)
    local = {(r - min_r, c - min_c) for r, c in cells}
    height, width = max_r - min_r + 1, max_c - min_c + 1
    empty = {(r, c) for r in range(height) for c in range(width) if (r, c) not in local}
    outside: set[tuple[int, int]] = set()
    queue = deque(
        p for p in empty if p[0] in (0, height - 1) or p[1] in (0, width - 1)
    )
    outside.update(queue)
    while queue:
        r, c = queue.popleft()
        for dr, dc in DIR4:
            p = (r + dr, c + dc)
            if p in empty and p not in outside:
                outside.add(p)
                queue.append(p)
    enclosed = empty - outside
    holes = 0
    while enclosed:
        holes += 1
        start = enclosed.pop()
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in DIR4:
                p = (r + dr, c + dc)
                if p in enclosed:
                    enclosed.remove(p)
                    queue.append(p)
    return holes


def component_stats(grid) -> list[dict]:
    stats = []
    for cells in components(grid):
        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)
        height, width = max_r - min_r + 1, max_c - min_c + 1
        area = len(cells)
        stats.append(
            {
                "cells": cells,
                "bbox": (min_r, max_r, min_c, max_c),
                "height": height,
                "width": width,
                "bbox_area": height * width,
                "area": area,
                "holes": hole_count(cells),
                "fills_bbox": area == height * width,
                "touches_edge": min_r == 0 or min_c == 0 or max_r == len(grid) - 1 or max_c == len(grid[0]) - 1,
            }
        )
    return stats


def intended_output(grid) -> list[list[int]]:
    _validate_grid(grid)
    out = [list(row) for row in grid]
    for stat in component_stats(grid):
        color = 8 if stat["holes"] == 1 else 2
        for r, c in stat["cells"]:
            out[r][c] = color
    return out


def _recolor_by(grid, choose_cyan) -> list[list[int]]:
    out = [list(row) for row in grid]
    for stat in component_stats(grid):
        color = 8 if choose_cyan(stat) else 2
        for r, c in stat["cells"]:
            out[r][c] = color
    return out


def rival_large_bbox(grid) -> list[list[int]]:
    """Wrong canonical-fitting shortcut: tall objects are called hollow."""
    return _recolor_by(grid, lambda stat: stat["height"] >= 4)


def rival_bbox_not_full(grid) -> list[list[int]]:
    """Wrong canonical-fitting shortcut: every non-rectangle is called hollow."""
    return _recolor_by(grid, lambda stat: not stat["fills_bbox"])


def rival_area_threshold(grid) -> list[list[int]]:
    """Wrong proxy: large pixel count, rather than topology, selects cyan."""
    return _recolor_by(grid, lambda stat: stat["area"] >= 10)


def observed(grid) -> dict[str, int]:
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_components": len(components(grid))}


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Apply the selected canonical Racket program in a relocated runtime."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_record()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(REPO), stage, TASK_ID)
        request = stage / "parity-request.json"
        request.write_text(json.dumps({"program": program, "grids": grids}))
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("parity-request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    outputs = [runner._apply_rule(bridge, name, grid) for grid in request["grids"]]
    print(json.dumps(outputs))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=240)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs
