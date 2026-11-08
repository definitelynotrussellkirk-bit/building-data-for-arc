#!/usr/bin/env python3
"""Source-bound lesson census for generator 7213d98ef029.

The shared semantic gate is intentionally small.  This probe uses the generator's
actual four-example schedule and declared competitors to census larger cohorts
without claiming universal induction.  It records the exact generator hash,
sampler, domain limits, unique-input count, and rival disagreements.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


BANDS = ("easy", "medium", "hard")


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(
        f"lesson_probe_generator_{hashlib.sha256(path.read_bytes()).hexdigest()[:16]}",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def run_probe(
    *,
    generator_path: Path,
    lessons_per_band: int = 100,
    seed_base: int = 72_130,
) -> dict[str, Any]:
    generator_path = Path(generator_path).resolve()
    if lessons_per_band <= 0:
        raise ValueError("lessons_per_band must be positive")

    source_bytes = generator_path.read_bytes()
    gen = _load_generator(generator_path)
    lesson_width = int(gen.EXAMPLES_NEEDED)
    if lesson_width != len(gen.SCENE_PROFILES):
        raise AssertionError(
            "probe assumes one scheduled demo per declared scene profile: "
            f"width={lesson_width}, scenes={len(gen.SCENE_PROFILES)}"
        )

    report: dict[str, Any] = {
        "schema": "7213d98ef029-lesson-probe-v1",
        "task_id": str(gen.TASK_ID),
        "generator_path": str(generator_path),
        "generator_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "generator_version": str(gen.VERSION),
        "rule_hash": str(gen.RULE_HASH),
        "oracle": "generator.rule_mirror (canonical parity covered by task tests and semantic gate)",
        "sampler": {
            "bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "lesson_width": lesson_width,
            "seed_base": seed_base,
            "seed_formula": "seed_base + 100000*band_index + lesson_index",
            "start_formula": "lesson_index",
            "demo_indices": "start + 0..lesson_width-1",
            "lesson_policy": "sliding scheduled demonstrations from one seed; no rejection sampling",
        },
        "domain_limits": {
            "shape_profiles": dict(gen.SHAPE_PROFILES),
            "scene_profiles": list(gen.SCENE_PROFILES),
            "palette_kinds": {name: list(colors) for name, colors in gen.PALETTES.items()},
            "incompatible_override_combinations": list(
                gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS
            ),
            "claim_limit": (
                "Finite deterministic census of declared schedules and rivals; "
                "not a proof of universal human or model induction."
            ),
        },
        "bands": {},
    }

    for band_index, band in enumerate(BANDS):
        unique_inputs: set[str] = set()
        scene_counts: Counter[str] = Counter()
        shape_counts: Counter[str] = Counter()
        palette_counts: Counter[str] = Counter()
        rival_demo_disagreements: Counter[str] = Counter()
        rival_refuted_lessons: Counter[str] = Counter()
        identifiable_lessons = 0
        failures: list[dict[str, Any]] = []

        for lesson_index in range(lessons_per_band):
            seed = seed_base + 100_000 * band_index + lesson_index
            start = lesson_index
            demos: list[dict[str, Any]] = []
            refuted_this_lesson = {
                name: False for name in gen.LESSON_COMPETITORS
            }

            for offset in range(lesson_width):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                self_errors = gen.self_check(grid, difficulty=band)
                strict_errors = gen.strict_canonical_like(grid)
                if self_errors or strict_errors:
                    failures.append(
                        {
                            "lesson_index": lesson_index,
                            "sample_index": sample_index,
                            "self_check": self_errors,
                            "strict": strict_errors,
                        }
                    )
                    continue

                output = gen.rule_mirror(grid)
                demos.append({"input": grid, "output": output})
                unique_inputs.add(_grid_key(grid))
                observed = gen.observe_overrides(grid)
                scene_counts[observed["scene_profile"]] += 1
                shape_counts[observed["shape_profile"]] += 1
                palette_counts[observed["palette_kind"]] += 1

                for name, rival in gen.LESSON_COMPETITORS.items():
                    if rival(grid) != output:
                        rival_demo_disagreements[name] += 1
                        refuted_this_lesson[name] = True

            reasons = gen.lesson_identifiable(demos, None)
            if reasons:
                failures.append(
                    {
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "start": start,
                        "lesson_reasons": reasons,
                    }
                )
            else:
                identifiable_lessons += 1
            for name, refuted in refuted_this_lesson.items():
                if refuted:
                    rival_refuted_lessons[name] += 1

        total_demos = lessons_per_band * lesson_width
        report["bands"][band] = {
            "lessons": lessons_per_band,
            "identifiable_lessons": identifiable_lessons,
            "total_demos": total_demos,
            "unique_inputs": len(unique_inputs),
            "duplicate_input_occurrences": total_demos - len(unique_inputs),
            "scene_counts": dict(sorted(scene_counts.items())),
            "shape_counts": dict(sorted(shape_counts.items())),
            "palette_counts": dict(sorted(palette_counts.items())),
            "rival_demo_disagreements": dict(sorted(rival_demo_disagreements.items())),
            "rival_refuted_lessons": dict(sorted(rival_refuted_lessons.items())),
            "failure_count": len(failures),
            "failure_examples": failures[:10],
        }

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generator",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "generator.py",
    )
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--seed-base", type=int, default=72_130)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = run_probe(
        generator_path=args.generator,
        lessons_per_band=args.lessons_per_band,
        seed_base=args.seed_base,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
    else:
        print(rendered, end="")

    failed = any(row["failure_count"] for row in report["bands"].values())
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
