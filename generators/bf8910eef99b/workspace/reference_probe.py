"""Independent oracle and probes for bf8910eef99b.

This module is reviewer tooling, not label authority.  Racket parity is explicit;
Python helpers never silently substitute for the canonical program.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys

TASK = "bf8910eef99b"
HERE = Path(__file__).resolve()

# Portable task-test runtimes place reviewer_support on PYTHONPATH.
from reviewer_support import canonical_pairs as _canonical_pairs, find_root
ROOT = find_root(HERE)

PALETTES = (
    frozenset((1, 2, 3, 4)),
    frozenset((1, 5, 7, 8)),
    frozenset((2, 3, 4, 6)),
    frozenset((2, 5, 8, 9)),
    frozenset((1, 3, 6, 9)),
    frozenset((4, 5, 7, 9)),
)
PROFILES = ("top_clip", "right_clip", "bottom_clip", "left_clip")


def load_generator(path=None):
    candidate = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or
                     ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_bf8910eef99b", candidate)
    if spec is None or spec.loader is None:
        raise ImportError(candidate)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=ROOT, labeled_only=True)


def _shape(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    return len(grid), width


def block(grid):
    """Return (top,left,(tl,tr,bl,br)) from pixels only."""
    _shape(grid)
    cells = [(r, c, value) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value != 0]
    if len(cells) != 4:
        raise ValueError(f"expected four nonzero cells, found {len(cells)}")
    rows = sorted({r for r, _, _ in cells})
    cols = sorted({c for _, c, _ in cells})
    if len(rows) != 2 or len(cols) != 2 or rows[1] != rows[0] + 1 or cols[1] != cols[0] + 1:
        raise ValueError("nonzero cells do not form a 2x2 block")
    br, bc = rows[0], cols[0]
    if any(grid[br + dr][bc + dc] == 0 for dr in (0, 1) for dc in (0, 1)):
        raise ValueError("2x2 block is not solid")
    colors = (grid[br][bc], grid[br][bc + 1],
              grid[br + 1][bc], grid[br + 1][bc + 1])
    return br, bc, colors


def _paint(out, rows, cols, color):
    h, w = len(out), len(out[0])
    for r in rows:
        for c in cols:
            if 0 <= r < h and 0 <= c < w and out[r][c] == 0:
                out[r][c] = color


def oracle_output(grid):
    """Independent transcription of the canonical opposite-quadrant rule."""
    br, bc, (tl, tr, bl, brr) = block(grid)
    out = deepcopy(grid)
    _paint(out, (br + 2, br + 3), (bc + 2, bc + 3), tl)
    _paint(out, (br + 2, br + 3), (bc - 2, bc - 1), tr)
    _paint(out, (br - 2, br - 1), (bc + 2, bc + 3), bl)
    _paint(out, (br - 2, br - 1), (bc - 2, bc - 1), brr)
    return out


def complete_stamps_only(grid):
    """Rival: discard a whole 2x2 stamp when any part is clipped."""
    br, bc, colors = block(grid)
    h, w = _shape(grid)
    out = deepcopy(grid)
    specs = (
        ((br + 2, br + 3), (bc + 2, bc + 3), colors[0]),
        ((br + 2, br + 3), (bc - 2, bc - 1), colors[1]),
        ((br - 2, br - 1), (bc + 2, bc + 3), colors[2]),
        ((br - 2, br - 1), (bc - 2, bc - 1), colors[3]),
    )
    for rows, cols, color in specs:
        if all(0 <= r < h for r in rows) and all(0 <= c < w for c in cols):
            _paint(out, rows, cols, color)
    return out



_CANONICAL_PALETTE_SETS = frozenset({
    frozenset((1, 2, 4, 6)),
    frozenset((3, 7, 8, 9)),
    frozenset((2, 3, 5, 6)),
    frozenset((1, 2, 3, 5)),
})


def canonical_palette_memorization(grid):
    """Rival: clip correctly only for exact palettes seen in canonical data."""
    _, _, colors = block(grid)
    if frozenset(colors) in _CANONICAL_PALETTE_SETS:
        return oracle_output(grid)
    return complete_stamps_only(grid)


def single_cell_copies(grid):
    """Rival: copy each color once, at the near corner of its target patch."""
    br, bc, colors = block(grid)
    out = deepcopy(grid)
    for (r, c), color in zip(((br + 2, bc + 2), (br + 2, bc - 1),
                              (br - 1, bc + 2), (br - 1, bc - 1)), colors):
        _paint(out, (r,), (c,), color)
    return out


def same_quadrant_stamps(grid):
    """Rival: extend each source corner outward into the same quadrant."""
    br, bc, (tl, tr, bl, brr) = block(grid)
    out = deepcopy(grid)
    _paint(out, (br - 2, br - 1), (bc - 2, bc - 1), tl)
    _paint(out, (br - 2, br - 1), (bc + 2, bc + 3), tr)
    _paint(out, (br + 2, br + 3), (bc - 2, bc - 1), bl)
    _paint(out, (br + 2, br + 3), (bc + 2, bc + 3), brr)
    return out


def absolute_corner_stamps(grid):
    """Rival: use grid corners rather than offsets from the source block."""
    _, _, (tl, tr, bl, brr) = block(grid)
    h, w = _shape(grid)
    out = deepcopy(grid)
    _paint(out, (h - 2, h - 1), (w - 2, w - 1), tl)
    _paint(out, (h - 2, h - 1), (0, 1), tr)
    _paint(out, (0, 1), (w - 2, w - 1), bl)
    _paint(out, (0, 1), (0, 1), brr)
    return out


def clockwise_color_roles(grid):
    """Rival: correct geometry, but source colors are rotated clockwise."""
    br, bc, (tl, tr, bl, brr) = block(grid)
    out = deepcopy(grid)
    _paint(out, (br + 2, br + 3), (bc + 2, bc + 3), tr)
    _paint(out, (br + 2, br + 3), (bc - 2, bc - 1), brr)
    _paint(out, (br - 2, br - 1), (bc + 2, bc + 3), tl)
    _paint(out, (br - 2, br - 1), (bc - 2, bc - 1), bl)
    return out


RIVALS = {
    "complete_stamps_only": complete_stamps_only,
    "canonical_palette_memorization": canonical_palette_memorization,
    "single_cell_copies": single_cell_copies,
    "same_quadrant_stamps": same_quadrant_stamps,
    "absolute_corner_stamps": absolute_corner_stamps,
    "clockwise_color_roles": clockwise_color_roles,
}


def observed(grid):
    h, w = _shape(grid)
    br, bc, colors = block(grid)
    if br == 1 and 2 <= bc <= w - 4:
        profile = "top_clip"
    elif bc == w - 3 and 2 <= br <= h - 4:
        profile = "right_clip"
    elif br == h - 3 and 2 <= bc <= w - 4:
        profile = "bottom_clip"
    elif bc == 1 and 2 <= br <= h - 4:
        profile = "left_clip"
    else:
        profile = "other"
    palette = frozenset(colors)
    try:
        palette_id = PALETTES.index(palette)
    except ValueError:
        palette_id = None
    return {"grid_h": h, "grid_w": w,
            "placement_profile": profile, "palette_id": palette_id}


def witness_input():
    """A lawful clipped case retained as the minimal complete-stamp witness."""
    grid = [[0] * 6 for _ in range(6)]
    grid[1][2], grid[1][3] = 1, 2
    grid[2][2], grid[2][3] = 3, 4
    return grid


def racket_outputs(grids):
    """Run the canonical Racket authority; raise when unavailable."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    canonical_file = ROOT / "shared/data/canonical/puzzles.jsonl"
    program = None
    with canonical_file.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                program = row["program_solution"]
                break
    if program is None:
        raise KeyError(TASK)
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8")
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
