#!/usr/bin/env python3
"""Source-bound findings-only audit. Exit 0 means expected defects reproduced.

Run from packet root:
  PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run \
    ../.venv/bin/python ../checks/audit/35e7d1dc7112/probe.py

Needs this packet's Python dependencies and included Racket, configured by
review.py run. Uses only this repository and the supported Catalog.apply API.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys

TASK = "35e7d1dc7112"
EXPECTED_SOURCE = "ae8c796c905d58e61d9a9eadc182e19942d403f06d633db82a4c839c35e40372"
EXPECTED_RULE = "301b98df0dd8"


def metrics(grid):
    counts = Counter(v for row in grid for v in row)
    bg = counts.most_common(1)[0][0]
    zeros = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 0]
    center = [(min(p[i] for p in zeros) + max(p[i] for p in zeros)) // 2 for i in (0, 1)]
    markers = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (bg, 0)]
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "distinct_colors": len(counts),
            "shape_size": len(zeros), "background": bg, "shape_center": center,
            "marker_cells": markers,
            "marker_dist": abs(markers[0][0] - center[0]) + abs(markers[0][1] - center[1])}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3] / "repo")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(root / "src"), str(root / "shared/runtime")]
    from arcpuzzles import Catalog
    from reviewer_support import canonical_pairs, load_selected_generator

    module, source, source_sha = load_selected_generator(TASK, root=root)
    assert source_sha == EXPECTED_SOURCE, ("source changed", source_sha)
    catalog = Catalog(root)
    description = catalog.describe(TASK)
    assert description["rule_hash"] == EXPECTED_RULE
    record = next(row for row in catalog.get(TASK)["variants"])
    rule = record["program_solution"]
    rule_sha = hashlib.sha256(rule.encode()).hexdigest()
    shutil.copyfile(source, out / "source_generator.py")
    (out / "canonical_rule.rkt").write_text(rule, encoding="utf-8")

    canonical = canonical_pairs(TASK, root=root, variant=0, labeled_only=True)
    request = {"grid_h": 13, "grid_w": 13, "shape_size": 2, "marker_dist": 2}
    override_grid = module.generate(0, 0, difficulty="easy", **request)
    override_metrics = metrics(override_grid)
    violations = {key: {"requested": value, "actual": override_metrics[key]}
                  for key, value in request.items() if override_metrics[key] != value}
    assert set(violations) == set(request), violations
    assert module.self_check(override_grid) == []

    # The only invalid promised invariant is distance=1 (hence zero march step).
    # Keeping h/w and shape size inside AXES avoids relying on a tiny-grid case.
    zero_step_grid = [[5] * 13 for _ in range(13)]
    zero_step_grid[6][6] = zero_step_grid[7][6] = 0
    zero_step_grid[6][7] = 2
    assert metrics(zero_step_grid)["marker_dist"] == 1
    assert module.self_check(zero_step_grid) == []

    # Apply every retained witness through real Racket. The final input is
    # expected to hit the bridge's 10-second evaluator timeout, not hang forever.
    inputs = [p["input"] for p in canonical] + [override_grid, zero_step_grid]
    applied = catalog.apply(TASK, inputs, timeout=90, check_generator_domain=True)
    write_json(out / "racket.json", applied)
    assert applied["generator_sha256"] == EXPECTED_SOURCE
    assert applied["executed_rule_hash"] == EXPECTED_RULE
    results = applied["results"]
    canonical_checks = [
        {"variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
         "matches_label": result["output"] == pair["output"],
         "generator_domain": result["generator_domain"]}
        for pair, result in zip(canonical, results[:len(canonical)], strict=True)
    ]
    assert all(item["matches_label"] for item in canonical_checks), canonical_checks
    override_result, zero_step_result = results[-2:]
    assert override_result["valid_output"] and override_result["generator_domain"]["status"] == "valid"
    assert not zero_step_result["valid_output"]
    assert "timed out" in (zero_step_result["error"] or "").lower(), zero_step_result
    assert zero_step_result["generator_domain"]["status"] == "valid", zero_step_result

    # Focused profile support, not a blanket battery. The hard sampling branch
    # uses h=20..24 while canonical heights are <=18. The emergency fallback
    # has h=15, so absence of envelope support below is a finite observation.
    canonical_profiles = sorted({(len(p["input"]), len(p["input"][0]),
                                  len({v for row in p["input"] for v in row})) for p in canonical})
    lower = [min(p[i] for p in canonical_profiles) for i in range(3)]
    upper = [max(p[i] for p in canonical_profiles) for i in range(3)]
    profile_results = {}
    for band in ("easy", "medium", "hard"):
        rows = []
        for index in range(20):
            grid = module.generate(71731, index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            rows.append({"sample_index": index, "profile": profile,
                         "exact": profile in canonical_profiles,
                         "envelope": all(lower[i] <= profile[i] <= upper[i] for i in range(3))})
        profile_results[band] = {"seed": 71731, "draws": 20, "rows": rows,
                                 "exact_hits": sum(r["exact"] for r in rows),
                                 "envelope_hits": sum(r["envelope"] for r in rows)}
    assert profile_results["hard"]["exact_hits"] == profile_results["hard"]["envelope_hits"] == 0

    write_json(out / "witnesses.json", {
        "exact_controls": {"seed": 0, "sample_index": 0, "difficulty": "easy",
                           "overrides": request, "observed": override_metrics,
                           "violations": violations, "self_check": [],
                           "input": override_grid, "output": override_result["output"]},
        "zero_step_validator": {"construction": "13x13 bg=5; zeros=(6,6),(7,6); marker=(6,7,color2)",
                                "observed": metrics(zero_step_grid), "self_check": [],
                                "input": zero_step_grid, "output": None,
                                "racket_error": zero_step_result["error"]},
    })
    report = {
        "schema": "arc-focused-audit-v1", "task_id": TASK, "verdict": "reproduced_defects",
        "generator_sha256": source_sha, "canonical_rule_hash": EXPECTED_RULE,
        "canonical_rule_source_sha256": rule_sha,
        "executed_rule_text_sha256": applied["rule_text_sha256"],
        "canonical_scope": "variant 0: three train pairs plus one labeled test pair; other ledger row duplicates these pairs",
        "canonical_checks": canonical_checks,
        "exact_controls": {"seed": 0, "sample_index": 0, "difficulty": "easy", "violations": violations},
        "validator_defect": {"marker_distance": 1, "self_check": [],
                             "public_apply_domain": zero_step_result["generator_domain"],
                             "racket_error": zero_step_result["error"],
                             "scope": "hand-authored validator counterexample; no claim ordinary generate emits distance 1"},
        "canonical_profiles": canonical_profiles, "profiles": profile_results,
        "test_inventory": {"task_local_tests": [], "focused_root_tests_found": []},
        "prior_audit_lead": None,
        "limits": ["No exhaustive seed search, full battery, or lesson-identifiability census.",
                   "Profile rows are input diagnostics; only six retained inputs were executed by Catalog.apply.",
                   "No training-safety approval and no target changes."],
    }
    write_json(out / "report.json", report)
    print(json.dumps({"task_id": TASK, "verdict": report["verdict"],
                      "canonical_matches": sum(x["matches_label"] for x in canonical_checks),
                      "exact_control_violations": violations, "zero_step_error": zero_step_result["error"],
                      "profile_hits": {k: {x: v[x] for x in ("exact_hits", "envelope_hits")} for k, v in profile_results.items()}}, indent=2))


if __name__ == "__main__":
    main()
