"""Independent oracle and audit helpers for a51a8e285ce9.

This module deliberately re-derives panel geometry and D4 matching.  It is test
and review tooling only; generated labels remain the canonical Racket rule's
responsibility.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
TASK = "a51a8e285ce9"
CODES = ("id", "r1", "r2", "r3", "fh", "fv", "tr", "atr")
ROTATIONS = CODES[:4]
REFLECTIONS = CODES[4:]


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_row():
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise LookupError(f"canonical task {TASK} is absent")


def canonical_pairs():
    row = canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(test)


def normalize(cells: Iterable[tuple[int, int]]):
    cells = tuple(cells)
    if not cells:
        return tuple()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _dims(cells):
    cells = normalize(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def transform(cells, code):
    cells = normalize(cells)
    h, w = _dims(cells)
    if code == "id":
        raw = cells
    elif code == "r1":
        raw = tuple((c, h - 1 - r) for r, c in cells)
    elif code == "r2":
        raw = tuple((h - 1 - r, w - 1 - c) for r, c in cells)
    elif code == "r3":
        raw = tuple((w - 1 - c, r) for r, c in cells)
    elif code == "fh":
        raw = tuple((r, w - 1 - c) for r, c in cells)
    elif code == "fv":
        raw = tuple((h - 1 - r, c) for r, c in cells)
    elif code == "tr":
        raw = tuple((c, r) for r, c in cells)
    elif code == "atr":
        raw = tuple((w - 1 - c, h - 1 - r) for r, c in cells)
    else:
        raise ValueError(f"unknown transform {code!r}")
    return normalize(raw)


def orbit(cells):
    return {transform(cells, code) for code in CODES}


def connected(cells):
    todo = set(cells)
    if not todo:
        return False
    seen = {next(iter(todo))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if q in todo and q not in seen:
                seen.add(q)
                stack.append(q)
    return seen == todo


def parse(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty list of non-empty rows")
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be integer ARC colors")
    if (w - 2) % 3:
        raise ValueError("width must equal 3*panel_w+2")
    panel_w = (w - 2) // 3
    if panel_w < 1:
        raise ValueError("panels must be non-empty")
    separators = (panel_w, 2 * panel_w + 1)
    if any(grid[r][c] != 8 for c in separators for r in range(h)):
        raise ValueError("separator columns must be full-height color 8")
    panels = []
    for index in range(3):
        left = index * (panel_w + 1)
        cells = [(r, c) for r in range(h) for c in range(panel_w) if grid[r][left + c] != 0]
        colors = {grid[r][left + c] for r, c in cells}
        if not cells:
            raise ValueError(f"panel {index} is empty")
        if len(colors) != 1:
            raise ValueError(f"panel {index} must contain one object color")
        support = normalize(cells)
        if not connected(support):
            raise ValueError(f"panel {index} support is disconnected")
        panels.append({"support": support, "color": next(iter(colors)), "raw": tuple(cells)})
    protos = panels[:2]
    query = panels[2]
    matches = [i for i, p in enumerate(protos) if query["support"] in orbit(p["support"])]
    if len(matches) != 1:
        raise ValueError(f"query must match exactly one prototype, got {matches}")
    return {
        "h": h,
        "w": w,
        "panel_w": panel_w,
        "separators": separators,
        "panels": panels,
        "protos": protos,
        "query": query,
        "match_index": matches[0],
    }


def support_grid(cells, color):
    cells = normalize(cells)
    h, w = _dims(cells)
    out = [[0] * w for _ in range(h)]
    for r, c in cells:
        out[r][c] = color
    return out


def geometry_output(grid):
    info = parse(grid)
    return support_grid(info["protos"][info["match_index"]]["support"], info["query"]["color"])


def observed(grid):
    info = parse(grid)
    proto = info["protos"][info["match_index"]]["support"]
    query = info["query"]["support"]
    codes = [code for code in CODES if transform(proto, code) == query]
    if len(codes) != 1:
        raise ValueError(f"transform is not uniquely observable: {codes}")
    sizes = {len(p["support"]) for p in info["protos"]}
    if len(sizes) != 1:
        raise ValueError(f"prototype_size is not exact: {sorted(sizes)}")
    return {
        "grid_h": info["h"],
        "panel_w": info["panel_w"],
        "prototype_size": next(iter(sizes)),
        "match_index": info["match_index"],
        "transform": codes[0],
        "palette_size": len({v for row in grid for v in row}),
    }


def object_offsets(grid):
    info = parse(grid)
    return tuple((min(r for r, _ in p["raw"]), min(c for _, c in p["raw"])) for p in info["panels"])


def racket_outputs(grids):
    """Require and execute the selected Racket rule; never Python-fallback."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    program = canonical_row()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(json.dumps({"program": program, "grids": grids}))
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    outputs=[runner._apply_rule(bridge,name,g) for g in request['grids']]
    print(json.dumps(outputs))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        return json.loads(result["stdout"])
