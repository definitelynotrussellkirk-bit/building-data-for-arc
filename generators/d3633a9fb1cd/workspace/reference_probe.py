"""Independent oracle and audit helpers for d3633a9fb1cd.

This module intentionally does not import implementation helpers from generator.py.
The Python oracle is supplementary test evidence; the canonical Racket rule remains
label authority and can be invoked with :func:`racket_outputs`.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "d3633a9fb1cd"
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError("canonical task is absent")


def canonical_pairs():
    row = canonical()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def _neighbors(point, h, w):
    r, c = point
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc


def _components(grid, value):
    h, w = len(grid), len(grid[0])
    pending = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == value}
    result = []
    while pending:
        start = min(pending)
        pending.remove(start)
        comp = {start}
        queue = deque([start])
        while queue:
            point = queue.popleft()
            for nxt in _neighbors(point, h, w):
                if nxt in pending:
                    pending.remove(nxt)
                    comp.add(nxt)
                    queue.append(nxt)
        result.append(comp)
    return result


def rooms(grid):
    """Return the two framed wall components as sorted bounding boxes."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    boxes = []
    for comp in _components(grid, 5):
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        box = (min(rs), min(cs), max(rs), max(cs))
        r0, c0, r1, c1 = box
        perimeter = (
            {(r0, c) for c in range(c0, c1 + 1)}
            | {(r1, c) for c in range(c0, c1 + 1)}
            | {(r, c0) for r in range(r0, r1 + 1)}
            | {(r, c1) for r in range(r0, r1 + 1)}
        )
        if not perimeter <= comp:
            raise ValueError(f"wall component does not contain a rectangular frame: {box}")
        boxes.append(box)
    if len(boxes) != 2:
        raise ValueError(f"expected two wall components, found {len(boxes)}")

    a, b = boxes
    horizontal = (a[3] < b[1] or b[3] < a[1]) and not (a[2] < b[0] or b[2] < a[0])
    vertical = (a[2] < b[0] or b[2] < a[0]) and not (a[3] < b[1] or b[3] < a[1])
    if horizontal:
        return "horizontal", sorted(boxes, key=lambda box: box[1])
    if vertical:
        return "vertical", sorted(boxes, key=lambda box: box[0])
    raise ValueError("frames must be separated horizontally or vertically")


def _inside(box, point):
    r0, c0, r1, c1 = box
    r, c = point
    return r0 < r < r1 and c0 < c < c1


def observed(grid):
    orientation, boxes = rooms(grid)
    seed_counts = []
    barrier = False
    for box in boxes:
        r0, c0, r1, c1 = box
        vals = [
            grid[r][c]
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] not in (0, 5)
        ]
        seed_counts.append(len(vals))
        barrier |= any(
            grid[r][c] == 5
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
        )
    mode = { (1, 1): "single", (1, 2): "mixed", (2, 2): "double" }.get(tuple(sorted(seed_counts)))
    if mode is None:
        raise ValueError(f"unsupported seed counts: {seed_counts}")
    if orientation == "horizontal":
        depth = boxes[0][2] - boxes[0][0] - 1
        spans = [box[3] - box[1] - 1 for box in boxes]
        gap = boxes[1][1] - boxes[0][3] - 1
    else:
        depth = boxes[0][3] - boxes[0][1] - 1
        spans = [box[2] - box[0] - 1 for box in boxes]
        gap = boxes[1][0] - boxes[0][2] - 1
    return {
        "room_depth": depth,
        "room_span_a": spans[0],
        "room_span_b": spans[1],
        "gap": gap,
        "orientation": orientation,
        "seed_mode": mode,
        "barrier": barrier,
    }


def _seed_cells(grid):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]


def _distance_map(grid, start):
    h, w = len(grid), len(grid[0])
    queue = deque([start])
    steps = {start: 0}
    while queue:
        point = queue.popleft()
        for nxt in _neighbors(point, h, w):
            if grid[nxt[0]][nxt[1]] != 5 and nxt not in steps:
                steps[nxt] = steps[point] + 1
                queue.append(nxt)
    return steps


def geometry_output(grid, *, break_ties=False):
    """Independent shortest-path Voronoi oracle for the written task rule."""
    out = deepcopy(grid)
    seeds = _seed_cells(grid)
    maps = [(color, _distance_map(grid, (r, c))) for r, c, color in seeds]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            candidates = [(steps[(r, c)], color) for color, steps in maps if (r, c) in steps]
            if not candidates:
                continue
            best = min(distance for distance, _ in candidates)
            winners = sorted(color for distance, color in candidates if distance == best)
            if len(winners) == 1 or break_ties:
                out[r][c] = winners[0]
    return out


def component_manhattan_output(grid):
    """Plausible wrong shortcut: Manhattan distance within each open component."""
    h, w = len(grid), len(grid[0])
    component = {}
    next_id = 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5 or (r, c) in component:
                continue
            queue = deque([(r, c)])
            component[(r, c)] = next_id
            while queue:
                point = queue.popleft()
                for nxt in _neighbors(point, h, w):
                    if grid[nxt[0]][nxt[1]] != 5 and nxt not in component:
                        component[nxt] = next_id
                        queue.append(nxt)
            next_id += 1
    seeds = _seed_cells(grid)
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            options = [
                (abs(r - sr) + abs(c - sc), color)
                for sr, sc, color in seeds
                if component.get((sr, sc)) == component.get((r, c))
            ]
            if not options:
                continue
            best = min(distance for distance, _ in options)
            winners = [color for distance, color in options if distance == best]
            if len(winners) == 1:
                out[r][c] = winners[0]
    return out


def has_detour_counterexample(grid):
    return geometry_output(grid) != component_manhattan_output(grid)


def has_tie_counterexample(grid):
    return geometry_output(grid) != geometry_output(grid, break_ties=True)


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
        (stage / "request.json").write_text(json.dumps({"grids": grids}))
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('request.json').read_text())
rule,_=runner._load_rule('d3633a9fb1cd')
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(rule))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        return json.loads(result["stdout"])


def distribution_audit(module, count=100):
    report = {"schema": "d3633a9fb1cd-independent-audit-v1", "bands": {}}
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        unique = set()
        for index in range(count):
            grid = module.generate(7000 + index, index * 13 + 5, difficulty=band)
            counts["draws"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["detour_counterexamples"] += has_detour_counterexample(grid)
            counts["tie_counterexamples"] += has_tie_counterexample(grid)
            counts[f"orientation_{observed(grid)['orientation']}"] += 1
            counts[f"seed_mode_{observed(grid)['seed_mode']}"] += 1
            counts["barrier"] += observed(grid)["barrier"]
            unique.add(json.dumps(grid, separators=(",", ":")))
        counts["unique_inputs"] = len(unique)
        report["bands"][str(band)] = dict(counts)
    return report
