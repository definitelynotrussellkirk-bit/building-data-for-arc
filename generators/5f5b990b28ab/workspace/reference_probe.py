"""Independent review oracle for ARC task 5f5b990b28ab.

The production generator is loaded only by :func:`load_generator`; all object
analysis and rival solvers below are deliberately task-local and independent.
Canonical Racket remains the label authority.
"""
from __future__ import annotations

from collections import deque
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable, Iterable

ROOT = Path(__file__).resolve().parents[3]
TASK = "5f5b990b28ab"
PALETTE = (2, 4, 6, 7, 3, 5, 9)
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs as _canonical_pairs  # noqa: E402


def load_generator(path: str | Path | None = None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    return _canonical_pairs(TASK, root=ROOT)


def canonical_program() -> str:
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK and row.get("program_solution"):
                return str(row["program_solution"])
    raise KeyError(TASK)


def rectangular_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or value not in (0, 8) for row in grid for value in row):
        raise ValueError("input cells must be integer colours 0 or 8")
    return len(grid), width


def components(grid: Any) -> list[set[tuple[int, int]]]:
    height, width = rectangular_grid(grid)
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    }
    result: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            row, col = queue.popleft()
            for neighbour in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbour in unseen:
                    unseen.remove(neighbour)
                    cells.add(neighbour)
                    queue.append(neighbour)
        result.append(cells)
    return sorted(result, key=min)


def bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("empty component")
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def box_area(cells: Iterable[tuple[int, int]]) -> int:
    r0, c0, r1, c1 = bbox(cells)
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def box_width(cells: Iterable[tuple[int, int]]) -> int:
    _, c0, _, c1 = bbox(cells)
    return c1 - c0 + 1


def is_nested(objects: list[set[tuple[int, int]]]) -> bool:
    ordered = sorted(objects, key=lambda cells: (-box_area(cells), bbox(cells)))
    for outer, inner in zip(ordered, ordered[1:]):
        ro0, co0, ro1, co1 = bbox(outer)
        ri0, ci0, ri1, ci1 = bbox(inner)
        if not (ro0 < ri0 and co0 < ci0 and ri1 < ro1 and ci1 < co1):
            return False
    return bool(ordered)


def observed_profile(grid: Any) -> str:
    height, width = rectangular_grid(grid)
    objects = components(grid)
    count = len(objects)
    nested = is_nested(objects)
    if (height, width, count, nested) == (13, 13, 3, True):
        return "canonical_nested3"
    if count == 2 and nested:
        return "nested2"
    if count == 4 and nested:
        return "nested4"
    if count == 3 and not nested:
        return "area_stress3"
    if count == 4 and not nested:
        return "area_stress4"
    raise ValueError(
        f"grid is outside the declared scene profiles: "
        f"shape={(height, width)} count={count} nested={nested}"
    )


def _paint_by_order(grid: Any, key: Callable[[set[tuple[int, int]]], Any]) -> list[list[int]]:
    height, width = rectangular_grid(grid)
    out = [[0] * width for _ in range(height)]
    objects = sorted(components(grid), key=key)
    for index, cells in enumerate(objects):
        colour = PALETTE[index]
        for row, col in cells:
            out[row][col] = colour
    return out


def oracle_output(grid: Any) -> list[list[int]]:
    return _paint_by_order(grid, lambda cells: (-box_area(cells), bbox(cells)))


def scan_order_rival(grid: Any) -> list[list[int]]:
    return _paint_by_order(grid, lambda cells: bbox(cells))


def perimeter_order_rival(grid: Any) -> list[list[int]]:
    return _paint_by_order(grid, lambda cells: (-len(cells), bbox(cells)))


def width_order_rival(grid: Any) -> list[list[int]]:
    return _paint_by_order(grid, lambda cells: (-box_width(cells), bbox(cells)))


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Execute the real selected Racket source in a portable staged runtime."""
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
        (stage / "parity-request.json").write_text(
            json.dumps({"program": canonical_program(), "grids": grids}),
            encoding="utf-8",
        )
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
finally:
    bridge.shutdown()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket worker failed: {result['stderr']} {result['stdout']}"
            )
        return json.loads(result["stdout"])
