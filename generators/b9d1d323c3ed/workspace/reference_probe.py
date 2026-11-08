"""Independent probes for ARC generator b9d1d323c3ed.

This module is deliberately independent of ``generator.py``.  It is test and
review tooling, not a label authority.  The optional Racket path executes the
repository's selected canonical program and never silently falls back to the
Python oracle.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any

TASK_ID = "b9d1d323c3ed"
HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]


def load_generator(path: str | os.PathLike[str] | None = None):
    selected = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or HOME / "generator.py")
    spec = importlib.util.spec_from_file_location(f"generator_under_test_{TASK_ID}", selected)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {selected}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict[str, Any]:
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise LookupError(TASK_ID)


def canonical_pairs() -> list[dict[str, list[list[int]]]]:
    row = canonical_row()
    test = row.get("test")
    pairs = list(row.get("train") or []) + (test if isinstance(test, list) else [test])
    return [
        {"input": [list(line) for line in pair["input"]],
         "output": [list(line) for line in pair["output"]]}
        for pair in pairs
    ]


def normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _rectangular_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty row sequence")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be nonempty sequences")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    return [list(row) for row in grid]


def bbox(grid: Any) -> tuple[int, int, int, int]:
    values = _rectangular_grid(grid)
    cells = [(r, c) for r, row in enumerate(values) for c, value in enumerate(row) if value != 0]
    if not cells:
        raise ValueError("grid contains no non-background cell")
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), max(rows), min(cols), max(cols)


def analyze(grid: Any) -> dict[str, Any]:
    values = _rectangular_grid(grid)
    r1, r2, c1, c2 = bbox(values)
    colors = sorted({value for row in values for value in row if value != 0})
    crop = [row[c1:c2 + 1] for row in values[r1:r2 + 1]]
    return {
        "grid_h": len(values),
        "grid_w": len(values[0]),
        "fg_colors": colors,
        "fg_color": colors[0] if len(colors) == 1 else None,
        "bbox": (r1, r2, c1, c2),
        "bbox_h": r2 - r1 + 1,
        "bbox_w": c2 - c1 + 1,
        "crop": crop,
    }


def intended_output(grid: Any) -> list[list[int]]:
    """Independent specification: crop the nonzero bbox and concatenate it twice."""
    crop = analyze(grid)["crop"]
    return [row + row for row in crop]


def fixed_3x3_rival(grid: Any) -> list[list[int]]:
    """Plausible canonical shortcut: always crop 3x3 at the bbox's top-left."""
    values = _rectangular_grid(grid)
    r1, _, c1, _ = bbox(values)
    h, w = len(values), len(values[0])
    crop = [
        [values[r][c] if 0 <= r < h and 0 <= c < w else 0
         for c in range(c1, c1 + 3)]
        for r in range(r1, r1 + 3)
    ]
    return [row + row for row in crop]


def witness_input() -> list[list[int]]:
    """Exact 8x8 counterexample: a 2x2 diagonal object, centered."""
    grid = [[0] * 8 for _ in range(8)]
    grid[3][3] = 4
    grid[4][4] = 4
    return grid


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Execute the selected canonical Racket source in a relocated runtime."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_row()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-racket-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        (stage / "request.json").write_text(json.dumps({"program": program, "grids": grids}))
        script = r'''\
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge, name, grid) for grid in request["grids"]]))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["timed_out"] or result["exit_code"] != 0:
            raise RuntimeError(f"Racket parity worker failed: {result}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(count: int = 100, *, use_racket: bool = False) -> dict[str, Any]:
    module = load_generator()
    report: dict[str, Any] = {
        "schema": "b9d1d323c3ed-reference-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "canonical_rule_hash": normalized_rule_hash(canonical_row()["program_solution"]),
        "bands": {},
        "failures": [],
    }
    racket_batch: list[list[list[int]]] = []
    for band in ("easy", "medium", "hard"):
        strict = witness = changed = 0
        shapes: set[tuple[int, int]] = set()
        bbox_shapes: set[tuple[int, int]] = set()
        inputs: set[str] = set()
        for index in range(count):
            seed = 10_000 + index
            grid = module.generate(seed, index, difficulty=band)
            failures = module.self_check(deepcopy(grid))
            if failures:
                report["failures"].append({"band": band, "index": index, "self_check": failures})
                continue
            truth = intended_output(grid)
            strict += not bool(module.strict_canonical_like(deepcopy(grid)))
            witness += fixed_3x3_rival(grid) != truth
            changed += truth != grid
            info = analyze(grid)
            shapes.add((info["grid_h"], info["grid_w"]))
            bbox_shapes.add((info["bbox_h"], info["bbox_w"]))
            inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            if use_racket:
                racket_batch.append(grid)
        report["bands"][band] = {
            "draws": count,
            "strict_canonical_like": strict,
            "fixed_3x3_refutations": witness,
            "changed_outputs": changed,
            "distinct_grid_shapes": len(shapes),
            "distinct_bbox_shapes": len(bbox_shapes),
            "distinct_inputs": len(inputs),
        }
    if use_racket:
        expected = [intended_output(grid) for grid in racket_batch]
        actual = racket_outputs(racket_batch)
        report["racket_cases"] = len(actual)
        report["racket_mismatches"] = sum(a != b for a, b in zip(actual, expected))
        if report["racket_mismatches"]:
            report["failures"].append({"racket_mismatches": report["racket_mismatches"]})
    report["passed"] = not report["failures"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit(args.count, use_racket=args.racket)
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
