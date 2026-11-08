"""Independent oracle and audit helpers for ARC task 00a3a71adae9.

This module deliberately does not import helpers from the production generator.
The Python oracle is supplementary test evidence; ``racket_outputs`` executes the
selected canonical Racket authority and never silently falls back to Python.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

TASK = "00a3a71adae9"
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load_generator(path: str | Path | None = None):
    source = Path(path or ROOT / "generators" / TASK / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_00a3a71adae9", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_record() -> dict:
    with (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise KeyError(f"canonical task {TASK} is absent")


def canonical_pairs() -> list[dict]:
    from reviewer_support import canonical_pairs as load_pairs
    return load_pairs(TASK, root=ROOT)


def components(grid: list[list[int]]) -> list[tuple[tuple[int, int], ...]]:
    """Return color-2 four-connected components in canonical top-left order."""
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2}
    found: list[tuple[tuple[int, int], ...]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                q = (r + dr, c + dc)
                if q in unseen:
                    unseen.remove(q)
                    stack.append(q)
        found.append(tuple(sorted(cells)))
    return sorted(found, key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells)))


def grown(cells: tuple[tuple[int, int], ...], h: int, w: int) -> set[tuple[int, int]]:
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if 0 <= r + dr < h and 0 <= c + dc < w
    }


def object_stats(grid: list[list[int]]) -> list[dict]:
    h, w = len(grid), len(grid[0])
    mask = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1}
    if not mask:
        raise ValueError("mask is empty")
    stats = []
    for index, cells in enumerate(components(grid)):
        halo = grown(cells, h, w)
        distance = min(abs(r - mr) + abs(c - mc) for r, c in halo for mr, mc in mask)
        stats.append({
            "index": index,
            "cells": cells,
            "grown": halo,
            "score": len(halo & mask),
            "distance": distance,
            "top_left": (min(r for r, _ in cells), min(c for _, c in cells)),
        })
    if not stats:
        raise ValueError("no color-2 objects")
    return stats


def selected_stats(grid: list[list[int]], mode: str = "authority") -> dict:
    rows = object_stats(grid)
    if mode == "authority":
        key = lambda row: (-row["score"], row["distance"], row["index"])
    elif mode == "distance_only":
        key = lambda row: (row["distance"], row["index"])
    elif mode == "overlap_then_scan":
        key = lambda row: (-row["score"], row["index"])
    elif mode == "reverse_scan_tie":
        key = lambda row: (-row["score"], row["distance"], -row["index"])
    else:
        raise ValueError(f"unknown mode {mode!r}")
    return min(rows, key=key)


def crop(cells: tuple[tuple[int, int], ...]) -> list[list[int]]:
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    occupied = set(cells)
    return [[8 if (r, c) in occupied else 0 for c in range(c0, c1 + 1)] for r in range(r0, r1 + 1)]


def reference_output(grid: list[list[int]], mode: str = "authority") -> list[list[int]]:
    original = deepcopy(grid)
    result = crop(selected_stats(grid, mode)["cells"])
    if grid != original:
        raise AssertionError("oracle mutated its input")
    return result


def semantic_profile(grid: list[list[int]]) -> str:
    rows = object_stats(grid)
    best_score = max(row["score"] for row in rows)
    score_tied = [row for row in rows if row["score"] == best_score]
    if len(score_tied) == 1:
        return "overlap_priority"
    best_distance = min(row["distance"] for row in score_tied)
    distance_tied = [row for row in score_tied if row["distance"] == best_distance]
    return "distance_priority" if len(distance_tied) == 1 else "scan_tiebreak"


def observed(grid: list[list[int]]) -> dict[str, int | str]:
    chosen = selected_stats(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n": len(components(grid)),
        "motif_size": len(chosen["cells"]),
        "mask_cells": sum(value == 1 for row in grid for value in row),
        "texture": semantic_profile(grid),
    }


def rival_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {
        name: reference_output(grid, name)
        for name in ("distance_only", "overlap_then_scan", "reverse_scan_tie")
    }


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Execute the selected canonical Racket program for every grid."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {"program": canonical_record()["program_solution"], "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request), encoding="utf-8")
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
        if result["timed_out"] or result["exit_code"]:
            raise RuntimeError(f"Racket parity worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket parity worker returned an incomplete batch")
        return outputs
