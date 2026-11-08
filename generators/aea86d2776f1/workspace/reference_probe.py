"""Independent oracle and shortcut probes for task aea86d2776f1.

This helper deliberately does not import implementation helpers from generator.py.
The canonical Racket program remains label authority; the Python mirror exists for
fast regression tests and human-readable counterexamples.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
TASK = "aea86d2776f1"
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


def _grid(value):
    if value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return [list(row) for row in value]


def canonical_pairs():
    row = canonical()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [
        {"input": _grid(pair["input"]), "output": _grid(pair["output"])}
        for pair in row["train"] + test
    ]


def _identity(grid):
    return [row[:] for row in grid]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


_TRANSFORMS = (_identity, _rotate_cw, _flip_lr, _rotate_180)
_COMMAND_COLS = (1, 3, 7, 9)


def _panels(grid):
    return (
        [list(row[1:4]) for row in grid[2:5]],
        [list(row[7:10]) for row in grid[2:5]],
    )


def _decode(command):
    return (0 if command <= 4 else 1), (command - 1) % 4


def _mosaic(tiles):
    return [tiles[0][r] + tiles[1][r] for r in range(3)] + [
        tiles[2][r] + tiles[3][r] for r in range(3)
    ]


def intended_output(grid):
    panels = _panels(grid)
    tiles = []
    for col in _COMMAND_COLS:
        source, transform = _decode(grid[0][col])
        tiles.append(_TRANSFORMS[transform](panels[source]))
    return _mosaic(tiles)


def alternating_sources_rival(grid):
    """Wrong rule: source panels alternate, seeded only by the first command."""
    panels = _panels(grid)
    first_source, _ = _decode(grid[0][_COMMAND_COLS[0]])
    tiles = []
    for index, col in enumerate(_COMMAND_COLS):
        _, transform = _decode(grid[0][col])
        tiles.append(_TRANSFORMS[transform](panels[(first_source + index) % 2]))
    return _mosaic(tiles)


def monochrome_templates_rival(grid):
    """Wrong rule: retain panel occupancy but collapse each panel to one color."""
    panels = []
    for panel in _panels(grid):
        colors = [value for row in panel for value in row if value]
        color = colors[0] if colors else 0
        panels.append([[color if value else 0 for value in row] for row in panel])
    tiles = []
    for col in _COMMAND_COLS:
        source, transform = _decode(grid[0][col])
        tiles.append(_TRANSFORMS[transform](panels[source]))
    return _mosaic(tiles)


def _crop_top_left(panel):
    points = [(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value]
    if not points:
        return [[0] * 3 for _ in range(3)]
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    r1 = max(r for r, _ in points)
    c1 = max(c for _, c in points)
    crop = [row[c0:c1 + 1] for row in panel[r0:r1 + 1]]
    result = [[0] * 3 for _ in range(3)]
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            result[r][c] = value
    return result


def cropped_templates_rival(grid):
    """Wrong rule: crop each panel to its object bbox before transforming it."""
    panels = tuple(_crop_top_left(panel) for panel in _panels(grid))
    tiles = []
    for col in _COMMAND_COLS:
        source, transform = _decode(grid[0][col])
        tiles.append(_TRANSFORMS[transform](panels[source]))
    return _mosaic(tiles)


def observed(grid):
    left, right = _panels(grid)
    commands = [grid[0][col] for col in _COMMAND_COLS]
    return {
        "left_cells": sum(value != 0 for row in left for value in row),
        "right_cells": sum(value != 0 for row in right for value in row),
        "left_colors": len({value for row in left for value in row if value}),
        "right_colors": len({value for row in right for value in row if value}),
        "source_balance": sum(command <= 4 for command in commands),
        "transform_count": len({(command - 1) % 4 for command in commands}),
    }


def racket_outputs(grids):
    """Execute the selected canonical rule in the packet's real Racket runtime."""
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
