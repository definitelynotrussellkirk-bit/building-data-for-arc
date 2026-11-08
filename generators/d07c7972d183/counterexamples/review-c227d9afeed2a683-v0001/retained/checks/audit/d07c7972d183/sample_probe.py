#!/usr/bin/env python3
"""Reproduce the d07c7972d183 top-left sampler support audit."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def load_generator(repo: Path):
    sys.path.insert(0, str(repo / "shared/runtime"))
    path = repo / "generators/d07c7972d183/generator.py"
    spec = importlib.util.spec_from_file_location("audit_d07_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    module, source = load_generator(repo)
    counts = {}
    reps = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        row = {"draws": 0, "top_left_one": 0, "top_left_zero": 0, "other": 0}
        for offset in range(400):
            seed = 70000 + band_index * 1000 + offset
            sample_index = offset * 11
            grid = module.generate(seed, sample_index, difficulty=band)
            value = grid[0][0]
            row["draws"] += 1
            if value == 0:
                row["top_left_zero"] += 1
            elif value == 1:
                row["top_left_one"] += 1
            else:
                row["other"] += 1
            if offset < 2:
                reps.append({"band": band, "seed": seed, "sample_index": sample_index, "top_left": value})
        counts[band] = row
    canonical_input = json.loads(args.input.read_text())
    issues = module.self_check(canonical_input) if hasattr(module, "self_check") else ["self_check unavailable"]
    report = {
        "schema": "d07c7972d183-top-left-audit-v1",
        "task_id": "d07c7972d183",
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "schedule": {
            "bands": ["easy", "medium", "hard"],
            "seeds": "70000 + band_index*1000 + offset, offset=0..399",
            "sample_index": "offset*11",
            "total_draws": 1200,
        },
        "observed": counts,
        "all_sampled_top_left_zero": all(v["top_left_zero"] == v["draws"] for v in counts.values()),
        "canonical_counterexample_top_left": canonical_input[0][0],
        "canonical_counterexample_self_check_issues": issues,
        "canonical_counterexample_validator_accepts": not issues,
        "representative_draws": reps,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["all_sampled_top_left_zero"] and report["canonical_counterexample_validator_accepts"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
