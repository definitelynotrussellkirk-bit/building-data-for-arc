#!/usr/bin/env python3
"""Reproduce the task's shortcut, distribution change, and Racket witnesses.

Run through the packet's run_with_racket.py wrapper. Use a new --out-dir.
An optional --baseline-generator compares a retained source file using the
same seed/index population. Distribution counts use Python mirrors; the
separately saved public apply receipt contains the actual Racket labels.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from reviewer_support import canonical_pairs, find_root

TASK = "48bda9528e71"
BANDS = ("easy", "medium", "hard")
MINIMAL_INPUT = [[4, 4, 4, 4, 8], [4, 2, 4, 4, 8], [4, 4, 8, 8, 8],
                 [4, 4, 8, 8, 8], [8, 8, 8, 8, 8]]
MINIMAL_OUTPUT = [[8, 8, 8, 8, 2], [8, 8, 8, 8, 2], [8, 8, 2, 2, 8],
                  [8, 8, 2, 8, 8], [2, 2, 8, 8, 8]]


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def grid_hash(grid):
    return digest_bytes(json.dumps(grid, separators=(",", ":")).encode())


def load_generator(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def measure(module, source, rivals, per_band):
    rows, summaries = [], []
    for population, overrides in (("default", {}),
                                  ("general_override", {"scene_profile": "general"})):
        for band in BANDS:
            counts, hashes = Counter(), set()
            for seed in range(per_band):
                index = 17 * seed + 3
                grid = module.generate(seed, index, difficulty=band, **overrides)
                errors = module.self_check(grid)
                expected = module.rule_mirror(grid)
                matches = {name: rival(grid) == expected for name, rival in rivals.items()}
                sha = grid_hash(grid)
                hashes.add(sha)
                counts["draws"] += 1
                counts["valid"] += not errors
                counts["canonical_profiles"] += module.canonical_profile_signature(grid) is not None
                for name, same in matches.items():
                    counts["refutes:" + name] += not same
                rows.append({"population": population, "band": band, "seed": seed,
                             "sample_index": index, "overrides": overrides,
                             "input_sha256": sha, "validator_errors": errors,
                             "rival_matches_python_mirror": matches})
            summaries.append({"population": population, "band": band,
                              "unique_inputs": len(hashes), **counts})
    return {"generator_sha256": digest_bytes(source.read_bytes()),
            "version": module.VERSION, "seed_range_inclusive": [0, per_band - 1],
            "sample_index_formula": "17 * seed + 3",
            "label_basis": "Python mirror; see separate Racket case receipt",
            "summaries": summaries, "draws": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--baseline-generator", type=Path)
    parser.add_argument("--per-band", type=int, default=100)
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    source = root / "generators" / TASK / "generator.py"
    current = load_generator(source, "convexification_current")
    rivals = {
        namespace + ":" + name: rival
        for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS")
        for name, rival in getattr(current, namespace, {}).items()
    }
    if not rivals:
        raise RuntimeError("current source has no declared rivals; no coverage claim is possible")
    populations = {"current": measure(current, source, rivals, args.per_band)}
    if args.baseline_generator:
        baseline = args.baseline_generator.resolve()
        old = load_generator(baseline, "convexification_baseline")
        populations["baseline"] = measure(old, baseline, rivals, args.per_band)
    write_json(out / "distribution.json", populations)

    cases, seen = [], set()
    for pair in canonical_pairs(TASK, root=root):
        sha = grid_hash(pair["input"])
        if sha not in seen:
            cases.append({"name": "canonical-" + str(len(seen)), "kind": "canonical",
                          "input": pair["input"], "expected": pair["output"]})
            seen.add(sha)
    for index, (grid, expected) in enumerate(zip(current._d4_variants(MINIMAL_INPUT),
                                                current._d4_variants(MINIMAL_OUTPUT), strict=True)):
        cases.append({"name": "minimum-d4-" + str(index), "kind": "constructed",
                      "input": grid, "expected": expected})
    retained = [[8] * 9 for _ in range(9)]
    for r in range(2, 7):
        for c in range(2, 7):
            if r < 5 or c < 5:
                retained[r][c] = 4
    retained[3][3] = 2
    cases.append({"name": "retained-audit-9x9", "kind": "constructed", "input": retained})
    for band in BANDS:
        for phase in range(4):
            cases.append({"name": band + "-phase-" + str(phase), "kind": "generated",
                          "band": band, "seed": 41, "sample_index": phase, "overrides": {},
                          "input": current.generate(41, phase, difficulty=band)})
    write_json(out / "cases.json", cases)
    write_json(out / "input.json", [case["input"] for case in cases])
    argv = [sys.executable, "-m", "arcpuzzles", "--library", str(root), "apply", TASK,
            "--input", str(out / "input.json"), "--out", str(out / "racket.json")]
    run = subprocess.run(argv, cwd=root, text=True, capture_output=True)
    write_json(out / "command.json", {"argv": argv, "cwd": str(root),
                                     "exit_code": run.returncode})
    (out / "command.log").write_text(run.stdout + run.stderr)
    if run.returncode:
        raise RuntimeError("public Racket application failed; see command.log")
    reference = json.loads((out / "racket.json").read_text())
    if reference["generator_sha256"] != digest_bytes(source.read_bytes()):
        raise RuntimeError("generator changed during witness execution")
    comparisons = []
    for case, actual in zip(cases, reference["results"], strict=True):
        grid, answer = case["input"], actual["output"]
        errors = current.self_check(grid)
        if errors or answer is None or current.rule_mirror(grid) != answer:
            raise AssertionError((case["name"], errors, actual))
        if "expected" in case and case["expected"] != answer:
            raise AssertionError("literal/canonical output mismatch: " + case["name"])
        alternatives = {}
        for name, rival in rivals.items():
            predicted = rival(grid)
            differences = [[r, c] for r in range(len(answer)) for c in range(len(answer[0]))
                           if answer[r][c] != predicted[r][c]]
            if case["kind"] == "canonical" and differences:
                raise AssertionError("declared shortcut does not fit canonical data: " + name)
            if case["kind"] == "constructed" and len(differences) != 1:
                raise AssertionError("constructed witness must have exactly one differing cell")
            alternatives[name] = {"output": predicted, "different_cells": differences}
        comparisons.append({**case, "racket_output": answer, "validator_errors": errors,
                            "rivals": alternatives})
    result = {"task_id": TASK, "generator_sha256": reference["generator_sha256"],
              "executed_rule_hash": reference["executed_rule_hash"],
              "rule_text_sha256": reference["rule_text_sha256"],
              "racket_cases": len(cases), "racket_errors": 0,
              "python_mirror_matches_racket": len(cases), "cases": comparisons}
    write_json(out / "witnesses.json", result)
    print(json.dumps({"racket_cases": len(cases), "generator_sha256": result["generator_sha256"],
                      "distributions": {name: report["summaries"] for name, report in populations.items()}},
                     indent=2))


if __name__ == "__main__":
    main()
