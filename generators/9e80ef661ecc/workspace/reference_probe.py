"""Independent probes for the 9e80ef661ecc hole-count recoloring task.

The production generator remains responsible for sampling.  This module gives
reviewers and task-local tests a deliberately separate component extractor,
hole counter, semantic oracle, rival rules, and optional real-Racket parity
runner.  It is evidence tooling, not a replacement label authority.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Iterable, Sequence

TASK = "9e80ef661ecc"
HERE = Path(__file__).resolve()


def _find_repo_root() -> Path:
    for parent in HERE.parents:
        if (parent / "shared" / "data" / "canonical" / "puzzles.jsonl").is_file():
            return parent
    configured = os.environ.get("ARCPUZZLES_REPO_ROOT")
    if configured:
        root = Path(configured).resolve()
        if (root / "shared" / "data" / "canonical" / "puzzles.jsonl").is_file():
            return root
    raise RuntimeError("could not locate repository root")


ROOT = _find_repo_root()
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

Grid = list[list[int]]
Cell = tuple[int, int]


def load_generator(path: str | Path | None = None):
    candidate = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_9e80ef661ecc", candidate)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {candidate}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical() -> dict:
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs() -> list[dict]:
    row = canonical()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(test)


def _validate_grid(grid: Sequence[Sequence[int]]) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be nonempty")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("rows must be nonempty")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be ARC integers 0..9")
    return len(grid), width


def components(grid: Sequence[Sequence[int]], *, merge_colors: bool = False) -> list[dict]:
    """Extract orthogonally connected foreground objects.

    With ``merge_colors=False`` (the intended object relation), an edge joins
    equal-colored cells only.  ``merge_colors=True`` supplies a plausible rival
    that merges touching foreground colors.
    """
    h, w = _validate_grid(grid)
    seen: set[Cell] = set()
    result: list[dict] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = int(grid[r][c])
            todo = [(r, c)]
            seen.add((r, c))
            cells: set[Cell] = set()
            while todo:
                rr, cc = todo.pop()
                cells.add((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in seen:
                        continue
                    value = int(grid[nr][nc])
                    if value == 0:
                        continue
                    if not merge_colors and value != color:
                        continue
                    seen.add((nr, nc))
                    todo.append((nr, nc))
            rows = [p[0] for p in cells]
            cols = [p[1] for p in cells]
            bbox = (min(rows), min(cols), max(rows), max(cols))
            result.append({"color": color, "cells": cells, "bbox": bbox})
    return result


def hole_regions(component: dict) -> list[set[Cell]]:
    """Complement regions enclosed by the object's own cells in its bbox."""
    cells = set(component["cells"])
    r0, c0, r1, c1 = component["bbox"]
    background = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1) if (r, c) not in cells}
    outside: set[Cell] = set()
    todo = deque(
        p for p in background
        if p[0] in (r0, r1) or p[1] in (c0, c1)
    )
    outside.update(todo)
    while todo:
        r, c = todo.popleft()
        for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if q in background and q not in outside:
                outside.add(q)
                todo.append(q)
    pending = background - outside
    holes: list[set[Cell]] = []
    while pending:
        start = next(iter(pending))
        region = {start}
        queue = [start]
        pending.remove(start)
        while queue:
            r, c = queue.pop()
            for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if q in pending:
                    pending.remove(q)
                    region.add(q)
                    queue.append(q)
        holes.append(region)
    return holes


def hole_count(component: dict) -> int:
    return len(hole_regions(component))


def output_color(n_holes: int) -> int:
    return {0: 2, 1: 3, 2: 4, 3: 6}.get(int(n_holes), 9)


def intended_output(grid: Sequence[Sequence[int]]) -> Grid:
    out = [list(row) for row in grid]
    for obj in components(grid):
        color = output_color(hole_count(obj))
        for r, c in obj["cells"]:
            out[r][c] = color
    return out


def object_stats(grid: Sequence[Sequence[int]]) -> list[dict]:
    stats = []
    for obj in components(grid):
        r0, c0, r1, c1 = obj["bbox"]
        regions = hole_regions(obj)
        stats.append({
            "color": obj["color"],
            "area": len(obj["cells"]),
            "bbox": (r1 - r0 + 1, c1 - c0 + 1),
            "holes": len(regions),
            "enclosed_cells": sum(map(len, regions)),
            "cells": set(obj["cells"]),
        })
    return stats


def foreground_area_lookup_rival(grid: Sequence[Sequence[int]]) -> Grid:
    """Strong canonical shortcut: infer output solely from foreground area."""
    out = [list(row) for row in grid]
    lookup = {4: 2, 9: 2, 8: 3, 12: 3, 13: 4}
    for obj in components(grid):
        color = lookup.get(len(obj["cells"]), int(obj["color"]))
        for r, c in obj["cells"]:
            out[r][c] = color
    return out


def enclosed_cell_lookup_rival(grid: Sequence[Sequence[int]]) -> Grid:
    """Canonical-fitting proxy that counts enclosed cells, not regions."""
    out = [list(row) for row in grid]
    lookup = {0: 2, 1: 3, 4: 3, 2: 4}
    for obj in components(grid):
        enclosed = sum(map(len, hole_regions(obj)))
        color = lookup.get(enclosed, 9)
        for r, c in obj["cells"]:
            out[r][c] = color
    return out


def canonical_range_only_rival(grid: Sequence[Sequence[int]]) -> Grid:
    """Fits 0/1/2-hole canonicals but incorrectly maps every larger count to 4."""
    out = [list(row) for row in grid]
    for obj in components(grid):
        holes = hole_count(obj)
        color = {0: 2, 1: 3}.get(holes, 4)
        for r, c in obj["cells"]:
            out[r][c] = color
    return out


def merged_foreground_rival(grid: Sequence[Sequence[int]]) -> Grid:
    """Incorrectly treats touching different colors as one object."""
    out = [list(row) for row in grid]
    for obj in components(grid, merge_colors=True):
        color = output_color(hole_count(obj))
        for r, c in obj["cells"]:
            out[r][c] = color
    return out


def same_color_global_rival(grid: Sequence[Sequence[int]]) -> Grid:
    """Incorrectly pools all disconnected cells of a color before counting holes."""
    _validate_grid(grid)
    out = [list(row) for row in grid]
    colors = sorted({v for row in grid for v in row if v})
    for color in colors:
        cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        obj = {"color": color, "cells": cells, "bbox": (min(rows), min(cols), max(rows), max(cols))}
        mapped = output_color(hole_count(obj))
        for r, c in cells:
            out[r][c] = mapped
    return out


def cross_color_adjacencies(grid: Sequence[Sequence[int]]) -> list[tuple[Cell, Cell]]:
    h, w = _validate_grid(grid)
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0:
                continue
            for nr, nc in ((r + 1, c), (r, c + 1)):
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] not in (0, grid[r][c]):
                    result.append(((r, c), (nr, nc)))
    return result


def racket_outputs(grids: Iterable[Sequence[Sequence[int]]]) -> list[Grid]:
    """Require the real canonical Racket program and apply it to every grid."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    src = ROOT / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    values = [[list(row) for row in grid] for grid in grids]
    program = canonical()["program_solution"]
    with tempfile.TemporaryDirectory(prefix="9e80ef661ecc-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(json.dumps({"program": program, "grids": values}))
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path("parity-request.json").read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request["grids"]]))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=240)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket parity worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(values):
            raise RuntimeError("Racket parity worker returned an incomplete batch")
        return outputs
