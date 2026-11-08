"""Independent oracle and audit helpers for ARC task 5a44a210e9ea.

The production generator is deliberately not imported by the geometry/oracle
helpers below.  Canonical Racket remains label authority; this Python mirror is
only a small, readable regression oracle and distribution probe.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
TASK = "5a44a210e9ea"
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
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK:
                    return row["program_solution"]
    raise KeyError(TASK)


def _rectangular_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be integer ARC colours 0..9")
    return len(grid), width


def components(body: list[list[int]], color: int = 1) -> list[set[tuple[int, int]]]:
    """Return 4-connected components of ``color`` without production helpers."""
    height, width = _rectangular_grid(body)
    unseen = {(r, c) for r in range(height) for c in range(width) if body[r][c] == color}
    result: list[set[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        queue = deque([start])
        cells = {start}
        while queue:
            r, c = queue.popleft()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (rr, cc) in unseen:
                    unseen.remove((rr, cc))
                    cells.add((rr, cc))
                    queue.append((rr, cc))
        result.append(cells)
    return sorted(result, key=lambda cells: min(cells))


def bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("empty component")
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def frame_cells(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
        return set()
    return {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }


def is_rect_frame(cells: set[tuple[int, int]]) -> bool:
    return bool(cells) and cells == frame_cells(bbox(cells))


def analyze(grid: Any) -> dict[str, Any]:
    height, width = _rectangular_grid(grid)
    if height < 2:
        raise ValueError("grid needs a palette row and body")
    palette_columns = [c for c, value in enumerate(grid[0]) if value != 0]
    palette = [grid[0][c] for c in palette_columns]
    body = [list(row) for row in grid[1:]]
    objects = components(body, 1)
    frames = sorted((cells for cells in objects if is_rect_frame(cells)),
                    key=lambda cells: -(lambda box: (box[2]-box[0]+1)*(box[3]-box[1]+1))(bbox(cells)))
    nonframes = [cells for cells in objects if not is_rect_frame(cells)]
    if palette_columns == list(range(len(palette_columns))):
        palette_layout = "packed"
    elif palette_columns and palette_columns[0] == 0 and len(palette_columns) >= 2:
        palette_layout = "gapped"
    else:
        palette_layout = "other"
    return {
        "grid_h": height,
        "grid_w": width,
        "palette": palette,
        "palette_columns": palette_columns,
        "palette_size": len(palette),
        "palette_layout": palette_layout,
        "body": body,
        "components": objects,
        "frames": frames,
        "nonframes": nonframes,
        "scene_kind": "touching_decoy" if nonframes else "clean",
    }


def oracle_output(grid: Any) -> list[list[int]]:
    """Mirror the selected rule using independent component enumeration."""
    info = analyze(grid)
    palette = info["palette"]
    if not palette:
        raise ValueError("palette is empty")
    body = info["body"]
    out = [[0 for _ in row] for row in body]
    for index, cells in enumerate(info["frames"]):
        colour = palette[min(index, len(palette) - 1)]
        for r, c in cells:
            out[r][c] = colour
    return out


def prefix_palette_rival(grid: Any) -> list[list[int]]:
    """Wrong rule: stop palette parsing at the first zero in row 0."""
    _rectangular_grid(grid)
    prefix: list[int] = []
    for value in grid[0]:
        if value == 0:
            break
        prefix.append(value)
    if not prefix:
        return [[0 for _ in row] for row in grid[1:]]
    altered = deepcopy(grid)
    altered[0] = prefix + [0] * (len(grid[0]) - len(prefix))
    return oracle_output(altered)


def no_palette_reuse_rival(grid: Any) -> list[list[int]]:
    """Wrong rule: silently discard frames deeper than the palette."""
    info = analyze(grid)
    out = [[0 for _ in row] for row in info["body"]]
    for colour, cells in zip(info["palette"], info["frames"]):
        for r, c in cells:
            out[r][c] = colour
    return out


def paint_every_component_rival(grid: Any) -> list[list[int]]:
    """Wrong rule: rank and recolour every blue component, even malformed ones."""
    info = analyze(grid)
    palette = info["palette"]
    out = [[0 for _ in row] for row in info["body"]]
    objects = sorted(info["components"],
                     key=lambda cells: -(lambda box: (box[2]-box[0]+1)*(box[3]-box[1]+1))(bbox(cells)))
    for index, cells in enumerate(objects):
        colour = palette[min(index, len(palette) - 1)]
        for r, c in cells:
            out[r][c] = colour
    return out


def observed_axes(grid: Any) -> dict[str, Any]:
    info = analyze(grid)
    return {name: info[name] for name in (
        "grid_h", "grid_w", "palette_size", "palette_layout", "scene_kind"
    )}


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Require and execute the real canonical Racket rule; never fall back."""
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
            json.dumps({"program": canonical_program(), "grids": grids}), encoding="utf-8"
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
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs
