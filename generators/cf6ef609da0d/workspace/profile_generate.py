#!/usr/bin/env python3
"""Measure deterministic generation latency across difficulty bands.

This authoring probe distinguishes a genuinely slow or failing placement profile
from an interrupted outer harness.  It is source-bound, records observable axes,
and exits nonzero when any requested draw fails.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from typing import Any

SCRIPT = Path(__file__).resolve()
TASK_ROOT = SCRIPT.parents[1]
REPO_ROOT = SCRIPT.parents[3]
GENERATOR_PATH = TASK_ROOT / "generator.py"
RUNTIME = REPO_ROOT / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"generation_profiler_{TASK_ROOT.name}", GENERATOR_PATH
    )
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_report(*, seeds: int, bands: list[str]) -> dict[str, Any]:
    if seeds < 1:
        raise ValueError("seeds must be at least 1")
    generator = _load_generator()
    draws: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for band in bands:
        for ordinal in range(seeds):
            seed = ordinal + 1
            sample_index = ordinal + 1
            started = time.perf_counter()
            try:
                grid = generator.generate(
                    seed, sample_index, difficulty=band
                )
                elapsed = time.perf_counter() - started
                draws.append(
                    {
                        "difficulty": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "elapsed_seconds": elapsed,
                        "height": len(grid),
                        "width": len(grid[0]),
                        "observed_axes": generator.observe_overrides(grid),
                        "self_check_errors": generator.self_check(grid),
                    }
                )
            except Exception as exc:  # diagnostic: retain exact profile/error
                elapsed = time.perf_counter() - started
                failures.append(
                    {
                        "difficulty": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "elapsed_seconds": elapsed,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )

    return {
        "schema": "arcpuzzles-generation-profile-v1",
        "task_id": str(generator.TASK_ID),
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "bands": bands,
        "requested_seeds_per_band": seeds,
        "draws": draws,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument(
        "--bands",
        nargs="+",
        choices=("easy", "medium", "hard"),
        default=["easy", "medium", "hard"],
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        report = build_report(seeds=args.seeds, bands=list(args.bands))
    except ValueError as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "task_id": report["task_id"],
                "generator_sha256": report["generator_sha256"],
                "draws": len(report["draws"]),
                "failures": len(report["failures"]),
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
