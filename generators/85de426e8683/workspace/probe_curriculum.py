#!/usr/bin/env python3
"""Audit cyclic lessons against the generator's declared shortcut rivals.

This is a fast distribution diagnostic, not a label authority. It uses the
reviewed Python mirror to compare each declared ``LESSON_COMPETITORS`` rule
against complete generated demonstration windows. The repository Racket
battery remains the source-of-truth check for labels.
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

SCRIPT = Path(__file__).resolve()
TASK_ROOT = SCRIPT.parents[1]
REPO_ROOT = SCRIPT.parents[3]
GENERATOR_PATH = TASK_ROOT / "generator.py"
RUNTIME = REPO_ROOT / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"curriculum_probe_{TASK_ROOT.name}", GENERATOR_PATH
    )
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot import {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_report(*, seed: int, starts: int, difficulty: str) -> dict[str, Any]:
    gen = _load_generator()
    lesson_size = int(gen.EXAMPLES_NEEDED)
    windows: list[dict[str, Any]] = []
    profile_counts: Counter[str] = Counter()
    unique_indices: set[int] = set()

    for start in range(starts):
        demos = []
        scene_summaries = []
        for sample_index in range(start, start + lesson_size):
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            output = gen.rule_mirror(grid)
            facts = gen._analyze_scene(grid)
            profile = str(facts.get("scene_profile"))
            profile_counts[profile] += 1
            unique_indices.add(sample_index)
            demos.append({"input": grid, "output": output})
            scene_summaries.append(
                {
                    "sample_index": sample_index,
                    "scene_profile": profile,
                    "height": len(grid),
                    "width": len(grid[0]),
                    "target_count": len(facts["targets"]),
                    "decoy_sizes": sorted(len(component) for component in facts["decoys"]),
                    "target_slopes": sorted(facts["slopes"]),
                    "distractor_colors": sorted(
                        {value for _, _, value in facts["non_gray_cells"]}
                    ),
                }
            )

        survivors = sorted(
            name
            for name, competitor in gen.LESSON_COMPETITORS.items()
            if all(competitor(item["input"]) == item["output"] for item in demos)
        )
        declared_findings = list(gen.lesson_identifiable(demos))
        windows.append(
            {
                "start": start,
                "sample_indices": list(range(start, start + lesson_size)),
                "scenes": scene_summaries,
                "surviving_competitors": survivors,
                "lesson_identifiable_findings": declared_findings,
            }
        )

    source_bytes = GENERATOR_PATH.read_bytes()
    return {
        "schema": "arc-curriculum-rival-probe-v1",
        "task_id": str(gen.TASK_ID),
        "generator_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "rule_hash": str(gen.RULE_HASH),
        "seed": seed,
        "difficulty": difficulty,
        "lesson_size": lesson_size,
        "lesson_windows": starts,
        "generated_demo_occurrences": starts * lesson_size,
        "unique_sample_indices": len(unique_indices),
        "sample_index_range": [min(unique_indices), max(unique_indices)] if unique_indices else None,
        "profile_occurrences": dict(sorted(profile_counts.items())),
        "declared_competitors": sorted(gen.LESSON_COMPETITORS),
        "all_windows_identifiable": all(
            not window["surviving_competitors"]
            and not window["lesson_identifiable_findings"]
            for window in windows
        ),
        "windows": windows,
        "authority_note": (
            "Diagnostic mirror only; use the repository Racket battery for "
            "authoritative output verification."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261002)
    parser.add_argument("--starts", type=int, default=8)
    parser.add_argument(
        "--difficulty", choices=("easy", "medium", "hard"), default="medium"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.starts < 1:
        parser.error("--starts must be at least 1")
    report = build_report(seed=args.seed, starts=args.starts, difficulty=args.difficulty)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "task_id": report["task_id"],
                "generator_sha256": report["generator_sha256"],
                "lesson_windows": report["lesson_windows"],
                "unique_sample_indices": report["unique_sample_indices"],
                "all_windows_identifiable": report["all_windows_identifiable"],
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0 if report["all_windows_identifiable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
