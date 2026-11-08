#!/usr/bin/env python3
"""Analyze retained Racket outputs against an interior-only shortcut."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def interior_only(grid):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    seeds = [
        (r, c, v)
        for r, row in enumerate(grid)
        for c, v in enumerate(row)
        if v != 0
    ]
    for r, c, value in seeds:
        destinations = ((r - 2, c), (r + 2, c), (r, c - 2), (r, c + 2))
        if all(0 <= rr < h and 0 <= cc < w for rr, cc in destinations):
            for rr, cc in destinations:
                out[rr][cc] = value
    return out


def main():
    metadata = json.loads((HERE / "metadata.json").read_text())
    racket = json.loads((HERE / "racket.json").read_text())
    rows = metadata["rows"]
    results = racket["results"]
    if len(rows) != len(results):
        raise AssertionError((len(rows), len(results)))

    comparisons = []
    for meta, result in zip(rows, results, strict=True):
        rival = interior_only(meta["input"])
        comparisons.append({
            "kind": meta["kind"],
            "seed": meta.get("seed"),
            "sample_index": meta.get("sample_index"),
            "input_sha256": result["input_sha256"],
            "racket_output_sha256": result["output_sha256"],
            "rival_output_sha256": sha(rival),
            "rival_matches_racket": rival == result["output"],
            "rival_output": rival,
        })

    ordinary = [row for row in comparisons if row["kind"] == "ordinary_generated"]
    canonical = next(row for row in comparisons if row["kind"] == "canonical_near_edge")
    too_close_meta = next(row for row in rows if row["kind"] == "validator_too_close")
    override_meta = next(row for row in rows if row["kind"] == "ignored_override")
    canonical_meta = next(row for row in rows if row["kind"] == "canonical_near_edge")
    canonical_result = results[comparisons.index(canonical)]

    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": metadata["task_id"],
        "generator_sha256": metadata["generator_sha256"],
        "executed_rule_hash": racket["executed_rule_hash"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "rule_hash_matches_catalog": racket["rule_hash_matches_catalog"],
        "ordinary_sample": metadata["ordinary_sample"],
        "ordinary_generated": {
            "denominator": len(ordinary),
            "minimum_border_margin": min(
                row["minimum_border_margin"]
                for row in rows
                if row["kind"] == "ordinary_generated"
            ),
            "interior_only_rival_matches": sum(
                row["rival_matches_racket"] for row in ordinary
            ),
            "all_self_checks_passed": all(
                not row["self_check"]
                for row in rows
                if row["kind"] == "ordinary_generated"
            ),
        },
        "canonical_counterexample": {
            "variant": canonical_meta["variant"],
            "split": canonical_meta["split"],
            "pair_index": canonical_meta["pair_index"],
            "minimum_border_margin": canonical_meta["minimum_border_margin"],
            "self_check": canonical_meta["self_check"],
            "input": canonical_meta["input"],
            "racket_output": canonical_result["output"],
            "interior_only_rival_output": canonical["rival_output"],
            "rival_matches_racket": canonical["rival_matches_racket"],
        },
        "validator_counterexample": {
            "input": too_close_meta["input"],
            "seed_cells": too_close_meta["seed_cells"],
            "pairwise_manhattan_distance": too_close_meta[
                "pairwise_manhattan_distance"
            ],
            "self_check": too_close_meta["self_check"],
            "contradicted_documented_invariant": (
                "no two cells within Manhattan distance 4"
            ),
        },
        "override_counterexample": {
            "seed": override_meta["seed"],
            "sample_index": override_meta["sample_index"],
            "difficulty": override_meta["difficulty"],
            "requested": override_meta["overrides"],
            "observed_seed_count": override_meta["observed_seed_count"],
            "observed_distinct_nonzero_colors": override_meta[
                "observed_distinct_nonzero_colors"
            ],
            "input": override_meta["input"],
            "self_check": override_meta["self_check"],
        },
        "commands": {
            "build": (
                "python3 review.py run python3 "
                "../checks/audit/2f889ed81450/build_inputs.py"
            ),
            "apply": (
                "python3 review.py run python3 -m arcpuzzles apply 2f889ed81450 "
                "--input ../checks/audit/2f889ed81450/input.json "
                "--out ../checks/audit/2f889ed81450/racket.json"
            ),
            "analyze": (
                "python3 review.py run python3 "
                "../checks/audit/2f889ed81450/analyze.py"
            ),
            "cwd": str(Path.cwd()),
        },
        "conclusion": (
            "The interior-only shortcut matches every one of 60 ordinary draws "
            "but fails a self_check-accepted canonical near-edge example; exact "
            "n_seeds/n_distinct_colors overrides are also ignored, and self_check "
            "accepts seeds at Manhattan distance 2 despite the documented invariant."
        ),
    }
    if report["ordinary_generated"]["interior_only_rival_matches"] != len(ordinary):
        raise AssertionError("rival did not fit all ordinary generated inputs")
    if report["canonical_counterexample"]["rival_matches_racket"]:
        raise AssertionError("canonical witness did not refute rival")
    if report["validator_counterexample"]["self_check"]:
        raise AssertionError("validator counterexample was rejected")
    if report["override_counterexample"]["observed_seed_count"] == 1:
        raise AssertionError("n_seeds override unexpectedly worked")

    (HERE / "rival.json").write_text(
        json.dumps(comparisons, indent=2, sort_keys=True) + "\n"
    )
    (HERE / "counterexample.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({
        "ordinary_rival_matches": report["ordinary_generated"][
            "interior_only_rival_matches"
        ],
        "ordinary_denominator": len(ordinary),
        "canonical_rival_matches": report["canonical_counterexample"][
            "rival_matches_racket"
        ],
        "too_close_self_check": report["validator_counterexample"]["self_check"],
        "override_observed_seed_count": report["override_counterexample"][
            "observed_seed_count"
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
