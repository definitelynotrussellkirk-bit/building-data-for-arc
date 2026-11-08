#!/usr/bin/env python3
"""Exhaust the finite lesson schedule against the generator's declared rivals.

This is an authoring probe, not an authority oracle.  It uses the selected
Python generator and its declared semantic contracts to check every cyclic
four-pair lesson start in a requested range, every query rotation, and the
native profile-floor seed recipe.  Racket-labelled production checks remain the
source of truth; this tool is intended to catch schedule regressions quickly
before running the heavier battery and lesson census.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

WORKSPACE = Path(__file__).resolve().parent
TASK_HOME = WORKSPACE.parent
REPO_ROOT = TASK_HOME.parents[1]
sys.path.insert(0, str(REPO_ROOT / "shared" / "runtime"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "ffdc0ddb44bd_curriculum_probe", TASK_HOME / "generator.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load selected generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_hash(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _pair(gen: Any, grid: list[list[int]]) -> dict[str, Any]:
    return {"input": grid, "output": gen.rule_mirror(deepcopy(grid))}


def _profile_floor_seed(task_id: str, band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{task_id}:{band}:{index}".encode("utf-8")
    ).hexdigest()
    return int(digest[:12], 16)


def run_probe(*, starts: int, seed: int) -> dict[str, Any]:
    gen = _load_generator()
    generator_raw = (TASK_HOME / "generator.py").read_bytes()
    rivals = dict(gen.LESSON_COMPETITORS)
    bands: dict[str, Any] = {}
    failures: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()

    for band in ("easy", "medium", "hard"):
        band_rotations = 0
        band_pairs = 0
        witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        profile_counts = {str(profile): 0 for profile in gen.SCHEDULE_PROFILES}

        for start in range(starts):
            lesson_seed = seed + start
            pairs = []
            for offset in range(4):
                sample_index = start + offset
                grid = gen.generate(
                    lesson_seed,
                    sample_index,
                    difficulty=band,
                )
                unique_inputs.add(_grid_hash(grid))
                profile = gen.schedule_profile(lesson_seed, sample_index, band)
                profile_counts[str(profile)] += 1
                for name, witness in gen.SEMANTIC_WITNESSES.items():
                    witness_hits[name] += int(bool(witness(deepcopy(grid))))
                pairs.append(_pair(gen, grid))
                band_pairs += 1

            for query_index, query in enumerate(pairs):
                demos = [
                    pair for index, pair in enumerate(pairs) if index != query_index
                ]
                reasons = gen.lesson_identifiable(deepcopy(demos), deepcopy(query))
                surviving = []
                for name, rival in rivals.items():
                    if all(
                        rival(deepcopy(pair["input"])) == pair["output"]
                        for pair in demos
                    ) and rival(deepcopy(query["input"])) != query["output"]:
                        surviving.append(name)
                if reasons or surviving:
                    failures.append(
                        {
                            "band": band,
                            "start": start,
                            "lesson_seed": lesson_seed,
                            "query_index": query_index,
                            "hook_reasons": reasons,
                            "surviving_rivals": surviving,
                            "input_hashes": [
                                _grid_hash(pair["input"]) for pair in pairs
                            ],
                        }
                    )
                band_rotations += 1

        exact_profiles = 0
        floor_profiles: list[dict[str, Any]] = []
        for index in range(20):
            floor_seed = _profile_floor_seed(gen.TASK_ID, band, index)
            sample_index = floor_seed % 7919 + index
            grid = gen.generate(floor_seed, sample_index, difficulty=band)
            palette_size = len({value for row in grid for value in row})
            profile = [len(grid), len(grid[0]), palette_size]
            is_exact = tuple(profile) in {(9, 16, 4), (10, 16, 4)}
            exact_profiles += int(is_exact)
            floor_profiles.append(
                {
                    "index": index,
                    "seed": floor_seed,
                    "sample_index": sample_index,
                    "profile": profile,
                    "exact_canonical_profile": is_exact,
                }
            )

        bands[band] = {
            "lesson_windows": starts,
            "materialized_pairs": band_pairs,
            "query_rotations": band_rotations,
            "schedule_profile_counts": profile_counts,
            "witness_hits": witness_hits,
            "profile_floor_exact_hits": exact_profiles,
            "profile_floor_draws": 20,
            "profile_floor_samples": floor_profiles,
        }
        if exact_profiles < 1:
            failures.append(
                {
                    "band": band,
                    "kind": "profile_floor",
                    "message": "no exact canonical profile in the pinned 20-draw census",
                }
            )

    return {
        "schema": "ffdc0ddb44bd-curriculum-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(generator_raw).hexdigest(),
        "declared_rule_hash": gen.RULE_HASH,
        "lesson_policy": {
            "pairs_per_window": 4,
            "demonstrations_per_rotation": 3,
            "queries_per_rotation": 1,
            "cyclic_starts_per_band": starts,
            "bands": ["easy", "medium", "hard"],
            "base_seed": seed,
        },
        "declared_rivals": sorted(rivals),
        "bands": bands,
        "summary": {
            "lesson_windows": starts * 3,
            "materialized_pairs": starts * 4 * 3,
            "query_rotations": starts * 4 * 3,
            "unique_inputs": len(unique_inputs),
            "failures": len(failures),
        },
        "limitations": [
            "Checks only the finite schedule starts requested by --starts.",
            "Checks only declared competitors; undeclared plausible rules may survive.",
            "Uses the Python rule mirror; the Racket battery and lesson census remain authoritative.",
        ],
        "failures": failures,
        "status": "passed" if not failures else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starts", type=int, default=32)
    parser.add_argument("--seed", type=int, default=1207)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.starts < 1:
        parser.error("--starts must be positive")

    report = run_probe(starts=args.starts, seed=args.seed)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(rendered, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
        print(args.out)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
