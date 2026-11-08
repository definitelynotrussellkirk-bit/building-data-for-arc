#!/usr/bin/env python3
"""Reproducible, task-local tests and shortcut/oracle census in a copied runtime.

Run from any directory. RACKET_PATH or a racket on PATH is required for census.
New task tests are staged explicitly because the static runtime manifest does
not automatically discover files added by a reviewer. No source tree is edited.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

TASK = "54a83e6bbc20"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def decode(grid):
    cuts, candidates = [], []
    for top in range(1, len(grid), 4):
        rows = grid[top:top + 3]
        cuts.append(tuple(sum(v == 8 for v in row[:5]) for row in rows))
        color = next(v for row in rows for v in row[7:] if v != 7)
        candidates.append((color, tuple(5 - sum(v == color for v in row[7:]) for row in rows)))
    return cuts, candidates


def rival(grid, omitted):
    """Greedy two-row complement match, ignoring one complete row's shape."""
    cuts, candidates = decode(grid)
    remaining = list(range(len(cuts)))
    out = [[7] * 11 for _ in grid]
    for i, cut in enumerate(cuts):
        selected = next((j for j in remaining if all(cut[r] == candidates[j][1][r]
                        for r in range(3) if r != omitted)), remaining[0])
        remaining.remove(selected)
        color = candidates[selected][0]
        for r, n in enumerate(cut):
            out[1 + 4 * i + r][:5] = [8] * n + [color] * (5 - n)
    return out


def expected_output(grid):
    cuts, candidates = decode(grid)
    by_cut = {cut: color for color, cut in candidates}
    out = [[7] * 11 for _ in grid]
    for i, cut in enumerate(cuts):
        for r, n in enumerate(cut):
            out[1 + 4 * i + r][:5] = [8] * n + [by_cut[cut]] * (5 - n)
    return out


def make_grid(cuts, order=None):
    n = len(cuts)
    grid = [[7] * 11 for _ in range(4 * n + 1)]
    order = list(range(n)) if order is None else order
    for i, cut in enumerate(cuts):
        for r, length in enumerate(cut):
            grid[1 + 4 * i + r][:length] = [8] * length
    for slot, i in enumerate(order):
        for r, length in enumerate(cuts[i]):
            grid[1 + 4 * slot + r][6 + length:] = [i + 1] * (5 - length)
    return grid


def first_width(a, b):
    """Independent finite geometry model of the authority's first placement.

    Negative shifts cannot have bbox origin (0,0). A disjoint union contained
    in its bounding box fills it exactly iff cardinality equals bounding area.
    This mirrors the authority's dr-then-dc search order, not target-width 5.
    """
    left = {(r, c) for r, n in enumerate(a) for c in range(n)}
    lo = min(b)
    right = {(r, c - lo) for r, n in enumerate(b) for c in range(n, 5)}
    size = len(left) + len(right)
    for dr in range(6):
        for dc in range(8):
            w = max(max(a), dc + 5 - lo)
            if (3 + dr) * w != size:
                continue
            if not left.intersection((r + dr, c + dc) for r, c in right):
                return w
    return None


def width_sweep(gen):
    shapes = list(itertools.product(range(1, 5), repeat=3))
    matrix = [[first_width(a, b) for b in shapes] for a in shapes]
    report = {}
    for n in (2, 3, 4):
        total = 0
        bad = []
        for group in itertools.combinations(range(64), n):
            total += 1
            counts = Counter(matrix[i][j] for i in group for j in group if matrix[i][j] is not None)
            unsafe = any(count >= counts[5] for w, count in counts.items() if w != 5)
            if unsafe:
                cuts = [shapes[i] for i in group]
                bad.append({"cuts": cuts, "width_counts": dict(counts),
                            "validator_errors": gen.self_check(make_grid(cuts))})
        report[str(n)] = {"cutsets": total, "non_unique_width_five_modes": bad,
                          "unsafe_count": len(bad)}
    return report


def census(args):
    # Worker has no original repository on its import path.
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source
    from scripts.generator_semantic_gate import _RuleOracle
    gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
    source_hash = hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest()
    rule_hash = hashlib.sha256(canonical_rule_source(TASK).encode()).hexdigest()
    oracle = _RuleOracle(TASK)
    if not oracle.ready:
        raise RuntimeError(oracle.error)
    out = Path(args.out)
    failures, witnesses = [], {}
    report = {"task_id": TASK, "phase": args.phase, "generator_sha256": source_hash,
              "rule_source_sha256": rule_hash, "runtime_cwd": str(Path.cwd()), "command": [sys.executable, *sys.argv],
              "seed_base": args.seed_base, "per_band": args.per_band,
              "seed_formula": "seed_base + i; sample_index=i, for each difficulty",
              "oracle_sample_indices_per_band": list(range(min(args.oracle_samples, args.per_band))),
              "bands": {}, "failures": failures}
    canonical = canonical_pairs(TASK)
    report["canonical_rivals"] = {
        f"ignore_row_{r}": {"train_matches": sum(rival(p["input"], r) == p["output"] for p in canonical[:3]),
                           "train_total": 3, "all_pairs_matches": sum(rival(p["input"], r) == p["output"] for p in canonical),
                           "all_pairs_total": len(canonical)} for r in range(3)}
    oracle_total = 0
    started = time.monotonic()
    try:
        for band in ("easy", "medium", "hard"):
            inputs, outputs, shapes = set(), set(), set()
            areas, scene_profiles, shape_profiles = Counter(), Counter(), Counter()
            scores = Counter()
            equal_area = 0
            oracle_matches = 0
            for i in range(args.per_band):
                seed = args.seed_base + i
                grid = gen.generate(seed, i, difficulty=band)
                before = digest(grid)
                errors = gen.self_check(grid)
                if errors:
                    failures.append({"stage": "self_check", "band": band, "seed": seed, "sample_index": i,
                                     "errors": errors, "input": grid})
                expected = expected_output(grid)
                mirror = gen.rule_mirror(grid)
                if mirror != expected:
                    failures.append({"stage": "mirror", "input": grid, "expected": expected, "actual": mirror})
                if gen.generate(seed, i, difficulty=band) != grid or digest(grid) != before:
                    failures.append({"stage": "determinism_or_mutation", "seed": seed, "sample_index": i})
                cuts, _ = decode(grid)
                shapes.update(cuts)
                areas.update(sum(c) for c in cuts)
                equal_area += len({sum(c) for c in cuts}) == 1
                observed = gen.observe_overrides(grid)
                scene_profiles[str(observed.get("scene_profile"))] += 1
                shape_profiles[str(observed.get("shape_profile", "not-declared"))] += 1
                inputs.add(digest(grid)); outputs.add(digest(expected))
                actual = None
                if i < args.oracle_samples:
                    actual, error = oracle.apply(grid); oracle_total += 1
                    if error or actual != expected:
                        failures.append({"stage": "racket", "band": band, "seed": seed, "sample_index": i,
                                         "error": error, "input": grid, "actual": actual, "expected": expected})
                    else:
                        oracle_matches += 1
                for r in range(3):
                    name = f"ignore_row_{r}"
                    alternative = rival(grid, r)
                    scores[name] += alternative == expected
                    if alternative != expected and name not in witnesses:
                        if actual is None:
                            actual, error = oracle.apply(grid); oracle_total += 1
                            if error or actual != expected:
                                failures.append({"stage": "witness_oracle", "error": error, "input": grid,
                                                 "actual": actual, "expected": expected})
                        witnesses[name] = {"task_id": TASK, "generator_sha256": source_hash,
                            "rule_source_sha256": rule_hash, "seed": seed, "sample_index": i,
                            "difficulty": band, "overrides": {}, "input": grid,
                            "actual_racket_output": actual, "rival_name": name,
                            "rival_output": alternative, "validator_errors": errors,
                            "command": report.get("command"), "runtime_cwd": str(Path.cwd())}
                for name, fn in gen.SEMANTIC_RIVALS.items():
                    if name.startswith("ignore_row_"):
                        continue
                    scores[name] += fn(grid) == expected
            report["bands"][band] = {"samples": args.per_band, "unique_inputs": len(inputs),
                "unique_outputs": len(outputs), "distinct_cut_vectors": len(shapes), "cut_vectors": sorted(shapes),
                "cyan_area_counts": dict(areas), "equal_area_scenes": equal_area,
                "scene_profiles": dict(scene_profiles), "shape_profiles": dict(shape_profiles),
                "rival_matches": dict(scores), "oracle_matches": oracle_matches}
            print(f"{band}: {args.per_band} draws, {len(shapes)} cuts, rivals {dict(scores)}", flush=True)
        # All 64 individual cuts in two-piece scenes, each checked by real Racket.
        basis_matches = 0
        for cut in itertools.product(range(1, 5), repeat=3):
            other = (1, 1, 1) if cut != (1, 1, 1) else (4, 4, 4)
            grid = make_grid([cut, other], [1, 0])
            expected = expected_output(grid)
            actual, error = oracle.apply(grid); oracle_total += 1
            if error or actual != expected:
                failures.append({"stage": "64_shape_oracle_basis", "cuts": [cut, other], "error": error,
                                 "input": grid, "actual": actual, "expected": expected})
            else:
                basis_matches += 1
        report["shape_basis_racket"] = {"matches": basis_matches, "total": 64}
        if args.width_sweep:
            report["width_sweep"] = width_sweep(gen)
            # Retain real oracle behavior for every unsafe cutset in two orders.
            unsafe = []
            for row in report["width_sweep"]["4"]["non_unique_width_five_modes"]:
                for order in (list(range(4)), list(reversed(range(4)))):
                    grid = make_grid(row["cuts"], order)
                    actual, error = oracle.apply(grid); oracle_total += 1
                    unsafe.append({"task_id": TASK, "generator_sha256": source_hash,
                        "rule_source_sha256": rule_hash, "cuts": row["cuts"], "candidate_order": order,
                        "input": grid, "actual_racket_output": actual, "racket_error": error,
                        "intended_width_five_output": expected_output(grid), "validator_errors": gen.self_check(grid),
                        "outside_proposed_distribution": True})
            write(out / "unsafe_width_examples.json", unsafe)
        for name, witness in witnesses.items():
            write(out / f"witness_{name}.json", witness)
        report["witness_paths"] = [f"witness_{n}.json" for n in sorted(witnesses)]
        report["oracle_calls"] = oracle_total
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        write(out / "census.json", report)
    finally:
        oracle.close()
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=("tests", "census"), default="census")
    parser.add_argument("--out", required=True)
    parser.add_argument("--phase", default="final")
    parser.add_argument("--runtime", help="New, empty standalone runtime directory")
    parser.add_argument("--per-band", type=int, default=120)
    parser.add_argument("--oracle-samples", type=int, default=20)
    parser.add_argument("--seed-base", type=int, default=1000)
    parser.add_argument("--width-sweep", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.per_band < 1 or args.oracle_samples < 0:
        parser.error("per-band must be positive and oracle-samples nonnegative")
    if args.worker:
        return census(args)
    task_home = Path(__file__).resolve().parents[1]
    repo = task_home.parents[1]
    sys.path.insert(0, str(repo / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    runtime = Path(args.runtime).resolve() if args.runtime else Path(tempfile.mkdtemp(prefix="arcpuzzles-task-review-"))
    receipt = prepare_runtime(Catalog(repo), runtime, TASK)
    shutil.copy2(__file__, runtime / "task_review.py")
    for test in (task_home / "tests").glob("test_*.py"):
        shutil.copy2(test, runtime / "tests" / test.name)
    env = dict(os.environ)
    env.pop("PYTHONPATH", None); env.pop("PYTHONHOME", None)
    env["PYTHONNOUSERSITE"] = "1"
    if args.action == "tests":
        command = [sys.executable, "-m", "pytest", "-q"] + [
            "tests/" + p.name for p in sorted((task_home / "tests").glob("test_*.py"))]
    else:
        command = [sys.executable, "task_review.py", "--worker", "--out", str(out), "--phase", args.phase,
                   "--per-band", str(args.per_band), "--oracle-samples", str(args.oracle_samples),
                   "--seed-base", str(args.seed_base)]
        if args.width_sweep:
            command.append("--width-sweep")
    started = time.monotonic()
    result = subprocess.run(command, cwd=runtime, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out / (args.action + ".log")).write_text(result.stdout)
    print(result.stdout, end="")
    write(out / "run.json", {"task_id": TASK, "phase": args.phase, "command": command,
        "runtime_cwd": str(runtime), "exit_code": result.returncode,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "generator_sha256": hashlib.sha256((task_home / "generator.py").read_bytes()).hexdigest(),
        "staged_source_files": [r for r in receipt["files"] if r["library_path"].startswith(f"generators/{TASK}/")],
        "test_files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((task_home / "tests").glob("test_*.py"))}})
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
