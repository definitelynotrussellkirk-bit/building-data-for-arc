"""Independent oracle and reusable probes for task 7de2798953a7.

This module is reviewer/test tooling. The canonical Racket program remains the
label authority; ``intended_output`` is an independently written parity oracle.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

TASK = "7de2798953a7"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    source = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    from reviewer_support import canonical_pairs as read_pairs, find_root

    return read_pairs(TASK, root=find_root(__file__))


def canonical_record():
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK:
                return record
    raise KeyError(TASK)


def pair_rows(grid):
    """Return (row, color, left, right) for exactly-two same-colour gaps."""
    result = []
    for r, row in enumerate(grid):
        for color in sorted(set(row) - {0}):
            positions = [c for c, value in enumerate(row) if value == color]
            if (
                len(positions) == 2
                and positions[1] - positions[0] >= 3
                and all(value == 0 for value in row[positions[0] + 1 : positions[1]])
            ):
                result.append((r, color, positions[0], positions[1]))
    return result


def mismatched_rows(grid):
    result = []
    for r, row in enumerate(grid):
        occupied = [(c, value) for c, value in enumerate(row) if value != 0]
        if len(occupied) == 2 and occupied[0][1] != occupied[1][1]:
            result.append((r, occupied[0], occupied[1]))
    return result


def intended_output(grid):
    out = deepcopy(grid)
    for r, color, left, right in pair_rows(grid):
        for step, c in enumerate(range(left + 1, right), start=1):
            if step % 2 == 1:
                out[r][c] = color
    return out


def solid_fill_rival(grid):
    out = deepcopy(grid)
    for r, color, left, right in pair_rows(grid):
        for c in range(left + 1, right):
            out[r][c] = color
    return out


def right_phase_rival(grid):
    out = deepcopy(grid)
    for r, color, left, right in pair_rows(grid):
        for step, c in enumerate(range(right - 1, left, -1), start=1):
            if step % 2 == 1:
                out[r][c] = color
    return out


def any_two_nonzero_rival(grid):
    """Canonical-fitting shortcut: ignore the same-colour precondition."""
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        occupied = [(c, value) for c, value in enumerate(row) if value != 0]
        if len(occupied) != 2:
            continue
        (left, color), (right, _) = occupied
        if right - left < 3 or not all(v == 0 for v in row[left + 1 : right]):
            continue
        for step, c in enumerate(range(left + 1, right), start=1):
            if step % 2 == 1:
                out[r][c] = color
    return out


def observed(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": len(pair_rows(grid)),
    }


def shortcut_witness():
    """A lawful task input where equal-endpoint and any-two rules disagree."""
    return [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 0, 0, 0, 5, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 4, 0, 0, 0, 4, 0],
    ]


def racket_outputs(grids):
    """Execute the real canonical rule in a relocated runtime; never fallback."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_record()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8"
        )
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path('parity-request.json').read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge, name, g) for g in request['grids']]))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        return json.loads(result["stdout"])
