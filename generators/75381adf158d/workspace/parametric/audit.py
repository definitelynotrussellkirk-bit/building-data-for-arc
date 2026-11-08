#!/usr/bin/env python3
"""Bounded self-audit for the enclosed-hole / largest-escape family."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_audit_75381_family", HERE / "family.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load family.py")
FAMILY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FAMILY
SPEC.loader.exec_module(FAMILY)


def run(seeds: int) -> dict:
    if type(seeds) is not int or not 1 <= seeds <= 200:
        raise ValueError("seeds must be in 1..200")
    dimensions, hole_counts, hole_sizes = set(), set(), set()
    max_nonzero = pairs = causal = rivals = 0
    for seed in range(seeds):
        episodes = {mode: FAMILY.generate(seed, {"mode": mode}, 2, 4) for mode in FAMILY.MODES}
        inputs = [[p["input"] for p in episodes[mode]["train"] + episodes[mode]["test"]] for mode in FAMILY.MODES]
        if inputs[0] != inputs[1]:
            raise AssertionError(f"settings changed inputs at seed {seed}")
        for mode, episode in episodes.items():
            audit = FAMILY.teaching_audit(episode)
            if audit["declared_setting_survivors"] != [mode] or audit["query_disagreeing_named_survivors"]:
                raise AssertionError({"seed": seed, "mode": mode, "audit": audit})
            rivals += len(audit["named_rivals_checked"])
        for pair_a, pair_b in zip(episodes["canonical"]["train"] + episodes["canonical"]["test"],
                                  episodes["largest_escape"]["train"] + episodes["largest_escape"]["test"]):
            if pair_a["output"] == pair_b["output"]:
                raise AssertionError(f"settings equivalent at seed {seed}")
            facts = FAMILY.analyse(pair_a["input"])
            dimensions.add((facts["height"], facts["width"]))
            hole_counts.add(facts["enclosed_regions"])
            hole_sizes.update(facts["enclosed_sizes"])
            max_nonzero = max(max_nonzero, facts["nonzero"])
            trace = FAMILY.dependency_trace(pair_a["input"])
            if trace["output"] == trace["smallest_escape_output"]:
                raise AssertionError(f"wrong-intermediate separation failed at seed {seed}")
            causal += 1
            pairs += 1
    for seed in (0, 17):
        for mode in FAMILY.MODES:
            for demos in (2, 6):
                episode = FAMILY.generate(seed, {"mode": mode}, demos, 4)
                if len(episode["train"]) != demos or len(episode["test"]) != 4:
                    raise AssertionError("count boundary failure")
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": FAMILY.TASK_ID,
        "status": "passed",
        "seed_count": seeds,
        "setting_episodes": seeds * len(FAMILY.MODES),
        "pairs_checked": pairs,
        "causal_separations": causal,
        "named_rival_checks": rivals,
        "matched_inputs": True,
        "settings_distinct": True,
        "dimensions_seen": [list(item) for item in sorted(dimensions)],
        "enclosed_region_counts_seen": sorted(hole_counts),
        "enclosed_sizes_seen": sorted(hole_sizes),
        "max_nonzero_cells": max_nonzero,
        "count_boundaries": {"demos": [2, 6], "queries": [4, 4], "seeds": [0, 17]},
        "program_sha256": {mode: hashlib.sha256(FAMILY.program({"mode": mode}).encode()).hexdigest() for mode in FAMILY.MODES},
        "limits": "Finite declared-rival and sampled-scene audit; not a universal uniqueness proof."
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run(args.seeds)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
