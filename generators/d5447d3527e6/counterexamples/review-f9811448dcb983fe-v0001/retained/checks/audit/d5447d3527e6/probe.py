#!/usr/bin/env python3
"""Findings-only census and selected-rule audit for d5447d3527e6."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

TASK = "d5447d3527e6"
BANDS = ("easy", "medium", "hard")


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def support_module():
    for parent in Path(__file__).resolve().parents:
        for location in (parent / "shared/runtime", parent / "repo/shared/runtime", parent):
            if (location / "reviewer_support.py").is_file():
                sys.path.insert(0, str(location))
                import reviewer_support
                return reviewer_support
    raise FileNotFoundError("Local reviewer_support.py not found")


def runs(grid):
    found = []
    for col in range(len(grid[0])):
        row = 0
        while row < len(grid):
            if grid[row][col] != 5:
                row += 1
                continue
            start = row
            while row < len(grid) and grid[row][col] == 5:
                row += 1
            found.append((start, col, row - start))
    return found


def mirror(grid, whitelist=False, require_multiple=False):
    result = [row[:] for row in grid]
    targets = [(row, col, length) for row, col, length in runs(grid)
               if length >= 3 and length % 2]
    if require_multiple and len(targets) < 2:
        return result
    for row, col, length in targets:
        if not whitelist or length in (3, 5):
            result[row + length // 2][col] = 2
    return result


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=10007)
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    if args.out.exists():
        parser.error("--out must be a new file")
    support = support_module()
    root = support.find_root(__file__)
    module, source, source_sha = support.load_selected_generator(TASK, root=root)
    pairs = support.canonical_pairs(TASK, root=root, labeled_only=True)
    canonical_profiles = sorted({profile(pair["input"]) for pair in pairs})
    bounds = [(min(p[i] for p in canonical_profiles), max(p[i] for p in canonical_profiles))
              for i in range(3)]
    settings = {"seed": args.seed, "count_per_band": args.count,
                "sample_index_start": 0, "bands": list(BANDS)}
    report = {"schema": "d5447d3527e6-adversarial-audit-v1", "task_id": TASK,
              "generator_sha256": source_sha,
              "canonical_file_sha256": hashlib.sha256(support.canonical_path(root).read_bytes()).hexdigest(),
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "settings": settings, "settings_sha256": digest(settings),
              "canonical_profiles": canonical_profiles, "canonical_envelope": bounds,
              "canonical": [], "per_band": {}, "failures": [],
              "measurement_basis": "Census agreement uses the independent Python run-center mirror; authoritative Racket is separately executed on the three canonical inputs, one hand-built counterexample, and each band's index-0 draw."}
    for pair in pairs:
        grid = pair["input"]
        report["canonical"].append({"split": pair["split"], "pair_index": pair["pair_index"],
                                    "input_sha256": digest(grid), "profile": profile(grid),
                                    "run_lengths": [length for _, _, length in runs(grid)],
                                    "target_count": sum(length >= 3 and length % 2 for _, _, length in runs(grid)),
                                    "self_check": module.self_check(grid),
                                    "mirror_matches_stored_output": mirror(grid) == pair["output"],
                                    "whitelist_matches_stored_output": mirror(grid, whitelist=True) == pair["output"],
                                    "multiple_target_gate_matches_stored_output": mirror(grid, require_multiple=True) == pair["output"]})
    first_inputs = []
    pooled = set()
    for band in BANDS:
        shapes, lengths, targets = Counter(), Counter(), Counter()
        unique = set()
        exact = envelope = whitelist_fit = threshold_fit = accepted = 0
        population_hash = hashlib.sha256()
        first = None
        for index in range(args.count):
            try:
                grid = module.generate(args.seed, index, difficulty=band)
                errors = module.self_check(grid, difficulty=band)
                if errors:
                    raise ValueError(f"self_check: {errors}")
                run_data = runs(grid)
                inp_hash = digest(grid)
                unique.add(inp_hash)
                pooled.add(inp_hash)
                population_hash.update(json.dumps([band, args.seed, index, inp_hash], separators=(",", ":")).encode() + b"\n")
                shapes[f"{len(grid)}x{len(grid[0])}"] += 1
                lengths.update(length for _, _, length in run_data)
                target_count = sum(length >= 3 and length % 2 for _, _, length in run_data)
                targets[target_count] += 1
                exact += profile(grid) in canonical_profiles
                envelope += all(lo <= value <= hi for value, (lo, hi) in zip(profile(grid), bounds))
                whitelist_fit += mirror(grid, whitelist=True) == mirror(grid)
                threshold_fit += mirror(grid, require_multiple=True) == mirror(grid)
                accepted += 1
                if index == 0:
                    first = {"seed": args.seed, "sample_index": index, "input_sha256": inp_hash,
                             "profile": profile(grid), "run_data": run_data,
                             "input_rows": ["".join(map(str, row)) for row in grid]}
                    first_inputs.append(grid)
            except Exception as exc:
                report["failures"].append({"difficulty": band, "seed": args.seed,
                                           "sample_index": index, "exception": type(exc).__name__,
                                           "message": str(exc)[:600]})
        report["per_band"][band] = {"attempted": args.count, "accepted": accepted,
                                    "unique_inputs": len(unique), "population_sha256": population_hash.hexdigest(),
                                    "shape_histogram": dict(sorted(shapes.items())),
                                    "run_length_histogram": dict(sorted(lengths.items())),
                                    "target_count_histogram": dict(sorted(targets.items())),
                                    "exact_canonical_profile_hits": exact,
                                    "canonical_envelope_hits": envelope,
                                    "whitelist_mirror_agreements": whitelist_fit,
                                    "multiple_target_gate_mirror_agreements": threshold_fit,
                                    "first_draw": first}
    witness = [[0] * 7 for _ in range(9)]
    for row in range(1, 8):
        witness[row][2] = 5
    for row in range(2, 6):
        witness[row][5] = 5
    report["length7_counterexample"] = {"input": witness, "input_sha256": digest(witness),
                                        "profile": profile(witness), "self_check": module.self_check(witness),
                                        "mirror_output": mirror(witness),
                                        "whitelist_output": mirror(witness, whitelist=True)}
    inputs = [pair["input"] for pair in pairs] + [witness] + first_inputs
    save(args.out.parent / "authority-inputs.json", {"inputs": inputs})
    sys.path.insert(0, str(root / "src"))
    from arcpuzzles import Catalog
    authority = Catalog(root).apply(TASK, inputs, reference="canonical", check_generator_domain=True, timeout=120)
    authority["reproducer"] = {"script": str(Path(__file__).resolve()), "settings": settings,
                               "cwd": str(Path.cwd()), "operation": "Catalog(root).apply(task, inputs, reference='canonical', check_generator_domain=True, timeout=120)"}
    save(args.out.parent / "racket.json", authority)
    report["authority"] = {"executed_rule_hash": authority["executed_rule_hash"],
                           "catalog_rule_hash": authority["catalog_rule_hash"],
                           "rule_hash_matches_catalog": authority["rule_hash_matches_catalog"],
                           "generator_sha256": authority["generator_sha256"],
                           "receipt_sha256": hashlib.sha256((args.out.parent / "racket.json").read_bytes()).hexdigest(),
                           "input_count": len(inputs),
                           "all_match_mirror": all(item["output"] == mirror(grid) for grid, item in zip(inputs, authority["results"], strict=True)),
                           "length7_differs_from_whitelist": authority["results"][len(pairs)]["output"] != mirror(witness, whitelist=True)}
    report["pooled_unique_inputs"] = len(pooled)
    report["source_unchanged"] = hashlib.sha256(source.read_bytes()).hexdigest() == source_sha
    report["status"] = "reproduced" if not report["failures"] and report["source_unchanged"] and report["authority"]["all_match_mirror"] and report["authority"]["length7_differs_from_whitelist"] else "verification_failed"
    save(args.out, report)
    print(json.dumps({"status": report["status"], "generator_sha256": source_sha,
                      "sampled_inputs": len(pooled), "authoritative_inputs": len(inputs),
                      "out": str(args.out.resolve())}, sort_keys=True))
    return 0 if report["status"] == "reproduced" else 1


if __name__ == "__main__":
    raise SystemExit(main())
