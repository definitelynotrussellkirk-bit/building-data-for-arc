"""Independent oracle and reusable audit helpers for 0ab5dc1f5386.

This module deliberately does not import production transformation helpers.  It
implements the selected Racket semantics directly, plus explicit rival rules
used by task-local tests and the review report.  The Racket bridge is optional
and never silently falls back to Python.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "0ab5dc1f5386"
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _grid(value):
    if value and isinstance(value[0], str):
        return [[int(ch) for ch in row] for row in value]
    return [list(row) for row in value]


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
    return [
        {"input": _grid(pair["input"]), "output": _grid(pair["output"])}
        for pair in row["train"] + test
    ]


def normalized_rule_hash(source):
    import hashlib
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _components(grid, *, same_color):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            start = (r, c)
            color = grid[r][c]
            stack = [start]
            seen.add(start)
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in seen:
                        continue
                    value = grid[nr][nc]
                    if value != 0 and (not same_color or value == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((start, cells))
    return result


def frame_boxes(grid):
    boxes = []
    for start, cells in _components(grid, same_color=True):
        if grid[start[0]][start[1]] != 8:
            continue
        r1 = min(r for r, _ in cells)
        r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        c2 = max(c for _, c in cells)
        if len(cells) == 2 * ((r2 - r1 + 1) + (c2 - c1 + 1)) - 4:
            boxes.append((r1, c1, r2, c2))
    return sorted(boxes)


def shape_info(grid):
    shapes = []
    for start, cells in _components(grid, same_color=False):
        if grid[start[0]][start[1]] == 8:
            continue
        r1 = min(r for r, _ in cells)
        r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        c2 = max(c for _, c in cells)
        crop = tuple(tuple(grid[r][c] for c in range(c1, c2 + 1))
                     for r in range(r1, r2 + 1))
        shapes.append((r2 - r1 + 1, c2 - c1 + 1, crop))
    return shapes


def _paint(grid, frame, crop):
    out = grid
    r1, c1, _, _ = frame
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            if value != 0:
                out[r1 + 1 + r][c1 + 1 + c] = value
    return out


def intended_output(grid):
    out = deepcopy(grid)
    shapes = shape_info(grid)
    used = []
    for frame in frame_boxes(grid):
        ih, iw = frame[2] - frame[0] - 1, frame[3] - frame[1] - 1
        match = next((shape for shape in shapes
                      if shape[0] == ih and shape[1] == iw and shape not in used), None)
        if match is not None:
            used.append(match)
            _paint(out, frame, match[2])
    return out


def rotate_to_fit_output(grid):
    """Plausible shortcut: a transposed crop may be rotated to fit."""
    out = deepcopy(grid)
    shapes = shape_info(grid)
    used = []
    for frame in frame_boxes(grid):
        ih, iw = frame[2] - frame[0] - 1, frame[3] - frame[1] - 1
        exact = next((shape for shape in shapes
                      if shape[0] == ih and shape[1] == iw and shape not in used), None)
        match = exact
        crop = exact[2] if exact else None
        if match is None:
            match = next((shape for shape in shapes
                          if shape[0] == iw and shape[1] == ih and shape not in used), None)
            if match is not None:
                crop = tuple(tuple(row) for row in zip(*match[2][::-1]))
        if match is not None:
            used.append(match)
            _paint(out, frame, crop)
    return out


def last_match_output(grid):
    """Plausible shortcut: choose the last matching component, not first."""
    out = deepcopy(grid)
    shapes = shape_info(grid)
    used = []
    for frame in frame_boxes(grid):
        ih, iw = frame[2] - frame[0] - 1, frame[3] - frame[1] - 1
        candidates = [shape for shape in shapes
                      if shape[0] == ih and shape[1] == iw and shape not in used]
        if candidates:
            match = candidates[-1]
            used.append(match)
            _paint(out, frame, match[2])
    return out


def flatten_shape_output(grid):
    """Plausible shortcut: preserve mask but flatten every crop to one color."""
    out = deepcopy(grid)
    shapes = shape_info(grid)
    used = []
    for frame in frame_boxes(grid):
        ih, iw = frame[2] - frame[0] - 1, frame[3] - frame[1] - 1
        match = next((shape for shape in shapes
                      if shape[0] == ih and shape[1] == iw and shape not in used), None)
        if match is None:
            continue
        used.append(match)
        color = next(value for row in match[2] for value in row if value != 0)
        crop = tuple(tuple(color if value else 0 for value in row) for row in match[2])
        _paint(out, frame, crop)
    return out


def reuse_shape_output(grid):
    """Known-wrong competitor: ignore the one-use constraint."""
    out = deepcopy(grid)
    shapes = shape_info(grid)
    for frame in frame_boxes(grid):
        ih, iw = frame[2] - frame[0] - 1, frame[3] - frame[1] - 1
        match = next((shape for shape in shapes if shape[0] == ih and shape[1] == iw), None)
        if match is not None:
            _paint(out, frame, match[2])
    return out


def occurrence_use_output(grid):
    """Plausible shortcut: use equal-valued source occurrences separately."""
    out = deepcopy(grid)
    shapes = shape_info(grid)
    used_indices = set()
    for frame in frame_boxes(grid):
        ih, iw = frame[2] - frame[0] - 1, frame[3] - frame[1] - 1
        match_index = next((index for index, shape in enumerate(shapes)
                            if index not in used_indices
                            and shape[0] == ih and shape[1] == iw), None)
        if match_index is not None:
            used_indices.add(match_index)
            _paint(out, frame, shapes[match_index][2])
    return out


def observed_profile(grid):
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


def loose_crops(grid):
    return [shape[2] for shape in shape_info(grid)]


def racket_outputs(grids):
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(json.dumps({
            "program": canonical()["program_solution"], "grids": grids,
        }))
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
