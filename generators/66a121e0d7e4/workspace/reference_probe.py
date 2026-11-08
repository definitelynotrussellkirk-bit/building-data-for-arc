"""Independent oracle and audit helpers for ARC task 66a121e0d7e4.

The implementation deliberately does not import transformation helpers from the
production generator.  It gives task-local tests a second executable statement
of the selected Racket rule and of the most important shortcut hypotheses.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

TASK = "66a121e0d7e4"
HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs as _canonical_pairs, find_root


def load_generator(path=None):
    source = Path(path or HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_66a121e0d7e4", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=find_root(__file__), labeled_only=True)


def _coerce(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty row sequence")
    result = []
    for row in grid:
        if not isinstance(row, (list, tuple)) or not row:
            raise ValueError("rows must be nonempty sequences")
        result.append(list(row))
    width = len(result[0])
    if any(len(row) != width for row in result):
        raise ValueError("grid must be rectangular")
    return result


def selectors(grid):
    g = _coerce(grid)
    rows = tuple(r for r in range(1, len(g)) if g[r][0] == 8)
    cols = tuple(c for c in range(1, len(g[0])) if g[0][c] == 8)
    return g, rows, cols


def extract(grid, *, row_limit=None, col_limit=None, span=False):
    g, rows, cols = selectors(grid)
    if row_limit is not None:
        rows = rows[:row_limit]
    if col_limit is not None:
        cols = cols[:col_limit]
    if span and rows and cols:
        rows = tuple(range(min(rows), max(rows) + 1))
        cols = tuple(range(min(cols), max(cols) + 1))
    if not rows or not cols:
        return [[0]]
    return [[g[r][c] for c in cols] for r in rows]


def rotate_cw(matrix):
    return [list(row) for row in zip(*matrix[::-1])]


def rotate_180(matrix):
    return [row[::-1] for row in matrix[::-1]]


def rotate_ccw(matrix):
    return [list(row) for row in zip(*matrix)][::-1]


def apply_command(matrix, command):
    matrix = [list(row) for row in matrix]
    if command == 1:
        return matrix
    if command == 2:
        return rotate_cw(matrix)
    if command == 3:
        return rotate_180(matrix)
    if command == 4:
        return rotate_ccw(matrix)
    raise ValueError(f"unsupported command {command!r}")


def rule_output(grid):
    g = _coerce(grid)
    return apply_command(extract(g), g[0][0])


def first_three_rival(grid):
    g = _coerce(grid)
    return apply_command(extract(g, row_limit=3, col_limit=3), g[0][0])


def ignore_command_rival(grid):
    return extract(grid)


def selector_span_rival(grid):
    g = _coerce(grid)
    return apply_command(extract(g, span=True), g[0][0])


def observed(grid):
    g, rows, cols = selectors(grid)
    return {
        "shape": (len(g), len(g[0])),
        "cmd": g[0][0],
        "n_rows": len(rows),
        "n_cols": len(cols),
        "rows": rows,
        "cols": cols,
    }


def racket_outputs(grids):
    """Run the selected canonical Racket program; never fall back to Python."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    sys.path.insert(0, str(REPO / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    import tempfile

    with (REPO / "shared/data/canonical/puzzles.jsonl").open() as handle:
        row = next(json.loads(line) for line in handle if json.loads(line).get("task_id") == TASK)

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(REPO), stage, TASK)
        request = {"program": row["program_solution"], "grids": grids}
        (stage / "request.json").write_text(json.dumps(request))
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


def audit(module, count=200):
    records = {
        "samples": 0,
        "self_check_errors": 0,
        "nondeterministic": 0,
        "oracle_mismatches": 0,
        "first_three_disagreements": 0,
        "ignore_command_disagreements": 0,
        "selector_span_disagreements": 0,
    }
    profiles = set()
    samples = []
    for band in (None, "easy", "medium", "hard"):
        for index in range(count):
            seed = 12000 + index
            sample_index = index * 17 + 3
            grid = module.generate(seed, sample_index, difficulty=band)
            records["samples"] += 1
            records["self_check_errors"] += bool(module.self_check(grid))
            records["nondeterministic"] += grid != module.generate(seed, sample_index, difficulty=band)
            records["oracle_mismatches"] += module.rule_mirror(grid) != rule_output(grid)
            records["first_three_disagreements"] += rule_output(grid) != first_three_rival(grid)
            records["ignore_command_disagreements"] += rule_output(grid) != ignore_command_rival(grid)
            records["selector_span_disagreements"] += rule_output(grid) != selector_span_rival(grid)
            info = observed(grid)
            profiles.add((band, *info["shape"], info["cmd"], info["n_rows"], info["n_cols"]))
            if index < 4:
                samples.append(grid)
    return {
        "schema": f"{TASK}-independent-audit-v1",
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "counts": records,
        "profiles": sorted(profiles, key=repr),
        "sample_hashes": [
            hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            for grid in samples
        ],
    }, samples


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()

    module = load_generator(args.generator)
    report, samples = audit(module, args.count)
    if args.racket:
        grids = [pair["input"] for pair in canonical_pairs()] + samples
        racket = racket_outputs(grids)
        report["racket"] = {
            "checked": len(grids),
            "mismatches": [
                index for index, (grid, output) in enumerate(zip(grids, racket))
                if rule_output(grid) != output
            ],
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    bad = any(report["counts"][name] for name in ("self_check_errors", "nondeterministic", "oracle_mismatches"))
    bad = bad or bool(report.get("racket", {}).get("mismatches"))
    return int(bad)


if __name__ == "__main__":
    raise SystemExit(main())
