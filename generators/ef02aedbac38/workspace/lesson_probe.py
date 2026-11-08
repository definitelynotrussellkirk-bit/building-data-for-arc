#!/usr/bin/env python3
"""Source-bound curriculum probe for ef02aedbac38.

The probe uses fixed-seed lessons with sample indices 0..3 as demonstrations
and index 4 as the query.  It measures input uniqueness, density-role coverage,
semantic-rival disagreements, and `lesson_identifiable` over every lesson.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_ID = "ef02aedbac38"
BANDS = ("easy", "medium", "hard")


def _sha256_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_hash(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_inputs(canonical_path: Path) -> list[list[list[int]]]:
    for line in canonical_path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return [
                pair["input"]
                for split in ("train", "test")
                for pair in row[split]
            ]
    raise RuntimeError(f"canonical task {TASK_ID} not found in {canonical_path}")


def _role(grid: list[list[int]]) -> str:
    five = sum(value == 5 for row in grid for value in row)
    other = sum(value != 5 for row in grid for value in row)
    if five > other:
        return "dense"
    if five < other:
        return "sparse"
    return "tie"


def audit(generator_path: Path, canonical_path: Path, lessons: int) -> dict[str, Any]:
    gen = _load_generator(generator_path)
    canonical = _canonical_inputs(canonical_path)
    rivals = dict(gen.LESSON_COMPETITORS)
    canonical_fit = {
        name: all(rival(grid) == gen._rule_mirror(grid) for grid in canonical)
        for name, rival in rivals.items()
    }

    report: dict[str, Any] = {
        "schema": "ef02aedbac38-density-lesson-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": _sha256_bytes(generator_path),
        "generator_version": gen.VERSION,
        "canonical_path": str(canonical_path),
        "canonical_sha256": _sha256_bytes(canonical_path),
        "lessons_per_band": lessons,
        "sampler": {
            "seed": "0..lessons_per_band-1",
            "demonstration_sample_indices": [0, 1, 2, 3],
            "query_sample_index": 4,
            "shared_seed_within_lesson": True,
            "difficulty_bands": list(BANDS),
        },
        "domain_limits": {
            "dimensions": "3..25 by 3..25",
            "palette": "exactly {5, X}, X in 1..4 or 6..9",
            "per_color_minimum_cells": 2,
            "minimum_total_4_connected_components": 3,
            "each_color_spans": "at least two rows and two columns",
            "claim_scope": "sampled generator lessons only; no universal induction claim",
        },
        "canonical_rival_fit": canonical_fit,
        "bands": {},
    }

    for band in BANDS:
        unique_inputs: set[str] = set()
        role_windows = 0
        identifiable = 0
        failures: list[dict[str, Any]] = []
        rival_stats = {
            name: {
                "generated_input_disagreements": 0,
                "lessons_killed_by_demo": 0,
                "query_disagreements": 0,
                "query_relevant_and_killed": 0,
            }
            for name in rivals
        }

        for seed in range(lessons):
            grids = [gen.generate(seed, index, difficulty=band) for index in range(5)]
            for grid in grids:
                errors = gen.self_check(grid)
                if errors:
                    failures.append({"seed": seed, "kind": "self_check", "errors": errors})
                unique_inputs.add(_grid_hash(grid))

            demos = [
                {"input": grid, "output": gen._rule_mirror(grid)}
                for grid in grids[:4]
            ]
            query = {"input": grids[4]}
            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                failures.append({"seed": seed, "kind": "lesson", "reasons": reasons})
            else:
                identifiable += 1

            novel_roles = {
                _role(grid)
                for grid in grids[:4]
                if gen.strict_canonical_like(grid)
            }
            if {"sparse", "dense"} <= novel_roles:
                role_windows += 1
            else:
                failures.append(
                    {
                        "seed": seed,
                        "kind": "density_roles",
                        "observed_novel_roles": sorted(novel_roles),
                    }
                )

            for name, rival in rivals.items():
                demo_disagreements = [
                    rival(demo["input"]) != demo["output"] for demo in demos
                ]
                query_disagrees = rival(query["input"]) != gen._rule_mirror(query["input"])
                rival_stats[name]["generated_input_disagreements"] += sum(
                    rival(grid) != gen._rule_mirror(grid) for grid in grids
                )
                rival_stats[name]["lessons_killed_by_demo"] += any(demo_disagreements)
                rival_stats[name]["query_disagreements"] += query_disagrees
                rival_stats[name]["query_relevant_and_killed"] += (
                    query_disagrees and any(demo_disagreements)
                )

        report["bands"][band] = {
            "lessons": lessons,
            "generated_inputs": lessons * 5,
            "unique_inputs": len(unique_inputs),
            "balanced_density_demo_windows": role_windows,
            "identifiable_lessons": identifiable,
            "rivals": rival_stats,
            "failures": failures,
        }

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--canonical", type=Path)
    args = parser.parse_args()
    if args.lessons < 1:
        parser.error("--lessons must be positive")

    task_dir = Path(__file__).resolve().parent.parent
    repo_root = task_dir.parents[1]
    generator_path = (args.generator or task_dir / "generator.py").resolve()
    canonical_path = (
        args.canonical or repo_root / "shared/data/canonical/puzzles.jsonl"
    ).resolve()
    result = audit(generator_path, canonical_path, args.lessons)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    failure_count = sum(len(row["failures"]) for row in result["bands"].values())
    for band, row in result["bands"].items():
        print(
            f"{band}: identifiable={row['identifiable_lessons']}/{row['lessons']} "
            f"balanced={row['balanced_density_demo_windows']}/{row['lessons']} "
            f"unique={row['unique_inputs']}/{row['generated_inputs']}"
        )
    print(f"wrote {args.out}; failures={failure_count}")
    return 1 if failure_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
