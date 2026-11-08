"""Independent semantic probes for task 5bb29951ab1a.

This file is reviewer tooling, not a label authority.  It deliberately derives
outputs from the published adjacency rule instead of importing generator helpers.
"""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import sys

TASK = "5bb29951ab1a"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: str | os.PathLike[str] | None = None):
    target = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", target)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {target}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    from reviewer_support import canonical_pairs as load_pairs, find_root

    return load_pairs(TASK, root=find_root(__file__))


def colors(grid):
    counts = Counter(value for row in grid for value in row)
    nonzero = [(count, color) for color, count in counts.items() if color != 0]
    if len(nonzero) != 2:
        raise ValueError(f"expected exactly two nonzero colors, found {sorted(counts)}")
    nonzero.sort(reverse=True)
    (rect_count, rect_color), (dot_count, dot_color) = nonzero
    if rect_count <= dot_count:
        raise ValueError("rectangle color must be strictly more frequent than dot color")
    return rect_color, dot_color


def dot_directions(grid, r, c, rect_color):
    h, w = len(grid), len(grid[0])
    directions = []
    for name, (dr, dc) in (("up", (-1, 0)), ("down", (1, 0)),
                           ("left", (0, -1)), ("right", (0, 1))):
        rr, cc = r + dr, c + dc
        if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == rect_color:
            directions.append(name)
    return tuple(directions)


def intended_output(grid):
    rect_color, dot_color = colors(grid)
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == dot_color:
                adjacent = len(dot_directions(grid, r, c, rect_color))
                out[r][c] = rect_color if adjacent >= 2 else 0
    return out


def corner_or_dense_output(grid):
    """Plausible shortcut: keep 3/4-neighbor holes and corner notches only.

    It agrees with every canonical pair, which contains no dot supported by
    exactly two opposite rectangle neighbors, but disagrees with the intended
    threshold rule on a straight bridge between two rectangles.
    """
    rect_color, dot_color = colors(grid)
    out = [list(row) for row in grid]
    opposite = {frozenset(("up", "down")), frozenset(("left", "right"))}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != dot_color:
                continue
            directions = dot_directions(grid, r, c, rect_color)
            keep = len(directions) >= 3 or (len(directions) == 2 and frozenset(directions) not in opposite)
            out[r][c] = rect_color if keep else 0
    return out


def observed(grid):
    rect_color, dot_color = colors(grid)
    absorb = reject = one = zero = opposite_two = 0
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != dot_color:
                continue
            directions = dot_directions(grid, r, c, rect_color)
            n = len(directions)
            absorb += n >= 2
            reject += n < 2
            one += n == 1
            zero += n == 0
            opposite_two += n == 2 and frozenset(directions) in {
                frozenset(("up", "down")), frozenset(("left", "right"))
            }
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_absorb": absorb,
        "n_reject": reject,
        "one_neighbor_rejects": one,
        "isolated_rejects": zero,
        "opposite_two_witnesses": opposite_two,
        "rect_color": rect_color,
        "dot_color": dot_color,
    }



def canonical_record():
    """Return the first selected canonical row, including its Racket source."""
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def shortcut_witness():
    """Small exact input separating the threshold rule from a corner-only rival.

    The dot at row 2, column 3 has exactly two opposite rectangle neighbors and
    must be absorbed.  Row 1, column 6 is a one-neighbor negative; row 4,
    column 7 is isolated.  Coordinates are zero-based.
    """
    return [
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 0, 2, 2, 1, 0, 0],
        [0, 2, 2, 1, 2, 2, 0, 0, 0],
        [0, 2, 2, 0, 2, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]


def racket_outputs(grids):
    """Execute the selected canonical Racket program on a batch of grids.

    This is intentionally fail-closed: an unavailable or failing Racket runtime
    raises rather than silently substituting the Python oracle.
    """
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
        request = stage / "parity-request.json"
        request.write_text(json.dumps({"program": program, "grids": grids}), encoding="utf-8")
        script = r"""
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path('parity-request.json').read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    outputs = [runner._apply_rule(bridge, name, grid) for grid in request['grids']]
    print(json.dumps(outputs))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket worker failed: stderr={result['stderr']!r} stdout={result['stdout']!r}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs
