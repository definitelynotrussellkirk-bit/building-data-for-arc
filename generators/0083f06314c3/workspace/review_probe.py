#!/usr/bin/env python3
"""Task-local, relocated verification: tests, coverage, and Racket witnesses.

From the packet root:
  python3 run_with_racket.py python3 generators/0083f06314c3/workspace/review_probe.py \
      --mode census --count 80 --out ../checks/probes/before

The normal entry prepares a standalone runtime with the repository's copier,
then copies this task's tests/workspace (new files are not in runtime_files.json).
The child uses ONLY that runtime's imports, not source/sibling checkouts.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from collections import Counter

TASK = "0083f06314c3"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def overlap_footprints(gen, grid):
    a = gen._analyze(grid)
    if a is None:
        raise ValueError("invalid grid in coverage probe")
    cells = gen._nonzero_cells(a["selected"])
    return [{(r + dr, c + dc) for dr, dc, _ in cells}
            for r, c in a["selected_matches"]]


def disjoint_rival(gen, grid):
    """Greedy row-major selection of cell-disjoint exact occurrences."""
    a = gen._analyze(grid)
    chosen = set()
    for footprint in overlap_footprints(gen, grid):
        if not footprint & chosen:
            chosen.update(footprint)
    return [[8 if (r, c) in chosen else 0 for c in range(a["board_w"])]
            for r in range(a["height"])]


def overlap_fixture(gen):
    a = [[2, 0, 0], [2, 2, 0]] + [[0, 0, 0] for _ in range(4)]
    b = [[3, 3, 3], [0, 3, 0], [0, 3, 0]] + [[0, 0, 0] for _ in range(3)]
    selector = [[2]] + [[0] for _ in range(5)]
    board = [[0] * 8 for _ in range(6)]
    for r, c in ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)):
        board[r][c] = 2
    for r, c in ((3, 5), (3, 6), (3, 7), (4, 6), (5, 6)):
        board[r][c] = 3
    return gen._assemble([a, b, selector, board])


def in_runtime(args) -> int:
    gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.mode == "tests":
        cmd = [sys.executable, "-m", "pytest", "-q", f"puzzle_generators/per_puzzle/{TASK}/tests"]
        result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out / "pytest.log").write_text(result.stdout)
        write_json(out / "pytest.json", {"argv": cmd, "cwd": str(Path.cwd()), "exit_code": result.returncode})
        print(result.stdout)
        return result.returncode

    from arc_repl.racket_bridge import RacketBridge
    from scripts.rule_smoke import load_rules, rule_application
    program = load_rules([TASK])[TASK]
    canonical = next(json.loads(s) for s in Path("data/canonical/puzzles.jsonl").open()
                     if json.loads(s).get("task_id") == TASK)
    bridge = RacketBridge(max_calls_before_restart=100)
    failures = []
    try:
        mutation = copy.deepcopy(canonical["train"][0]["input"])
        mutation[0][1] = 9
        reference = bridge.eval_text(rule_application(program, mutation))
        mirror = gen.rule_mirror(mutation)
        write_json(out / "interior9.json", {
            "input": mutation, "self_check": gen.self_check(mutation),
            "racket_output": reference, "python_mirror": mirror,
            "mirror_matches_racket": mirror == reference,
            "domain_note": "Malformed structural-color cell; after repair this must be rejected, not relabeled.",
        })
        fixture = overlap_fixture(gen)
        fixture_out = bridge.eval_text(rule_application(program, fixture))
        canonical_fit = []
        pairs = list(canonical["train"])
        test = canonical.get("test")
        if isinstance(test, dict):
            pairs.append(test)
        elif isinstance(test, list):
            pairs.extend(test)
        for pair in pairs:
            if "output" in pair:
                canonical_fit.append(disjoint_rival(gen, pair["input"]) == pair["output"])
        write_json(out / "overlap_counterexample.json", {
            "input": fixture, "self_check": gen.self_check(fixture),
            "racket_output": fixture_out, "mirror_output": gen.rule_mirror(fixture),
            "disjoint_rival_output": disjoint_rival(gen, fixture),
            "rival_fits_canonical_pairs": canonical_fit,
            "origin": "hand-built semantic witness, not claimed to be an ordinary draw",
        })
        if gen.self_check(fixture) or fixture_out != gen.rule_mirror(fixture):
            failures.append("overlap fixture domain/parity")
        if fixture_out == disjoint_rival(gen, fixture):
            failures.append("overlap fixture does not refute rival")

        counts = Counter()
        selectors = Counter()
        bands = {}
        first_overlap = None
        first_selector1 = None
        elapsed = []
        for band in ("easy", "medium", "hard"):
            bc = Counter()
            for i in range(args.count):
                seed = args.seed_base + i
                started = time.perf_counter()
                grid = gen.generate(seed, i, difficulty=band)
                elapsed.append(time.perf_counter() - started)
                a = gen._analyze(grid)
                footprints = overlap_footprints(gen, grid)
                overlapping = any(x & y for j, x in enumerate(footprints) for y in footprints[j + 1:])
                strict = not gen.strict_canonical_like(grid)
                selectors[str(a["selector"])] += 1
                info = {"seed": seed, "sample_index": i, "difficulty": band, "input": grid}
                if overlapping and first_overlap is None:
                    first_overlap = info
                if a["selector"] == 1 and first_selector1 is None:
                    first_selector1 = info
                for k, value in {"draws": 1, "strict": strict, "overlap": overlapping,
                                 "panel0": a["selected_index"] == 0,
                                 "one_selected_copy": len(footprints) == 1}.items():
                    counts[k] += int(value)
                    bc[k] += int(value)
                if args.racket_all:
                    actual = bridge.eval_text(rule_application(program, grid))
                    counts["racket_checked"] += 1
                    if actual != gen.rule_mirror(grid):
                        failures.append({**info, "kind": "mirror_mismatch", "racket_output": actual})
                if grid != gen.generate(seed, i, difficulty=band):
                    failures.append({**info, "kind": "nondeterministic"})
            bands[band] = dict(bc)
        if args.axis_corners:
            axes = tuple(gen.AXES)
            boundaries = [(6, 8), (3, 4), (8, 12), (3, 5), (1, 2), (1, 2)]
            corner_results = []
            for seed, index in ((10, 1), (11, 3)):
                for values in itertools.product(*boundaries):
                    overrides = dict(zip(axes, values))
                    grid = gen.generate(seed, index, difficulty="hard", **overrides)
                    actual = bridge.eval_text(rule_application(program, grid))
                    observed = gen.observe_overrides(grid)
                    ok = observed == overrides and not gen.self_check(grid) and actual == gen.rule_mirror(grid)
                    corner_results.append({"seed": seed, "sample_index": index,
                                           "difficulty": "hard", "overrides": overrides,
                                           "observed": observed, "passed": ok})
                    counts["override_racket_checked"] += 1
                    if not ok:
                        failures.append({"kind": "axis_corner", "input": grid,
                                         "racket_output": actual, **corner_results[-1]})
            write_json(out / "axis_corners.json", corner_results)
        for name, info in (("generated_overlap", first_overlap), ("generated_selector1", first_selector1)):
            if info:
                actual = bridge.eval_text(rule_application(program, info["input"]))
                write_json(out / (name + ".json"), {
                    **info, "racket_output": actual,
                    "mirror_output": gen.rule_mirror(info["input"]),
                    "disjoint_rival_output": disjoint_rival(gen, info["input"]),
                })
                if actual != gen.rule_mirror(info["input"]):
                    failures.append(name + " parity")
        result = {"task_id": TASK, "generator_version": gen.VERSION,
                  "generator_sha256": hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
                  "seed_base": args.seed_base, "samples_per_band": args.count,
                  "counts": dict(counts), "by_band": bands, "selectors": dict(selectors),
                  "generation_seconds_total": sum(elapsed), "generation_seconds_max": max(elapsed),
                  "failures": failures, "all_generated_draws_determinism_checked": True}
        write_json(out / "census.json", result)
        print(json.dumps(result, indent=2))
        return 1 if failures else 0
    finally:
        bridge.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("census", "tests"), default="census")
    parser.add_argument("--out", required=True)
    parser.add_argument("--count", type=int, default=80)
    parser.add_argument("--seed-base", type=int, default=1000)
    parser.add_argument("--racket-all", action="store_true")
    parser.add_argument("--axis-corners", action="store_true")
    parser.add_argument("--in-runtime", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.count <= 0:
        parser.error("--count must be positive")
    if args.in_runtime:
        return in_runtime(args)

    import shutil
    task_home = Path(__file__).resolve().parents[1]
    library = task_home.parents[1]
    if not (library / "src/arcpuzzles").is_dir():
        parser.error("Run the normal entry from a source checkout, not a copied runtime")
    sys.path.insert(0, str(library / "src"))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-review-probe-") as temporary:
        root = Path(temporary)
        prepare_runtime(Catalog(library), root, TASK)
        dest = root / "puzzle_generators/per_puzzle" / TASK
        # The task's freshly added files are not yet in the catalog mapping.
        for name in ("tests", "workspace"):
            shutil.copytree(task_home / name, dest / name, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        script = dest / "workspace/review_probe.py"
        cmd = [sys.executable, str(script), "--in-runtime", "--mode", args.mode,
               "--out", str(out), "--count", str(args.count), "--seed-base", str(args.seed_base)]
        if args.racket_all:
            cmd.append("--racket-all")
        if args.axis_corners:
            cmd.append("--axis-corners")
        env = dict(os.environ, PYTHONPATH=str(root), PYTHONNOUSERSITE="1")
        env.pop("PYTHONHOME", None)
        result = subprocess.run(cmd, cwd=root, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out / "run.log").write_text(result.stdout)
        write_json(out / "runtime.json", {
            "cwd": str(root), "argv": cmd, "exit_code": result.returncode,
            "isolated_import_root": str(root), "task_additions": ["tests", "workspace"],
            "runtime_manifest_sha256": hashlib.sha256((root / "RUNTIME_MANIFEST.json").read_bytes()).hexdigest(),
            "note": "Ordinary copied runtime; no predecessor/sibling imports. Not an OS-enforced read sandbox.",
        })
        print(result.stdout)
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
