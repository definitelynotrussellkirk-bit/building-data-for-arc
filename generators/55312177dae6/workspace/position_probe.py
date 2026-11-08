#!/usr/bin/env python3
"""Measure row-major target-index patterns for generator 55312177dae6."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("position_probe_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--samples-per-band", type=int, default=2000)
    parser.add_argument("--seed-base", type=int, default=900000)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    path = args.generator.resolve()
    gen = load_generator(path)
    report = {
        "task_id": gen.TASK_ID,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "samples_per_band": args.samples_per_band,
        "seed_policy": f"seed={args.seed_base}+index; sample_index=index",
        "bands": {},
    }
    passed = True
    for band in ("easy", "medium", "hard"):
        counts: Counter[str] = Counter()
        for index in range(args.samples_per_band):
            grid = gen.generate(args.seed_base + index, index, difficulty=band)
            info = gen._analyze(grid)
            if info.get("errors"):
                raise AssertionError(info["errors"])
            key = ",".join(map(str, info["target_indices"]))
            counts[key] += 1
        report["bands"][band] = {
            "target_index_pairs": dict(sorted(counts.items())),
            "distinct_pairs": len(counts),
        }
        passed = passed and set(counts) == {"1,2", "1,3", "2,3"}
    report["interpretation"] = (
        "The first component is deliberately always a distractor, but all three "
        "remaining two-of-three target index pairs occur in every band; neither "
        "second-object nor last-object selection fits the distribution."
    )
    report["passed"] = passed
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
