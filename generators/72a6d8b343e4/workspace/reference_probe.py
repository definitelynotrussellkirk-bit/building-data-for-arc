"""Independent review helpers for the Endpoint Bridge generator.

The Python oracle is supplementary: the selected Racket program remains label
authority.  ``racket_outputs`` deliberately fails when that authority cannot be
executed; it never substitutes this mirror silently.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys

TASK = "72a6d8b343e4"
TASK_ROOT = Path(__file__).resolve().parents[1]
ROOT = TASK_ROOT.parents[1]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or TASK_ROOT / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_endpoint_bridge_generator", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    from reviewer_support import canonical_pairs as read_pairs

    return read_pairs(TASK, root=ROOT)


def positions_by_color(grid) -> dict[int, list[tuple[int, int]]]:
    positions: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                positions[value].append((r, c))
    return dict(positions)


def _axis_path(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    (r1, c1), (r2, c2) = a, b
    if r1 == r2:
        lo, hi = sorted((c1, c2))
        return [(r1, c) for c in range(lo, hi + 1)]
    if c1 == c2:
        lo, hi = sorted((r1, r2))
        return [(r, c1) for r in range(lo, hi + 1)]
    return []


def reference_output(grid) -> list[list[int]]:
    """Independent literal rule: only exactly-two aligned colours bridge."""
    output = deepcopy(grid)
    for color, points in positions_by_color(grid).items():
        if len(points) != 2:
            continue
        for r, c in _axis_path(points[0], points[1]):
            output[r][c] = color
    return output


def observed(grid) -> dict[str, int]:
    counts = Counter(lines=0, adjacent=0, misaligned=0, triplets=0)
    orientations = Counter(horizontal=0, vertical=0)
    for points in positions_by_color(grid).values():
        if len(points) == 2:
            path = _axis_path(points[0], points[1])
            if not path:
                counts["misaligned"] += 1
            elif len(path) == 2:
                counts["adjacent"] += 1
                orientations["horizontal" if points[0][0] == points[1][0] else "vertical"] += 1
            else:
                counts["lines"] += 1
                orientations["horizontal" if points[0][0] == points[1][0] else "vertical"] += 1
        elif len(points) == 3:
            aligned = [
                _axis_path(points[i], points[j])
                for i in range(3)
                for j in range(i + 1, 3)
            ]
            aligned = [path for path in aligned if len(path) >= 3]
            if len(aligned) == 1:
                counts["triplets"] += 1
    palette = {value for row in grid for value in row}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_lines": counts["lines"],
        "n_adjacent": counts["adjacent"],
        "n_misaligned": counts["misaligned"],
        "n_triplets": counts["triplets"],
        "palette_size": len(palette),
        "horizontal": orientations["horizontal"],
        "vertical": orientations["vertical"],
    }


def profile(grid) -> tuple[int, int, int]:
    facts = observed(grid)
    return facts["grid_h"], facts["grid_w"], facts["palette_size"]


def misaligned_witness() -> list[list[int]]:
    grid = [[0] * 9 for _ in range(8)]
    grid[1][1] = grid[5][6] = 4
    grid[6][1] = grid[6][5] = 7
    return grid


def extra_occurrence_witness() -> list[list[int]]:
    grid = [[0] * 9 for _ in range(8)]
    grid[1][1] = grid[1][6] = grid[4][4] = 4
    grid[6][1] = grid[6][5] = 7
    return grid


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    row = next(
        json.loads(line)
        for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if line.strip() and json.loads(line).get("task_id") == TASK
    )
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": row["program_solution"], "grids": grids})
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
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs
