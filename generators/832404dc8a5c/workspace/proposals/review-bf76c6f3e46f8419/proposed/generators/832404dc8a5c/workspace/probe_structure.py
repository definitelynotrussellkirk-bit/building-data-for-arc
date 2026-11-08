#!/usr/bin/env python3
"""Input-only reproduction of defect_lint's exact structural-count cohort.

Run through review.py run with --out ../checks/structural-warning.json.
No generator, canonical rule, threshold, or gate is changed; no labels are made.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import review_diagnostics
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "832404dc8a5c"
BANDS = ("easy", "medium", "hard")


def sha(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def describe(grid):
    components = review_diagnostics.objects(grid)
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(1, h - 1) if grid[r][0] == grid[r][-1] == 4]
    cols = [c for c in range(1, w - 1) if grid[0][c] == grid[-1][c] == 4]
    return {"height": h, "width": w, "object_count": len(components),
            "component_counts_by_color": dict(sorted(Counter(c for c, _ in components).items())),
            "anchored_rows": rows, "anchored_columns": cols,
            "has_adjacent_lanes": any(b == a + 1 for axis in (rows, cols) for a, b in zip(axis, axis[1:])),
            "input_sha256": sha(json.dumps(grid, separators=(",", ":")))}


def summarize(rows, canonical_counts):
    counts = sorted({r["object_count"] for r in rows})
    return {"draws": len(rows), "exact_counts": counts,
            "minimum": min(counts), "maximum": max(counts),
            "canonical_exact_intersection": sorted(set(counts) & canonical_counts),
            "adjacent_lane_draws": sum(r["has_adjacent_lanes"] for r in rows)}


def collect_report(root, baseline=None):
    gen, source, source_hash = load_selected_generator(TASK_ID, root=root)
    pairs = [p for p in canonical_pairs(TASK_ID, root=root) if p["split"] == "train"]
    if len(pairs) != 3:
        raise ValueError("Expected this task's three canonical training pairs")
    canonical = [{"variant": p["variant"], "pair_index": p["pair_index"], **describe(p["input"])} for p in pairs]
    with canonical_path(root).open(encoding="utf-8") as handle:
        programs = {r["program_solution"] for line in handle if line.strip()
                    for r in [json.loads(line)] if r.get("task_id") == TASK_ID}
    if len(programs) != 1:
        raise ValueError("Expected one exact canonical program")
    program = programs.pop()
    normalized_hash = sha(" ".join(program.split()))
    if gen.RULE_HASH != normalized_hash[:12]:
        raise ValueError("Declared rule hash differs from the selected canonical rule")
    draws = []
    for band in BANDS:
        for sd in range(1, 21):
            grid = gen.generate(sd, sd, difficulty=band)
            errors = gen.self_check(grid, difficulty=band)
            if errors:
                raise ValueError(f"Invalid cohort input {band}/{sd}: {errors}")
            profile = gen.schedule_profile(sd, sd, difficulty=band)
            draws.append({"seed": sd, "sample_index": sd, "difficulty": band,
                          "schedule_profile": profile,
                          "profile_family": "canonical" if profile.startswith("canonical_") else "diagnostic",
                          **describe(grid)})
    canonical_counts = {r["object_count"] for r in canonical}
    profiles = sorted({r["schedule_profile"] for r in draws})
    documents = [source, root / f"generators/{TASK_ID}/SUMMARY.md",
                 root / f"generators/{TASK_ID}/notes.md",
                 root / f"generators/{TASK_ID}/evidence/associated_notes.jsonl"]
    if baseline is not None:
        documents.append(baseline.resolve())
    helper = Path(review_diagnostics.__file__).resolve()
    if not helper.is_relative_to(root.resolve()):
        raise ValueError("Structural helper belongs to another source tree")
    if sha(source.read_bytes()) != source_hash:
        raise ValueError("Generator source changed during diagnosis")
    return {
        "schema": "832404dc8a5c-structural-warning-diagnosis-v1", "task_id": TASK_ID,
        "generator_sha256": source_hash, "rule_source_sha256": sha(program),
        "rule_normalized_sha256": normalized_hash, "declared_rule_hash": gen.RULE_HASH,
        "probe_sha256": sha(Path(__file__).read_bytes()), "structural_helper_sha256": sha(helper.read_bytes()),
        "cohort": {"bands": list(BANDS), "seeds": list(range(1, 21)), "sample_index": "equals seed",
                   "call": "generate(sd, sd, difficulty=band)", "overrides": {}, "total_draws": len(draws)},
        "method": "review_diagnostics.objects: count nonzero, same-color, 4-connected components; zero is excluded. Input-only; no generated reference labels or output metrics.",
        "canonical_train": canonical, "canonical_train_exact_counts": sorted(canonical_counts),
        "draws": draws, "overall": summarize(draws, canonical_counts),
        "by_band": {b: summarize([r for r in draws if r["difficulty"] == b], canonical_counts) for b in BANDS},
        "by_profile": {p: summarize([r for r in draws if r["schedule_profile"] == p], canonical_counts) for p in profiles},
        "by_band_profile": {b: {p: summarize([r for r in draws if r["difficulty"] == b and r["schedule_profile"] == p], canonical_counts)
                                 for p in profiles} for b in BANDS},
        "by_band_family": {b: {p: summarize([r for r in draws if r["difficulty"] == b and r["profile_family"] == p], canonical_counts)
                                for p in ("canonical", "diagnostic")} for b in BANDS},
        "document_review": {"files_sha256": {str(p): sha(p.read_bytes()) for p in documents},
                            "finding": "Manual inspection found no nonadjacency requirement in current or supplied baseline module grammar/INVARIANTS/self_check, task summary, or retained design-decision note. Canonical lane positions are observations, not an added hard grammar rule."},
        "interpretation": "Exact-set disjointness reproduces the measured warning. Numeric min/max intervals summarize this cohort only; overlap does not establish distribution equivalence, canonical reachability, or acceptance. Preserve the blocker for maintainer judgment; no sampler tuning or gate modification was performed.",
        "command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("Choose a new evidence path; existing evidence is preserved")
    report = collect_report(find_root(__file__), args.baseline)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"out": str(args.out), "generator_sha256": report["generator_sha256"],
                      "canonical_train_exact_counts": report["canonical_train_exact_counts"],
                      "overall": report["overall"], "by_band_family": report["by_band_family"]}, sort_keys=True))


if __name__ == "__main__":
    main()
