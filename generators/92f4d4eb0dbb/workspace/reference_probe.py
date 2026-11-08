"""Independent oracle and rival probes for ARC task 92f4d4eb0dbb.

The helpers here intentionally do not import semantic helpers from generator.py.
The selected Racket rule remains the label authority; the Python mirror is only
supplementary regression and curriculum evidence.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "92f4d4eb0dbb"
sys.path.insert(0, str(ROOT / "shared/runtime"))
sys.path.insert(0, str(ROOT / "src"))


def load_generator(path=None):
    source = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_92f4", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row():
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise FileNotFoundError(f"canonical row {TASK} not found")


def canonical_pairs():
    row = canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def canonical_rule_hash():
    source = canonical_row()["program_solution"]
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def one_rows(grid):
    return [r for r, row in enumerate(grid) for value in row if value == 1]


def intended_output(grid):
    """Strict rule: recolor only color-1 cells strictly below bbox midpoint."""
    rows = one_rows(grid)
    if not rows:
        return deepcopy(grid)
    threshold_twice = min(rows) + max(rows)
    return [
        [2 if value == 1 and 2 * r > threshold_twice else value
         for value in row]
        for r, row in enumerate(grid)
    ]


def inclusive_midpoint(grid):
    """Plausible wrong rule: recolor the integer midpoint row as lower half."""
    rows = one_rows(grid)
    if not rows:
        return deepcopy(grid)
    threshold_twice = min(rows) + max(rows)
    return [
        [2 if value == 1 and 2 * r >= threshold_twice else value
         for value in row]
        for r, row in enumerate(grid)
    ]


def pixel_centroid(grid):
    """Plausible wrong rule: split at the mean row of occupied pixels."""
    rows = one_rows(grid)
    if not rows:
        return deepcopy(grid)
    row_sum = sum(rows)
    count = len(rows)
    return [
        [2 if value == 1 and count * r > row_sum else value
         for value in row]
        for r, row in enumerate(grid)
    ]


RIVALS = {
    "inclusive_midpoint": inclusive_midpoint,
    "pixel_centroid": pixel_centroid,
}


def observed(grid):
    ones = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value == 1]
    if not ones:
        return {"grid_h": len(grid), "grid_w": len(grid[0]), "span": 0,
                "shape_kind": None}
    r0 = min(r for r, _ in ones)
    r1 = max(r for r, _ in ones)
    c0 = min(c for _, c in ones)
    c1 = max(c for _, c in ones)
    normalized = {(r - r0, c - c0) for r, c in ones}
    span = r1 - r0 + 1
    # Reconstruct the public shape templates independently.
    templates = {
        "frame": {
            (r, c)
            for r in range(span)
            for c in range(5)
            if r in {0, span - 1} or c in {0, 4}
        },
        "notched_frame": {
            (r, c)
            for r in range(span)
            for c in range(5)
            if (r in {0, span - 1} or c in {0, 4})
            and (r, c) != (span - 1, 2)
        },
        "ladder": {
            (r, c)
            for r in range(span)
            for c in range(5)
            if r in {0, span - 1} or c in {0, 2, 4}
        },
        "diamond": set(),
        "zigzag": set(),
    }
    for r in range(span):
        distance = min(r, span - 1 - r)
        if distance == 0:
            cols = {2}
        elif distance == 1:
            cols = {1, 2, 3}
        else:
            cols = {0, 2, 4}
        templates["diamond"].update((r, c) for c in cols)
    positions = [0, 1, 2, 3, 2, 1]
    for r in range(span):
        p = positions[r % len(positions)]
        templates["zigzag"].update({(r, p), (r, p + 1)})
    kind = None
    for name, cells in templates.items():
        if normalized == cells or normalized == {
            (r, 4 - c) for r, c in cells
        }:
            kind = name
            break
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "span": span,
        "shape_kind": kind,
    }


def grid_sha256(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def racket_outputs(grids):
    """Require the real selected Racket rule; no Python fallback."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_row()["program_solution"]
    with tempfile.TemporaryDirectory(prefix="92f4d4eb0dbb-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids})
        )
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path("parity-request.json").read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request["grids"]]))
finally:
    bridge.shutdown()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket parity worker failed: {result}")
        return json.loads(result["stdout"])
