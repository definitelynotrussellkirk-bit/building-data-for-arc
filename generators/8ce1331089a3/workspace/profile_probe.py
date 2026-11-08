#!/usr/bin/env python3
"""Fast source-only census for generator 8ce1331089a3.

This does not replace the Racket-backed battery.  It gives future reviewers a
cheap first pass over profile support, distractors, semantic witnesses, and
named rival disagreement before paying the full portable-runtime copy cost.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import importlib.util
import json
from pathlib import Path
import sys

TASK_HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load_generator():
    path = TASK_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("probe_generator_8ce1331089a3", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=40, help="samples per band")
    parser.add_argument("--seed", type=int, default=20260928)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be positive")

    gen = load_generator()
    report = {
        "task_id": gen.TASK_ID,
        "version": gen.VERSION,
        "samples_per_band": args.samples,
        "bands": {},
    }
    failed = False
    for band_index, band in enumerate(("easy", "medium", "hard")):
        profiles: Counter[str] = Counter()
        distractor_counts: Counter[str] = Counter()
        route_counts: Counter[str] = Counter()
        witness_hits = Counter({name: 0 for name in gen.SEMANTIC_WITNESSES})
        rival_disagreements = Counter({name: 0 for name in gen.SEMANTIC_RIVALS})
        errors: list[dict] = []
        for sample_index in range(args.samples):
            grid = gen.generate(
                args.seed + band_index * 100_000 + sample_index,
                sample_index,
                difficulty=band,
            )
            reasons = gen.self_check(grid, difficulty=band)
            if reasons:
                errors.append({"sample_index": sample_index, "reasons": reasons[:3]})
                continue
            facts = gen._analysis(grid)
            profile = (
                facts["height"],
                facts["width"],
                facts["palette_size"],
                facts["n_pixels"],
            )
            profiles[repr(profile)] += 1
            distractor_counts[str(len(facts["distractors"]))] += 1
            for route, count in facts["route_counts"].items():
                route_counts[route] += count
            expected = gen.rule_mirror(grid)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                witness_hits[name] += int(bool(witness(grid)))
            for name, rival in gen.SEMANTIC_RIVALS.items():
                rival_disagreements[name] += int(
                    rival(copy.deepcopy(grid)) != expected
                )
        row = {
            "generated": args.samples,
            "invalid": len(errors),
            "error_examples": errors[:3],
            "profiles": dict(sorted(profiles.items())),
            "distractor_count_histogram": dict(sorted(distractor_counts.items())),
            "matching_route_cell_totals": dict(sorted(route_counts.items())),
            "witness_hits": dict(sorted(witness_hits.items())),
            "rival_disagreements": dict(sorted(rival_disagreements.items())),
        }
        report["bands"][band] = row
        if errors or any(value == 0 for value in witness_hits.values()) or any(
            value == 0 for value in rival_disagreements.values()
        ):
            failed = True

    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
