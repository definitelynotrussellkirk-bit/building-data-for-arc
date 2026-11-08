"""Independent oracle and probes for task 531905d00c4b.

This module deliberately does not import implementation helpers from generator.py.
Its Python oracle is supplementary test tooling; canonical Racket remains the
label authority and can be required with ``racket_outputs``.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
TASK = "531905d00c4b"
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    source = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs():
    row = canonical()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def _components(grid):
    """Return same-color 4-connected nonzero components."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, tuple(sorted(cells))))
    return result


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _crop_component(grid, color, cells):
    r0, c0, r1, c1 = _bbox(cells)
    out = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in cells:
        out[r - r0][c - c0] = color
    return out


def _pad(grid, height, width):
    out = [[0] * width for _ in range(height)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            out[r][c] = value
    return out


def _separator(grid):
    for r, row in enumerate(grid):
        if all(v == 0 for v in row):
            return r
    raise ValueError("no all-zero separator row")


def _index_bbox(grid, sep):
    points = [
        (r, c)
        for r in range(sep + 1, len(grid))
        for c, value in enumerate(grid[r])
        if value != 0
    ]
    if not points:
        raise ValueError("empty index area")
    return _bbox(points)


def parse(grid):
    sep = _separator(grid)
    library = [list(row) for row in grid[:sep]]
    components = sorted(_components(library), key=lambda item: (_bbox(item[1])[1], _bbox(item[1])[0]))
    if not components:
        raise ValueError("empty prototype library")
    crops = [(color, _crop_component(library, color, cells)) for color, cells in components]
    ph = max(len(tile) for _, tile in crops)
    pw = max(len(tile[0]) for _, tile in crops)
    tiles = {color: _pad(tile, ph, pw) for color, tile in crops}
    r0, c0, r1, c1 = _index_bbox(grid, sep)
    index = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    return {
        "sep": sep,
        "library": library,
        "components": components,
        "tiles": tiles,
        "tile_h": ph,
        "tile_w": pw,
        "index_bbox": (r0, c0, r1, c1),
        "index": index,
    }


def _mosaic(index, tiles, tile_h, tile_w):
    out = [[0] * (len(index[0]) * tile_w) for _ in range(len(index) * tile_h)]
    for ir, row in enumerate(index):
        for ic, token in enumerate(row):
            tile = tiles.get(token, [[0] * tile_w for _ in range(tile_h)])
            for r in range(tile_h):
                for c in range(tile_w):
                    value = tile[r][c]
                    if value:
                        out[ir * tile_h + r][ic * tile_w + c] = value
    return out


def intended_output(grid):
    parts = parse(grid)
    return _mosaic(parts["index"], parts["tiles"], parts["tile_h"], parts["tile_w"])


def absolute_row_rival(grid):
    """Wrong rule: preserve each prototype's absolute library row offset."""
    parts = parse(grid)
    lib_h = parts["sep"]
    pw = parts["tile_w"]
    tiles = {}
    for color, cells in parts["components"]:
        _, c0, _, c1 = _bbox(cells)
        tile = [[0] * (c1 - c0 + 1) for _ in range(lib_h)]
        for r, c in cells:
            tile[r][c - c0] = color
        tiles[color] = _pad(tile, lib_h, pw)
    return _mosaic(parts["index"], tiles, lib_h, pw)


def uncropped_index_rival(grid):
    """Wrong rule: tile the lower rectangle without cropping top/left zero padding."""
    parts = parse(grid)
    _, _, r1, c1 = parts["index_bbox"]
    raw = [row[:c1 + 1] for row in grid[parts["sep"] + 1:r1 + 1]]
    return _mosaic(raw, parts["tiles"], parts["tile_h"], parts["tile_w"])


def fixed_3x3_rival(grid):
    """Wrong rule: always normalize prototype tiles to the canonical 3x3 size."""
    parts = parse(grid)
    tiles = {}
    for color, tile in parts["tiles"].items():
        fixed = [[0] * 3 for _ in range(3)]
        for r in range(min(3, len(tile))):
            for c in range(min(3, len(tile[0]))):
                fixed[r][c] = tile[r][c]
        tiles[color] = fixed
    return _mosaic(parts["index"], tiles, 3, 3)


def racket_outputs(grids):
    """Execute the selected canonical rule in the repository's real Racket runtime."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {"program": canonical()["program_solution"], "grids": deepcopy(grids)}
        (stage / "parity-request.json").write_text(json.dumps(request), encoding="utf-8")
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
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs
