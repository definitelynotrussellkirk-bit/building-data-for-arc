#!/usr/bin/env python3
"""Bounded deterministic lesson sweep for future modal-composition reviews."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import prototype


def sweep(seed_count: int) -> dict:
    if type(seed_count) is not int or not 1 <= seed_count <= 512:
        raise ValueError("seed_count must be an exact integer in 1..512")
    counts = Counter()
    failures = []
    input_hashes = set()
    modes = Counter()
    sizes = Counter()
    for seed in range(seed_count):
        for demos in (2, 3, 6):
            for setting in prototype.SETTINGS:
                counts["episodes"] += 1
                try:
                    episode = prototype.generate(
                        seed, {prototype.PARAMETER_NAME: setting}, demos, 4
                    )
                    if episode["certificate"]["survivors"] != [setting]:
                        raise AssertionError("selected setting was not sole survivor")
                    for pair in episode["train"] + episode["test"]:
                        facts = prototype.features(pair["input"])
                        modes[facts["modal_color"]] += 1
                        sizes[facts["template_size"]] += 1
                        input_hashes.add(
                            hashlib.sha256(
                                json.dumps(pair["input"], separators=(",", ":")).encode()
                            ).hexdigest()
                        )
                        counts["pairs"] += 1
                except Exception as error:
                    failures.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "setting": setting,
                            "error": f"{type(error).__name__}: {error}",
                        }
                    )
    return {
        "schema": f"{prototype.TASK_ID}-modal-transform-sweep-v1",
        "status": "passed" if not failures else "failed",
        "seed_count": seed_count,
        "demo_counts": [2, 3, 6],
        "settings": list(prototype.SETTINGS),
        "episodes": counts["episodes"],
        "pairs": counts["pairs"],
        "unique_input_hashes": len(input_hashes),
        "modal_color_occurrences": {str(k): modes[k] for k in sorted(modes)},
        "template_size_occurrences": {str(k): sizes[k] for k in sorted(sizes)},
        "failures": failures[:20],
        "limits": "Python construction/certificate sweep; protected Racket is retained separately by verify.py and native qualification.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = sweep(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "episodes", "pairs", "unique_input_hashes")}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
