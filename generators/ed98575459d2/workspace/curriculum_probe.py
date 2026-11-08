#!/usr/bin/env python3
"""Source-bound curriculum audit for ed98575459d2.

The probe intentionally discovers rivals from the generator's live
``CANONICAL_SHORTCUTS`` and ``LESSON_COMPETITORS`` declarations.  It checks
canonical fit, every cyclic start of the deterministic profile schedule, and a
small production-sampler census.  It also materializes one ordinary generated
witness for each canonical-fitting shortcut.

Run from the packet root:

    python3 run_with_racket.py python3 \
      generators/ed98575459d2/workspace/curriculum_probe.py \
      --lessons-per-band 25 --out ../checks/curriculum-probe.json
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "ed98575459d2"
HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parent / "generator.py"
DIFFICULTIES = (None, "easy", "medium", "hard")


def _load_generator(path: Path = GENERATOR_PATH):
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _demo(generator, grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {
        "input": copy.deepcopy(grid),
        "output": generator.rule_mirror(grid),
    }


def _grid_sha256(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _difficulty_label(value: str | None) -> str:
    return "default" if value is None else value


def build_report(
    *,
    generator,
    canonical_root: str | Path,
    seed: int = 20261004,
    lessons_per_band: int = 25,
) -> dict[str, Any]:
    """Build a JSON-serializable, source-bound curriculum report."""
    if type(lessons_per_band) is not int or lessons_per_band < 1:
        raise ValueError("lessons_per_band must be a positive integer")

    canonical = canonical_pairs(TASK_ID, root=Path(canonical_root))
    shortcuts: dict[str, Any] = {}
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        matches = [rival(pair["input"]) == pair["output"] for pair in canonical]
        shortcuts[name] = {
            "matched_canonical_pairs": sum(matches),
            "canonical_pair_count": len(matches),
            "fits_all_canonical_pairs": all(matches),
        }

    schedule_len = len(generator.SCHEDULE_PROFILES)
    failed_windows: list[dict[str, Any]] = []
    surviving_windows: list[dict[str, Any]] = []
    cyclic_windows: list[dict[str, Any]] = []
    competitor_stats = {
        name: {"cyclic_windows": 0, "refuted_windows": 0, "surviving_windows": 0}
        for name in generator.LESSON_COMPETITORS
    }

    for difficulty in DIFFICULTIES:
        for start in range(schedule_len):
            pairs = [
                _demo(generator, generator.generate(seed, start + offset, difficulty=difficulty))
                for offset in range(generator.EXAMPLES_NEEDED + 1)
            ]
            demos = pairs[: generator.EXAMPLES_NEEDED]
            query = pairs[generator.EXAMPLES_NEEDED]
            reasons = generator.lesson_identifiable(demos, query)
            label = _difficulty_label(difficulty)
            if reasons:
                failed_windows.append(
                    {"difficulty": label, "cyclic_start": start, "reasons": list(reasons)}
                )

            refuted: list[str] = []
            surviving: list[str] = []
            for name, rival in generator.LESSON_COMPETITORS.items():
                competitor_stats[name]["cyclic_windows"] += 1
                survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
                if survives:
                    competitor_stats[name]["surviving_windows"] += 1
                    surviving.append(name)
                    if rival(query["input"]) != query["output"]:
                        surviving_windows.append(
                            {
                                "difficulty": label,
                                "cyclic_start": start,
                                "competitor": name,
                            }
                        )
                else:
                    competitor_stats[name]["refuted_windows"] += 1
                    refuted.append(name)

            cyclic_windows.append(
                {
                    "difficulty": label,
                    "cyclic_start": start,
                    "profiles": [
                        generator.schedule_profile(seed, start + offset, difficulty)
                        for offset in range(generator.EXAMPLES_NEEDED)
                    ],
                    "identifiable": not reasons,
                    "refuted_competitors": sorted(refuted),
                    "surviving_competitors": sorted(surviving),
                }
            )

    sampled: dict[str, Any] = {}
    sampled_grid_hashes: set[str] = set()
    for difficulty in DIFFICULTIES:
        label = _difficulty_label(difficulty)
        refutations = {name: 0 for name in generator.LESSON_COMPETITORS}
        profile_counts = {name: 0 for name in generator.SCHEDULE_PROFILES}
        local_hashes: set[str] = set()
        for lesson_index in range(lessons_per_band):
            base = lesson_index * (generator.EXAMPLES_NEEDED + 1)
            demos = []
            for offset in range(generator.EXAMPLES_NEEDED):
                index = base + offset
                grid = generator.generate(seed + lesson_index, index, difficulty=difficulty)
                pair = _demo(generator, grid)
                demos.append(pair)
                digest = _grid_sha256(grid)
                local_hashes.add(digest)
                sampled_grid_hashes.add(digest)
                profile_counts[generator.schedule_profile(seed + lesson_index, index, difficulty)] += 1
            for name, rival in generator.LESSON_COMPETITORS.items():
                if any(rival(pair["input"]) != pair["output"] for pair in demos):
                    refutations[name] += 1
        sampled[label] = {
            "lessons": lessons_per_band,
            "demos_per_lesson": generator.EXAMPLES_NEEDED,
            "unique_demo_inputs": len(local_hashes),
            "profile_counts": profile_counts,
            "competitor_refutations": refutations,
        }

    witnesses: dict[str, Any] = {}
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        found = None
        for difficulty in DIFFICULTIES:
            for index in range(max(20, schedule_len * 4)):
                grid = generator.generate(seed, index, difficulty=difficulty)
                intended = generator.rule_mirror(grid)
                rival_output = rival(grid)
                if intended != rival_output:
                    found = {
                        "seed": seed,
                        "sample_index": index,
                        "difficulty": _difficulty_label(difficulty),
                        "profile": generator.schedule_profile(seed, index, difficulty),
                        "observable_axes": generator.observe_overrides(grid),
                        "validator_errors": generator.self_check(grid, difficulty=difficulty),
                        "input_sha256": _grid_sha256(grid),
                        "input": grid,
                        "intended_output": intended,
                        "rival_output": rival_output,
                        "rival_differs": True,
                    }
                    break
            if found is not None:
                break
        if found is None:
            witnesses[name] = {"rival_differs": False, "error": "no ordinary witness found"}
        else:
            witnesses[name] = found

    generator_sha = hashlib.sha256(Path(generator.__file__).read_bytes()).hexdigest()
    return {
        "schema": "arcpuzzles-task-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": generator_sha,
        "rule_hash": getattr(generator, "RULE_HASH", None),
        "seed": seed,
        "examples_needed": generator.EXAMPLES_NEEDED,
        "schedule_profiles": list(generator.SCHEDULE_PROFILES),
        "cyclic_start_count_per_band": schedule_len,
        "canonical_pair_count": len(canonical),
        "canonical_shortcuts": shortcuts,
        "lesson_competitors": competitor_stats,
        "cyclic_windows": cyclic_windows,
        "failed_windows": failed_windows,
        "surviving_competitor_windows": surviving_windows,
        "sampled_lessons_per_band": lessons_per_band,
        "sampled_bands": sampled,
        "sampled_unique_demo_inputs_all_bands": len(sampled_grid_hashes),
        "shortcut_witnesses": witnesses,
        "limitations": [
            "Finite checks cover declared rivals, not every conceivable learner hypothesis.",
            "The sampled census uses Python rule_mirror; Racket authority is checked separately by the battery/apply receipt.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261004)
    parser.add_argument("--lessons-per-band", type=int, default=25)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    generator = _load_generator()
    report = build_report(
        generator=generator,
        canonical_root=find_root(__file__),
        seed=args.seed,
        lessons_per_band=args.lessons_per_band,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 1 if report["failed_windows"] or report["surviving_competitor_windows"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
