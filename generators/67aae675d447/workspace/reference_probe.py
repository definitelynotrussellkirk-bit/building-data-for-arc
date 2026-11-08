"""Independent geometry oracle and reusable probes for 67aae675d447.

This module deliberately re-derives frames and the bbox-outline rule from pixels.
It is test tooling, not label authority.  ``racket_outputs`` executes the pinned
canonical Racket program and never substitutes the Python oracle.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile

TASK_ID = "67aae675d447"
ROOT_HINT = Path(__file__).resolve()

# Explicit independent enumeration: four rotations, then their reflections.
BASES = (
    ((0, 1), (1, 0)), ((1, 0), (0, -1)),
    ((0, -1), (-1, 0)), ((-1, 0), (0, 1)),
    ((0, -1), (1, 0)), ((-1, 0), (0, -1)),
    ((0, 1), (-1, 0)), ((1, 0), (0, 1)),
)


def _support():
    from reviewer_support import canonical_pairs as read_pairs, find_root, load_selected_generator
    return read_pairs, find_root, load_selected_generator


def root():
    _, find_root, _ = _support()
    return find_root(ROOT_HINT)


def load_generator():
    _, _, load_selected_generator = _support()
    return load_selected_generator(TASK_ID, root=root())[0]


def canonical_pairs():
    read_pairs, _, _ = _support()
    return read_pairs(TASK_ID, root=root(), labeled_only=True)


def frame(grid, colors):
    positions = {}
    for color in colors:
        hits = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(hits) != 1:
            raise ValueError(f"color {color}: expected one marker, found {len(hits)}")
        positions[color] = hits[0]
    origin = positions[colors[0]]
    x, y = [tuple(positions[color][i] - origin[i] for i in (0, 1)) for color in colors[1:]]
    if (x, y) not in BASES:
        raise ValueError(f"colors {colors} do not form an orthogonal cardinal frame")
    return origin, x, y


def project(frm, point):
    origin, x, y = frm
    dr, dc = point[0] - origin[0], point[1] - origin[1]
    return dr * x[0] + dc * x[1], dr * y[0] + dc * y[1]


def lift(frm, uv):
    origin, x, y = frm
    u, v = uv
    return origin[0] + u * x[0] + v * y[0], origin[1] + u * x[1] + v * y[1]


def motif(grid):
    src = frame(grid, (2, 3, 4))
    return {
        project(src, (r, c))
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8 and max(abs(project(src, (r, c))[0]), abs(project(src, (r, c))[1])) <= 3
    }


def geometry_output(grid, *, mode="perimeter"):
    """Independent pixel oracle plus named deliberately-wrong rivals."""
    src, tgt = frame(grid, (2, 3, 4)), frame(grid, (5, 6, 7))
    points = motif(grid)
    if not points:
        raise ValueError("source motif is empty")
    u0, u1 = min(u for u, _ in points), max(u for u, _ in points)
    v0, v1 = min(v for _, v in points), max(v for _, v in points)
    out = deepcopy(grid)
    if mode == "copy_motif":
        cells = points
        target = tgt
    elif mode == "corners_only":
        cells = {(u0, v0), (u0, v1), (u1, v0), (u1, v1)}
        target = tgt
    elif mode == "solid_bbox":
        cells = {(u, v) for u in range(u0, u1 + 1) for v in range(v0, v1 + 1)}
        target = tgt
    elif mode == "source_basis_at_target":
        cells = {
            (u, v)
            for u in range(u0, u1 + 1)
            for v in range(v0, v1 + 1)
            if u in (u0, u1) or v in (v0, v1)
        }
        target = (tgt[0], src[1], src[2])
    elif mode == "perimeter":
        cells = {
            (u, v)
            for u in range(u0, u1 + 1)
            for v in range(v0, v1 + 1)
            if u in (u0, u1) or v in (v0, v1)
        }
        target = tgt
    else:
        raise ValueError(f"unknown oracle mode {mode!r}")
    h, w = len(grid), len(grid[0])
    for uv in cells:
        r, c = lift(target, uv)
        if not (0 <= r < h and 0 <= c < w):
            raise ValueError(f"target projection {uv} is out of bounds")
        out[r][c] = 8
    return out


def observed(grid):
    src, tgt = frame(grid, (2, 3, 4)), frame(grid, (5, 6, 7))
    near = motif(grid)
    all_eights = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8}
    near_global = {lift(src, uv) for uv in near}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_motif": len(near),
        "bbox_u_span": max(u for u, _ in near) - min(u for u, _ in near),
        "bbox_v_span": max(v for _, v in near) - min(v for _, v in near),
        "n_distractors": len(all_eights - near_global),
        "source_orientation": BASES.index(src[1:]),
        "target_orientation": BASES.index(tgt[1:]),
    }


def orientation_witness():
    """Explicit lawful input where source-basis-at-target is observably wrong."""
    g = [[0] * 15 for _ in range(11)]
    src = ((5, 3), *BASES[0])
    tgt = ((5, 11), *BASES[1])
    for frm, colors in ((src, (2, 3, 4)), (tgt, (5, 6, 7))):
        for uv, color in zip(((0, 0), (1, 0), (0, 1)), colors):
            r, c = lift(frm, uv)
            g[r][c] = color
    for uv in ((-2, -1), (1, 2), (2, 1)):
        r, c = lift(src, uv)
        if g[r][c] != 0:
            raise AssertionError("bad witness construction")
        g[r][c] = 8
    return g


def racket_outputs(grids):
    """Execute the selected canonical Racket authority on a batch."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    repo = root()
    sys.path.insert(0, str(repo / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = None
    ledger = repo / "shared/data/canonical/puzzles.jsonl"
    if not ledger.is_file():
        ledger = repo / "data/canonical/puzzles.jsonl"
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row["program_solution"]
                break
    if program is None:
        raise KeyError(TASK_ID)
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(repo), stage, TASK_ID)
        (stage / "parity-request.json").write_text(json.dumps({"program": program, "grids": grids}))
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path("parity-request.json").read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request["grids"]]))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        return json.loads(result["stdout"])
