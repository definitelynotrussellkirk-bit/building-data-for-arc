"""Independent oracle, shortcut witness, and repeatable audit for ad4e576b99c4.

This file is reviewer tooling, not label authority.  ``--racket`` explicitly
executes the repository's canonical Racket program and never falls back to the
Python oracle.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "ad4e576b99c4"
ROOT = Path(__file__).resolve().parents[3]
HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared/runtime"))

from reviewer_support import canonical_pairs as _canonical_pairs, find_root


def load_generator(path=None):
    path = Path(path or HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_ad4e576b99c4", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    root = find_root(__file__)
    return _canonical_pairs(TASK_ID, root=root, labeled_only=True)


def geometry(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("expected a nonempty list grid")
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        raise ValueError("ragged grid")
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    sixes = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6]
    if not cells or not sixes:
        raise ValueError("missing color-5 patch or color-6 field")
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    r1, c1 = max(r for r, _ in cells), max(c for _, c in cells)
    boundary = min(r for r, _ in sixes)
    side = "left" if c0 == 0 else "right" if c1 == w - 1 else "interior"
    return {
        "h": h,
        "w": w,
        "r0": r0,
        "c0": c0,
        "r1": r1,
        "c1": c1,
        "boundary": boundary,
        "patch_height": r1 - r0 + 1,
        "patch_width": c1 - c0 + 1,
        "side": side,
    }


def observed(grid):
    g = geometry(grid)
    return {
        "grid_h": g["h"],
        "grid_w": g["w"],
        "bottom_rows": g["h"] - g["boundary"],
        "patch_width": g["patch_width"],
        "patch_height": g["patch_height"],
        "side": g["side"],
    }


def source_mask(grid):
    g = geometry(grid)
    return {
        (r - g["r0"], c - g["c0"])
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    }


def canonical_comb(height, width):
    return {
        (r, c)
        for r in range(height)
        for c in range(width)
        if r < 2 or c % 2 == 0
    }


def _render(grid, mask):
    """Direct cell-map translation, intentionally independent of production helpers."""
    g = geometry(grid)
    h, w = g["h"], g["w"]
    ph, pw = g["patch_height"], g["patch_width"]
    move_right = g["c0"] < w // 2
    max_shift = max(0, ph - 3)
    final_start = w - pw - max_shift if move_right else max_shift
    out = []
    for r in range(h):
        row = []
        shift = max(0, r - g["r0"] - 2)
        start = w - pw - shift if move_right else shift
        for c in range(w):
            if g["r0"] <= r <= g["r1"] and start <= c < start + pw:
                source_c = g["c0"] + c - start
                row.append(grid[r][source_c])
            elif r == g["boundary"] and (
                (move_right and c < final_start + pw - 1)
                or (not move_right and c > final_start)
            ):
                row.append(9)
            elif r < g["boundary"]:
                row.append(1)
            else:
                row.append(6)
        out.append(row)
    return out


def oracle_output(grid):
    return _render(grid, source_mask(grid))


def fixed_public_comb(grid):
    """Plausible wrong rule: geometry is inferred, but the public mask is memorized."""
    g = geometry(grid)
    # Build a source-shaped surrogate and apply the same cell-map geometry.
    surrogate = deepcopy(grid)
    for r in range(g["r0"], g["r1"] + 1):
        for c in range(g["c0"], g["c1"] + 1):
            surrogate[r][c] = 1
    for dr, dc in canonical_comb(g["patch_height"], g["patch_width"]):
        surrogate[g["r0"] + dr][g["c0"] + dc] = 5
    return _render(surrogate, canonical_comb(g["patch_height"], g["patch_width"]))


def witness_input():
    """Explicit 16x16 odd-tooth input on which copy-mask and fixed-comb disagree."""
    h = w = 16
    boundary = 11
    r0, c0 = 6, 0
    grid = [[1] * w for _ in range(h)]
    for r in range(boundary, h):
        grid[r] = [6] * w
    for dr in range(5):
        for dc in range(5):
            if dr < 2 or dc % 2 == 1:
                grid[r0 + dr][c0 + dc] = 5
    return grid


def racket_outputs(grids):
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    # Read the canonical authority, not the Python mirror or selected base file.
    canonical_path = ROOT / "shared/data/canonical/puzzles.jsonl"
    program = None
    with canonical_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row["program_solution"]
                break
    if not program:
        raise KeyError(TASK_ID)

    with tempfile.TemporaryDirectory(prefix="ad4e576b99c4-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8"
        )
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    outputs=[runner._apply_rule(bridge,name,g) for g in request['grids']]
    print(json.dumps(outputs))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=240)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count):
    canonical = canonical_pairs()
    assert all(oracle_output(pair["input"]) == pair["output"] for pair in canonical)
    assert all(fixed_public_comb(pair["input"]) == pair["output"] for pair in canonical)

    totals = Counter()
    by_band = {}
    racket_grids = [pair["input"] for pair in canonical] + [witness_input()]
    for band in (None, "easy", "medium", "hard"):
        row = Counter()
        shapes, axes, masks, signatures = set(), set(), set(), set()
        for index in range(count):
            seed = 910_000 + index
            sample_index = index * 7 + 1
            grid = module.generate(seed, sample_index, difficulty=band)
            issues = module.self_check(grid, difficulty=band)
            row["samples"] += 1
            row["self_check_errors"] += bool(issues)
            row["strict_errors"] += bool(module.strict_canonical_like(grid))
            row["nondeterministic"] += grid != module.generate(seed, sample_index, difficulty=band)
            row["oracle_mismatch"] += module.rule_mirror(grid) != oracle_output(grid)
            row["rival_disagreement"] += fixed_public_comb(grid) != oracle_output(grid)
            row["witness_hits"] += module.SEMANTIC_WITNESSES["noncanonical_source_mask"](grid)
            obs = observed(grid)
            shapes.add((obs["grid_h"], obs["grid_w"]))
            axes.add(tuple(obs.items()))
            masks.add(tuple(sorted(source_mask(grid))))
            signatures.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            if index < 12:
                racket_grids.append(grid)
        row.update(
            distinct_shapes=len(shapes),
            distinct_axis_tuples=len(axes),
            distinct_masks=len(masks),
            distinct_inputs=len(signatures),
        )
        by_band[str(band)] = dict(row)
        totals.update(row)

    witness = witness_input()
    return {
        "schema": "ad4e576b99c4-reference-probe-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "task_id": TASK_ID,
        "generator_version": module.VERSION,
        "generator_sha256": hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rule_hash": module.RULE_HASH,
        "canonical_pairs": len(canonical),
        "counts": dict(totals),
        "by_band": by_band,
        "witness": {
            "input": witness,
            "intended_python": oracle_output(witness),
            "fixed_public_comb": fixed_public_comb(witness),
            "differing_cells": [
                [r, c]
                for r in range(len(witness))
                for c in range(len(witness[0]))
                if oracle_output(witness)[r][c] != fixed_public_comb(witness)[r][c]
            ],
        },
        "warning": "Python geometry is supplementary evidence; use --racket for authority parity.",
    }, racket_grids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=250, help="samples per difficulty band")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true", help="require canonical Racket parity")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    report["racket"] = {"status": "not_requested", "checked": 0}
    code = int(
        report["counts"].get("self_check_errors", 0)
        or report["counts"].get("strict_errors", 0)
        or report["counts"].get("nondeterministic", 0)
        or report["counts"].get("oracle_mismatch", 0)
    )
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            expected = [oracle_output(grid) for grid in grids]
            mismatches = [i for i, (a, b) in enumerate(zip(outputs, expected)) if a != b]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            report["witness"]["intended_racket"] = outputs[len(canonical_pairs())]
            code = max(code, int(bool(mismatches)))
        except Exception as exc:
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"counts": report["counts"], "racket": report["racket"]}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
