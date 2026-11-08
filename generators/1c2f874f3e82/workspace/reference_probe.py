"""Independent oracle and audit helpers for ARC task 1c2f874f3e82.

This module is reviewer tooling, not label authority.  Its geometry code is kept
separate from the production generator so task tests can catch shared mistakes.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

TASK = "1c2f874f3e82"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs as _canonical_pairs, find_root


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=find_root(__file__))


def color_cells(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    todo = deque(seen)
    while todo:
        r, c = todo.popleft()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in cells and point not in seen:
                seen.add(point)
                todo.append(point)
    return seen == cells


def transform(offset, marker_color):
    dr, dc = offset
    if marker_color == 3:
        return dr, dc
    if marker_color == 4:
        return dc, -dr
    if marker_color == 5:
        return dr, -dc
    raise ValueError(f"unsupported marker color {marker_color}")


def rule_output(grid, *, source_limit=None, first_marker_only=False):
    """Independent literal geometry implementation of the canonical rule."""
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    h, w = len(grid), len(grid[0])
    anchors = color_cells(grid, 1)
    source = sorted(color_cells(grid, 2))
    if len(anchors) != 1 or not source:
        raise ValueError("expected one anchor and a nonempty source")
    if source_limit is not None:
        source = source[:source_limit]
    ar, ac = anchors[0]
    offsets = [(r - ar, c - ac) for r, c in source]
    out = [[0] * w for _ in range(h)]
    for marker_color in (3, 4, 5):
        markers = sorted(color_cells(grid, marker_color))
        if first_marker_only:
            markers = markers[:1]
        for mr, mc in markers:
            for offset in offsets:
                dr, dc = transform(offset, marker_color)
                rr, cc = mr + dr, mc + dc
                if 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = 8
    return out


def fixed_four_rival(grid):
    return rule_output(grid, source_limit=4)


def at_most_five_rival(grid):
    return rule_output(grid, source_limit=5)


def first_marker_rival(grid):
    return rule_output(grid, first_marker_only=True)


def observed(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "source_cells": len(color_cells(grid, 2)),
        "n_markers": sum(len(color_cells(grid, color)) for color in (3, 4, 5)),
    }


def racket_outputs(grids):
    """Require the real canonical Racket bridge; never fall back to Python."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    import tempfile

    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        rows = (json.loads(line) for line in handle)
        row = next(record for record in rows if record.get("task_id") == TASK)
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "request.json").write_text(json.dumps({"program": row["program_solution"], "grids": grids}))
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
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        return json.loads(result["stdout"])


def audit(module, count):
    counters = Counter()
    profiles = set()
    samples = []
    for band in (None, "easy", "medium", "hard"):
        for index in range(count):
            grid = module.generate(12000 + index, index * 17 + 3, difficulty=band)
            counters["samples"] += 1
            counters["self_check_errors"] += bool(module.self_check(grid))
            counters["nondeterministic"] += grid != module.generate(12000 + index, index * 17 + 3, difficulty=band)
            counters["fixed_four_disagreements"] += rule_output(grid) != fixed_four_rival(grid)
            counters["at_most_five_disagreements"] += rule_output(grid) != at_most_five_rival(grid)
            counters["first_marker_disagreements"] += rule_output(grid) != first_marker_rival(grid)
            stats = observed(grid)
            profiles.add((stats["grid_h"], stats["grid_w"], len({v for row in grid for v in row})))
            if index < 8:
                samples.append(grid)
    return {
        "schema": f"{TASK}-independent-audit-v1",
        "version": module.VERSION,
        "counts": dict(counters),
        "profiles": sorted(profiles),
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "sample_hashes": [hashlib.sha256(json.dumps(g, separators=(",", ":")).encode()).hexdigest() for g in samples],
    }, samples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=250)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    module = load_generator(args.generator)
    report, samples = audit(module, args.count)
    if args.racket:
        grids = [pair["input"] for pair in canonical_pairs()] + samples
        outputs = racket_outputs(grids)
        mismatches = [i for i, (g, out) in enumerate(zip(grids, outputs)) if rule_output(g) != out]
        report["racket"] = {"checked": len(grids), "mismatches": mismatches}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return int(bool(report["counts"]["self_check_errors"] or report["counts"]["nondeterministic"] or report.get("racket", {}).get("mismatches")))


if __name__ == "__main__":
    raise SystemExit(main())
