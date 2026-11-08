#!/usr/bin/env python3
"""Reproducible shortcut/distribution probe for generator d53534afb2ff.

The probe deliberately reads the generator's *declared* shortcut and competitor
mappings rather than duplicating their names.  It verifies canonical-fit claims,
materializes one exact generated disagreement per rival, and checks every cyclic
start of the four-example teaching schedule.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs  # noqa: E402


def _load_generator():
    source = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location("probe_generator_d53534afb2ff", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _pair_id(pair: dict[str, Any]) -> str:
    return f"v{pair['variant']}:{pair['split']}:{pair['pair_index']}"


def _first(values: Iterable[int], count: int) -> tuple[int, ...]:
    result = tuple(values)
    if len(result) < count:
        raise ValueError(f"need at least {count} seeds, got {len(result)}")
    return result[:count]


def run_probe(
    *,
    per_band: int = 100,
    seeds: Iterable[int] | None = None,
) -> dict[str, Any]:
    """Return a JSON-safe report bound to the current generator bytes."""
    if type(per_band) is not int or per_band <= 0:
        raise ValueError("per_band must be a positive integer")

    generator = _load_generator()
    source = TASK_DIR / "generator.py"
    seed_values = _first(range(per_band) if seeds is None else seeds, per_band)
    pairs = canonical_pairs(generator.TASK_ID, root=REPO)

    canonical_report: dict[str, Any] = {}
    for name, rival in sorted(generator.CANONICAL_SHORTCUTS.items()):
        disagreements = [
            _pair_id(pair)
            for pair in pairs
            if rival(pair["input"]) != pair["output"]
        ]
        canonical_report[name] = {
            "fits_all_pairs": not disagreements,
            "pair_count": len(pairs),
            "disagreements": disagreements,
        }

    competitor_names = tuple(sorted(generator.LESSON_COMPETITORS))
    profile_counts: Counter[str] = Counter()
    profile_role_palettes: dict[str, set[tuple[tuple[int, ...], ...]]] = defaultdict(set)
    witness_counts: Counter[str] = Counter()
    first_witnesses: dict[str, Any] = {}
    unique_inputs: set[str] = set()
    unresolved_lessons: list[dict[str, Any]] = []
    lesson_count = 0
    schedule_size = int(generator.EXAMPLES_NEEDED)
    cyclic_starts = tuple(range(schedule_size))

    for difficulty in ("easy", "medium", "hard"):
        for seed in seed_values:
            # Eight unique positions cover two complete cycles while the window
            # checks below exercise every possible cyclic start.
            samples: dict[int, tuple[list[list[int]], list[list[int]], str]] = {}
            for sample_index in range(schedule_size * 2):
                grid = generator.generate(seed, sample_index, difficulty=difficulty)
                intended = generator.rule_mirror(grid)
                profile = generator.observe_overrides(grid)["scene_profile"]
                analysis = generator.analyze_scene(grid)
                palette_signature = (
                    tuple(sorted(frame["color"] for frame in analysis["frames"])),
                    tuple(sorted(obj["color"] for obj in analysis["inside_objects"])),
                    tuple(sorted(obj["color"] for obj in analysis["outside_objects"])),
                )
                profile_role_palettes[profile].add(palette_signature)
                samples[sample_index] = (grid, intended, profile)
                profile_counts[profile] += 1
                unique_inputs.add(_grid_key(grid))
                for name, rival in sorted(generator.LESSON_COMPETITORS.items()):
                    rival_output = rival(grid)
                    if rival_output != intended:
                        witness_counts[name] += 1
                        first_witnesses.setdefault(
                            name,
                            {
                                "difficulty": difficulty,
                                "seed": seed,
                                "sample_index": sample_index,
                                "scene_profile": profile,
                                "input": grid,
                                "intended_output": intended,
                                "rival_output": rival_output,
                            },
                        )

            for start in cyclic_starts:
                demos = [
                    {
                        "input": samples[start + offset][0],
                        "output": samples[start + offset][1],
                    }
                    for offset in range(schedule_size)
                ]
                query_grid, query_output, query_profile = samples[start + schedule_size]
                lesson_count += 1
                for name, rival in sorted(generator.LESSON_COMPETITORS.items()):
                    fits_demos = all(
                        rival(demo["input"]) == demo["output"] for demo in demos
                    )
                    differs_on_query = rival(query_grid) != query_output
                    if fits_demos and differs_on_query:
                        unresolved_lessons.append(
                            {
                                "difficulty": difficulty,
                                "seed": seed,
                                "cyclic_start": start,
                                "query_profile": query_profile,
                                "rival": name,
                            }
                        )

    missing = sorted(set(competitor_names) - set(first_witnesses))
    return {
        "schema": "d53534afb2ff-review-probe-v1",
        "task_id": generator.TASK_ID,
        "generator_version": generator.VERSION,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash": generator.RULE_HASH,
        "canonical_pair_count": len(pairs),
        "canonical_shortcuts": canonical_report,
        "lesson_competitors": list(competitor_names),
        "sampling": {
            "bands": ["easy", "medium", "hard"],
            "seeds_per_band": per_band,
            "seed_values": list(seed_values),
            "sample_indices_per_seed": list(range(schedule_size * 2)),
            "draws_total": 3 * per_band * schedule_size * 2,
            "unique_inputs": len(unique_inputs),
            "profile_counts": dict(sorted(profile_counts.items())),
            "profile_role_palette_signatures": {
                profile: len(signatures)
                for profile, signatures in sorted(profile_role_palettes.items())
            },
            "rival_disagreement_counts": dict(sorted(witness_counts.items())),
        },
        "lesson_policy": {
            "demos_per_lesson": schedule_size,
            "cyclic_starts_tested": list(cyclic_starts),
            "lessons_tested": lesson_count,
            "unresolved_lessons": unresolved_lessons,
        },
        "first_generated_witnesses": first_witnesses,
        "errors": (
            ([f"no generated disagreement for rivals: {missing}"] if missing else [])
            + (["one or more canonical shortcut declarations do not fit all canonical pairs"]
               if any(not item["fits_all_pairs"] for item in canonical_report.values()) else [])
            + (["one or more cyclic lessons leave a declared rival unresolved"]
               if unresolved_lessons else [])
            + (["one or more profiles encode a fixed role palette"]
               if any(len(signatures) < 2 for signatures in profile_role_palettes.values()) else [])
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run_probe(per_band=args.per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(args.out),
        "draws": report["sampling"]["draws_total"],
        "lessons": report["lesson_policy"]["lessons_tested"],
        "errors": report["errors"],
    }, sort_keys=True))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
