#!/usr/bin/env python3
"""Source-bound lesson census for generator 6058ff1ae20c.

The probe samples complete three-demo-plus-query lessons from the generator's
actual default schedule.  It scores the generator's declared competitors
against ``rule_mirror``; the battery's rule-smoke and semantic gates separately
bind that mirror/contract to the canonical Racket authority.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


TASK_ID = "6058ff1ae20c"
PROBE_VERSION = "lesson-probe-v1"
TASK_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_ROOT / "generator.py"


def _load_generator():
    name = f"lesson_probe_{TASK_ID}"
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _seed(band: str, lesson_index: int) -> int:
    payload = f"{PROBE_VERSION}|{TASK_ID}|{band}|{lesson_index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _freeze(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _grid_stats(grid) -> dict[str, Any]:
    marks = [value for row in grid for value in row if value]
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "palette_size": len({value for row in grid for value in row}),
        "seed_count": len(marks),
        "distinct_seed_colors": len(set(marks)),
    }


def run_probe(*, lessons_per_band: int) -> dict[str, Any]:
    if lessons_per_band < 100:
        raise ValueError("lessons_per_band must be at least 100")
    gen = _load_generator()
    source_sha256 = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    bands = ("easy", "medium", "hard")
    n_demos = gen.EXAMPLES_NEEDED

    result: dict[str, Any] = {
        "schema": "arc-generator-lesson-probe/1",
        "task_id": TASK_ID,
        "probe_version": PROBE_VERSION,
        "generator": {
            "path": str(GENERATOR_PATH),
            "sha256": source_sha256,
            "version": gen.VERSION,
            "rule_hash": gen.RULE_HASH,
        },
        "sampler": {
            "bands": list(bands),
            "lessons_per_band": lessons_per_band,
            "examples_per_lesson": n_demos,
            "queries_per_lesson": 1,
            "seed_formula": (
                "uint64_be(sha256('lesson-probe-v1|TASK_ID|band|lesson_index')[:8])"
            ),
            "sample_index_formula": (
                "lesson_start = lesson_index * 11; use consecutive indexes "
                "lesson_start..lesson_start+EXAMPLES_NEEDED for demos+query"
            ),
            "overrides": {},
            "output_authority_for_probe": "generator.rule_mirror",
            "authority_binding": (
                "canonical-pair regression + battery rule_smoke/semantic_gate"
            ),
        },
        "declared_domain": {
            "axes": gen.AXES,
            "scene_profiles": list(gen.SCENE_PROFILES),
            "difficulty_bands": list(bands),
            "grid_dimension_limits": [5, 12],
            "seed_count_limits": [1, 2],
        },
        "bands": {},
        "totals": {},
        "failures": [],
    }

    total_lessons = 0
    total_inputs = 0
    total_unique_inputs = 0
    total_identifiability_failures = 0
    total_contract_failures = 0

    for band in bands:
        seen_inputs: set[tuple[tuple[int, ...], ...]] = set()
        profiles: Counter[str] = Counter()
        schedule_profiles: Counter[str] = Counter()
        rival_disagreements: Counter[str] = Counter()
        rival_demo_survivals: Counter[str] = Counter()
        heights: list[int] = []
        widths: list[int] = []
        palette_sizes: list[int] = []
        seed_counts: list[int] = []
        distinct_seed_colors: list[int] = []
        invalid_inputs = 0
        strict_rejections = 0
        identifiability_failures = 0
        lesson_rival_survivors: Counter[str] = Counter()
        examples: list[dict[str, Any]] = []

        for lesson_index in range(lessons_per_band):
            seed = _seed(band, lesson_index)
            start = lesson_index * 11
            episode = []
            for offset in range(n_demos + 1):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                errors = gen.self_check(grid)
                strict_errors = gen.strict_canonical_like(grid)
                if errors:
                    invalid_inputs += 1
                    if len(examples) < 8:
                        examples.append({
                            "kind": "self_check",
                            "lesson_index": lesson_index,
                            "sample_index": sample_index,
                            "errors": list(errors),
                        })
                if strict_errors:
                    strict_rejections += 1
                    if len(examples) < 8:
                        examples.append({
                            "kind": "strict_canonical_like",
                            "lesson_index": lesson_index,
                            "sample_index": sample_index,
                            "errors": list(strict_errors),
                        })

                observed = gen.observe_overrides(grid)
                profile = observed["scene_profile"]
                scheduled = gen.schedule_profile(seed, sample_index, band)
                profiles[profile] += 1
                schedule_profiles[scheduled] += 1
                if profile != scheduled and len(examples) < 8:
                    examples.append({
                        "kind": "schedule_mismatch",
                        "lesson_index": lesson_index,
                        "sample_index": sample_index,
                        "observed": profile,
                        "scheduled": scheduled,
                    })

                stats = _grid_stats(grid)
                heights.append(stats["height"])
                widths.append(stats["width"])
                palette_sizes.append(stats["palette_size"])
                seed_counts.append(stats["seed_count"])
                distinct_seed_colors.append(stats["distinct_seed_colors"])
                seen_inputs.add(_freeze(grid))

                output = gen.rule_mirror(grid)
                for name, rival in gen.LESSON_COMPETITORS.items():
                    if rival(grid) != output:
                        rival_disagreements[name] += 1
                episode.append({"input": grid, "output": output})

            demos = episode[:n_demos]
            query = episode[-1]
            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                identifiability_failures += 1
                if len(examples) < 8:
                    examples.append({
                        "kind": "lesson_identifiable",
                        "lesson_index": lesson_index,
                        "reasons": list(reasons),
                    })

            for name, rival in gen.LESSON_COMPETITORS.items():
                fits_all_demos = all(
                    rival(item["input"]) == item["output"] for item in demos
                )
                if fits_all_demos:
                    rival_demo_survivals[name] += 1
                    if rival(query["input"]) != query["output"]:
                        lesson_rival_survivors[name] += 1

        sampled_inputs = lessons_per_band * (n_demos + 1)
        band_report = {
            "lessons": lessons_per_band,
            "sampled_inputs": sampled_inputs,
            "unique_inputs": len(seen_inputs),
            "duplicate_inputs": sampled_inputs - len(seen_inputs),
            "profile_counts": dict(sorted(profiles.items())),
            "scheduled_profile_counts": dict(sorted(schedule_profiles.items())),
            "observed_limits": {
                "grid_h": [min(heights), max(heights)],
                "grid_w": [min(widths), max(widths)],
                "palette_size": [min(palette_sizes), max(palette_sizes)],
                "seed_count": [min(seed_counts), max(seed_counts)],
                "distinct_seed_colors": [
                    min(distinct_seed_colors), max(distinct_seed_colors)
                ],
            },
            "self_check_rejections": invalid_inputs,
            "strict_rejections": strict_rejections,
            "rival_grid_disagreements": dict(sorted(rival_disagreements.items())),
            "rival_survived_all_demos": dict(sorted(rival_demo_survivals.items())),
            "rival_survived_demos_and_changed_query": dict(
                sorted(lesson_rival_survivors.items())
            ),
            "lesson_identifiability_failures": identifiability_failures,
            "failure_examples": examples,
        }
        result["bands"][band] = band_report

        total_lessons += lessons_per_band
        total_inputs += sampled_inputs
        total_unique_inputs += len(seen_inputs)
        total_identifiability_failures += identifiability_failures
        total_contract_failures += invalid_inputs + strict_rejections

    result["totals"] = {
        "lessons": total_lessons,
        "sampled_inputs": total_inputs,
        "unique_inputs_summed_within_bands": total_unique_inputs,
        "lesson_identifiability_failures": total_identifiability_failures,
        "self_or_strict_contract_failures": total_contract_failures,
    }

    for band, report in result["bands"].items():
        if report["lesson_identifiability_failures"]:
            result["failures"].append(
                f"{band}: {report['lesson_identifiability_failures']} lessons unidentifiable"
            )
        if report["self_check_rejections"] or report["strict_rejections"]:
            result["failures"].append(
                f"{band}: generated inputs violated self/strict contract"
            )
        for name in gen.LESSON_COMPETITORS:
            if report["rival_grid_disagreements"].get(name, 0) == 0:
                result["failures"].append(
                    f"{band}: competitor {name!r} never disagreed"
                )
            if report["rival_survived_all_demos"].get(name, 0):
                result["failures"].append(
                    f"{band}: competitor {name!r} survived at least one demo window"
                )

    result["status"] = "PASS" if not result["failures"] else "FAIL"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lessons-per-band", type=int, default=120)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run_probe(lessons_per_band=args.lessons_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "out": str(args.out),
        "totals": report["totals"],
    }, sort_keys=True))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
