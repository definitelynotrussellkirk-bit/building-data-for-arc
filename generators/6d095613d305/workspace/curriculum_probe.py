#!/usr/bin/env python3
"""Audit H49 lesson windows against the generator's declared semantic rivals.

The probe intentionally imports rival declarations from the generator instead of
maintaining a second rival-name list.  It samples every cyclic lesson start for
an explicit seed range and records enough source identity to reproduce counts.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "6d095613d305"
HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
RUNTIME = REPO_ROOT / "shared" / "runtime"
if RUNTIME.is_dir():
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(f"curriculum_probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _grid_sha256(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def audit_curriculum(*, seed_start: int, seed_count: int, bands: list[str]) -> dict[str, Any]:
    if seed_count <= 0:
        raise ValueError("seed_count must be positive")
    if not bands:
        raise ValueError("at least one difficulty band is required")

    gen = _load_generator()
    lesson_starts = list(range(len(gen.SCHEDULE_PROFILES)))
    sample_indices = list(range(max(lesson_starts) + gen.EXAMPLES_NEEDED + 1))
    seeds = list(range(seed_start, seed_start + seed_count))

    draws: dict[tuple[str, int, int], dict[str, Any]] = {}
    profile_counts: Counter[str] = Counter()
    rival_witness_counts: Counter[str] = Counter()
    strict_count = 0
    validation_failures: list[dict[str, Any]] = []

    for band in bands:
        for seed in seeds:
            for sample_index in sample_indices:
                grid = gen.generate(seed, sample_index, difficulty=band)
                errors = gen.self_check(grid)
                if errors:
                    validation_failures.append(
                        {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "errors": errors,
                        }
                    )
                output = gen.rule_mirror(grid)
                observed = gen.observe_overrides(grid)
                profile_counts[observed["crossing_profile"]] += 1
                if not gen.strict_canonical_like(grid):
                    strict_count += 1
                for name, rival in gen.LESSON_COMPETITORS.items():
                    if rival(grid) != output:
                        rival_witness_counts[name] += 1
                draws[(band, seed, sample_index)] = {
                    "input": grid,
                    "output": output,
                    "sha256": _grid_sha256(grid),
                    "profile": observed["crossing_profile"],
                }

    window_failures: list[dict[str, Any]] = []
    windows = 0
    expected_profiles = set(gen.SCHEDULE_PROFILES)
    for band in bands:
        for seed in seeds:
            for start in lesson_starts:
                windows += 1
                demos = [
                    {
                        "input": draws[(band, seed, index)]["input"],
                        "output": draws[(band, seed, index)]["output"],
                    }
                    for index in range(start, start + gen.EXAMPLES_NEEDED)
                ]
                query_record = draws[(band, seed, start + gen.EXAMPLES_NEEDED)]
                query = {"input": query_record["input"], "output": query_record["output"]}
                errors = list(gen.lesson_identifiable(demos, query))
                profiles = {
                    draws[(band, seed, index)]["profile"]
                    for index in range(start, start + gen.EXAMPLES_NEEDED)
                }
                if profiles != expected_profiles:
                    errors.append(
                        f"profile coverage {sorted(profiles)} != {sorted(expected_profiles)}"
                    )
                surviving = [
                    name
                    for name, rival in gen.LESSON_COMPETITORS.items()
                    if all(rival(pair["input"]) == pair["output"] for pair in demos)
                ]
                if surviving:
                    errors.append(f"surviving rivals: {surviving}")
                if errors:
                    window_failures.append(
                        {
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "errors": errors,
                            "demo_input_sha256": [
                                draws[(band, seed, index)]["sha256"]
                                for index in range(start, start + gen.EXAMPLES_NEEDED)
                            ],
                        }
                    )

    generator_path = TASK_DIR / "generator.py"
    generator_sha = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    unique_hashes = {record["sha256"] for record in draws.values()}
    report = {
        "schema": "h49_curriculum_probe/1",
        "task_id": TASK_ID,
        "generator_sha256": generator_sha,
        "rule_hash": gen.RULE_HASH,
        "sample_spec": {
            "bands": bands,
            "seed_start": seed_start,
            "seed_count": seed_count,
            "seed_stop_exclusive": seed_start + seed_count,
            "sample_indices": sample_indices,
            "lesson_starts": lesson_starts,
            "lesson_examples": gen.EXAMPLES_NEEDED,
        },
        "counts": {
            "draw_records": len(draws),
            "unique_draws": len(unique_hashes),
            "strict_canonical_like": strict_count,
            "lesson_windows": windows,
            "failed_windows": len(window_failures),
            "validation_failures": len(validation_failures),
        },
        "profile_counts": dict(sorted(profile_counts.items())),
        "rival_witness_counts": {
            name: rival_witness_counts[name]
            for name in sorted(gen.LESSON_COMPETITORS)
        },
        "validation_failures": validation_failures,
        "window_failures": window_failures,
    }
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=24)
    parser.add_argument(
        "--bands",
        nargs="+",
        default=["easy", "medium", "hard"],
        choices=["easy", "medium", "hard"],
    )
    parser.add_argument("--out", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = audit_curriculum(
        seed_start=args.seed_start,
        seed_count=args.seed_count,
        bands=list(args.bands),
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)
    return 1 if report["counts"]["failed_windows"] or report["counts"]["validation_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
