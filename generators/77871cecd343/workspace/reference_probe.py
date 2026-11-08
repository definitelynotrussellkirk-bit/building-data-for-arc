"""Independent oracle and repeatable semantic/distribution probe for 77871cecd343.

This module is test tooling.  The Python oracle is derived from the visible
geometry and is supplementary evidence; ``racket_outputs`` executes the
selected canonical Racket authority when requested and never silently falls
back to Python.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "77871cecd343"
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs as _canonical_pairs, canonical_path  # noqa: E402

QUADRANTS = ("top_left", "top_right", "bottom_left", "bottom_right")


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK, root=ROOT)


def axes(grid):
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(rows) != 1 or len(cols) != 1:
        raise ValueError(f"expected one full color-9 row/column, got {rows=} {cols=}")
    return rows[0], cols[0]


def source_cells(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]


def intended_output(grid):
    """Independent reflection oracle using only detected cross geometry."""
    sr, sc = axes(grid)
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    for r, c in source_cells(grid):
        for rr, cc in ((r, 2 * sc - c), (2 * sr - r, c), (2 * sr - r, 2 * sc - c)):
            if 0 <= rr < h and 0 <= cc < w and rr != sr and cc != sc:
                out[rr][cc] = 8
    return out


def _rival_reflection(grid, guessed_r, guessed_c):
    actual_r, actual_c = axes(grid)
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    for r, c in source_cells(grid):
        for rr, cc in (
            (r, 2 * guessed_c - c),
            (2 * guessed_r - r, c),
            (2 * guessed_r - r, 2 * guessed_c - c),
        ):
            if 0 <= rr < h and 0 <= cc < w and rr != actual_r and cc != actual_c:
                out[rr][cc] = 8
    return out


def centered_cross_rival(grid):
    """Plausible wrong rule: use the geometric center, ignoring the 9-cross."""
    return _rival_reflection(grid, len(grid) // 2, len(grid[0]) // 2)


def quadrant_offset_rival(grid):
    """Wrong rule that memorizes the retired quadrant-to-offset schedule."""
    actual_r, actual_c = axes(grid)
    center_r, center_c = len(grid) // 2, len(grid[0]) // 2
    if (actual_r, actual_c) == (center_r, center_c):
        guessed_offset = (0, 0)
    else:
        obs = observed(grid)
        guessed_offset = {
            "top_left": (0, 0),
            "top_right": (-1, 1),
            "bottom_left": (1, 0),
            "bottom_right": (0, -1),
        }[obs["source_quadrant"]]
    return _rival_reflection(
        grid,
        center_r + guessed_offset[0],
        center_c + guessed_offset[1],
    )


def observed(grid):
    sr, sc = axes(grid)
    cells = source_cells(grid)
    quadrants = {
        ("top" if r < sr else "bottom") + "_" + ("left" if c < sc else "right")
        for r, c in cells
    }
    if len(quadrants) != 1:
        raise ValueError(f"source cells do not occupy exactly one quadrant: {sorted(quadrants)}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "row_offset": sr - len(grid) // 2,
        "col_offset": sc - len(grid[0]) // 2,
        "source_quadrant": next(iter(quadrants)),
        "shape_cells": len(cells),
    }


def witness_input():
    """Exact off-center-cross counterexample to the centered-cross shortcut."""
    h = w = 9
    sr, sc = 3, 4
    grid = [[0] * w for _ in range(h)]
    for c in range(w):
        grid[sr][c] = 9
    for r in range(h):
        grid[r][sc] = 9
    for r, c in ((0, 0), (0, 1), (1, 0)):
        grid[r][c] = 1
    return grid


def racket_outputs(grids):
    """Require and execute the selected canonical Racket rule for ``grids``."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    canonical = canonical_pairs()
    program = None
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK and row.get("program_solution"):
                    program = row["program_solution"]
                    break
    if not program:
        raise FileNotFoundError(f"no canonical Racket program for {TASK}")
    assert canonical
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8"
        )
        script = r'''import json
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
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count):
    report = {
        "schema": f"{TASK}-independent-probe-v1",
        "version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "canonical": {},
        "bands": {},
    }
    pairs = canonical_pairs()
    report["canonical"] = {
        "pairs": len(pairs),
        "self_check_rejected": sum(bool(module.self_check(p["input"])) for p in pairs),
        "python_oracle_mismatches": sum(intended_output(p["input"]) != p["output"] for p in pairs),
        "center_rival_mismatches": sum(centered_cross_rival(p["input"]) != p["output"] for p in pairs),
        "quadrant_offset_rival_mismatches": sum(
            quadrant_offset_rival(p["input"]) != p["output"] for p in pairs
        ),
    }
    all_grids = []
    for band in ("easy", "medium", "hard"):
        counts = Counter()
        unique = set()
        values = {name: set() for name in ("grid_h", "grid_w", "row_offset", "col_offset", "source_quadrant", "shape_cells")}
        offsets_by_quadrant = {quadrant: set() for quadrant in QUADRANTS}
        for index in range(count):
            grid = module.generate(1009 + index, index, difficulty=band)
            all_grids.append(grid)
            counts["draws"] += 1
            counts["invalid"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(1009 + index, index, difficulty=band)
            counts["changed"] += intended_output(grid) != grid
            counts["center_rival_disagreements"] += centered_cross_rival(grid) != intended_output(grid)
            counts["quadrant_offset_rival_disagreements"] += quadrant_offset_rival(grid) != intended_output(grid)
            obs = observed(grid)
            for key, value in obs.items():
                values[key].add(value)
            offsets_by_quadrant[obs["source_quadrant"]].add((obs["row_offset"], obs["col_offset"]))
            unique.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
        report["bands"][band] = {
            **counts,
            "unique_inputs": len(unique),
            "support": {key: sorted(value) for key, value in values.items()},
            "offset_pairs_by_quadrant": {
                quadrant: [list(pair) for pair in sorted(pairs)]
                for quadrant, pairs in offsets_by_quadrant.items()
            },
        }
    return report, all_grids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    report["racket"] = {"status": "not_requested", "checked": 0}
    code = int(
        report["canonical"]["self_check_rejected"]
        or report["canonical"]["python_oracle_mismatches"]
        or any(row["invalid"] or row["nondeterministic"] for row in report["bands"].values())
    )
    if args.racket:
        try:
            selected = [p["input"] for p in canonical_pairs()] + [witness_input()] + grids[:64]
            outputs = racket_outputs(selected)
            expected = [intended_output(grid) for grid in selected]
            mismatches = [i for i, pair in enumerate(zip(outputs, expected)) if pair[0] != pair[1]]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            code = max(code, int(bool(mismatches)))
        except Exception as exc:
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            code = 2
    source = args.generator or ROOT / f"generators/{TASK}/generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
