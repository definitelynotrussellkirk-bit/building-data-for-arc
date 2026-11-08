#!/usr/bin/env python3
"""Source-bound findings-only audit. Exit 0 means expected defects reproduced.

Run from packet root:
  PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run \
    ../.venv/bin/python ../checks/audit/388e9ae29018/probe.py
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys

TASK = "388e9ae29018"
EXPECTED_SOURCE = "cff7fbd6a45be9f6f3e60a16f99a5a8a828f17276a0fa073da55a1817f10b536"
EXPECTED_RULE = "07d0b4adce4b"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def metrics(grid):
    counts = Counter(v for row in grid for v in row)
    # Easy-band cases have exactly one complete ring of each relevant color.
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "colors": sorted(counts),
            "color_counts": dict(counts), "red_radius": counts[2] // 4,
            "gray_radius": counts[5] // 4}


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
    assert catalog.describe(TASK)["rule_hash"] == EXPECTED_RULE
    record = catalog.get(TASK)["variants"][0]
    rule = record["program_solution"]
    shutil.copyfile(source, out / "source_generator.py")
    (out / "canonical_rule.rkt").write_text(rule, encoding="utf-8")
    canonical = canonical_pairs(TASK, root=root, variant=0, labeled_only=True)

    cases = [
        {"name": "joint_dimensions_fallback", "seed": 0, "sample_index": 0, "difficulty": "easy",
         "overrides": {"grid_h": 12, "grid_w": 12, "texture": "r3", "gray_radius": 2}},
        {"name": "red_radius_ignored", "seed": 1, "sample_index": 0, "difficulty": "easy",
         "overrides": {"red_radius": "r3", "gray_radius": 2}},
        {"name": "gray_radius_ignored", "seed": 2, "sample_index": 0, "difficulty": "easy",
         "overrides": {"red_radius": "r3", "gray_radius": 2}},
    ]
    for case in cases:
        case["input"] = module.generate(case["seed"], case["sample_index"],
                                         difficulty=case["difficulty"], **case["overrides"])
        case["observed"] = metrics(case["input"])
        case["self_check"] = module.self_check(case["input"])
        assert case["self_check"] == [], case
    assert (cases[0]["observed"]["grid_h"], cases[0]["observed"]["grid_w"]) == (18, 18)
    assert cases[1]["observed"]["red_radius"] == 2
    assert cases[2]["observed"]["gray_radius"] == 1

    # Keep actual Racket labels for all three override witnesses and all four
    # unique canonical pairs; the domain result is evaluated by public apply.
    applied = catalog.apply(TASK, [p["input"] for p in canonical] + [p["input"] for p in cases],
                            timeout=90, check_generator_domain=True)
    write_json(out / "racket.json", applied)
    assert applied["generator_sha256"] == EXPECTED_SOURCE
    assert applied["executed_rule_hash"] == EXPECTED_RULE
    canonical_checks = []
    for pair, result in zip(canonical, applied["results"][:len(canonical)], strict=True):
        canonical_checks.append({"variant": pair["variant"], "split": pair["split"],
                                 "pair_index": pair["pair_index"],
                                 "profile": [len(pair["input"]), len(pair["input"][0]),
                                             len({v for row in pair["input"] for v in row})],
                                 "matches_label": result["output"] == pair["output"],
                                 "generator_domain": result["generator_domain"],
                                 "preserved_other_color_cells": sum(v in (8, 9) for row in result["output"] for v in row)})
    assert all(row["matches_label"] for row in canonical_checks), canonical_checks
    assert all(row["generator_domain"]["status"] == "invalid" for row in canonical_checks)
    for case, result in zip(cases, applied["results"][len(canonical):], strict=True):
        case["output"] = result["output"]
        case["public_apply_domain"] = result["generator_domain"]
        assert result["valid_output"] and result["generator_domain"]["status"] == "valid"

    canonical_profiles = sorted({tuple(row["profile"]) for row in canonical_checks})
    lower = [min(p[i] for p in canonical_profiles) for i in range(3)]
    upper = [max(p[i] for p in canonical_profiles) for i in range(3)]
    profiles = {}
    for band in ("easy", "medium", "hard"):
        rows = []
        for index in range(20):
            grid = module.generate(71731, index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            rows.append({"sample_index": index, "profile": profile,
                         "exact": profile in canonical_profiles,
                         "envelope": all(lower[i] <= profile[i] <= upper[i] for i in range(3))})
        profiles[band] = {"seed": 71731, "draws": 20, "rows": rows,
                          "exact_hits": sum(r["exact"] for r in rows),
                          "envelope_hits": sum(r["envelope"] for r in rows)}
    assert all(r["exact_hits"] == r["envelope_hits"] == 0 for r in profiles.values())

    # A concrete transfer-risk comparison: remove all non-red/non-gray foreground
    # cells from an otherwise correct output. This agrees with every generator
    # output by source construction but differs on canonical examples. It is not
    # claimed to be an ambiguous production query within the restricted domain.
    rival_canonical = []
    for index, result in enumerate(applied["results"][:len(canonical)]):
        rival = [[v if v in (2, 5, 7) else 7 for v in row] for row in result["output"]]
        rival_canonical.append({"canonical_index": index,
                                "different_cells": sum(a != b for ra, rb in zip(rival, result["output"])
                                                       for a, b in zip(ra, rb))})
    assert all(x["different_cells"] > 0 for x in rival_canonical)

    write_json(out / "witnesses.json", {"override_cases": cases,
                                       "canonical_pair_0": {**canonical[0],
                                                            "self_check": module.self_check(canonical[0]["input"])}})
    report = {
        "schema": "arc-focused-audit-v1", "task_id": TASK, "verdict": "reproduced_defects",
        "generator_sha256": source_sha, "canonical_rule_hash": EXPECTED_RULE,
        "canonical_rule_source_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "executed_rule_text_sha256": applied["rule_text_sha256"],
        "canonical_scope": "variant 0: three train pairs plus one labeled test pair; other ledger row duplicates these pairs",
        "canonical_checks": canonical_checks, "canonical_profiles": canonical_profiles,
        "profiles": profiles,
        "exact_controls": [{k: case[k] for k in ("name", "seed", "sample_index", "difficulty", "overrides", "observed", "self_check")} for case in cases],
        "joint_constraint": "At h=w=12, red radius3 and gray radius2 both require centers in 4..7; their maximum L1 center distance is6, while placement requires >=3+2+3=8. Fallback returns18x18 rather than rejecting incompatibility.",
        "shortcut_risk": {"status": "domain transfer risk, not a reproduced ambiguous production lesson",
                          "rival": "Erase colors other than2,5,7 from correct output",
                          "canonical_differences": rival_canonical,
                          "basis": "Every generator branch writes only2,5,7; canonical rule preserves unrelated objects and handles Vs."},
        "test_inventory": {"task_local_tests": [], "focused_root_tests_found": []},
        "prior_audit_lead": {"return_id": "review-baa9b009b81b43b3:v0001", "same_source": True,
                             "finding": "invalid palette_kind accepted; not rerun or claimed newly measured here"},
        "limits": ["No exhaustive seed search, full battery, or lesson-identifiability census.",
                   "Profile rows are input diagnostics; only seven retained inputs were executed by Catalog.apply.",
                   "No training-safety approval and no target changes."],
    }
    write_json(out / "report.json", report)
    print(json.dumps({"task_id": TASK, "verdict": report["verdict"],
                      "canonical_matches": sum(r["matches_label"] for r in canonical_checks),
                      "canonical_domain_rejections": sum(r["generator_domain"]["status"] == "invalid" for r in canonical_checks),
                      "exact_controls": report["exact_controls"],
                      "profile_hits": {k: {x: v[x] for x in ("exact_hits", "envelope_hits")} for k, v in profiles.items()}}, indent=2))


if __name__ == "__main__":
    main()
