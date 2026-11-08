#!/usr/bin/env python3
"""Run task tests and a source-bound semantic census in a relocated runtime.

From the packet root:
  python3 run_with_racket.py python3 generators/f16508733f0a/workspace/review_checks.py \
      --out ../checks/focused-final --phase final --seeds 16

The worker imports only copied runtime sources. It iterates the actual rival
registries, checks their canonical fit, and covers every cyclic lesson start.
Two explicitly labelled diagnostic rivals allow reproduction on version 2.0.0,
which did not declare colour-agreement or closure competitors. No solve episode
or masked query is read. A failed census retains all failures, not just totals.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

TASK_ID = "f16508733f0a"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def majority_probe(grid):
    output = copy.deepcopy(grid)
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            cells = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
            values = [grid[y][x] for y, x in cells]
            nz = [v for v in values if v]
            if len(nz) == 3:
                colour = min(set(nz), key=lambda v: (-nz.count(v), v))
                y, x = cells[values.index(0)]
                output[y][x] = colour
    return output


def worker(args):
    sys.path.insert(0, str(Path.cwd()))
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source, normalized_rule_hash
    from scripts.rule_smoke import rule_application
    gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
    source = canonical_rule_source(TASK_ID)
    failures = []
    result = dict(task_id=TASK_ID, phase=args.phase, runtime_directory=str(Path.cwd()),
                  generator_sha256=sha(gen.__file__), rule_sha256=hashlib.sha256(source.encode()).hexdigest(),
                  normalized_rule_hash=normalized_rule_hash(source), seed_range=[0, args.seeds - 1],
                  sample_index_range=[0, 8], bands=["easy", "medium", "hard"], failures=failures)
    started = time.monotonic()
    test = subprocess.run([sys.executable, "-m", "pytest", "-q", "review_tests"],
                          capture_output=True, text=True)
    (args.out / "pytest.log").write_text(test.stdout + test.stderr)
    result["pytest_exit_code"] = test.returncode
    if args.tests_only:
        result["elapsed_seconds"] = time.monotonic() - started
        (args.out / "report.json").write_text(json.dumps(result, indent=2) + "\n")
        return test.returncode

    def closure_probe(grid):
        current = copy.deepcopy(grid)
        for _ in range(len(grid) * len(grid[0]) + 1):
            updated = gen.rule_mirror(current)
            if updated == current:
                return current
            current = updated
        raise RuntimeError("Completion failed to converge")

    declared = {name: getattr(gen, name, {}) for name in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")}
    rivals = {}
    for registry in declared.values():
        rivals.update(registry)
    probes = {"ignore_colour_agreement": majority_probe, "repeat_until_stable": closure_probe}
    result["diagnostic_only_rivals"] = sorted(set(probes) - set(rivals))
    for name, fn in probes.items():
        rivals.setdefault(name, fn)
    pairs = canonical_pairs(TASK_ID)
    usable = [p for p in pairs if p.get("input") and p.get("output")]
    result["canonical_pairs"] = len(usable)
    result["registry_names"] = {name: sorted(value) for name, value in declared.items()}
    result["canonical_fit"] = {
        name: sum(fn(p["input"]) == p["output"] for p in usable) for name, fn in rivals.items()}
    for name in declared["CANONICAL_SHORTCUTS"]:
        if result["canonical_fit"][name] != len(usable):
            failures.append({"kind": "false_canonical_shortcut", "rival": name})
    result["rival_refutations"] = {name: 0 for name in rivals}
    result["rival_lesson_witnesses"] = {name: 0 for name in rivals}
    result["first_witnesses"] = {}
    result["racket_checked"] = 0
    result["racket_mismatches"] = 0
    result["generated"] = 0
    result["lesson_windows"] = 0
    result["lesson_policy"] = "Same seed and band; sequential indices; 3 demos + next query; all six cyclic starts. Overlapping windows are not independent."
    unique = set()
    bridge = None
    if not args.no_racket:
        from arc_repl.racket_bridge import RacketBridge
        bridge = RacketBridge(max_calls_before_restart=500)
    try:
        for seed in range(args.seeds):
            for band in result["bands"]:
                batch = []
                for index in range(9):
                    locator = dict(seed=seed, sample_index=index, difficulty=band, overrides={})
                    try:
                        grid = gen.generate(seed, index, difficulty=band)
                        errors = gen.self_check(grid) + gen.strict_canonical_like(grid)
                        if errors:
                            failures.append(dict(kind="validator", **locator, input=grid, errors=errors))
                        output = gen.rule_mirror(grid)
                        if bridge is not None:
                            actual = bridge.eval_text(rule_application(source, grid))
                            result["racket_checked"] += 1
                            if actual != output:
                                result["racket_mismatches"] += 1
                                failures.append(dict(kind="racket_mismatch", **locator, input=grid,
                                                     actual=actual, mirror=output))
                            output = actual
                        batch.append({"input": grid, "output": output})
                        unique.add(json.dumps(grid, separators=(",", ":")))
                        result["generated"] += 1
                        for name, rival in rivals.items():
                            other = rival(grid)
                            if other != output:
                                result["rival_refutations"][name] += 1
                                result["first_witnesses"].setdefault(name, dict(**locator, input=grid,
                                      output=output, output_authority="racket" if bridge else "python_mirror",
                                      rival_output=other))
                    except Exception as exc:
                        failures.append(dict(kind="generation_or_execution", **locator, exception=repr(exc)))
                        batch.append(None)
                for start in range(6):
                    window = batch[start:start + 4]
                    if any(p is None for p in window):
                        continue
                    demos, query = window[:3], window[3]
                    result["lesson_windows"] += 1
                    reasons = gen.lesson_identifiable(demos, query)
                    if reasons:
                        failures.append(dict(kind="lesson_hook", seed=seed, difficulty=band, start=start, reasons=reasons))
                    for name, rival in rivals.items():
                        refuted = any(rival(p["input"]) != p["output"] for p in demos)
                        result["rival_lesson_witnesses"][name] += int(refuted)
                        if not refuted and rival(query["input"]) != query["output"]:
                            failures.append(dict(kind="surviving_rival_changes_query", seed=seed, difficulty=band,
                                                 start=start, rival=name, query=query))
    finally:
        if bridge is not None:
            bridge.close()
    result["unique_inputs"] = len(unique)
    result["elapsed_seconds"] = time.monotonic() - started
    result["status"] = "pass" if not failures and test.returncode == 0 else "fail"
    (args.out / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "generated", "unique_inputs", "lesson_windows", "racket_checked", "racket_mismatches", "rival_refutations", "rival_lesson_witnesses")}))
    return 0 if result["status"] == "pass" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--phase", default="final")
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--no-racket", action="store_true")
    parser.add_argument("--tests-only", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.worker:
        return worker(args)
    repo = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repo / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-focused-") as directory:
        runtime = Path(directory)
        manifest = prepare_runtime(Catalog(repo), runtime, TASK_ID)
        shutil.copytree(repo / "generators" / TASK_ID / "tests", runtime / "review_tests")
        shutil.copy2(__file__, runtime / "review_checks.py")
        command = [sys.executable, "review_checks.py", "--worker", "--out", str(args.out),
                   "--phase", args.phase, "--seeds", str(args.seeds)]
        if args.no_racket:
            command.append("--no-racket")
        if args.tests_only:
            command.append("--tests-only")
        run = run_process(command, runtime, timeout=1200)
        run["cwd"] = str(runtime)
        run["generator_sha256"] = next(x["sha256"] for x in manifest["files"]
                                       if x["library_path"] == f"generators/{TASK_ID}/generator.py")
        (args.out / "execution.json").write_text(json.dumps(run, indent=2) + "\n")
        print(run["stdout"])
        print(run["stderr"], file=sys.stderr)
        return run["exit_code"] if not run["timed_out"] else 124


if __name__ == "__main__":
    raise SystemExit(main())
