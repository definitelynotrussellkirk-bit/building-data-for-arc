#!/usr/bin/env python3
"""Reproduce the two findings-only audits without modifying either target.

From the packet root:
  python3 run_with_racket.py python3 generators/5da2f80a4a4f/workspace/audit_probe.py \
    --out ../checks/audits/reproduced

An exit status of zero means the recorded findings were reproduced and the
control checks passed. It does NOT mean the audited generators are issue-free.
The probe stages the two targets independently of the original working tree.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

TASKS = ("5faf9d5e3e6d", "91fd8c09b08e")


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def clockwise(grid):
    return [list(row) for row in zip(*grid[::-1])]


def cropped_body(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
             if v != 0 and (r, c) != (0, 0)]
    top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
    left, right = min(c for _, c in cells), max(c for _, c in cells)
    return [row[left:right + 1] for row in grid[top:bottom + 1]]


def transform_rule(grid, changed_code=None):
    body, key = cropped_body(grid), grid[0][0]
    if key == changed_code:
        # The episode's unseen code gets a different meaning. Every body has
        # four distinct transforms, so this cannot accidentally equal truth.
        return clockwise(body) if key == 1 else body
    return {1: body, 2: clockwise(body), 3: [row[::-1] for row in body[::-1]],
            4: [row[::-1] for row in body]}[key]


def mirror_empty_targets(grid):
    """Independent reading of the audit target's documented clean grammar."""
    result = deepcopy(grid)
    for r, row in enumerate(grid):
        anchors = [c for c, v in enumerate(row) if v == 9]
        if len(anchors) != 1:
            continue
        for c, v in enumerate(row):
            target = 2 * anchors[0] - c
            if v not in (0, 9) and 0 <= target < len(row) and row[target] == 0:
                result[r][target] = v
    return result


def clean_mirror_grammar(grid):
    for row in grid:
        anchors = [c for c, v in enumerate(row) if v == 9]
        cells = [c for c, v in enumerate(row) if v not in (0, 9)]
        if not anchors and not cells:
            continue
        if len(anchors) != 1 or not cells:
            return False
        if any(not 0 <= 2 * anchors[0] - c < len(row)
               or row[2 * anchors[0] - c] != 0 for c in cells):
            return False
    return True


def worker(args):
    from puzzle_generators.runner import _apply_rule, _open_bridge_with_rule
    from puzzle_generators.rule_wrap import wrap_rule
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source, normalized_rule_hash

    report = {"schema": "arcpuzzles-findings-audit-v1", "tasks": {},
              "unexpected_failures": [], "racket_executions": 0}

    def require(condition, name, **detail):
        if not condition:
            report["unexpected_failures"].append({"name": name, **detail})

    for task in TASKS:
        mod = importlib.import_module(f"puzzle_generators.per_puzzle.{task}.generator")
        source = canonical_rule_source(task)
        bridge, fn = _open_bridge_with_rule(wrap_rule(source))

        def execute(grid):
            report["racket_executions"] += 1
            return _apply_rule(bridge, fn, grid)

        result = {"version": mod.VERSION,
                  "generator_sha256": hashlib.sha256(Path(mod.__file__).read_bytes()).hexdigest(),
                  "rule_hash": normalized_rule_hash(source),
                  "rule_source_sha256": hashlib.sha256(source.encode()).hexdigest()}
        try:
            pairs = canonical_pairs(task)
            for index, pair in enumerate(pairs):
                require(execute(pair["input"]) == pair["output"], "canonical_output",
                        task_id=task, index=index)
            result["canonical_pairs_checked"] = len(pairs)
            if task == TASKS[0]:
                # Exact seed/index sequence of the separately saved public CLI episode.
                episode = [{"input": mod.generate(42, index)} for index in range(4)]
                for pair in episode:
                    pair["output"] = execute(pair["input"])
                    require(not mod.self_check(pair["input"]), "transform_self_check", task_id=task)
                    require(pair["output"] == transform_rule(pair["input"]),
                            "transform_oracle", task_id=task)
                demos, query = episode[:3], episode[3]
                code = query["input"][0][0]
                fits = all(transform_rule(p["input"], code) == p["output"] for p in demos)
                rival_output = transform_rule(query["input"], code)
                require(fits and rival_output != query["output"], "unseen_code_finding_missing")
                result["default_three_demo_episode"] = {
                    "seed": 42, "sample_indices": [0, 1, 2, 3],
                    "train_key_codes": [p["input"][0][0] for p in demos],
                    "query_key_code": code, "train": demos, "query": query,
                    "rival_output": rival_output, "rival_fits_all_demos": fits,
                    "declares_examples_needed": hasattr(mod, "EXAMPLES_NEEDED"),
                    "declares_lesson_identifiable": callable(getattr(mod, "lesson_identifiable", None)),
                }
                counts = {"windows": 0, "query_code_unseen": 0}
                for seed in range(12):
                    for band in ("easy", "medium", "hard"):
                        rows = [mod.generate(seed, i, difficulty=band) for i in range(40)]
                        for start in range(0, 40, 4):
                            train = {g[0][0] for g in rows[start:start + 3]}
                            counts["windows"] += 1
                            counts["query_code_unseen"] += rows[start + 3][0][0] not in train
                result["public_four_pair_stride_key_census"] = counts
                result["key_census_uses_racket"] = False
            else:
                # This scene is deliberately outside the generated clean grammar,
                # but self_check accepts it. Racket overwrites existing sources.
                conflict = [[0] * 9 for _ in range(7)]
                conflict[3] = [0, 0, 1, 0, 9, 0, 2, 0, 0]
                actual, promised = execute(conflict), mirror_empty_targets(conflict)
                errors = mod.self_check(conflict)
                require(errors == [] and actual != promised and not clean_mirror_grammar(conflict),
                        "validator_hole_finding_missing")
                result["collision_counterexample"] = {
                    "input": conflict, "self_check_reasons": errors,
                    "racket_output": actual, "documented_empty_target_output": promised,
                    "inside_default_generated_grammar": False,
                }
                base = mod.generate(42, 0)
                observed_palette = sorted({v for row in base for v in row if v not in (0, 9)})
                override_cases = {}
                for name, value in (("palette_size", 1), ("n_distinct_colors", 1),
                                    ("palette_kind", "warm"), ("texture", "cool"),
                                    ("unknown_axis", 1)):
                    drawn = mod.generate(42, 0, **{name: value})
                    override_cases[name] = {"requested": value, "identical_to_default": drawn == base}
                require(len(observed_palette) > 1 and
                        all(v["identical_to_default"] for v in override_cases.values()),
                        "inert_override_finding_missing")
                result["inert_overrides"] = {"seed": 42, "sample_index": 0, "input": base,
                                              "observed_body_palette": observed_palette,
                                              "cases": override_cases}
                try:
                    mod.generate(42, 0, grid_h=3)
                except ValueError as error:
                    result["declared_valid_grid_h_3"] = {"accepted": False, "exception": str(error)}
                else:
                    result["declared_valid_grid_h_3"] = {"accepted": True}
                    require(False, "declared_axis_range_finding_missing")
                count = 0
                for band in ("easy", "medium", "hard"):
                    for index in range(64):
                        grid = mod.generate(20261002 + index, index, difficulty=band)
                        require(clean_mirror_grammar(grid), "default_grammar", band=band, index=index)
                        require(not mod.self_check(grid), "mirror_self_check", band=band, index=index)
                        require(execute(grid) == mirror_empty_targets(grid),
                                "mirror_default_label", band=band, index=index)
                        count += 1
                result["clean_default_samples_racket_checked"] = count
        finally:
            bridge.shutdown()
        report["tasks"][task] = result
    report["findings_reproduced"] = not report["unexpected_failures"]
    dump(args.out / "report.json", report)
    print(json.dumps({"findings_reproduced": report["findings_reproduced"],
                      "unexpected_failures": len(report["unexpected_failures"]),
                      "racket_executions": report["racket_executions"]}, sort_keys=True))
    return 0 if report["findings_reproduced"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    args.out = args.out.resolve()
    if args.worker:
        return worker(args)
    repo = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repo / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    args.out.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-audit-probe-") as directory:
        stage = Path(directory)
        manifest = prepare_runtime(Catalog(repo), stage, task_ids=list(TASKS))
        dump(args.out / "runtime_manifest.json", manifest)
        shutil.copy2(__file__, stage / "audit_probe_worker.py")
        command = [sys.executable, "-E", "-s", str(stage / "audit_probe_worker.py"),
                   "--worker", "--out", str(args.out)]
        run = run_process(command, stage, timeout=180)
        run["probe_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        dump(args.out / "execution.json", run)
        print(run["stdout"], end="")
        if run["stderr"]:
            print(run["stderr"], file=sys.stderr, end="")
        return 0 if run["exit_code"] == 0 and not run["timed_out"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
