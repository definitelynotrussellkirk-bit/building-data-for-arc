"""Independent oracle and probes for the 9a35b20efa99 repair.

This module is test/evidence support.  It deliberately does not import geometry
helpers or semantic rivals from the production generator.  The selected Racket
program remains the label authority.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK = "9a35b20efa99"
ROOT = Path(find_root(__file__))

BASE_SHAPES = {
    "corner_l3": frozenset({(0, 0), (1, 0), (1, 1)}),
    "corner_l4": frozenset({(0, 0), (1, 0), (2, 0), (2, 1)}),
    "branch5": frozenset({(0, 0), (1, 0), (1, 1), (1, 2), (2, 0)}),
    "blob6": frozenset({(0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0)}),
}


def load_generator(path=None):
    path = Path(path or ROOT / "generators" / TASK / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_9a35b20efa99", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=ROOT)


def normalize_cells(cells):
    cells = set(cells)
    if not cells:
        return frozenset()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


def rotate_cells_cw(cells):
    return normalize_cells((c, -r) for r, c in cells)


def rotated(cells, turns):
    result = normalize_cells(cells)
    for _ in range(turns % 4):
        result = rotate_cells_cw(result)
    return result


def rotate_grid_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def rotate_grid_180(grid):
    return rotate_grid_cw(rotate_grid_cw(grid))


def rotate_grid_ccw(grid):
    return rotate_grid_cw(rotate_grid_180(grid))


def analyze(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be nonempty")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be nonempty")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors")
    anchors = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if len(anchors) != 1:
        raise ValueError(f"expected one anchor, found {len(anchors)}")
    motif = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value not in (0, 9)]
    if not motif:
        raise ValueError("missing motif")
    colors = {value for _, _, value in motif}
    if len(colors) != 1:
        raise ValueError("motif must be monochrome")
    cells = {(r, c) for r, c, _ in motif}
    stack = [next(iter(cells))]
    seen = {stack[0]}
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            point = (r + dr, c + dc)
            if point in cells and point not in seen:
                seen.add(point)
                stack.append(point)
    if seen != cells:
        raise ValueError("motif must be one 4-connected component")
    min_r = min(r for r, _ in cells)
    max_r = max(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    max_c = max(c for _, c in cells)
    local = normalize_cells(cells)
    matches = []
    for name, base in BASE_SHAPES.items():
        for turns in range(4):
            if local == rotated(base, turns):
                matches.append((name, turns))
    if len(matches) != 1:
        raise ValueError(f"motif is outside the four-shape manifold: {sorted(local)}")
    anchor = anchors[0]
    return {
        "height": len(grid),
        "width": width,
        "anchor": anchor,
        "motif_color": next(iter(colors)),
        "motif_cells": cells,
        "shape_kind": matches[0][0],
        "motif_rotation": matches[0][1],
        "bbox": (min_r, min_c, max_r, max_c),
    }


def observed(grid):
    info = analyze(grid)
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "motif_color": info["motif_color"],
        "motif_rotation": info["motif_rotation"],
    }


def source_is_above(grid):
    info = analyze(grid)
    return info["bbox"][2] < info["anchor"][0]


def is_corner_l(grid):
    return analyze(grid)["shape_kind"] in {"corner_l3", "corner_l4"}


def rule_output(grid):
    """Independent direct translation of the written crop/rotate/stamp rule."""
    info = analyze(grid)
    h, w = info["height"], info["width"]
    ar, ac = info["anchor"]
    min_r, min_c, max_r, max_c = info["bbox"]
    crop = [list(row[min_c : max_c + 1]) for row in grid[min_r : max_r + 1]]
    ch, cw = len(crop), len(crop[0])
    variants = (crop, rotate_grid_cw(crop), rotate_grid_180(crop), rotate_grid_ccw(crop))
    offsets = ((-ch - 1, -cw - 1), (-ch - 1, 1), (1, -cw - 1), (1, 1))
    out = [[0] * w for _ in range(h)]
    out[ar][ac] = 9
    for variant, (dr, dc) in zip(variants, offsets):
        for r, row in enumerate(variant):
            for c, value in enumerate(row):
                rr, cc = ar + dr + r, ac + dc + c
                if value and 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = value
    return out


def above_only_output(grid):
    return rule_output(grid) if source_is_above(grid) else deepcopy(grid)


def corner_l_only_output(grid):
    return rule_output(grid) if is_corner_l(grid) else deepcopy(grid)


def shortcut_witness():
    """A branch below the anchor; both canonical-fitting shortcuts fail."""
    grid = [[0] * 13 for _ in range(13)]
    grid[6][6] = 9
    for dr, dc in BASE_SHAPES["branch5"]:
        grid[10 + dr][5 + dc] = 2
    return grid


def racket_outputs(grids):
    """Require the real selected Racket authority; never fall back to Python."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    pair = canonical_pairs()[0]
    del pair  # force canonical data validation before runtime preparation
    canonical_path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    program = None
    for line in canonical_path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            program = row["program_solution"]
            break
    if program is None:
        raise ValueError("canonical rule missing")
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
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
