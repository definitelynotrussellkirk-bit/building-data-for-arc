"""Independent geometry probes for task 7fd453cd0339 tests.

This module is test evidence, not the selected generator or label authority.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Iterable

TASK_ID = "7fd453cd0339"
Cell = tuple[int, int]
Grid = list[list[int]]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or Path(__file__).resolve().parents[1] / "generator.py")
    spec = importlib.util.spec_from_file_location(f"reviewed_generator_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid: Grid) -> list[tuple[int, set[Cell]]]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result: list[tuple[int, set[Cell]]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: set[Cell] = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def bbox(cells: Iterable[Cell]) -> tuple[int, int, int, int]:
    points = tuple(cells)
    return (
        min(r for r, _ in points),
        min(c for _, c in points),
        max(r for r, _ in points),
        max(c for _, c in points),
    )


def corner_output(grid: Grid) -> Grid:
    """Independent mirror: retain the distinct bbox corners per component."""
    out = [[0 for _ in row] for row in grid]
    for color, cells in components(grid):
        r0, c0, r1, c1 = bbox(cells)
        for r, c in {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}:
            out[r][c] = color
    return out


def observed(grid: Grid) -> dict[str, object]:
    comps = components(grid)
    colors = {color for color, _ in comps}
    palettes = {
        "canonical_24": {2, 4},
        "canonical_35": {3, 5},
        "broad": {1, 6, 7, 8, 9},
    }
    matches = [name for name, values in palettes.items() if colors <= values]
    if len(matches) != 1:
        raise ValueError(f"cannot infer palette_kind from colors {sorted(colors)}")
    has_line = False
    for _, cells in comps:
        r0, c0, r1, c1 = bbox(cells)
        has_line |= r0 == r1 or c0 == c1
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "rectangles": len(comps),
        "palette_kind": matches[0],
        "texture": "counterexample" if has_line else "canonical",
    }


def witness_differences(expected: Grid, rival: Grid) -> list[tuple[int, int, int, int]]:
    return [
        (r, c, expected[r][c], rival[r][c])
        for r in range(len(expected))
        for c in range(len(expected[0]))
        if expected[r][c] != rival[r][c]
    ]


def _canonical_program(root: Path) -> str:
    """Load the selected public canonical Racket program from this runtime."""
    import json
    from reviewer_support import canonical_path

    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                program = record.get("program_solution")
                if not isinstance(program, str) or not program.strip():
                    raise ValueError(f"{TASK_ID}: canonical program is absent")
                return program
    raise KeyError(TASK_ID)


def racket_outputs(grids: list[Grid]) -> list[Grid]:
    """Require the real staged Racket runtime and apply the canonical program."""
    import json
    import tempfile

    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    from reviewer_support import find_root

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    root = find_root(__file__)
    sys_path = str(root / "src")
    if sys_path not in os.sys.path:
        os.sys.path.insert(0, sys_path)
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(root), stage, TASK_ID)
        request = {"program": _canonical_program(root), "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request), encoding="utf-8")
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("parity-request.json").read_text(encoding="utf-8"))
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    outputs = [runner._apply_rule(bridge, name, grid) for grid in request["grids"]]
    print(json.dumps(outputs))
finally:
    bridge.close()
'''
        result = run_process([os.sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket worker failed: stderr={result['stderr']!r} stdout={result['stdout']!r}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs
