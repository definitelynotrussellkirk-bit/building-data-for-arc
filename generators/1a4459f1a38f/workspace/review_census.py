#!/usr/bin/env python3
"""Reproducible distribution/shortcut census for generator 1a4459f1a38f.

The probe deliberately uses the checked-in source rather than a prepared runtime,
so a reviewer can run it directly from any extracted review packet.  It measures
curriculum-slot balance, semantic-witness incidence, actual named-rival
answer disagreements, and all contiguous 3-demo + 1-query lesson windows.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any


HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parent
REPO_ROOT = HERE.parents[2]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
GENERATOR_PATH = TASK_HOME / "generator.py"


def load_generator() -> ModuleType:
    """Load the selected source generator with its portable runtime helpers."""
    sys.path.insert(0, str(RUNTIME_ROOT))
    spec = importlib.util.spec_from_file_location(
        "reviewed_generator_1a4459f1a38f", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pair(module: ModuleType, grid: list[list[int]]) -> dict[str, Any]:
    return {
        "input": grid,
        "output": module._candidate_output("largest_cells", grid),
    }


def build_report(
    *,
    draws: int = 32,
    seed_count: int = 8,
    base_seed: int = 17000,
    module: ModuleType | None = None,
) -> dict[str, Any]:
    """Return a JSON-safe census over deterministic seeds and sliding lessons."""
    if draws < 4:
        raise ValueError("draws must be at least 4 for a 3-demo + 1-query lesson")
    if seed_count < 1:
        raise ValueError("seed_count must be positive")
    module = module or load_generator()

    report: dict[str, Any] = {
        "schema": "arc-generator-review-census-v1",
        "task_id": module.TASK_ID,
        "generator_version": module.VERSION,
        "parameters": {
            "draws_per_seed": draws,
            "seed_count": seed_count,
            "base_seed": base_seed,
        },
        "bands": {},
    }

    for band_index, band in enumerate(("easy", "medium", "hard")):
        profile_counts: Counter[str] = Counter()
        witness_hits: Counter[str] = Counter()
        rival_disagreements: Counter[str] = Counter()
        failed_windows: list[dict[str, Any]] = []
        total_windows = 0

        for seed_offset in range(seed_count):
            seed = base_seed + band_index * 100_000 + seed_offset
            grids = [
                module.generate(seed, sample_index, difficulty=band)
                for sample_index in range(draws)
            ]

            for sample_index, grid in enumerate(grids):
                profile_counts[module.CURRICULUM_SCHEDULE[sample_index % 4]] += 1
                for name, predicate in module.SEMANTIC_WITNESSES.items():
                    if predicate(grid):
                        witness_hits[name] += 1
                official = module._candidate_output("largest_cells", grid)
                for witness, rivals in module.WITNESS_RIVALS.items():
                    if not module.SEMANTIC_WITNESSES[witness](grid):
                        continue
                    for rival in rivals:
                        if module._candidate_output(rival, grid) != official:
                            rival_disagreements[f"{witness}:{rival}"] += 1

            pairs = [_pair(module, grid) for grid in grids]
            for start in range(draws - 3):
                total_windows += 1
                problems = module.lesson_identifiable(
                    pairs[start : start + 3], pairs[start + 3]
                )
                if problems and len(failed_windows) < 50:
                    failed_windows.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start_sample_index": start,
                            "problems": problems,
                        }
                    )

        expected_rivals = [
            f"{witness}:{rival}"
            for witness, rivals in module.WITNESS_RIVALS.items()
            for rival in rivals
        ]
        report["bands"][band] = {
            "grids": draws * seed_count,
            "profile_counts": dict(sorted(profile_counts.items())),
            "semantic_witness_hits": {
                name: witness_hits[name]
                for name in sorted(module.SEMANTIC_WITNESSES)
            },
            "rival_disagreements": {
                name: rival_disagreements[name]
                for name in sorted(expected_rivals)
            },
            "lesson_windows": {
                "total": total_windows,
                "passed": total_windows - len(failed_windows),
                "failed": len(failed_windows),
                "failure_examples": failed_windows,
            },
        }

    return report


def _has_failure(report: dict[str, Any]) -> bool:
    for band in report["bands"].values():
        if band["lesson_windows"]["failed"]:
            return True
        if any(count == 0 for count in band["semantic_witness_hits"].values()):
            return True
        if any(count == 0 for count in band["rival_disagreements"].values()):
            return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws", type=int, default=32)
    parser.add_argument("--seed-count", type=int, default=8)
    parser.add_argument("--base-seed", type=int, default=17000)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--allow-failures",
        action="store_true",
        help="emit the report but return zero even when the census finds a gap",
    )
    args = parser.parse_args(argv)

    report = build_report(
        draws=args.draws,
        seed_count=args.seed_count,
        base_seed=args.base_seed,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if args.allow_failures or not _has_failure(report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
