#!/usr/bin/env python3
"""Source-bound lesson census for generator ``bb432515d2e6``.

The probe deliberately reads competitor declarations from the selected generator
rather than duplicating a rival-name list.  It checks every cyclic lesson start
in a requested deterministic range, verifies the canonical-shortcut declaration
against all canonical pairs, and emits a compact JSON report suitable for review
evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]
REPO = HERE.parents[3]
GEN_PATH = TASK_DIR / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_sha256(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_generator():
    spec = importlib.util.spec_from_file_location("lesson_probe_bb432515d2e6", GEN_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GEN_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize_grid(grid: Any) -> list[list[int]]:
    return [
        [int(value) for value in row] if isinstance(row, str) else [int(value) for value in row]
        for row in grid
    ]


def _canonical_pairs(task_id: str) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != task_id:
                continue
            for pair in row.get("train", []) + [row.get("test")]:
                if not pair:
                    continue
                pairs.append(
                    {
                        "input": _normalize_grid(pair["input"]),
                        "output": _normalize_grid(pair["output"]),
                    }
                )
    return pairs


def run_probe(*, starts_per_band: int = 100, seed: int = 20261003) -> dict[str, Any]:
    if starts_per_band < 1:
        raise ValueError("starts_per_band must be positive")
    gen = _load_generator()
    difficulties = ("easy", "medium", "hard")
    competitor_names = sorted(gen.LESSON_COMPETITORS)
    witness_names = sorted(gen.SEMANTIC_WITNESSES)

    lesson_failures: list[dict[str, Any]] = []
    survivor_counts: Counter[str] = Counter({name: 0 for name in competitor_names})
    witness_counts: Counter[str] = Counter({name: 0 for name in witness_names})
    profile_counts: Counter[str] = Counter()
    unique_demo_hashes: set[str] = set()
    unique_query_hashes: set[str] = set()
    lessons_by_band: Counter[str] = Counter()

    for difficulty in difficulties:
        for start in range(starts_per_band):
            lessons_by_band[difficulty] += 1
            demos: list[dict[str, Any]] = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                validation = gen.self_check(grid, difficulty=difficulty)
                if validation:
                    lesson_failures.append(
                        {
                            "difficulty": difficulty,
                            "start": start,
                            "kind": "self_check",
                            "sample_index": sample_index,
                            "reasons": validation,
                        }
                    )
                observation = gen.observe_overrides(grid)
                profile_counts[observation["profile"]] += 1
                for name, witness in gen.SEMANTIC_WITNESSES.items():
                    if witness(grid):
                        witness_counts[name] += 1
                unique_demo_hashes.add(_grid_sha256(grid))
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})

            query_index = start + gen.EXAMPLES_NEEDED
            query_grid = gen.generate(seed, query_index, difficulty=difficulty)
            unique_query_hashes.add(_grid_sha256(query_grid))
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                lesson_failures.append(
                    {
                        "difficulty": difficulty,
                        "start": start,
                        "kind": "lesson_identifiable",
                        "reasons": reasons,
                    }
                )

            for name, competitor in gen.LESSON_COMPETITORS.items():
                if all(competitor(pair["input"]) == pair["output"] for pair in demos):
                    survivor_counts[name] += 1

    canonical_pairs = _canonical_pairs(gen.TASK_ID)
    canonical_shortcut_failures: list[dict[str, Any]] = []
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        mismatches = [
            index
            for index, pair in enumerate(canonical_pairs)
            if shortcut(pair["input"]) != pair["output"]
        ]
        if mismatches:
            canonical_shortcut_failures.append(
                {"shortcut": name, "mismatching_pair_indices": mismatches}
            )

    lesson_count = sum(lessons_by_band.values())
    return {
        "schema": "bb432515d2e6-lesson-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": file_sha256(GEN_PATH),
        "rule_hash": gen.RULE_HASH,
        "seed": seed,
        "difficulties": list(difficulties),
        "starts_per_band": starts_per_band,
        "lesson_policy": (
            f"{gen.EXAMPLES_NEEDED} consecutive demonstrations from every start; "
            "the following sample is the query"
        ),
        "examples_per_lesson": gen.EXAMPLES_NEEDED,
        "lesson_count": lesson_count,
        "lessons_by_band": dict(lessons_by_band),
        "overlapping_demo_windows": True,
        "unique_demo_inputs": len(unique_demo_hashes),
        "unique_query_inputs": len(unique_query_hashes),
        "lesson_failure_count": len(lesson_failures),
        "lesson_failures": lesson_failures,
        "competitors": competitor_names,
        "competitor_survivor_counts": {
            name: int(survivor_counts[name]) for name in competitor_names
        },
        "witness_counts_over_overlapping_demo_slots": {
            name: int(witness_counts[name]) for name in witness_names
        },
        "profile_counts_over_overlapping_demo_slots": dict(profile_counts),
        "canonical_pair_count": len(canonical_pairs),
        "canonical_shortcuts": sorted(gen.CANONICAL_SHORTCUTS),
        "canonical_shortcut_failures": canonical_shortcut_failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--starts-per-band", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20261003)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(starts_per_band=args.starts_per_band, seed=args.seed)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    if report["lesson_failure_count"] or report["canonical_shortcut_failures"]:
        raise SystemExit(1)
    if any(report["competitor_survivor_counts"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
