"""Independent oracle and reproducible probes for be6269bef667.

This module is task-local test tooling.  The Python mirror is supplementary:
``racket_outputs`` executes the canonical Racket authority when parity evidence
is requested and never silently substitutes the mirror.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "be6269bef667"
DIRECTIONS = {1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs():
    row = canonical()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def ray_output(grid, *, down_ignores_walls=False):
    """Independent direct interpreter for the documented directional rays."""
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in DIRECTIONS:
                continue
            dr, dc = DIRECTIONS[value]
            rr, cc = r, c
            while 0 <= rr < h and 0 <= cc < w:
                if grid[rr][cc] == 5 and not (down_ignores_walls and value == 3):
                    break
                out[rr][cc] += 1
                rr += dr
                cc += dc
    return out


def observed(grid):
    counts = Counter(v for row in grid for v in row)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_emitters": sum(counts[value] for value in DIRECTIONS),
        "n_walls": counts[5],
    }


def has_downward_wall_witness(grid):
    """A downward emitter reaches a wall with at least one cell beyond it."""
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 3:
                continue
            for rr in range(r + 1, h):
                if grid[rr][c] == 5:
                    if rr < h - 1:
                        return True
                    break
    return False


def witness_input():
    """Small legal input where the canonical-fitting downward shortcut fails."""
    grid = [[0] * 8 for _ in range(7)]
    for r, c, value in (
        (0, 3, 3), (2, 3, 5), (6, 3, 1),
        (3, 1, 2), (3, 6, 4),
        (0, 0, 1), (6, 7, 4),
        (1, 6, 2), (5, 1, 3),
        (1, 1, 5), (1, 5, 5), (5, 5, 5),
    ):
        grid[r][c] = value
    return grid


def racket_outputs(grids):
    """Execute the selected canonical Racket program in a relocated runtime."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids})
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
            raise RuntimeError(
                f"Racket worker failed: {result['stderr']} {result['stdout']}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count):
    report = {
        "schema": f"{TASK}-independent-audit-v1",
        "version": getattr(module, "VERSION", None),
        "canonical": {},
        "bands": {},
        "warning": "Python ray interpreter is supplementary, not label authority.",
    }
    pairs = canonical_pairs()
    report["canonical"] = {
        "pairs": len(pairs),
        "oracle_mismatches": [
            i for i, pair in enumerate(pairs) if ray_output(pair["input"]) != pair["output"]
        ],
        "rival_mismatches": [
            i
            for i, pair in enumerate(pairs)
            if ray_output(pair["input"], down_ignores_walls=True) != pair["output"]
        ],
        "self_check_errors": [module.self_check(pair["input"]) for pair in pairs],
    }
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        shapes, inputs = set(), set()
        for i in range(count):
            grid = module.generate(4099 + i, i * 13 + 5, difficulty=band)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(
                4099 + i, i * 13 + 5, difficulty=band
            )
            counts["witnesses"] += has_downward_wall_witness(grid)
            counts["rival_disagreements"] += ray_output(grid) != ray_output(
                grid, down_ignores_walls=True
            )
            shapes.add((len(grid), len(grid[0])))
            inputs.add(hashlib.sha256(json.dumps(grid).encode()).hexdigest())
        report["bands"][str(band)] = dict(
            counts, distinct_shapes=len(shapes), distinct_inputs=len(inputs)
        )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=250)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report = audit(module, args.count)
    generator_path = args.generator or ROOT / f"generators/{TASK}/generator.py"
    report["generator_sha256"] = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    grids = [pair["input"] for pair in canonical_pairs()] + [witness_input()]
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        bool(report["canonical"]["oracle_mismatches"])
        or any(report["canonical"]["self_check_errors"])
        or any(
            row["self_check_errors"] or row["nondeterministic"]
            for row in report["bands"].values()
        )
    )
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            mismatches = [
                i for i, (grid, output) in enumerate(zip(grids, outputs))
                if ray_output(grid) != output
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # retained as explicit evidence, never fallback
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
