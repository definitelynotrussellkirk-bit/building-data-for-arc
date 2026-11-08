#!/usr/bin/env python3
"""Measure whether generated lessons teach per-target corner orientation.

The canonical rule is local to each 2x2 window.  A weaker solver can inspect the
first target in a grid, remember its missing-corner orientation, and complete only
targets with that same orientation.  This probe checks whether that rival fits
canonical pairs and sampled generator outputs, then supplies a lawful mixed-
orientation witness on which it must disagree.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "552c2402dce3"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_generator(repo: Path):
    runtime = repo / "shared" / "runtime"
    sys.path.insert(0, str(runtime))
    source = repo / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_generator_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def _canonical_record(canonical_path: Path) -> dict[str, Any]:
    with canonical_path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise KeyError(f"task {TASK_ID} not found in {canonical_path}")


def _normalize_rows(rows: list[str] | list[list[int]]) -> list[list[int]]:
    return [[int(value) for value in row] if isinstance(row, str) else list(row) for row in rows]


def _broadcast_first_orientation(gen, grid):
    """Complete only targets matching the first target's missing orientation."""
    normalized = gen._normalize_grid(grid)
    targets = gen._target_windows(normalized)
    if not targets:
        return [row[:] for row in normalized]
    return gen._fill_targets(normalized, allowed_missing={targets[0]["missing"]})


def _mixed_orientation_witness() -> list[list[int]]:
    grid = [[0] * 9 for _ in range(7)]
    # Reading-order target: missing top-left at anchor (1, 1).
    for cell in ((1, 2), (2, 1), (2, 2)):
        grid[cell[0]][cell[1]] = 8
    # Second target: missing bottom-right at anchor (4, 5).
    for cell in ((4, 5), (4, 6), (5, 5)):
        grid[cell[0]][cell[1]] = 8
    return grid


def run(repo: Path, seeds: int, samples: int) -> dict[str, Any]:
    gen, generator_path = _load_generator(repo)
    canonical_path = repo / "shared" / "data" / "canonical" / "puzzles.jsonl"
    canonical = _canonical_record(canonical_path)

    canonical_results = []
    canonical_pairs = [
        *(('train', index, pair) for index, pair in enumerate(canonical["train"])),
        ('test', 0, canonical["test"]),
    ]
    for split, index, pair in canonical_pairs:
        input_grid = _normalize_rows(pair["input"])
        expected = _normalize_rows(pair["output"])
        canonical_results.append(
            {
                "split": split,
                "pair_index": index,
                "target_orientations": [
                    target["missing"] for target in gen._target_windows(input_grid)
                ],
                "broadcast_matches_expected": _broadcast_first_orientation(gen, input_grid)
                == expected,
            }
        )

    orientation_cardinality = Counter()
    broadcast_mismatches: list[dict[str, Any]] = []
    sampled = 0
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(seeds):
            for sample_index in range(samples):
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                targets = gen._target_windows(grid)
                orientations = sorted({target["missing"] for target in targets})
                orientation_cardinality[str(len(orientations))] += 1
                official = gen._solve_true_local_rule(grid)
                rival = _broadcast_first_orientation(gen, grid)
                if rival != official:
                    broadcast_mismatches.append(
                        {
                            "difficulty": difficulty,
                            "seed": seed,
                            "sample_index": sample_index,
                            "orientations": orientations,
                        }
                    )
                sampled += 1

    witness = _mixed_orientation_witness()
    witness_info, witness_errors = gen._analyze(witness)
    witness_official = gen._solve_true_local_rule(witness)
    witness_rival = _broadcast_first_orientation(gen, witness)

    canonical_train_fit = all(
        item["broadcast_matches_expected"]
        for item in canonical_results
        if item["split"] == "train"
    )
    canonical_test_rejects = any(
        not item["broadcast_matches_expected"]
        for item in canonical_results
        if item["split"] == "test"
    )
    mixed_count = sum(
        count for cardinality, count in orientation_cardinality.items() if int(cardinality) > 1
    )
    common_evidence = (
        canonical_train_fit
        and canonical_test_rejects
        and witness_errors == []
        and witness_rival != witness_official
    )

    return {
        "schema": "mixed-orientation-gap-probe/1",
        "task_id": TASK_ID,
        "generator_sha256": _sha256(generator_path),
        "canonical_sha256": _sha256(canonical_path),
        "sample_plan": {
            "difficulties": [None, "easy", "medium", "hard"],
            "seed_range": [0, seeds - 1],
            "sample_index_range": [0, samples - 1],
            "total": sampled,
        },
        "generated": {
            "orientation_cardinality_histogram": dict(sorted(orientation_cardinality.items())),
            "mixed_orientation_count": mixed_count,
            "broadcast_rival_mismatch_count": len(broadcast_mismatches),
            "first_mismatches": broadcast_mismatches[:10],
        },
        "canonical": canonical_results,
        "lawful_mixed_witness": {
            "input": witness,
            "self_check_errors": gen.self_check(witness),
            "analysis_errors": witness_errors,
            "target_orientations": (
                list(witness_info["missing_corners"]) if witness_info is not None else []
            ),
            "official_output": witness_official,
            "broadcast_rival_output": witness_rival,
            "rival_differs": witness_rival != witness_official,
        },
        "gap_present": common_evidence and len(broadcast_mismatches) == 0,
        "gap_closed": (
            common_evidence
            and mixed_count == sampled
            and len(broadcast_mismatches) == sampled
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--samples", type=int, default=16)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--expect", choices=("any", "gap", "closed"), default="any")
    args = parser.parse_args()
    if args.seeds < 1 or args.samples < 1:
        parser.error("--seeds and --samples must be positive")

    repo = Path(__file__).resolve().parents[3]
    report = run(repo, args.seeds, args.samples)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    if args.expect == "gap":
        return 0 if report["gap_present"] else 1
    if args.expect == "closed":
        return 0 if report["gap_closed"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
