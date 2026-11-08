#!/usr/bin/env python3
"""Source-bound lesson probe for generator 9fe97c2dd8a4.

The probe intentionally reads the generator's live ``LESSON_COMPETITORS`` and
``CANONICAL_SHORTCUTS`` declarations instead of maintaining a second rival
list.  It audits all five cyclic schedule starts, reports overlapping-draw and
unique-input counts separately, and records whether any declared rival survives
all demonstrations in a lesson.
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

TASK_ID = "9fe97c2dd8a4"
HERE = Path(__file__).resolve()
GENERATOR_PATH = HERE.parents[1] / "generator.py"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(payload)


def _load_generator():
    source_hash = _sha256_bytes(GENERATOR_PATH.read_bytes())
    name = f"lesson_probe_generator_{TASK_ID}_{source_hash[:12]}"
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module, source_hash


def _data_root() -> Path:
    for root in HERE.parents:
        for candidate in (root / "shared" / "data", root / "data"):
            if (candidate / "canonical" / "puzzles.jsonl").is_file():
                return candidate
    raise RuntimeError("canonical data root not found")


def _canonical_row() -> dict[str, Any]:
    path = _data_root() / "canonical" / "puzzles.jsonl"
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"canonical row {TASK_ID} not found in {path}")


def _fits(rule, pairs: list[dict[str, Any]]) -> bool:
    return all(
        rule(copy.deepcopy(pair["input"])) == pair["output"]
        for pair in pairs
    )


def run_probe(*, lessons_per_band: int = 100) -> dict[str, Any]:
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")

    gen, source_hash = _load_generator()
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}) or {})
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}) or {})
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}) or {})
    canonical = _canonical_row()
    train_pairs = list(canonical.get("train", []))
    test_pairs = list(canonical.get("test", []))
    all_pairs = train_pairs + test_pairs

    canonical_rule_results: dict[str, Any] = {}
    for declaration, rules in (
        ("LESSON_COMPETITORS", competitors),
        ("CANONICAL_SHORTCUTS", shortcuts),
    ):
        canonical_rule_results[declaration] = {
            name: {
                "fits_training_demonstrations": _fits(rule, train_pairs),
                "fits_all_canonical_pairs": _fits(rule, all_pairs),
                "training_pairs": len(train_pairs),
                "all_pairs": len(all_pairs),
            }
            for name, rule in sorted(rules.items())
        }

    bands: dict[str, Any] = {}
    all_unique_inputs: set[str] = set()
    for difficulty in ("easy", "medium", "hard"):
        unique_inputs: set[str] = set()
        profile_counts: Counter[str] = Counter()
        witness_counts: Counter[str] = Counter()
        competitor_survivals: Counter[str] = Counter()
        competitor_query_changes: Counter[str] = Counter()
        hook_failures: list[dict[str, Any]] = []
        survivor_examples: list[dict[str, Any]] = []
        sampled_draws = 0
        surviving_lessons = 0

        for lesson_index in range(lessons_per_band):
            # Enumerate every cyclic start before advancing the seed.  At 100
            # lessons this is exactly seeds 0..19 x starts 0..4.
            seed, start = divmod(lesson_index, 5)
            demos: list[dict[str, Any]] = []
            for offset in range(gen.EXAMPLES_NEEDED):
                sample_index = start + offset
                grid = gen.generate(
                    seed, sample_index, difficulty=difficulty
                )
                output = gen.rule_mirror(grid)
                demos.append({"input": grid, "output": output})
                sampled_draws += 1
                digest = _grid_hash(grid)
                unique_inputs.add(digest)
                all_unique_inputs.add(digest)
                profile = gen.schedule_profile(
                    seed, sample_index, difficulty=difficulty
                )
                profile_counts[str(profile)] += 1
                for name, predicate in witnesses.items():
                    if predicate(copy.deepcopy(grid)):
                        witness_counts[name] += 1

            query_index = start + gen.EXAMPLES_NEEDED
            query_grid = gen.generate(
                seed, query_index, difficulty=difficulty
            )
            query = {
                "input": query_grid,
                "output": gen.rule_mirror(query_grid),
            }
            sampled_draws += 1
            digest = _grid_hash(query_grid)
            unique_inputs.add(digest)
            all_unique_inputs.add(digest)
            profile = gen.schedule_profile(
                seed, query_index, difficulty=difficulty
            )
            profile_counts[str(profile)] += 1
            for name, predicate in witnesses.items():
                if predicate(copy.deepcopy(query_grid)):
                    witness_counts[name] += 1

            surviving: list[str] = []
            query_changing: list[str] = []
            for name, competitor in sorted(competitors.items()):
                if all(
                    competitor(copy.deepcopy(pair["input"]))
                    == pair["output"]
                    for pair in demos
                ):
                    competitor_survivals[name] += 1
                    surviving.append(name)
                    if (
                        competitor(copy.deepcopy(query["input"]))
                        != query["output"]
                    ):
                        competitor_query_changes[name] += 1
                        query_changing.append(name)

            if surviving:
                surviving_lessons += 1
                if len(survivor_examples) < 5:
                    survivor_examples.append(
                        {
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "cyclic_start": start,
                            "survivors": surviving,
                            "query_changing": query_changing,
                        }
                    )

            reasons = gen.lesson_identifiable(demos, query)
            if reasons and len(hook_failures) < 5:
                hook_failures.append(
                    {
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "cyclic_start": start,
                        "reasons": list(reasons),
                    }
                )

        bands[difficulty] = {
            "lessons": lessons_per_band,
            "lesson_policy": (
                "seed=lesson_index//5; cyclic_start=lesson_index%5; "
                f"{gen.EXAMPLES_NEEDED} consecutive demos plus one query"
            ),
            "sampled_draws_with_overlap": sampled_draws,
            "unique_inputs": len(unique_inputs),
            "schedule_profile_counts": dict(sorted(profile_counts.items())),
            "witness_firings_on_overlapping_draws": dict(
                sorted(witness_counts.items())
            ),
            "competitor_survival_counts": {
                name: competitor_survivals.get(name, 0)
                for name in sorted(competitors)
            },
            "competitor_query_change_counts": {
                name: competitor_query_changes.get(name, 0)
                for name in sorted(competitors)
            },
            "surviving_lessons": surviving_lessons,
            "identifiable_lessons": lessons_per_band - len(hook_failures),
            "hook_failure_examples": hook_failures,
            "survivor_examples": survivor_examples,
        }

    return {
        "schema": "arcpuzzles-task-local-lesson-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH),
        "generator_sha256": source_hash,
        "examples_needed": int(gen.EXAMPLES_NEEDED),
        "schedule_profiles": list(gen.SCHEDULE_PROFILES),
        "declared_lesson_competitors": sorted(competitors),
        "declared_canonical_shortcuts": sorted(shortcuts),
        "canonical_rule_results": canonical_rule_results,
        "axis_contract": gen.AXES,
        "sampler": (
            f"{lessons_per_band} lessons per band; cyclic starts 0..4; "
            "seeds advance after each complete five-start cycle; outputs use "
            "the source-bound Python rule mirror, whose Racket parity is "
            "checked separately by the battery"
        ),
        "bands": bands,
        "unique_inputs_all_bands": len(all_unique_inputs),
        "limitations": [
            "This finite probe measures the declared sampler and rivals; it does not prove universal induction.",
            "Overlapping cyclic lesson windows reuse draws; unique-input counts are reported separately.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe(lessons_per_band=args.lessons_per_band)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(payload, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
        print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
