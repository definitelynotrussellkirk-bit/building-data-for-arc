"""Replay exact controls and named-rival witnesses using the public Racket API.

Run through review.py run (or with src/shared/runtime on PYTHONPATH). The
report retains actual Racket labels and is authoring evidence, never solve input.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
from itertools import product
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "c6a453e86480"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def probe(seed, samples):
    root = find_root(__file__)
    source = root / "generators" / TASK / "generator.py"
    if not source.is_file():
        source = root / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("rank_probe_subject", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    report = {
        "schema": "c6a453e86480-distribution-probe-v1", "phase": "final",
        "task_id": TASK, "generator_sha256": digest(source),
        "probe_sha256": digest(__file__), "rule_hash": gen.RULE_HASH,
        "canonical_sha256": digest(canonical_path(root)),
        "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
        "default_sampling": {"base_seed": seed, "samples_per_band": samples,
                             "seed_expression": "base_seed + i // 12",
                             "sample_index_expression": "i % 12"},
        "failures": [], "bands": {},
        "limitation": "Finite named-rival and override evidence; not universal identifiability.",
    }
    for band in ("easy", "medium", "hard"):
        profiles, modes, hashes = Counter(), Counter(), set()
        for i in range(samples):
            grid = gen.generate(seed+i//12, i%12, difficulty=band)
            reasons = gen.self_check(grid)
            if reasons:
                report["failures"].append({"phase": "defaults", "band": band,
                                           "seed": seed+i//12, "index": i%12,
                                           "reasons": reasons, "input": grid})
            profiles[f"{len(grid)}x{len(grid[0])}:{len({v for row in grid for v in row})}"] += 1
            modes["row_two_occupied"] += int(1 in grid[2])
            modes["rank_trap"] += int(gen.SEMANTIC_WITNESSES["rank_trap"](grid))
            hashes.add(grid_hash(grid))
        report["bands"][band] = {"draws": samples, "unique_inputs": len(hashes),
                                  "profiles": dict(profiles), **modes}

    def integers(name):
        low, high = map(int, gen.AXES[name]["valid"].split(".."))
        return range(low, high+1)

    matrix_total = 0
    for band, height, width, count, kind, index in product(
            ("easy", "medium", "hard"), integers("grid_h"), integers("grid_w"),
            integers("n_blobs"), gen.PALETTE_KINDS, (0, 1)):
        overrides = {"grid_h": height, "grid_w": width,
                     "n_blobs": count, "palette_kind": kind}
        matrix_total += 1
        try:
            grid = gen.generate(seed, index, difficulty=band, **overrides)
            observed = gen.observe_overrides(grid)
            reasons = gen.self_check(grid)
            mismatch = {key: {"requested": value, "observed": observed.get(key)}
                        for key, value in overrides.items() if observed.get(key) != value}
            if reasons or mismatch:
                report["failures"].append({"phase": "matrix", "band": band,
                                           "seed": seed, "index": index,
                                           "overrides": overrides, "reasons": reasons,
                                           "mismatches": mismatch, "input": grid})
        except (ValueError, TypeError) as error:
            report["failures"].append({"phase": "matrix", "band": band, "seed": seed,
                                       "index": index, "overrides": overrides,
                                       "error": f"{type(error).__name__}: {error}"})
    report["exact_override_matrix"] = {
        "cases": matrix_total, "seed": seed, "sample_indices": [0, 1],
        "bands": ["easy", "medium", "hard"],
        "axes": {name: gen.AXES[name]["valid"] for name in
                 ("grid_h", "grid_w", "n_blobs", "palette_kind")},
    }

    canonical = canonical_pairs(TASK, root=root)
    report["canonical_rival_fit"] = {
        name: {"matches": sum(rival(pair["input"]) == pair["output"] for pair in canonical),
               "total": len(canonical)}
        for name, rival in gen.CANONICAL_SHORTCUTS.items()
    }
    cases = [{"kind": "canonical", "split": pair["split"],
              "pair_index": pair["pair_index"], "input": pair["input"],
              "expected": pair["output"]} for pair in canonical]
    first_focused = len(cases)
    for count, kind in product((3, 4), gen.PALETTE_KINDS):
        overrides = {"n_blobs": count, "palette_kind": kind}
        cases.append({"kind": "focused", "seed": seed, "sample_index": 0,
                      "difficulty": "medium", "overrides": overrides,
                      "input": gen.generate(seed, 0, difficulty="medium", **overrides)})
    permutation = {0: 0, 1: 1, **{color: 2+(color-1)%8 for color in range(2, 10)}}
    permuted_index = len(cases)
    cases.append({"kind": "legend_permutation", "source_case": first_focused,
                  "permutation": permutation,
                  "input": [[permutation[v] for v in row]
                            for row in cases[first_focused]["input"]]})
    former_start = len(cases)
    for index in range(8, 12):
        cases.append({"kind": "former_ambiguous_window", "seed": 12,
                      "sample_index": index, "difficulty": None, "overrides": {},
                      "input": gen.generate(12, index)})
    applied = Catalog(root).apply(TASK, [case["input"] for case in cases])
    report["reference_execution"] = applied
    report["reference_cases"] = cases
    report["witness_rival_checks"] = []
    for index, (case, result) in enumerate(zip(cases, applied["results"], strict=True)):
        output = result["output"]
        if gen.self_check(case["input"]) or output is None:
            report["failures"].append({"phase": "reference", "case": index,
                                       "reason": "invalid input or failed Racket execution"})
            continue
        if case["kind"] == "canonical" and output != case["expected"]:
            report["failures"].append({"phase": "canonical", "case": index})
        if case["kind"] == "focused":
            predictions = {name: rival(case["input"])
                           for name, rival in gen.LESSON_COMPETITORS.items()}
            refuted = {name: prediction != output for name, prediction in predictions.items()}
            report["witness_rival_checks"].append({"case": index, "refuted": refuted,
                                                   "rival_outputs": predictions})
            if not all(refuted.values()):
                report["failures"].append({"phase": "witness", "case": index,
                                           "survivors": [name for name, value in refuted.items() if not value]})
    expected_permuted = [[permutation[v] for v in row]
                         for row in applied["results"][first_focused]["output"]]
    report["legend_permutation_passed"] = (
        applied["results"][permuted_index]["output"] == expected_permuted)
    if not report["legend_permutation_passed"]:
        report["failures"].append({"phase": "legend_permutation"})
    report["former_window_refutations"] = {
        name: [rival(case["input"]) != result["output"] for case, result in
               zip(cases[former_start:], applied["results"][former_start:], strict=True)]
        for name, rival in gen.LESSON_COMPETITORS.items()
    }
    if any(sum(values) < 2 for values in report["former_window_refutations"].values()):
        report["failures"].append({"phase": "former_ambiguous_window"})
    report["status"] = "passed" if not report["failures"] else "failed"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261007)
    parser.add_argument("--samples", type=int, default=120)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output already exists; preserve it and select a new path")
    if args.samples < 1:
        parser.error("samples must be positive")
    report = probe(args.seed, args.samples)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"status": report["status"],
                      "matrix_cases": report["exact_override_matrix"]["cases"],
                      "reference_cases": len(report["reference_cases"]),
                      "failures": len(report["failures"]), "out": str(args.out)}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
