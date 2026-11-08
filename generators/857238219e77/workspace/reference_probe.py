"""Independent oracle and reusable audit tooling for task 857238219e77.

This module is test/review support, not label authority.  The optional Racket
path executes the selected canonical program and fails closed when unavailable.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Iterable

TASK = "857238219e77"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: str | os.PathLike | None = None):
    source = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_857238219e77", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_record() -> dict:
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise LookupError(f"canonical task {TASK} not found")


def canonical_pairs() -> list[dict]:
    row = canonical_record()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(test)


def vertical_runs(grid: list[list[int]]) -> list[dict]:
    """Parse the exact columnwise monochrome runs seen by the Racket rule."""
    h, w = len(grid), len(grid[0])
    runs: list[dict] = []
    for c in range(w):
        r = 0
        while r < h:
            color = grid[r][c]
            if color == 0:
                r += 1
                continue
            end = r + 1
            while end < h and grid[end][c] == color:
                end += 1
            runs.append({"color": color, "r0": r, "r1": end - 1,
                         "c": c, "length": end - r})
            r = end
    return runs


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent direct transcription of the documented object operation."""
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for run in vertical_runs(grid):
        if run["length"] == 3 and 0 < run["c"] < w - 1:
            r = run["r0"] + 1
            for c in range(run["c"] - 1, run["c"] + 2):
                out[r][c] = run["color"]
    return out


def observed(grid: list[list[int]]) -> dict:
    runs = vertical_runs(grid)
    w = len(grid[0])
    edge = [run for run in runs if run["length"] == 3 and run["c"] in (0, w - 1)]
    edge_side = None
    if len(edge) == 1:
        edge_side = "left" if edge[0]["c"] == 0 else "right"
    return {
        "grid_h": len(grid),
        "grid_w": w,
        "target_count": sum(run["length"] == 3 and 0 < run["c"] < w - 1 for run in runs),
        "n_distinct_colors": len({v for row in grid for v in row if v}),
        "edge_side": edge_side,
        "short_count": sum(run["length"] == 2 and 0 < run["c"] < w - 1 for run in runs),
        "long_count": sum(run["length"] == 4 and 0 < run["c"] < w - 1 for run in runs),
        "edge_count": len(edge),
        "run_count": len(runs),
    }


def racket_outputs(grids: Iterable[list[list[int]]]) -> list[list[list[int]]]:
    grids = list(grids)
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {"program": canonical_record()["program_solution"], "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request))
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("parity-request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge, name, grid) for grid in request["grids"]]))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket parity worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket parity worker returned an incomplete batch")
        return outputs
