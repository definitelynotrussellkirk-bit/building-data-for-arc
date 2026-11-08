#!/usr/bin/env python3
"""Standalone deterministic audit for candidate 17ea562973ac generators."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reference_probe import canonical_pairs, facts, load_generator, reference_output, semantic_profile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--samples", type=int, default=200)
    args = parser.parse_args()
    gen = load_generator(args.generator)
    report = {
        "canonical": {"pairs": 0, "accepted": 0, "oracle_matches": 0},
        "bands": {},
        "rival_counterexamples": {name: 0 for name in getattr(gen, "SEMANTIC_RIVALS", {})},
    }
    for pair in canonical_pairs():
        report["canonical"]["pairs"] += 1
        report["canonical"]["accepted"] += not bool(gen.self_check(pair["input"]))
        report["canonical"]["oracle_matches"] += reference_output(pair["input"]) == pair["output"]
    for band in ("easy", "medium", "hard"):
        counts = {}; profiles = {"two_markers": 0, "interior_marker": 0, "first_two_incomplete": 0}
        invalid = oracle_mismatch = 0
        for index in range(args.samples):
            grid = gen.generate(1907 + index, index * 11, difficulty=band)
            invalid += bool(gen.self_check(grid))
            oracle_mismatch += gen.rule_mirror(grid) != reference_output(grid)
            count = facts(grid)["num_cells"]
            counts[str(count)] = counts.get(str(count), 0) + 1
            for key, present in semantic_profile(grid).items():
                profiles[key] += bool(present)
            truth = reference_output(grid)
            for name, rival in getattr(gen, "SEMANTIC_RIVALS", {}).items():
                report["rival_counterexamples"][name] += rival(grid) != truth
        report["bands"][band] = {
            "samples": args.samples,
            "invalid": invalid,
            "oracle_mismatch": oracle_mismatch,
            "num_cells": counts,
            "semantic_profiles": profiles,
        }
    print(json.dumps(report, indent=2, sort_keys=True))
    return int(
        report["canonical"]["accepted"] != report["canonical"]["pairs"]
        or report["canonical"]["oracle_matches"] != report["canonical"]["pairs"]
        or any(row["invalid"] or row["oracle_mismatch"] for row in report["bands"].values())
    )


if __name__ == "__main__":
    raise SystemExit(main())
