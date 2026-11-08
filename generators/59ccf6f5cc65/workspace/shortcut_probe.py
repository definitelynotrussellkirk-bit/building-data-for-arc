#!/usr/bin/env python3
"""Declaration-driven shortcut and lesson probe for task 59ccf6f5cc65.

The probe intentionally reads the generator's public semantic declarations rather
than maintaining a second hard-coded rival list.  It checks canonical train/test
behavior, generated witness/rival disagreements, and every requested cyclic lesson
start.  Outputs are deterministic JSON suitable for retaining under ``checks/``.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "59ccf6f5cc65"
HERE = Path(__file__).resolve().parent
TASK_DIR = HERE.parent
GENERATOR_PATH = TASK_DIR / "generator.py"
REPO_ROOT = TASK_DIR.parents[1]
RUNTIME_DIR = REPO_ROOT / "shared" / "runtime"
if RUNTIME_DIR.exists() and str(RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR))

from reviewer_support import canonical_pairs, find_root  # noqa: E402

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _orange_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 7
    }
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        cells = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for dr, dc in _CARDINAL:
                neighbor = row + dr, col + dc
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        components.append(cells)
    return components


def independent_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent exact-cell oracle: recolor orange components at real corners."""
    out = copy.deepcopy(grid)
    height, width = len(grid), len(grid[0])
    corners = {(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)}
    for component in _orange_components(grid):
        if component & corners:
            for row, col in component:
                out[row][col] = 1
    return out


def _band_label(difficulty: str | None) -> str:
    return "default" if difficulty is None else difficulty


def _canonical_report(gen, pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for name, rival in sorted(gen.SEMANTIC_RIVALS.items()):
        comparisons = []
        for pair in pairs:
            predicted = rival(pair["input"])
            expected = pair["output"]
            comparisons.append(
                {
                    "split": pair.get("split"),
                    "pair_index": pair.get("pair_index"),
                    "fits": predicted == expected,
                    "input": pair["input"] if predicted != expected else None,
                    "expected": expected if predicted != expected else None,
                    "rival_output": predicted if predicted != expected else None,
                }
            )
        train = [item for item in comparisons if item["split"] == "train"]
        test = [item for item in comparisons if item["split"] == "test"]
        rows.append(
            {
                "name": name,
                "fits_all_train": bool(train) and all(item["fits"] for item in train),
                "fits_all_test": bool(test) and all(item["fits"] for item in test),
                "fits_all_canonical": all(item["fits"] for item in comparisons),
                "comparisons": comparisons,
            }
        )
    return rows


def build_report(*, per_band: int = 16, lesson_starts: int = 16, seed: int = 20261004) -> dict[str, Any]:
    if per_band < 1 or lesson_starts < 1:
        raise ValueError("per_band and lesson_starts must both be positive")
    gen = _load_generator()
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))

    witness_counts = Counter({name: 0 for name in gen.SEMANTIC_WITNESSES})
    rival_disagreements = Counter({name: 0 for name in gen.SEMANTIC_RIVALS})
    profile_counts: Counter[str] = Counter()
    observed_axis_counts: dict[str, Counter[str]] = {
        name: Counter() for name in gen.AXES
    }
    mirror_mismatches: list[dict[str, Any]] = []
    witness_claim_failures: list[dict[str, Any]] = []

    generated_count = 0
    for band_index, difficulty in enumerate((None, "easy", "medium", "hard")):
        for sample_index in range(per_band):
            sample_seed = seed + 1000 * band_index + sample_index
            grid = gen.generate(sample_seed, sample_index, difficulty=difficulty)
            intended = independent_output(grid)
            generated_count += 1
            profile_counts[f"{len(grid)}x{len(grid[0])}/p{len({v for row in grid for v in row})}"] += 1
            observed = gen.observe_overrides(grid)
            for name, value in observed.items():
                observed_axis_counts[name][str(value)] += 1
            if gen.rule_mirror(grid) != intended:
                mirror_mismatches.append(
                    {
                        "difficulty": _band_label(difficulty),
                        "seed": sample_seed,
                        "sample_index": sample_index,
                        "input": grid,
                        "independent_output": intended,
                        "rule_mirror_output": gen.rule_mirror(grid),
                    }
                )
            for name, rival in gen.SEMANTIC_RIVALS.items():
                if rival(grid) != intended:
                    rival_disagreements[name] += 1
            for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
                if not witness(grid):
                    continue
                witness_counts[witness_name] += 1
                for rival_name in gen.WITNESS_RIVALS.get(witness_name, ()):
                    if gen.SEMANTIC_RIVALS[rival_name](grid) == intended:
                        witness_claim_failures.append(
                            {
                                "difficulty": _band_label(difficulty),
                                "seed": sample_seed,
                                "sample_index": sample_index,
                                "witness": witness_name,
                                "rival": rival_name,
                                "input": grid,
                            }
                        )

    lessons = []
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        for start in range(lesson_starts):
            lesson_seed = seed + 100_000 + 1000 * band_index + start
            pairs_for_lesson = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(
                    lesson_seed,
                    start + offset,
                    difficulty=difficulty,
                )
                pairs_for_lesson.append(
                    {"input": grid, "output": independent_output(grid)}
                )
            demos = pairs_for_lesson[:-1]
            query = pairs_for_lesson[-1]
            survivors = []
            query_changing_survivors = []
            for name, rival in sorted(gen.LESSON_COMPETITORS.items()):
                if all(rival(pair["input"]) == pair["output"] for pair in demos):
                    survivors.append(name)
                    if rival(query["input"]) != query["output"]:
                        query_changing_survivors.append(name)
            lessons.append(
                {
                    "difficulty": difficulty,
                    "seed": lesson_seed,
                    "start": start,
                    "demo_indices": list(range(start, start + gen.EXAMPLES_NEEDED)),
                    "query_index": start + gen.EXAMPLES_NEEDED,
                    "survivors": survivors,
                    "query_changing_survivors": query_changing_survivors,
                    "hook_reasons": gen.lesson_identifiable(demos, query),
                }
            )

    canonical_mirror_mismatches = []
    for pair in pairs:
        independent = independent_output(pair["input"])
        if independent != pair["output"] or gen.rule_mirror(pair["input"]) != pair["output"]:
            canonical_mirror_mismatches.append(
                {
                    "split": pair.get("split"),
                    "pair_index": pair.get("pair_index"),
                    "input": pair["input"],
                    "expected": pair["output"],
                    "independent_output": independent,
                    "rule_mirror_output": gen.rule_mirror(pair["input"]),
                }
            )

    return {
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(REPO_ROOT)),
        "generator_version": gen.VERSION,
        "generator_sha256": _sha256(GENERATOR_PATH),
        "rule_hash": gen.RULE_HASH,
        "parameters": {
            "per_band": per_band,
            "lesson_starts": lesson_starts,
            "seed": seed,
            "generated_count": generated_count,
            "lesson_count": len(lessons),
            "lesson_policy": (
                f"{gen.EXAMPLES_NEEDED} consecutive demos and the next generated pair as query; "
                "all requested cyclic starts tested for easy/medium/hard"
            ),
        },
        "declared_rivals": sorted(gen.SEMANTIC_RIVALS),
        "declared_witnesses": sorted(gen.SEMANTIC_WITNESSES),
        "witness_rivals": {
            name: list(rivals) for name, rivals in sorted(gen.WITNESS_RIVALS.items())
        },
        "canonical_rivals": _canonical_report(gen, pairs),
        "canonical_mirror_mismatches": canonical_mirror_mismatches,
        "generated_rule_mirror_mismatches": mirror_mismatches,
        "generated_witness_claim_failures": witness_claim_failures,
        "generated_witness_counts": dict(sorted(witness_counts.items())),
        "generated_rival_disagreement_counts": dict(sorted(rival_disagreements.items())),
        "generated_profile_counts": dict(sorted(profile_counts.items())),
        "generated_observed_axis_counts": {
            name: dict(sorted(counts.items()))
            for name, counts in sorted(observed_axis_counts.items())
        },
        "lessons": lessons,
    }


def _has_failures(report: dict[str, Any]) -> bool:
    return bool(
        report["canonical_mirror_mismatches"]
        or report["generated_rule_mirror_mismatches"]
        or report["generated_witness_claim_failures"]
        or any(item["query_changing_survivors"] for item in report["lessons"])
        or any(item["hook_reasons"] for item in report["lessons"])
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=16)
    parser.add_argument("--lesson-starts", type=int, default=16)
    parser.add_argument("--seed", type=int, default=20261004)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = build_report(
        per_band=args.per_band,
        lesson_starts=args.lesson_starts,
        seed=args.seed,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 1 if _has_failures(report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
