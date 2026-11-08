"""Independent oracle and probes for task 99d5bc858270.

This module is test tooling, not label authority.  ``racket_outputs`` executes
this packet's selected canonical Racket program and never silently falls back to
Python.
"""
from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys

TASK = "99d5bc858270"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    path = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs():
    row = canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(test)


def light_and_direction(grid, *, vertical_corner_priority=False):
    h, w = len(grid), len(grid[0])
    lights = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4 and (r in (0, h - 1) or c in (0, w - 1))
    ]
    if len(lights) != 1:
        raise ValueError(f"expected one border light, found {len(lights)}")
    r, c = lights[0]
    if vertical_corner_priority and r in (0, h - 1):
        direction = (1, 0) if r == 0 else (-1, 0)
    elif c == 0:
        direction = (0, 1)
    elif c == w - 1:
        direction = (0, -1)
    elif r == 0:
        direction = (1, 0)
    else:
        direction = (-1, 0)
    return (r, c), direction


def _casters(grid, light):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) != light
    ]


def geometry_output(grid, *, farthest_only=False, vertical_corner_priority=False):
    """Independent transcription of the selected rule's observable geometry."""
    h, w = len(grid), len(grid[0])
    light, (dr, dc) = light_and_direction(
        grid, vertical_corner_priority=vertical_corner_priority
    )
    casters = _casters(grid, light)
    selected = casters
    if farthest_only:
        groups = defaultdict(list)
        for item in casters:
            r, c, _ = item
            groups[r if dc else c].append(item)
        if dr > 0:
            selected = [max(group, key=lambda x: x[0]) for group in groups.values()]
        elif dr < 0:
            selected = [min(group, key=lambda x: x[0]) for group in groups.values()]
        elif dc > 0:
            selected = [max(group, key=lambda x: x[1]) for group in groups.values()]
        else:
            selected = [min(group, key=lambda x: x[1]) for group in groups.values()]

    out = [[0] * w for _ in range(h)]
    for r, c, _ in selected:
        r, c = r + dr, c + dc
        while 0 <= r < h and 0 <= c < w:
            out[r][c] = 4
            r, c = r + dr, c + dc
    for r, c, value in casters:
        out[r][c] = value
    return out


def light_position(grid):
    (r, c), _ = light_and_direction(grid)
    h, w = len(grid), len(grid[0])
    if (r, c) == (0, 0):
        return 4
    if (r, c) == (0, w - 1):
        return 5
    if (r, c) == (h - 1, w - 1):
        return 6
    if (r, c) == (h - 1, 0):
        return 7
    if r == 0:
        return 0
    if c == w - 1:
        return 1
    if r == h - 1:
        return 2
    if c == 0:
        return 3
    raise ValueError("light is not on the border")


def _component_count(grid):
    h, w = len(grid), len(grid[0])
    light, _ = light_and_direction(grid)
    seen = set()
    total = 0
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 4) or (r, c) == light or (r, c) in seen:
                continue
            total += 1
            seen.add((r, c))
            queue = deque([(r, c)])
            while queue:
                rr, cc = queue.popleft()
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == value
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
    return total


def observed(grid):
    colors = {value for row in grid for value in row if value not in (0, 4)}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "light_position": light_position(grid),
        "n_colors": len(colors),
        "n_components": _component_count(grid),
    }


def shared_projection_gap_lengths(grid):
    light, (dr, dc) = light_and_direction(grid)
    casters = _casters(grid, light)
    groups = defaultdict(list)
    for r, c, _ in casters:
        groups[r if dc else c].append((r, c))
    lengths = []
    for group in groups.values():
        ordered = sorted(group, key=(lambda cell: cell[1]) if dc else (lambda cell: cell[0]))
        for first, second in zip(ordered, ordered[1:]):
            a = first[1] if dc else first[0]
            b = second[1] if dc else second[0]
            if b - a <= 1:
                continue
            gap_has_zero = any(
                grid[first[0]][coordinate] == 0
                if dc
                else grid[coordinate][first[1]] == 0
                for coordinate in range(a + 1, b)
            )
            if gap_has_zero:
                lengths.append(b - a)
    return lengths


def has_shared_projection_gap(grid):
    return bool(shared_projection_gap_lengths(grid))


def racket_outputs(grids):
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

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
        request = {"program": canonical_row()["program_solution"], "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request))
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
