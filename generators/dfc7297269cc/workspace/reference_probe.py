"""Independent oracle and repeatable probes for dfc7297269cc.

This module is test tooling, not label authority.  The Python rules below are
written independently of production helpers.  ``racket_outputs`` explicitly
executes the selected canonical Racket program when requested.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys

TASK_ID = "dfc7297269cc"

try:
    from reviewer_support import canonical_pairs as _canonical_pairs, find_root
except ModuleNotFoundError:
    _SOURCE_ROOT = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(_SOURCE_ROOT / "shared/runtime"))
    from reviewer_support import canonical_pairs as _canonical_pairs, find_root

ROOT = find_root(__file__)


def load_generator(path: str | os.PathLike | None = None):
    path = Path(
        path
        or os.environ.get("GENERATOR_UNDER_TEST")
        or ROOT / f"generators/{TASK_ID}/generator.py"
    ).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_dfc7297269cc", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def intended_output(grid):
    """Fill only horizontal nonzero/zero/same-nonzero triples, simultaneously."""
    out = deepcopy(grid)
    height = len(grid)
    width = len(grid[0])
    for row in range(height):
        for col in range(1, width - 1):
            color = grid[row][col - 1]
            if color != 0 and grid[row][col] == 0 and grid[row][col + 1] == color:
                out[row][col] = color
    return out


def span_fill_rival(grid):
    """Rival: fill every zero in the horizontal span of a repeated color."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        colors = sorted({value for value in row if value != 0})
        for color in colors:
            positions = [col for col, value in enumerate(row) if value == color]
            if len(positions) < 2:
                continue
            for col in range(positions[0], positions[-1] + 1):
                if grid[row_index][col] == 0:
                    out[row_index][col] = color
    return out


def any_endpoints_rival(grid):
    """Rival: fill a horizontal zero between any two nonzero endpoints."""
    out = deepcopy(grid)
    height = len(grid)
    width = len(grid[0])
    for row in range(height):
        for col in range(1, width - 1):
            if grid[row][col] == 0 and grid[row][col - 1] != 0 and grid[row][col + 1] != 0:
                out[row][col] = grid[row][col - 1]
    return out


def both_orientations_rival(grid):
    """Rival: apply the selected local predicate horizontally and vertically."""
    out = intended_output(grid)
    height = len(grid)
    width = len(grid[0])
    for row in range(1, height - 1):
        for col in range(width):
            color = grid[row - 1][col]
            if color != 0 and grid[row][col] == 0 and grid[row + 1][col] == color:
                out[row][col] = color
    return out


RIVALS = {
    "span_fill": span_fill_rival,
    "any_nonzero_endpoints": any_endpoints_rival,
    "horizontal_or_vertical": both_orientations_rival,
}


def active_motifs(grid):
    hits = []
    for row_index, row in enumerate(grid):
        for col in range(1, len(row) - 1):
            color = row[col - 1]
            if color != 0 and row[col] == 0 and row[col + 1] == color:
                hits.append((row_index, col, color))
    return hits


def observed(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "motifs": len(active_motifs(grid)),
        "n_colors": len({value for row in grid for value in row if value != 0}),
    }


def changed_cells(before, after):
    return [
        (row, col)
        for row in range(len(before))
        for col in range(len(before[0]))
        if before[row][col] != after[row][col]
    ]


def explicit_counterexamples():
    """Compact lawful scenes isolating each canonical-fitting shortcut."""
    span = [[0] * 7 for _ in range(5)]
    span[0][0] = span[0][2] = 1          # one positive anchor
    span[2][0] = span[2][3] = 2          # two-zero same-color gap

    unequal = [[0] * 7 for _ in range(5)]
    unequal[0][0] = unequal[0][2] = 1    # one positive anchor
    unequal[2][0], unequal[2][2] = 2, 3  # unequal one-zero gap

    vertical = [[0] * 7 for _ in range(5)]
    vertical[0][0] = vertical[0][2] = 1  # one positive anchor
    vertical[2][6] = vertical[4][6] = 2  # vertical sandwich
    return {
        "span_fill": span,
        "any_nonzero_endpoints": unequal,
        "horizontal_or_vertical": vertical,
    }


def racket_outputs(grids):
    """Run the selected canonical Racket rule; never substitute the Python oracle."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    source_root = ROOT
    sys.path.insert(0, str(source_root / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    canonical_file = source_root / "shared/data/canonical/puzzles.jsonl"
    program = None
    for line in canonical_file.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID and row.get("program_solution"):
            program = row["program_solution"]
            break
    if program is None:
        raise FileNotFoundError(f"no canonical Racket program for {TASK_ID}")

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(source_root), stage, TASK_ID)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8"
        )
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
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket parity worker failed: {result['stderr']} {result['stdout']}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket parity worker returned an incomplete batch")
        return outputs
