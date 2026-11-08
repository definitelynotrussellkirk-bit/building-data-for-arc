#!/usr/bin/env python3
"""Source-bound qualification probe for future reviewers of task 382eb0e592eb.

The shared battery remains authoritative.  This small task-local tool fills two
review-specific gaps cheaply: it proves that every declared canonical shortcut
really fits every labeled canonical pair, and it exhausts every cyclic start and
query rotation of the declared deterministic lesson schedule.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "382eb0e592eb"
DEFAULT_BANDS = ("easy", "medium", "hard")
SCHEMA = f"{TASK_ID}-qualification-v1"


def _pair(generator: Any, grid: list[list[int]]) -> dict[str, Any]:
    return {"input": grid, "output": generator.rule_mirror(grid)}


def qualify(seed: int = 0, bands: tuple[str, ...] = DEFAULT_BANDS) -> dict[str, Any]:
    """Return a deterministic, JSON-serializable qualification report."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if not bands or any(band not in {"easy", "medium", "hard"} for band in bands):
        raise ValueError("bands must contain easy, medium, and/or hard")

    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)

    shortcut_failures: list[dict[str, Any]] = []
    shortcut_names = sorted(generator.CANONICAL_SHORTCUTS)
    for name in shortcut_names:
        rival = generator.CANONICAL_SHORTCUTS[name]
        for pair in canonical:
            predicted = rival(pair["input"])
            if predicted != pair["output"]:
                shortcut_failures.append(
                    {
                        "rival": name,
                        "variant": pair["variant"],
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                        "predicted": predicted,
                        "expected": pair["output"],
                    }
                )

    period = int(generator.LESSON_SCHEDULE_PERIOD)
    pair_count = int(generator.EXAMPLES_NEEDED) + 1
    observed_profiles: set[str] = set()
    ambiguous_rotations: list[dict[str, Any]] = []
    lesson_windows = 0
    query_rotations = 0
    window_records: list[dict[str, Any]] = []

    for band in bands:
        for start in range(period):
            pairs = []
            profiles = []
            for offset in range(pair_count):
                sample_index = start + offset
                grid = generator.generate(seed, sample_index, difficulty=band)
                profile = generator.observe_overrides(grid)["scene_profile"]
                observed_profiles.add(profile)
                profiles.append(profile)
                pairs.append(_pair(generator, grid))
            lesson_windows += 1
            rotation_results = []
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                errors = generator.lesson_identifiable(demos, query)
                query_rotations += 1
                rotation_results.append(
                    {"query_index": query_index, "errors": list(errors)}
                )
                if errors:
                    ambiguous_rotations.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "profiles": profiles,
                            "errors": list(errors),
                        }
                    )
            window_records.append(
                {
                    "band": band,
                    "start": start,
                    "profiles": profiles,
                    "rotations": rotation_results,
                }
            )

    expected_profiles = sorted(generator.SCHEDULE_PROFILES)
    competitor_names = sorted(generator.LESSON_COMPETITORS)
    registries_agree = shortcut_names == competitor_names
    schedule_complete = sorted(observed_profiles) == expected_profiles
    passed = (
        not shortcut_failures
        and not ambiguous_rotations
        and registries_agree
        and schedule_complete
    )

    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "passed": passed,
        "source": {
            "path": str(source_path),
            "sha256": source_sha256,
            "rule_hash": generator.RULE_HASH,
            "file_sha256_recomputed": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        },
        "canonical_shortcuts": {
            "names": shortcut_names,
            "canonical_pair_count": len(canonical),
            "claims_checked": len(shortcut_names) * len(canonical),
            "all_fit": not shortcut_failures,
            "failures": shortcut_failures,
        },
        "lesson_competitors": {
            "names": competitor_names,
            "same_names_as_canonical_shortcuts": registries_agree,
        },
        "schedule": {
            "seed": seed,
            "bands": list(bands),
            "period": period,
            "demonstrations_per_rotation": generator.EXAMPLES_NEEDED,
            "pairs_per_window": pair_count,
            "lesson_windows": lesson_windows,
            "query_rotations": query_rotations,
            "observed_profiles": sorted(observed_profiles),
            "expected_profiles": expected_profiles,
            "all_profiles_observed": schedule_complete,
            "ambiguous_rotations": ambiguous_rotations,
            "windows": window_records,
        },
        "limits": [
            "This exhausts declared cyclic start residues at one fixed seed, not all seeds.",
            "Only declared executable rivals are tested; universal identifiability is not claimed.",
            "Racket parity and distributional sampling remain responsibilities of the shared battery/census.",
        ],
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = qualify(seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "lesson_windows": report["schedule"]["lesson_windows"],
                "query_rotations": report["schedule"]["query_rotations"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
