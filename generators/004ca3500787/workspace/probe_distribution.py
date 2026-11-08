"""Portable diagnostic for target-position leakage and lesson coverage.

Run with PYTHONPATH pointing to this checkout's shared/runtime (or a copied
runtime). This probe compares Python diagnostic predictions, not Racket output.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "004ca3500787"
BANDS = ("easy", "medium", "hard")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def old_target_rank(count: int, height: int, width: int) -> int:
    """Independent frozen version-4.0.0 predictor; no new helper calls."""
    if count == 4:
        return 3
    if count == 5:
        return 2
    return 1 if (height, width) in {(9, 12), (10, 13), (11, 13)} else 0


def old_prediction(gen, grid):
    # Extract components and normalize only the selected object. Do not compare
    # object shape classes in the shortcut itself.
    components = gen._components_4(grid)
    rank = old_target_rank(len(components), len(grid), len(grid[0]))
    return gen._mask(gen._d4_canonical(components[rank]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New JSON output filename")
    parser.add_argument("--seeds", type=int, default=25, help="Number of seeds beginning at zero")
    parser.add_argument("--indices", type=int, default=16, help="Number of consecutive sample indices")
    args = parser.parse_args()
    if args.seeds < 1 or args.indices < 4:
        parser.error("--seeds must be positive and --indices must be at least four")
    if args.out.exists():
        parser.error("--out must be a new file; retain previous evidence")

    root = find_root(__file__)
    source = Path(__file__).resolve().parent.parent / "generator.py"
    spec = importlib.util.spec_from_file_location("distribution_probe_target", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    rule_sources = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rule = row["program_solution"]
                rule_sources.append({
                    "variant": len(rule_sources),
                    "raw_rule_sha256": digest(rule.encode()),
                    "normalized_rule_sha256": digest(" ".join(rule.split()).encode()),
                })
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    report = {
        "schema": "004ca3500787-distribution-probe-v1",
        "task_id": TASK_ID,
        "version": gen.VERSION,
        "generator_sha256": digest(source.read_bytes()),
        "rule_sources": rule_sources,
        "comparison_basis": "Python rule_mirror diagnostic; not independent Racket execution",
        "configuration": {"seeds": args.seeds, "indices": args.indices, "bands": list(BANDS)},
        "canonical": {"usable_pairs": len(pairs)},
    }
    canonical_checks = {}
    for declaration, rivals in (("shortcuts", gen.CANONICAL_SHORTCUTS),
                                ("lesson_competitors", gen.LESSON_COMPETITORS)):
        checks = {}
        for name, rival in rivals.items():
            mismatches = [{"variant": p["variant"], "split": p["split"], "pair_index": p["pair_index"]}
                          for p in pairs if rival(p["input"]) != p["output"]]
            checks[name] = {"matches": len(pairs) - len(mismatches), "total": len(pairs),
                            "mismatches": mismatches}
        canonical_checks[declaration] = checks
    report["canonical"].update(canonical_checks)
    report["canonical"]["mirror_matches"] = sum(gen.rule_mirror(p["input"]) == p["output"] for p in pairs)

    ranks = defaultdict(Counter)
    old_hits = Counter()
    sample_totals = Counter()
    mask_cardinality = Counter()
    window_totals = Counter()
    rival_refutations = Counter()
    witness_coverage = Counter()
    failures = []
    for band in BANDS:
        for seed in range(args.seeds):
            scenes = []
            for index in range(args.indices):
                grid = gen.generate(seed, index, difficulty=band)
                analysis = gen._analysis(grid)
                errors = gen.self_check(grid, difficulty=band)
                if errors:
                    failures.append({"kind": "invalid_grid", "band": band, "seed": seed,
                                     "sample_index": index, "errors": errors})
                answer = gen.rule_mirror(grid)
                count = len(analysis["components"])
                ranks[(count, len(grid), len(grid[0]))][analysis["outlier"]["index"]] += 1
                old_hits[band] += old_prediction(gen, grid) == answer
                sample_totals[band] += 1
                scenes.append({"answer": answer,
                    "rivals": {name: rival(grid) != answer for name, rival in gen.LESSON_COMPETITORS.items()},
                    "witnesses": {name: bool(witness(grid)) for name, witness in gen.SEMANTIC_WITNESSES.items()}})
            for start in range(args.indices - 3):
                window = scenes[start:start + 4]
                window_totals[band] += 1
                mask_cardinality[len({json.dumps(s["answer"]) for s in window})] += 1
                for field, counts in (("rivals", rival_refutations), ("witnesses", witness_coverage)):
                    for name in window[0][field]:
                        hit = any(s[field][name] for s in window)
                        counts[name] += hit
                        if not hit:
                            failures.append({"kind": "missing_" + field, "name": name,
                                             "band": band, "seed": seed, "window_start": start})
    total_windows = sum(window_totals.values())
    report["default_samples"] = {"total": sum(sample_totals.values()),
        "old_position_predictor": {band: {"matches": old_hits[band], "total": sample_totals[band]} for band in BANDS},
        "actual_target_ranks_by_count_dimensions": [
            {"count": n, "height": h, "width": w, "ranks": sorted(freq),
             "frequencies": {str(rank): freq[rank] for rank in sorted(freq)}}
            for (n, h, w), freq in sorted(ranks.items())]}
    report["consecutive_four_windows"] = {
        "total": total_windows, "by_band": dict(window_totals),
        "distinct_output_mask_count_histogram": {str(k): v for k, v in sorted(mask_cardinality.items())},
        "rival_refutation_windows": {name: {"hits": hits, "total": total_windows} for name, hits in rival_refutations.items()},
        "witness_coverage_windows": {name: {"hits": hits, "total": total_windows} for name, hits in witness_coverage.items()},
    }
    report["failures"] = failures
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "generator_sha256": report["generator_sha256"],
        "version": gen.VERSION, "samples": report["default_samples"]["total"],
        "old_position_predictor": report["default_samples"]["old_position_predictor"],
        "windows": total_windows, "failures": len(failures)}, indent=2))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
