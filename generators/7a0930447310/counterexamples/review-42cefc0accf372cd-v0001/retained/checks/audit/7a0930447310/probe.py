#!/usr/bin/env python3
"""Bounded, findings-only audit; use the public helper and separate Racket apply.

Run through review.py run, or set PYTHONPATH to repo/src:repo/shared/runtime.
Collect into a new --out directory; compare reuses it and adds comparison.json.
No generator, canonical record, rule, manifest, or assignment is modified.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK = "7a0930447310"
SOURCE_SHA256 = "5b2f1174c34341e939397e82bb77ca682850bad126539ef90129dcd05ecf33a8"
RULE_HASH = "3b7ecb6b00ec"
OVERRIDES = {"tile_size": 3, "gap": 1, "tile_rows": 3, "tile_cols": 3, "special_count": 2}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.write("\n")


def collect(root, out):
    module, source, source_hash = load_selected_generator(TASK, root=root)
    if source_hash != SOURCE_SHA256:
        raise ValueError("Audit requires the pinned issued source; bytes differ")
    pairs = canonical_pairs(TASK, root=root, labeled_only=True)
    unique, ledger = {}, []
    for pair in pairs:
        key = digest({"input": pair["input"], "output": pair["output"]})
        if key not in unique:
            unique[key] = {"input": pair["input"], "output": pair["output"], "origins": []}
        identity = {name: pair[name] for name in ("variant", "split", "pair_index")}
        unique[key]["origins"].append(identity)
        ledger.append({**identity, "pair_sha256": key, "self_check_errors": module.self_check(pair["input"])})
    canonical, inputs, expected = [], [], []
    for key, pair in unique.items():
        grid = pair["input"]
        counts = Counter(value for row in grid for value in row if value)
        canonical.append({"apply_index": len(inputs), "pair_sha256": key, "origins": pair["origins"],
                          "shape": [len(grid), len(grid[0])], "nonzero_color_counts": dict(counts),
                          "self_check_errors": module.self_check(grid)})
        inputs.append(grid)
        expected.append(pair["output"])
    failures, sampled = [], 0
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(16):
            for sample_index in range(4):
                try:
                    grid = module.generate(seed, sample_index, difficulty=difficulty)
                    errors = module.self_check(grid)
                except Exception as error:
                    grid, errors = None, [f"{type(error).__name__}: {error}"]
                sampled += 1
                if errors:
                    failures.append({"difficulty": difficulty, "seed": seed, "sample_index": sample_index,
                                     "errors": errors, "input": grid})
    overridden = []
    for seed in range(16):
        grid = module.generate(seed, 0, **OVERRIDES)
        overridden.append({"seed": seed, "sample_index": 0, "shape": [len(grid), len(grid[0])],
                           "input_sha256": digest(grid), "self_check_errors": module.self_check(grid)})
        if seed == 0:
            inputs.append(grid)
    rule = None
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rule = row["program_solution"]
                break
    if rule is None or hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12] != RULE_HASH:
        raise ValueError("Canonical rule identity differs from the issued audit target")
    report = {
        "schema": "arcpuzzles-bounded-audit-v1", "task_id": TASK,
        "generator_sha256": source_hash, "generator_version": module.VERSION,
        "catalog_rule_hash": RULE_HASH, "rule_text_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "canonical_ledger_pairs": len(pairs), "canonical_unique_pairs": len(unique),
        "canonical_rejected_pairs": sum(bool(row["self_check_errors"]) for row in ledger),
        "canonical_rejected_unique_pairs": sum(bool(row["self_check_errors"]) for row in canonical),
        "canonical_ledger_results": ledger, "canonical_unique_results": canonical,
        "default_control": {"difficulty": [None, "easy", "medium", "hard"], "seed_range": [0, 15],
                            "sample_index_range": [0, 3], "calls": sampled,
                            "failures": failures, "passes": sampled - len(failures)},
        "override_probe": {"difficulty": None, "overrides": OVERRIDES, "seed_range": [0, 15],
                           "sample_index": 0, "calls": len(overridden),
                           "rejected": sum(bool(row["self_check_errors"]) for row in overridden),
                           "results": overridden, "retained_apply_index": len(inputs) - 1},
        "scope_limits": ["No source repair; no complete battery, lesson census, or shortcut proof.",
                         "self_check rejection and generator/validator disagreement are measured separately from Racket correctness."],
    }
    out.mkdir(parents=True, exist_ok=False)
    write(out / "apply-inputs.json", inputs)
    write(out / "canonical-expected.json", expected)
    write(out / "summary.json", report)
    print(json.dumps({key: report[key] for key in ("generator_sha256", "catalog_rule_hash",
                     "canonical_ledger_pairs", "canonical_unique_pairs", "canonical_rejected_pairs",
                     "canonical_rejected_unique_pairs")}))
    print(json.dumps({"default_passes": report["default_control"]["passes"],
                      "default_calls": sampled, "override_rejected": report["override_probe"]["rejected"],
                      "override_calls": len(overridden)}))


def compare(out, racket_path):
    record = json.loads(racket_path.read_text())
    expected = json.loads((out / "canonical-expected.json").read_text())
    inputs = json.loads((out / "apply-inputs.json").read_text())
    if record["generator_sha256"] != SOURCE_SHA256 or record["executed_rule_hash"] != RULE_HASH:
        raise ValueError("Racket receipt has different source/rule bytes")
    if len(record["results"]) != len(inputs):
        raise ValueError("Racket result count differs from the retained request")
    results = []
    for index, (grid, result) in enumerate(zip(inputs, record["results"])):
        if result["input"] != grid:
            raise ValueError("Racket receipt input differs from retained request")
        results.append({"apply_index": index, "error": result["error"],
                        "canonical_label_matches": result["output"] == expected[index] if index < len(expected) else None,
                        "input_sha256": result["input_sha256"], "output_sha256": result["output_sha256"]})
    comparison = {"task_id": TASK, "generator_sha256": SOURCE_SHA256, "catalog_rule_hash": RULE_HASH,
                  "canonical_compared": len(expected),
                  "canonical_matching": sum(row["canonical_label_matches"] is True for row in results),
                  "racket_errors": sum(bool(row["error"]) for row in results), "results": results}
    write(out / "comparison.json", comparison)
    print(json.dumps(comparison))
    return 0 if comparison["canonical_matching"] == len(expected) and not comparison["racket_errors"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--compare-racket", type=Path)
    args = parser.parse_args()
    if args.compare_racket:
        return compare(args.out, args.compare_racket)
    collect(args.root or find_root(__file__), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
