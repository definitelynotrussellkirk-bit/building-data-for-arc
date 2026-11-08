#!/usr/bin/env python3
"""Bounded self-audit for the 7ce16af847d6 waypoint family."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_audit_7ce16_family", HERE / "family.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load family.py")
FAMILY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FAMILY
SPEC.loader.exec_module(FAMILY)


def run(seeds: int) -> dict:
    if type(seeds) is not int or not 1 <= seeds <= 200:
        raise ValueError("seeds must be in 1..200")
    modes = FAMILY.MODES
    dimensions = set()
    target_counts = set()
    max_nonzero = 0
    pairs = 0
    causal = 0
    rivals = 0
    for seed in range(seeds):
        episodes = {mode: FAMILY.generate(seed, {"mode": mode}, 2, 4) for mode in modes}
        left = [p["input"] for p in episodes[modes[0]]["train"] + episodes[modes[0]]["test"]]
        right = [p["input"] for p in episodes[modes[1]]["train"] + episodes[modes[1]]["test"]]
        if left != right:
            raise AssertionError(f"settings changed inputs at seed {seed}")
        for mode, episode in episodes.items():
            audit = FAMILY.teaching_audit(episode)
            if audit["declared_setting_survivors"] != [mode] or audit["query_disagreeing_named_survivors"]:
                raise AssertionError({"seed": seed, "mode": mode, "audit": audit})
            rivals += len(audit["named_rivals_checked"])
        for pair_a, pair_b in zip(episodes[modes[0]]["train"] + episodes[modes[0]]["test"], episodes[modes[1]]["train"] + episodes[modes[1]]["test"]):
            if pair_a["output"] == pair_b["output"]:
                raise AssertionError(f"settings equivalent at seed {seed}")
            facts = FAMILY.analyse(pair_a["input"])
            dimensions.add((facts["height"], facts["width"]))
            target_counts.add(facts["targets"])
            max_nonzero = max(max_nonzero, facts["nonzero"])
            trace = FAMILY.dependency_trace(pair_a["input"])
            if trace["output"] == trace["skip_a_output"]:
                raise AssertionError(f"causal separation failed at seed {seed}")
            causal += 1
            pairs += 1
    for seed in (0, 17):
        for mode in modes:
            for demos in (2, 6):
                episode = FAMILY.generate(seed, {"mode": mode}, demos, 4)
                if len(episode["train"]) != demos or len(episode["test"]) != 4:
                    raise AssertionError("count boundary failure")
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": FAMILY.TASK_ID,
        "status": "passed",
        "seed_count": seeds,
        "setting_episodes": seeds * len(modes),
        "pairs_checked": pairs,
        "causal_separations": causal,
        "named_rival_checks": rivals,
        "matched_inputs": True,
        "settings_distinct": True,
        "dimensions_seen": [list(item) for item in sorted(dimensions)],
        "target_counts_seen": sorted(target_counts),
        "max_nonzero_cells": max_nonzero,
        "count_boundaries": {"demos": [2, 6], "queries": [4, 4], "seeds": [0, 17]},
        "program_sha256": {mode: hashlib.sha256(FAMILY.program({"mode": mode}).encode()).hexdigest() for mode in modes},
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
