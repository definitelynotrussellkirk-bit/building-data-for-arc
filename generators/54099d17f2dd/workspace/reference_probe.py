"""Independent authority probe for ARC task 54099d17f2dd.

The Python oracle intentionally does not import production generator helpers.
``racket_outputs`` executes the selected canonical Racket program and never
silently falls back to Python, making this useful for future generator reviews.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "54099d17f2dd"
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def canonical_record() -> dict[str, Any]:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(f"canonical task {TASK_ID} is absent")


def canonical_pairs() -> list[dict[str, list[list[int]]]]:
    from reviewer_support import canonical_pairs as load_pairs

    return load_pairs(TASK_ID, root=ROOT)


def _rectangular_shape(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty list")
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid rows must be non-empty lists")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int for row in grid for value in row):
        raise ValueError("grid cells must be integers")
    return len(grid), width


def extracted_rule_state(grid: list[list[int]]) -> dict[str, Any]:
    """Extract only the state the selected authority consumes."""
    h, w = _rectangular_shape(grid)
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    template = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(markers) != 1:
        raise ValueError(f"expected exactly one color-1 marker, found {len(markers)}")
    if not template:
        raise ValueError("expected at least one color-2 template cell")
    r0 = min(r for r, _ in template)
    c0 = min(c for _, c in template)
    offsets = tuple(sorted((r - r0, c - c0) for r, c in template))
    return {
        "height": h,
        "width": w,
        "marker": markers[0],
        "source_top_left": (r0, c0),
        "offsets": offsets,
    }


def reference_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python transcription of the selected Racket authority."""
    state = extracted_rule_state(grid)
    output = [[0] * state["width"] for _ in range(state["height"])]
    mr, mc = state["marker"]
    for dr, dc in state["offsets"]:
        r, c = mr + dr, mc + dc
        if not (0 <= r < state["height"] and 0 <= c < state["width"]):
            raise ValueError("marker-anchored template leaves the grid")
        output[r][c] = 8
    return output


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Execute the selected canonical Racket program for every supplied grid."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    src = ROOT / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        request = {
            "program": canonical_record()["program_solution"],
            "grids": grids,
        }
        (stage / "parity-request.json").write_text(
            json.dumps(request), encoding="utf-8"
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
        if result["timed_out"] or result["exit_code"]:
            raise RuntimeError(
                "Racket parity worker failed: "
                f"stderr={result['stderr']!r} stdout={result['stdout']!r}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket parity worker returned an incomplete batch")
        return outputs
