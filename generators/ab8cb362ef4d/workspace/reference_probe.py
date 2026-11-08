"""Independent oracle and reproducible probes for ab8cb362ef4d.

This module is test tooling.  It reads the canonical row, independently detects
color-5 components and computes the gravity transform.  It never supplies labels
to the production generator.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

TASK = "ab8cb362ef4d"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_row():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise LookupError(f"canonical row {TASK} not found")


def canonical_pairs():
    row = canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(test)


def _components_of_five(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5 or (r, c) in seen:
                continue
            seen.add((r, c))
            stack = [(r, c)]
            component = []
            while stack:
                point = stack.pop()
                component.append(point)
                pr, pc = point
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = (pr + dr, pc + dc)
                    if (0 <= nxt[0] < h and 0 <= nxt[1] < w
                            and grid[nxt[0]][nxt[1]] == 5 and nxt not in seen):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(component)
    return components


def frame_boxes(grid):
    boxes = []
    for component in _components_of_five(grid):
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        boxes.append((min(rows), min(cols), max(rows), max(cols)))
    return sorted(boxes)


def gravity_output(grid):
    """Independent mirror of the selected authority's observable behavior."""
    out = [[0 for _ in row] for row in grid]
    for r0, c0, r1, c1 in frame_boxes(grid):
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    out[r][c] = 5
        for c in range(c0 + 1, c1):
            values = [grid[r][c] for r in range(r0 + 1, r1) if grid[r][c] != 0]
            start = r1 - len(values)
            for offset, value in enumerate(values):
                out[start + offset][c] = value
    return out


def observed(grid):
    boxes = frame_boxes(grid)
    colors = {value for row in grid for value in row if value not in (0, 5)}
    overwritten = 0
    column_counts = []
    occupied_columns_per_box = []
    for r0, c0, r1, c1 in boxes:
        occupied = 0
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    overwritten += grid[r][c] != 5
        for c in range(c0 + 1, c1):
            count = sum(grid[r][c] not in (0, 5) for r in range(r0 + 1, r1))
            if count:
                occupied += 1
                column_counts.append(count)
        occupied_columns_per_box.append(occupied)
    if column_counts and all(count == 1 for count in column_counts):
        pattern = "separate"
    elif boxes and all(count == 1 for count in occupied_columns_per_box):
        pattern = "stacked"
    else:
        pattern = "mixed"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_frames": len(boxes),
        "n_colors": len(colors),
        "column_pattern": pattern,
        "border_overwrites": overwritten,
    }


def first_frame_only(grid):
    boxes = frame_boxes(grid)
    if not boxes:
        return [[0 for _ in row] for row in grid]
    full = gravity_output(grid)
    out = [[0 for _ in row] for row in grid]
    r0, c0, r1, c1 = boxes[0]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            out[r][c] = full[r][c]
    return out


def preserve_damaged_border(grid):
    out = gravity_output(grid)
    for r0, c0, r1, c1 in frame_boxes(grid):
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    out[r][c] = grid[r][c]
    return out


def one_per_column(grid):
    out = gravity_output(grid)
    for r0, c0, r1, c1 in frame_boxes(grid):
        for c in range(c0 + 1, c1):
            values = [grid[r][c] for r in range(r0 + 1, r1) if grid[r][c] != 0]
            for r in range(r0 + 1, r1):
                out[r][c] = 0
            if values:
                out[r1 - 1][c] = values[-1]
    return out


def racket_outputs(grids):
    """Execute the real selected Racket rule; never silently fall back."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix="ab8cb362ef4d-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {"program": canonical_row()["program_solution"], "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request), encoding="utf-8")
        script = r'''\
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("parity-request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    outputs = [runner._apply_rule(bridge, name, grid) for grid in request["grids"]]
    print(json.dumps(outputs))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket parity worker failed: {result}")
        return json.loads(result["stdout"])
