"""Independent geometry oracle and repeatable probes for task 34abaec056ef.

This module is reviewer tooling, not label authority.  Its coordinate code is
kept separate from the production generator so a shared implementation bug does
not make the regression suite tautological.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

TASK = "34abaec056ef"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))

# Every ordered orthogonal pair of unit cardinal vectors.
BASES = (
    ((0, 1), (1, 0)),
    ((1, 0), (0, -1)),
    ((0, -1), (-1, 0)),
    ((-1, 0), (0, 1)),
    ((0, -1), (1, 0)),
    ((-1, 0), (0, -1)),
    ((0, 1), (-1, 0)),
    ((1, 0), (0, 1)),
)
IGNORED_COLORS = frozenset({1, 5, 6, 7, 9})


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                test = row["test"] if isinstance(row["test"], list) else [row["test"]]
                return row["train"] + test
    raise ValueError(f"canonical task {TASK} is absent from {path}")


def frame(grid):
    positions = {}
    for color in (2, 3, 4):
        hits = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(hits) != 1:
            raise ValueError(f"color {color}: expected one marker, found {len(hits)}")
        positions[color] = hits[0]
    origin = positions[2]
    vx = tuple(positions[3][i] - origin[i] for i in (0, 1))
    vy = tuple(positions[4][i] - origin[i] for i in (0, 1))
    if (vx, vy) not in BASES:
        raise ValueError(f"not an ordered cardinal orthogonal frame: {(vx, vy)!r}")
    return origin, vx, vy


def project(f, point):
    origin, vx, vy = f
    dr, dc = point[0] - origin[0], point[1] - origin[1]
    return dr * vx[0] + dc * vx[1], dr * vy[0] + dc * vy[1]


def lift(f, uv):
    origin, vx, vy = f
    u, v = uv
    return origin[0] + u * vx[0] + v * vy[0], origin[1] + u * vx[1] + v * vy[1]


def intended_output(grid):
    """Independent mirror of the canonical local color-8 projection."""
    f = frame(grid)
    marker_uv = {
        project(f, (r, c))
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    }
    return [
        [8 if (c - 1, r - 1) in marker_uv else 0 for c in range(3)]
        for r in range(3)
    ]


def any_nonframe_color_output(grid):
    """Plausible shortcut: treat every occupied non-frame local cell as an 8."""
    f = frame(grid)
    occupied = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            uv = project(f, (r, c))
            if max(abs(uv[0]), abs(uv[1])) <= 1 and value not in (0, 2, 3, 4):
                occupied.add(uv)
    return [
        [8 if (c - 1, r - 1) in occupied else 0 for c in range(3)]
        for r in range(3)
    ]


def observed(grid):
    f = frame(grid)
    marker_uv = []
    local_noise = 0
    exterior_noise = 0
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            uv = project(f, (r, c))
            radius = max(abs(uv[0]), abs(uv[1]))
            if value == 8:
                marker_uv.append(uv)
            elif value in IGNORED_COLORS:
                if radius <= 1:
                    local_noise += 1
                elif radius > 2:
                    exterior_noise += 1
                else:
                    raise ValueError("ignored-color cell occupies the radius-2 ring")
    visible = sum(max(abs(u), abs(v)) <= 1 for u, v in marker_uv)
    outer = sum(max(abs(u), abs(v)) == 2 for u, v in marker_uv)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "orientation": BASES.index(f[1:]),
        "n_markers": visible,
        "n_outer_markers": outer,
        "n_local_distractors": local_noise,
        "n_exterior_distractors": exterior_noise,
    }


def color_shortcut_witness():
    """Explicit 9x9 input where a local color-5 cell must be ignored."""
    grid = [[0] * 9 for _ in range(9)]
    # Standard frame: vx=east, vy=south.
    grid[4][4] = 2
    grid[4][5] = 3
    grid[5][4] = 4
    grid[3][3] = 5  # local (-1,-1), rival falsely marks output[0][0]
    grid[3][5] = 8  # local (1,-1), intended output[0][2]
    return grid


def racket_outputs(grids):
    """Execute the real canonical Racket rule; no Python fallback."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = None
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                program = row["program_solution"]
                break
    if program is None:
        raise ValueError("canonical program is absent")

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
        return json.loads(result["stdout"])
