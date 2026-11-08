"""Independent review oracle and probes for ARC task 424c822d69f3.

The production generator is deliberately not imported here.  These helpers let
future reviewers inspect canonical support, exact controls, nearest-marker ties,
and plausible canonical shortcuts without copying production internals.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

TASK = "424c822d69f3"
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
SRC = ROOT / "src"
for path in (RUNTIME, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

PALETTES = {
    "warm": (3, 6, 9, 4),
    "cool": (2, 6, 8, 1),
    "broad": (1, 4, 7, 8),
    "small": (1, 6, 7, 2),
}
RECT_PATTERNS = {
    "small": ((2, 2),),
    "medium": ((2, 3),),
    "large": ((2, 7),),
    "varied": ((2, 4), (3, 2), (3, 3)),
}


def load_generator(path: str | Path | None = None):
    source = Path(path or ROOT / "generators" / TASK / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_424c822d69f3", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    from reviewer_support import canonical_pairs as read_pairs
    return read_pairs(TASK, root=ROOT, labeled_only=True)


def components(grid: list[list[int]], color: int = 5) -> list[tuple[tuple[int, int], ...]]:
    unseen = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    result: list[tuple[tuple[int, int], ...]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        todo = [start]
        cells = []
        while todo:
            r, c = todo.pop()
            cells.append((r, c))
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    todo.append(point)
        result.append(tuple(sorted(cells)))
    return sorted(result, key=lambda cells: (min(c for _, c in cells), min(r for r, _ in cells)))


def bbox(cells: tuple[tuple[int, int], ...]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def markers(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [(c, value) for c, value in enumerate(grid[0]) if value not in (0, 5)]


def nearest_marker(grid: list[list[int]], cells: tuple[tuple[int, int], ...]):
    _, c0, _, c1 = bbox(cells)
    center = (c0 + c1) // 2
    ranked = sorted((abs(col - center), col, color) for col, color in markers(grid))
    best = ranked[0][0]
    winners = [(col, color) for distance, col, color in ranked if distance == best]
    return winners[0] if len(winners) == 1 else None


def tie_objects(grid: list[list[int]]) -> list[dict]:
    found = []
    for cells in components(grid):
        if nearest_marker(grid, cells) is None:
            found.append({"bbox": bbox(cells)})
    return found


def reference_output(grid: list[list[int]]) -> list[list[int]]:
    original = deepcopy(grid)
    out = deepcopy(grid)
    for cells in components(grid):
        nearest = nearest_marker(grid, cells)
        if nearest is None:
            raise ValueError("independent oracle refuses undefined nearest-marker ties")
        _, color = nearest
        for r, c in cells:
            out[r][c] = color
    if grid != original:
        raise AssertionError("oracle mutated its input")
    return out


def rival_rank_order(grid: list[list[int]]) -> list[list[int]]:
    """Plausible shortcut: pair objects and legend markers by left-to-right rank."""
    out = deepcopy(grid)
    objs = components(grid)
    legend = markers(grid)
    if not objs or not legend:
        return out
    for index, cells in enumerate(objs):
        marker_index = 0 if len(objs) == 1 else round(index * (len(legend) - 1) / (len(objs) - 1))
        color = legend[marker_index][1]
        for r, c in cells:
            out[r][c] = color
    return out


def rival_vertical_overlap_only(grid: list[list[int]]) -> list[list[int]]:
    """Plausible shortcut: recolor only when a legend marker lies over the bbox."""
    out = deepcopy(grid)
    legend = markers(grid)
    for cells in components(grid):
        _, c0, _, c1 = bbox(cells)
        inside = [(col, color) for col, color in legend if c0 <= col <= c1]
        if not inside:
            continue
        center = (c0 + c1) // 2
        _, color = min(inside, key=lambda item: (abs(item[0] - center), item[0]))
        for r, c in cells:
            out[r][c] = color
    return out


def witness_facts(grid: list[list[int]]) -> dict[str, bool]:
    assignments = []
    outside = False
    for cells in components(grid):
        nearest = nearest_marker(grid, cells)
        if nearest is None:
            continue
        col, color = nearest
        _, c0, _, c1 = bbox(cells)
        assignments.append((col, color))
        outside |= not (c0 <= col <= c1)
    return {
        "shared_nearest": len(assignments) != len(set(assignments)),
        "nearest_outside_bbox": outside,
    }


def _layout_signature(name: str, width: int, count: int) -> tuple[int, ...]:
    if name == "left_biased":
        return tuple(range(0, 2 * count, 2))
    if name == "right_biased":
        return tuple(range(width - (2 * count - 1), width, 2))
    if name == "edges":
        if count == 2:
            return (0, width - 1)
        return tuple([0] + [round(i * (width - 1) / (count - 1)) for i in range(1, count - 1)] + [width - 1])
    if name == "evenly_spaced":
        return tuple(round((i + 1) * (width - 1) / (count + 1)) for i in range(count))
    raise ValueError(name)


def observed(grid: list[list[int]]) -> dict[str, int | str]:
    legend = markers(grid)
    cols = tuple(col for col, _ in legend)
    colors = frozenset(color for _, color in legend)
    count = len(legend)
    palette_matches = [
        name for name, palette in PALETTES.items()
        if colors == frozenset(palette[:count])
    ]
    if len(palette_matches) != 1:
        raise ValueError(f"cannot infer palette kind from {sorted(colors)}")
    layout = "scattered"
    for name in ("evenly_spaced", "left_biased", "right_biased", "edges"):
        if cols == _layout_signature(name, len(grid[0]), count):
            layout = name
            break
    dims = []
    for cells in components(grid):
        r0, c0, r1, c1 = bbox(cells)
        dims.append((r1 - r0 + 1, c1 - c0 + 1))
    dim_multiset = sorted(dims)
    rect_matches = []
    for name, pattern in RECT_PATTERNS.items():
        expected = sorted(pattern[index % len(pattern)] for index in range(len(dims)))
        if dim_multiset == expected:
            rect_matches.append(name)
    if len(rect_matches) != 1:
        raise ValueError(f"cannot infer rect profile from {dim_multiset}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_markers": count,
        "n_rects": len(dims),
        "marker_layout": layout,
        "rect_size_kind": rect_matches[0],
        "palette_kind": palette_matches[0],
    }


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Execute the selected Racket authority without a Python fallback."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    record = next(row for row in map(json.loads, (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()) if row.get("task_id") == TASK)
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {"program": record["program_solution"], "grids": grids}
        (stage / "request.json").write_text(json.dumps(request), encoding="utf-8")
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["timed_out"] or result["exit_code"]:
            raise RuntimeError(f"Racket parity worker failed: {result['stderr']} {result['stdout']}")
        return json.loads(result["stdout"])
