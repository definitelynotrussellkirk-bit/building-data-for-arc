"""Independent oracle and probes for ARC task 9fbd0923e6ae.

This module is test tooling.  It derives outputs from the public task contract
without importing production helpers.  The Racket helper requires the real
canonical authority and never silently falls back to Python.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "9fbd0923e6ae"
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_record():
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def _normalise_grid(grid):
    """Expand canonical ledger row strings into ordinary integer grids."""
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in grid
    ]


def canonical_pairs():
    row = canonical_record()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [
        {
            "input": _normalise_grid(pair["input"]),
            "output": _normalise_grid(pair["output"]),
        }
        for pair in [*row["train"], *test]
    ]


def canonical_rule_hash():
    program = canonical_record()["program_solution"]
    return hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]


def guide(grid):
    h, w = len(grid), len(grid[0])
    columns = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    rows = [r for r in range(h) if all(grid[r][c] == 5 for c in range(w))]
    if columns:
        return "vertical", columns[0]
    if rows:
        return "horizontal", rows[0]
    raise ValueError("grid has no full color-5 guide")


def mirror_point(point, orientation, axis):
    r, c = point
    if orientation == "vertical":
        return r, 2 * axis - c
    return 2 * axis - r, c


def intended_output(grid):
    target = grid[0][0]
    orientation, axis = guide(grid)
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != target or (r, c) == (0, 0):
                continue
            rr, cc = mirror_point((r, c), orientation, axis)
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = target
    return out


def selector_side_only(grid):
    """Wrong rival: reflect target cells only from the selector's side."""
    target = grid[0][0]
    orientation, axis = guide(grid)
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != target or (r, c) == (0, 0):
                continue
            coordinate = c if orientation == "vertical" else r
            if coordinate >= axis:
                continue
            rr, cc = mirror_point((r, c), orientation, axis)
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = target
    return out


def mirror_selector_too(grid):
    """Wrong rival: identical to the authority except it mirrors (0,0)."""
    target = grid[0][0]
    orientation, axis = guide(grid)
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != target:
                continue
            rr, cc = mirror_point((r, c), orientation, axis)
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = target
    return out


def position_name(length, axis):
    mapping = {
        "start": length // 3,
        "middle": length // 2,
        "end": (2 * length) // 3,
    }
    for name, value in mapping.items():
        if value == axis:
            return name
    return "custom"


def observed(grid):
    orientation, axis = guide(grid)
    target = grid[0][0]
    target_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == target and (r, c) != (0, 0)
    ]
    before = sum((c if orientation == "vertical" else r) < axis for r, c in target_cells)
    after = len(target_cells) - before
    layout = "both_sides" if before and after else (
        "selector_side" if before else "opposite_side"
    )
    distractor_values = [
        value
        for row in grid
        for value in row
        if value not in (0, 5, target)
    ]
    axis_length = len(grid[0]) if orientation == "horizontal" else len(grid)
    guide_noise = sum(value == 5 for row in grid for value in row) - axis_length
    line_length = len(grid[0]) if orientation == "vertical" else len(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "guide_orientation": orientation,
        "guide_position": position_name(line_length, axis),
        "n_targets": len(target_cells),
        "target_layout": layout,
        "n_distractors": len(distractor_values),
        "n_distractor_colors": len(set(distractor_values)),
        "n_guide_noise": guide_noise,
    }


def palette_size(grid):
    return len({value for row in grid for value in row})


def has_opposite_counterexample(grid):
    return intended_output(grid) != selector_side_only(grid)


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
