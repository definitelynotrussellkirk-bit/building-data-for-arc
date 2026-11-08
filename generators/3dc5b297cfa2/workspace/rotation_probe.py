#!/usr/bin/env python3
"""Exhaust the declared curriculum period under every one-query rotation."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

TASK_ID = "3dc5b297cfa2"
BANDS = ("easy", "medium", "hard")
HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def _seed_for(band: str, start: int, repetition: int) -> int:
    payload = f"{TASK_ID}|rotation-probe-v1|{band}|{start}|{repetition}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _load_generator():
    spec = importlib.util.spec_from_file_location("rotation_probe_generator", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_probe(*, seeds_per_start: int = 10) -> dict[str, Any]:
    """Check every period start, band, seed, and held-out pair."""
    if type(seeds_per_start) is not int or seeds_per_start < 1:
        raise ValueError("seeds_per_start must be a positive literal integer")

    gen = _load_generator()
    profiles = list(gen.SCHEDULE_PROFILES)
    period = len(profiles)
    failures: list[dict[str, Any]] = []
    lessons = 0
    rotations = 0
    minimum_black_demos = 2
    unique_inputs: set[str] = set()

    for band in BANDS:
        for start in range(period):
            for repetition in range(seeds_per_start):
                seed = _seed_for(band, start, repetition)
                pairs: list[dict[str, Any]] = []
                black_flags: list[bool] = []
                input_hashes: list[str] = []
                for offset in range(3):
                    sample_index = start + offset
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    errors = gen.self_check(grid, difficulty=band)
                    if errors:
                        failures.append(
                            {
                                "kind": "self_check",
                                "band": band,
                                "start": start,
                                "repetition": repetition,
                                "seed": seed,
                                "sample_index": sample_index,
                                "details": errors,
                            }
                        )
                    digest = _grid_hash(grid)
                    unique_inputs.add(digest)
                    input_hashes.append(digest)
                    black_flags.append(bool(gen.observe_overrides(grid)["black_shape"]))
                    pairs.append({"input": grid, "output": gen.rule_mirror(copy.deepcopy(grid))})

                lessons += 1
                for query_index in range(3):
                    rotations += 1
                    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                    black_demo_count = sum(
                        flag for index, flag in enumerate(black_flags) if index != query_index
                    )
                    minimum_black_demos = min(minimum_black_demos, black_demo_count)
                    reasons = gen.lesson_identifiable(demos, pairs[query_index])
                    if reasons:
                        failures.append(
                            {
                                "kind": "ambiguous_rotation",
                                "band": band,
                                "start": start,
                                "repetition": repetition,
                                "seed": seed,
                                "query_index": query_index,
                                "sample_indices": [start, start + 1, start + 2],
                                "profiles": [
                                    gen.schedule_profile(seed, start + offset, band)
                                    for offset in range(3)
                                ],
                                "black_shape": black_flags,
                                "input_sha256": input_hashes,
                                "details": reasons,
                            }
                        )

    ambiguous = sum(item["kind"] == "ambiguous_rotation" for item in failures)
    return {
        "schema": "3dc5b297cfa2-rotation-probe-v1",
        "status": "PASS" if not failures else "FAIL",
        "task_id": TASK_ID,
        "source_binding": {
            "generator_path": str(GENERATOR_PATH.relative_to(ROOT)),
            "generator_sha256": _sha256(GENERATOR_PATH),
            "declared_rule_hash": getattr(gen, "RULE_HASH", None),
            "probe_path": str(HERE.relative_to(ROOT)),
            "probe_sha256": _sha256(HERE),
        },
        "schedule_profiles": profiles,
        "schedule_starts": period,
        "bands": list(BANDS),
        "seeds_per_start": seeds_per_start,
        "lessons": lessons,
        "rotations": rotations,
        "ambiguous_rotations": ambiguous,
        "minimum_black_demos_after_holdout": minimum_black_demos,
        "unique_inputs": len(unique_inputs),
        "failure_count": len(failures),
        "failure_examples": failures[:20],
        "limits": [
            "This exhausts schedule starts and held-out positions, but samples a finite number of deterministic seeds.",
            "Only declared lesson competitors are tested; unnamed shortcuts may remain.",
            "The canonical Racket rule is unchanged; labels here use the source-bound Python mirror and are separately checked by the standard rule-smoke stage.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds-per-start", type=int, default=10)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run_probe(seeds_per_start=args.seeds_per_start)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        f"rotation-probe {report['status']}: {report['lessons']} lessons, "
        f"{report['rotations']} rotations, {report['ambiguous_rotations']} ambiguous"
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
