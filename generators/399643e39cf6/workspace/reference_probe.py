"""Independent oracle and source-bound probes for task 399643e39cf6.

The selected Racket program remains the label authority.  This module is test
and review tooling: it intentionally reimplements the visible geometry without
importing generator helpers, then optionally compares that mirror with Racket.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from typing import Iterable

TASK = "399643e39cf6"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    from reviewer_support import canonical_pairs as load_pairs, find_root

    return load_pairs(TASK, root=find_root(__file__), labeled_only=True)


def components(grid, *, include_markers=False):
    """Racket-compatible same-colour 4-connected components in row-major order."""
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if (r, c) in seen or color == 0 or (color == 9 and not include_markers):
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells = tuple(sorted(cells))
            rs = [p[0] for p in cells]
            cs = [p[1] for p in cells]
            found.append({
                "color": color,
                "cells": cells,
                "size": len(cells),
                "bbox": (min(rs), min(cs), max(rs), max(cs)),
            })
    return found


def selection_key(obj):
    return obj["size"], obj["bbox"][0], obj["bbox"][1], obj["color"]


def marker_vector(grid):
    markers = sorted(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    )
    if len(markers) != 2:
        raise ValueError(f"expected two markers, found {len(markers)}")
    (r1, c1), (r2, c2) = markers
    return (r2 - r1, c2 - c1), tuple(markers)


def _paint(out, cells, color):
    h, w = len(out), len(out[0])
    for r, c in cells:
        if 0 <= r < h and 0 <= c < w:
            out[r][c] = color


def rule_output(
    grid,
    *,
    selector="smallest",
    vector_mode="markers",
    remove_markers=True,
    copy_all=False,
):
    """Independent family of intended/rival outputs used by tests."""
    out = deepcopy(grid)
    vector, markers = marker_vector(grid)
    if vector_mode == "reverse":
        vector = (-vector[0], -vector[1])
    elif vector_mode == "fixed":
        vector = (5, 3)
    elif vector_mode != "markers":
        raise ValueError(vector_mode)

    if remove_markers:
        for r, c in markers:
            out[r][c] = 0

    objs = components([[0 if value == 9 else value for value in row] for row in grid])
    if copy_all:
        selected = objs
    elif selector == "smallest":
        selected = [min(objs, key=selection_key)]
    elif selector == "topmost":
        selected = [min(objs, key=lambda obj: (obj["bbox"][0], obj["bbox"][1], obj["color"]))]
    elif selector == "largest":
        selected = [min(objs, key=lambda obj: (-obj["size"], obj["bbox"][0], obj["bbox"][1], obj["color"]))]
    elif selector == "lowest_color":
        selected = [min(objs, key=lambda obj: (obj["color"], obj["bbox"][0], obj["bbox"][1]))]
    else:
        raise ValueError(selector)

    dr, dc = vector
    for obj in selected:
        _paint(out, ((r + dr, c + dc) for r, c in obj["cells"]), obj["color"])
    return out


def intended_output(grid):
    return rule_output(grid)


def generated_contract_errors(grid):
    """Check the production manifold, not merely output shape."""
    errors = []
    try:
        vector, markers = marker_vector(grid)
    except Exception as exc:
        return [str(exc)]
    if vector == (0, 0):
        errors.append("zero marker vector")
    objs = components([[0 if value == 9 else value for value in row] for row in grid])
    if len(objs) not in (2, 3):
        errors.append(f"expected 2 or 3 ordinary objects, found {len(objs)}")
        return errors
    chosen = min(objs, key=selection_key)
    topmost = min(objs, key=lambda obj: (obj["bbox"][0], obj["bbox"][1], obj["color"]))
    lowest = min(objs, key=lambda obj: (obj["color"], obj["bbox"][0], obj["bbox"][1]))
    if chosen is topmost:
        errors.append("smallest object is also topmost")
    if chosen is lowest:
        errors.append("smallest object is also lowest-colour")
    h, w = len(grid), len(grid[0])
    dr, dc = vector
    occupied = {(r, c) for obj in objs for r, c in obj["cells"]} | set(markers)
    for obj in objs:
        targets = {(r + dr, c + dc) for r, c in obj["cells"]}
        if not all(0 <= r < h and 0 <= c < w for r, c in targets):
            errors.append(f"translated color-{obj['color']} object is clipped")
        if targets & occupied:
            errors.append(f"translated color-{obj['color']} object overwrites input content")
    return errors


def racket_outputs(grids):
    """Require the actual selected Racket rule; never fall back to Python."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        program = next(
            json.loads(line)["program_solution"]
            for line in handle
            if line.strip() and json.loads(line).get("task_id") == TASK
        )
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "request.json").write_text(json.dumps({"program": program, "grids": grids}))
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('request.json').read_text())
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
