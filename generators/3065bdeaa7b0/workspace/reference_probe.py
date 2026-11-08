"""Independent oracle and rival probes for ARC task 3065bdeaa7b0.

This module intentionally does not import implementation helpers from generator.py.
The Python oracle is supplementary test evidence; the canonical Racket program
remains the label authority and can be required with ``racket_outputs``.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "3065bdeaa7b0"
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    source = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_3065", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row():
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise FileNotFoundError(f"canonical row {TASK} not found")


def canonical_pairs():
    row = canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def color_positions(grid):
    positions = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((r, c))
    return positions


def _range_between(a, b):
    step = 1 if a <= b else -1
    return range(a, b + step, step)


def path_cells(a, b):
    """Row-first path for an already ordered endpoint pair."""
    a, b = tuple(a), tuple(b)
    return (
        [(a[0], c) for c in _range_between(a[1], b[1])]
        + [(r, b[1]) for r in _range_between(a[0], b[0])]
    )


def pair_records(grid, *, at_least_two=False, limit=None, column_first=False):
    records = []
    for color, points in color_positions(grid).items():
        eligible = len(points) >= 2 if at_least_two else len(points) == 2
        if not eligible:
            continue
        key = (lambda p: (p[1], p[0])) if column_first else (lambda p: (p[0], p[1]))
        a, b = sorted(points, key=key)[:2]
        records.append((a, color, b))
    records.sort(key=lambda record: record[0])
    return records if limit is None else records[:limit]


def _paint(grid, records, *, first_writer_wins=False):
    out = deepcopy(grid)
    painted = set()
    for a, color, b in records:
        for r, c in path_cells(a, b):
            if first_writer_wins and (r, c) in painted:
                continue
            out[r][c] = color
            painted.add((r, c))
    return out


def intended_output(grid):
    return _paint(grid, pair_records(grid))


def first_two_pairs_only(grid):
    """Wrong rule: connect only the first two exact pairs."""
    return _paint(grid, pair_records(grid, limit=2))


def first_two_occurrences_of_every_color(grid):
    """Wrong rule: any color seen at least twice is treated as a pair."""
    return _paint(grid, pair_records(grid, at_least_two=True))


def left_to_right_endpoints(grid):
    """Wrong rule: choose the horizontal leg from the left endpoint."""
    return _paint(grid, pair_records(grid, column_first=True))


def first_writer_wins(grid):
    """Wrong rule: an earlier path owns intersections instead of later overwrite."""
    return _paint(grid, pair_records(grid), first_writer_wins=True)


RIVALS = {
    "first_two_pairs_only": first_two_pairs_only,
    "first_two_occurrences_of_every_color": first_two_occurrences_of_every_color,
    "left_to_right_endpoints": left_to_right_endpoints,
    "first_writer_wins": first_writer_wins,
}


def observed(grid):
    counts = Counter(v for row in grid for v in row if v)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": sum(count == 2 for count in counts.values()),
        "n_decoys": sum(count == 3 for count in counts.values()),
    }


def witness_flags(grid):
    records = pair_records(grid)
    paths = [set(path_cells(a, b)) for a, _, b in records]
    overlaps = set()
    for i, current in enumerate(paths):
        for previous in paths[:i]:
            overlaps.update(current & previous)
    return {
        "more_than_two_pairs": len(records) > 2,
        "ignored_nonpair_color": any(len(points) >= 3 for points in color_positions(grid).values()),
        "top_right_first": any(a[1] > b[1] for a, _, b in records),
        "path_overlap": bool(overlaps),
    }


def grid_sha256(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def racket_outputs(grids):
    """Require the repository's real canonical Racket authority; no fallback."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_row()["program_solution"]
    with tempfile.TemporaryDirectory(prefix="3065bdeaa7b0-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids})
        )
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
            raise RuntimeError(f"Racket parity worker failed: {result}")
        return json.loads(result["stdout"])
