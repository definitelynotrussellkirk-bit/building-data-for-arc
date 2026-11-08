"""Independent oracle and analysis helpers for task 65a142eb4d9b.

This module is reviewer tooling, not output authority.  The canonical Racket
program remains authoritative; ``racket_outputs`` executes it when requested.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

TASK = "65a142eb4d9b"
ROOT = Path(__file__).resolve().parents[3]
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_record():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs():
    row = canonical_record()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def _neighbors(r, c, h, w, *, diagonal=False):
    deltas = CARDINAL
    if diagonal:
        deltas = tuple(
            (dr, dc)
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if (dr, dc) != (0, 0)
        )
    return [
        (r + dr, c + dc)
        for dr, dc in deltas
        if 0 <= r + dr < h and 0 <= c + dc < w
    ]


def expandable_cells(grid):
    h, w = len(grid), len(grid[0])
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
        and all(grid[nr][nc] != value for nr, nc in _neighbors(r, c, h, w))
    ]


def same_color_components(grid, *, diagonal=False):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        color = grid[start[0]][start[1]]
        queue = deque([start])
        component = {start}
        while queue:
            r, c = queue.popleft()
            for point in _neighbors(r, c, h, w, diagonal=diagonal):
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    queue.append(point)
                    component.add(point)
        components.append((color, component))
    return components


def blocked_domino_count(grid):
    return sum(len(component) == 2 for _, component in same_color_components(grid))


def analysis(grid):
    h, w = len(grid), len(grid[0])
    expandable = expandable_cells(grid)
    by_color = Counter(value for row in grid for value in row if value != 0)
    diagonal_pairs = set()
    points = {(r, c): value for r, c, value in expandable}
    for (r, c), value in points.items():
        for dr, dc in ((1, 1), (1, -1)):
            other = (r + dr, c + dc)
            if points.get(other) == value:
                diagonal_pairs.add(tuple(sorted(((r, c), other))))
    return {
        "grid_h": h,
        "grid_w": w,
        "n_expandable_cells": len(expandable),
        "n_blocked_dominoes": blocked_domino_count(grid),
        "edge_expandable": sum(r in (0, h - 1) or c in (0, w - 1) for r, c, _ in expandable),
        "diagonal_expandable_pairs": len(diagonal_pairs),
        "expandable_with_repeated_color": sum(by_color[value] > 1 for _, _, value in expandable),
    }


def _paint_plus(output, r, c, color):
    h, w = len(output), len(output[0])
    output[r][c] = color
    for nr, nc in _neighbors(r, c, h, w):
        output[nr][nc] = color


def rule_output(grid):
    """Independent literal reading of the canonical local rule."""
    output = deepcopy(grid)
    for r, c, color in expandable_cells(grid):
        _paint_plus(output, r, c, color)
    return output


def expand_all_nonzero(grid):
    output = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                _paint_plus(output, r, c, color)
    return output


def globally_unique_colors(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    output = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0 and counts[color] == 1:
                _paint_plus(output, r, c, color)
    return output


def eight_connected_singletons(grid):
    singles = {
        next(iter(component))
        for _, component in same_color_components(grid, diagonal=True)
        if len(component) == 1
    }
    output = deepcopy(grid)
    for r, c in sorted(singles):
        _paint_plus(output, r, c, grid[r][c])
    return output


def interior_only(grid):
    h, w = len(grid), len(grid[0])
    output = deepcopy(grid)
    for r, c, color in expandable_cells(grid):
        if 0 < r < h - 1 and 0 < c < w - 1:
            _paint_plus(output, r, c, color)
    return output


RIVALS = {
    "expand_all_nonzero": expand_all_nonzero,
    "globally_unique_colors": globally_unique_colors,
    "eight_connected_singletons": eight_connected_singletons,
    "interior_only": interior_only,
}


def racket_outputs(grids):
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_record()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids})
        )
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket worker failed: {result['stderr']} {result['stdout']}"
            )
        return json.loads(result["stdout"])
