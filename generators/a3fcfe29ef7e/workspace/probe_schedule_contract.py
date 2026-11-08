#!/usr/bin/env python3
"""Exhaustively probe the declared cyclic lesson schedule and query rotations.

This is intentionally small and model-free.  It materializes one complete
``EXAMPLES_NEEDED + 1`` window for every declared schedule residue in every
band, then asks the generator's executable ``lesson_identifiable`` hook to
check every possible held-out query.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

TASK_ID = "a3fcfe29ef7e"
SCHEMA = "a3fcfe29ef7e-schedule-probe-v1"
BANDS = ("easy", "medium", "hard")


def _load_generator(repo_root: Path) -> ModuleType:
    runtime = repo_root / "shared" / "runtime"
    if runtime.is_dir():
        sys.path.insert(0, str(runtime))
    path = repo_root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"schedule_probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pair(generator: ModuleType, grid: list[list[int]]) -> dict[str, Any]:
    return {"input": grid, "output": generator.rule_mirror(grid)}


def probe(generator: ModuleType, *, seed: int = 0) -> dict[str, Any]:
    period = int(generator.LESSON_SCHEDULE_PERIOD)
    demo_count = int(generator.EXAMPLES_NEEDED)
    failures: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    invalid_pairs = 0
    ambiguous_rotations = 0

    for band_index, band in enumerate(BANDS):
        band_seed = int(seed) + band_index * 1_000_003
        for start in range(period):
            materialized: list[dict[str, Any]] = []
            profiles: list[str] = []
            for offset in range(demo_count + 1):
                sample_index = start + offset
                grid = generator.generate(
                    band_seed,
                    sample_index,
                    difficulty=band,
                )
                errors = generator.self_check(grid)
                if errors:
                    invalid_pairs += 1
                    failures.append(
                        {
                            "kind": "invalid_pair",
                            "band": band,
                            "start": start,
                            "sample_index": sample_index,
                            "errors": errors,
                        }
                    )
                materialized.append(_pair(generator, grid))
                profiles.append(
                    generator.schedule_profile(band_seed, sample_index, band)
                )

            for query_index, query in enumerate(materialized):
                demos = [
                    item for index, item in enumerate(materialized)
                    if index != query_index
                ]
                reasons = generator.lesson_identifiable(demos, query)
                if reasons:
                    ambiguous_rotations += 1
                    failures.append(
                        {
                            "kind": "ambiguous_rotation",
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "profiles": profiles,
                            "reasons": reasons,
                            "query": query,
                        }
                    )
                rows.append(
                    {
                        "band": band,
                        "start": start,
                        "query_index": query_index,
                        "profiles": profiles,
                        "identifiable": not reasons,
                        "reasons": reasons,
                    }
                )

    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "seed": int(seed),
        "contract": {
            "examples_needed": demo_count,
            "lesson_schedule_period": period,
            "bands": list(BANDS),
        },
        "summary": {
            "bands": len(BANDS),
            "schedule_starts": len(BANDS) * period,
            "query_rotations": len(rows),
            "invalid_pairs": invalid_pairs,
            "ambiguous_rotations": ambiguous_rotations,
        },
        "failures": failures,
        "rotations": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    parser.add_argument("--seed", type=int, default=20261008)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    generator = _load_generator(repo_root)
    report = probe(generator, seed=args.seed)
    source = repo_root / "generators" / TASK_ID / "generator.py"
    report["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()

    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
