#!/usr/bin/env python3
"""Bounded self-audit for the 2d4e8c8fa10e controller-axis family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_audit_family_2d4", HERE / "family.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load family.py")
FAMILY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FAMILY
SPEC.loader.exec_module(FAMILY)


def run(seeds: int) -> dict:
    if type(seeds) is not int or not 1 <= seeds <= 200:
        raise ValueError("seeds must be in 1..200")
    settings = (
        {"selection": "all_exact_squares"},
        {"selection": "controller_axis"},
    )
    orientations: set[str] = set()
    square_counts: set[int] = set()
    distractor_counts: set[int] = set()
    dimensions: set[tuple[int, int]] = set()
    episodes = 0
    pairs = 0
    for seed in range(seeds):
        generated = [FAMILY.generate(seed, setting, 2, 4) for setting in settings]
        left_inputs = [p["input"] for p in generated[0]["train"] + generated[0]["test"]]
        right_inputs = [p["input"] for p in generated[1]["train"] + generated[1]["test"]]
        if left_inputs != right_inputs:
            raise AssertionError(f"settings changed inputs at seed {seed}")
        for episode, expected in zip(generated, ("all_exact_squares", "controller_axis")):
            audit = FAMILY.teaching_audit(episode)
            if audit["survivors"] != [expected] or audit["query_disagreeing_survivors"]:
                raise AssertionError({"seed": seed, "expected": expected, "audit": audit})
            episodes += 1
        for pair_left, pair_right in zip(
            generated[0]["train"] + generated[0]["test"],
            generated[1]["train"] + generated[1]["test"],
        ):
            if pair_left["output"] == pair_right["output"]:
                raise AssertionError(f"settings equivalent at seed {seed}")
            state = FAMILY.observe(pair_left["input"])
            orientations.add(state["orientation"])
            square_counts.add(len(state["squares"]))
            distractor_counts.add(len(state["distractors"]))
            dimensions.add((state["height"], state["width"]))
            pairs += 1
    for seed in (0, 17):
        for setting in settings:
            for demos in (2, 6):
                episode = FAMILY.generate(seed, setting, demos, 4)
                if len(episode["train"]) != demos or len(episode["test"]) != 4:
                    raise AssertionError("count boundary failure")
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": FAMILY.TASK_ID,
        "status": "passed",
        "seed_count": seeds,
        "setting_episodes": episodes,
        "pairs_checked": pairs,
        "matched_inputs": True,
        "setting_outputs_distinct": True,
        "finite_rival_teaching_clear": True,
        "controller_orientations_seen": sorted(orientations),
        "square_counts_seen": sorted(square_counts),
        "distractor_counts_seen": sorted(distractor_counts),
        "dimensions_seen": [list(item) for item in sorted(dimensions)],
        "count_boundaries": {"demos": [2, 6], "queries": [4, 4], "seeds": [0, 17]},
        "program_sha256": {
            setting["selection"]: hashlib.sha256(FAMILY.program(setting).encode()).hexdigest()
            for setting in settings
        },
        "limits": "Finite declared-rival and sampled-scene audit; not a universal uniqueness proof.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=40)
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
