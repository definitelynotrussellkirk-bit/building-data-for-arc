#!/usr/bin/env python3
"""Exhaust consecutive curriculum starts and every query rotation.

This task-local reviewer tool supplements the shared production lesson census.
It checks only the generator's declared competitors; a pass is not a proof of
universal identifiability.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


def _load_generator():
    path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_4bf462ff34fb_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path


def _digest(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def run(*, period: int = 32, seeds: int = 8) -> dict[str, Any]:
    if period < 1 or seeds < 1:
        raise ValueError("period and seeds must be positive")
    gen, source = _load_generator()
    width = gen.EXAMPLES_NEEDED + 1
    failures: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()
    windows = rotations = 0
    profile_counts = {band: 0 for band in ("easy", "medium", "hard")}

    for band in ("easy", "medium", "hard"):
        for seed in range(seeds):
            for start in range(period):
                pairs = []
                for sample_index in range(start, start + width):
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    unique_inputs.add(_digest(grid))
                    profile_counts[band] += int(gen.is_canonical_profile(grid))
                    pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
                windows += 1
                for held_out in range(width):
                    demos = [pair for index, pair in enumerate(pairs) if index != held_out]
                    reasons = gen.lesson_identifiable(demos, pairs[held_out])
                    rotations += 1
                    if reasons:
                        failures.append(
                            {
                                "difficulty": band,
                                "seed": seed,
                                "start": start,
                                "held_out_position": held_out,
                                "sample_indices": list(range(start, start + width)),
                                "reasons": reasons,
                            }
                        )

    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    return {
        "schema": "4bf462ff34fb-cyclic-curriculum-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": source_hash,
        "settings": {
            "period": period,
            "seeds": seeds,
            "bands": ["easy", "medium", "hard"],
            "pairs_per_window": width,
            "demonstrations_per_rotation": gen.EXAMPLES_NEEDED,
            "rotations_per_window": width,
            "declared_competitors": sorted(gen.LESSON_COMPETITORS),
        },
        "counts": {
            "windows": windows,
            "rotations": rotations,
            "unique_inputs": len(unique_inputs),
            "canonical_profile_draws": profile_counts,
            "ambiguous_rotations": len(failures),
        },
        "failures": failures,
        "passed": not failures,
        "limits": [
            "Finite declared-rival check, not universal rule identifiability.",
            "Consecutive starts are enumerated only for the requested period and seed range.",
            "Labels use the Python rule mirror; the battery separately binds it to canonical Racket authority.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", type=int, default=32)
    parser.add_argument("--seeds", type=int, default=8)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run(period=args.period, seeds=args.seeds)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
