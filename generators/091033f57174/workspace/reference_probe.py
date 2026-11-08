"""Independent oracle and review probes for 091033f57174.

The selected Racket program remains the label authority.  This module mirrors
its observable behavior independently for focused regression tests and can run
real-Racket parity checks when the packet runtime is available.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys

TASK = "091033f57174"

try:
    from reviewer_support import canonical_pairs as _canonical_pairs, canonical_path, find_root
except ModuleNotFoundError:
    for _parent in Path(__file__).resolve().parents:
        _runtime = _parent / "shared/runtime"
        if (_runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_runtime))
            break
    from reviewer_support import canonical_pairs as _canonical_pairs, canonical_path, find_root

ROOT = Path(find_root(__file__)).resolve()


def _generator_path(path=None):
    if path is not None:
        candidate = Path(path).resolve()
        if candidate.is_dir():
            candidate = candidate / "generator.py"
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        return candidate
    for candidate in (
        ROOT / f"generators/{TASK}/generator.py",
        ROOT / f"puzzle_generators/per_puzzle/{TASK}/generator.py",
    ):
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(f"selected generator {TASK} is absent under {ROOT}")


def load_generator(path=None):
    selected = path or os.environ.get("GENERATOR_UNDER_TEST")
    generator_path = _generator_path(selected)
    spec = importlib.util.spec_from_file_location("reviewed_generator", generator_path)
    if spec is None or spec.loader is None:
        raise ImportError(generator_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=ROOT)


def canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def color_order(grid):
    seen = set()
    result = []
    for row in grid:
        for value in row:
            if value and value not in seen:
                seen.add(value)
                result.append(value)
    return result


def color_points(grid, color, *, omit_command_cell=False):
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color and not (omit_command_cell and (r, c) == (0, 0))
    ]


def route_cells(points, command):
    if len(points) != 2:
        raise ValueError(f"expected two endpoints, found {len(points)}")
    a, b = sorted(points)
    if command == 1:
        first = [(a[0], c) for c in range(min(a[1], b[1]), max(a[1], b[1]) + 1)]
        second = [(r, b[1]) for r in range(min(a[0], b[0]), max(a[0], b[0]) + 1)]
    else:
        first = [(r, a[1]) for r in range(min(a[0], b[0]), max(a[0], b[0]) + 1)]
        second = [(b[0], c) for c in range(min(a[1], b[1]), max(a[1], b[1]) + 1)]
    return tuple(dict.fromkeys(first + second))


def _paint(grid, records, command):
    out = [list(row) for row in grid]
    for color, points in records:
        for r, c in route_cells(points, command):
            out[r][c] = color
    return out


def oracle_output(grid, *, command_override=None):
    command = grid[0][0] if command_override is None else command_override
    records = []
    for color in color_order(grid):
        if color == grid[0][0]:
            continue
        points = color_points(grid, color)
        if len(points) == 2:
            records.append((color, points))
    return _paint(grid, records, command)


def route_three_marker_colors(grid):
    command = grid[0][0]
    records = []
    for color in color_order(grid):
        if color == command:
            continue
        points = color_points(grid, color)
        if len(points) >= 2:
            records.append((color, [points[0], points[-1]]))
    return _paint(grid, records, command)


def exclude_command_cell_only(grid):
    command = grid[0][0]
    records = []
    for color in color_order(grid):
        points = color_points(grid, color, omit_command_cell=True)
        if len(points) == 2:
            records.append((color, points))
    return _paint(grid, records, command)


def first_two_pairs_only(grid):
    command = grid[0][0]
    records = []
    for color in color_order(grid):
        if color == command:
            continue
        points = color_points(grid, color)
        if len(points) == 2:
            records.append((color, points))
            if len(records) == 2:
                break
    return _paint(grid, records, command)


def analyze(grid):
    command = grid[0][0]
    counts = Counter(value for row in grid for value in row)
    pair_colors = [
        color for color in color_order(grid)
        if color != command and counts[color] == 2
    ]
    triple_colors = [
        color for color in color_order(grid)
        if color != command and counts[color] == 3
    ]
    paths = [set(route_cells(color_points(grid, color), command)) for color in pair_colors]
    endpoint_sets = [set(color_points(grid, color)) for color in pair_colors]
    crossings = 0
    for left in range(len(paths)):
        for right in range(left + 1, len(paths)):
            interior = (paths[left] & paths[right]) - endpoint_sets[left] - endpoint_sets[right]
            crossings += len(interior)
    has_triple = bool(triple_colors)
    has_command_pair = counts[command] == 3
    texture = {
        (False, False): "plain",
        (True, False): "three_cells",
        (False, True): "cmd_color_pair",
        (True, True): "both",
    }[(has_triple, has_command_pair)]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": len(pair_colors),
        "command": command,
        "texture": texture,
        "pair_colors": pair_colors,
        "triple_colors": triple_colors,
        "path_crossings": crossings,
        "command_count": counts[command],
    }


def labeled(grid):
    return {"input": deepcopy(grid), "output": oracle_output(grid)}


def racket_outputs(grids):
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

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
    outputs=[runner._apply_rule(bridge,name,g) for g in request['grids']]
    print(json.dumps(outputs))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        return json.loads(result["stdout"])
