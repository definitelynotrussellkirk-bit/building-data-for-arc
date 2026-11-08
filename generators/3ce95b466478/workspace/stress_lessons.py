#!/usr/bin/env python3
"""Source-bound lesson census for task 3ce95b466478.

The probe follows the generator's actual sequential sample-index policy, audits
all declared canonical shortcuts and lesson competitors, and records enough
sampler detail to reproduce every window.  It is evidence about the sampled
finite domain, not a claim of universal induction.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from reference_probe import (
    CANONICAL_PROFILES,
    canonical_pairs,
    lesson_reasons,
    load_generator,
    observed,
    profile,
    solve_by_perimeter,
    solve_by_size,
)

TASK_ID = "3ce95b466478"
HOME = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _grid_hash(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=str)}


def _declared_callables(generator: Any, attribute: str) -> dict[str, Any]:
    value = getattr(generator, attribute, {})
    if not isinstance(value, dict):
        return {}
    return {str(name): fn for name, fn in value.items() if callable(fn)}


def audit_lessons(
    generator: Any,
    *,
    generator_path: Path,
    bands: Iterable[str] = ("easy", "medium", "hard"),
    lessons_per_band: int = 100,
    demos_per_lesson: int = 3,
    base_seed: int = 730_000,
) -> dict[str, Any]:
    if lessons_per_band < 1 or demos_per_lesson < 1:
        raise ValueError("lesson and demo counts must be positive")

    canonical = canonical_pairs()
    shortcuts = _declared_callables(generator, "CANONICAL_SHORTCUTS")
    semantic_rivals = _declared_callables(generator, "SEMANTIC_RIVALS")
    lesson_competitors = _declared_callables(generator, "LESSON_COMPETITORS")
    rival_names = sorted(set(semantic_rivals) | set(lesson_competitors))
    rivals = {
        name: lesson_competitors.get(name, semantic_rivals.get(name))
        for name in rival_names
    }

    failures: list[dict[str, Any]] = []
    shortcut_fit: dict[str, str] = {}
    for name, shortcut in sorted(shortcuts.items()):
        fit = sum(shortcut(pair["input"]) == pair["output"] for pair in canonical)
        shortcut_fit[name] = f"{fit}/{len(canonical)}"
        if fit != len(canonical):
            failures.append(
                {
                    "kind": "declared_shortcut_does_not_fit_canonical",
                    "shortcut": name,
                    "fit": shortcut_fit[name],
                }
            )

    band_reports: dict[str, Any] = {}
    all_hashes: set[str] = set()
    all_generated = 0
    for band_index, band in enumerate(tuple(bands)):
        input_hashes: set[str] = set()
        dimensions: Counter[tuple[int, int]] = Counter()
        profiles: Counter[tuple[int, int, int]] = Counter()
        blob_counts: Counter[int] = Counter()
        decoration_colors: Counter[int] = Counter()
        decoration_sizes: Counter[int] = Counter()
        start_modulo: Counter[int] = Counter()
        rival_disagreement_by_name: Counter[str] = Counter()
        disagreement_demo_hashes: set[str] = set()
        unidentifiable: list[dict[str, Any]] = []
        invalid_examples: list[dict[str, Any]] = []

        for lesson_index in range(lessons_per_band):
            seed = base_seed + band_index * 1_000_000 + lesson_index * 7_919
            start = lesson_index
            start_modulo[start % demos_per_lesson] += 1
            demos: list[dict[str, Any]] = []
            lesson_disagreements: Counter[str] = Counter()

            for offset in range(demos_per_lesson):
                sample_index = start + offset
                grid = generator.generate(
                    seed,
                    sample_index,
                    difficulty=band,
                )
                grid_hash = _grid_hash(grid)
                input_hashes.add(grid_hash)
                all_hashes.add(grid_hash)
                all_generated += 1

                errors = list(generator.self_check(grid))
                if errors:
                    invalid_examples.append(
                        {
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": sample_index,
                            "errors": errors,
                        }
                    )

                stats = observed(grid)
                dimensions[(stats["grid_h"], stats["grid_w"])] += 1
                profiles[profile(grid)] += 1
                blob_counts[stats["n_blobs"]] += 1
                decoration_colors[stats["decoration_color"]] += 1
                decoration_sizes[stats["decoration_size"]] += 1

                output = solve_by_size(grid)
                demos.append({"input": grid, "output": output})
                independent_perimeter = solve_by_perimeter(grid)

                for name, rival in rivals.items():
                    rival_output = rival(grid)
                    if name == "second_largest_perimeter" and rival_output != independent_perimeter:
                        failures.append(
                            {
                                "kind": "declared_rival_disagrees_with_independent_oracle",
                                "band": band,
                                "lesson_index": lesson_index,
                                "sample_index": sample_index,
                                "rival": name,
                                "input_sha256": grid_hash,
                            }
                        )
                    if rival_output != output:
                        rival_disagreement_by_name[name] += 1
                        lesson_disagreements[name] += 1
                        disagreement_demo_hashes.add(grid_hash)

            independent_reasons = lesson_reasons(demos)
            declared_reasons = list(generator.lesson_identifiable(demos, None))
            unresolved = [name for name in rival_names if lesson_disagreements[name] == 0]
            if independent_reasons or declared_reasons or unresolved:
                unidentifiable.append(
                    {
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "start_sample_index": start,
                        "independent_reasons": independent_reasons,
                        "declared_reasons": declared_reasons,
                        "unresolved_rivals": unresolved,
                    }
                )

        if invalid_examples:
            failures.append(
                {
                    "kind": "invalid_generated_examples",
                    "band": band,
                    "count": len(invalid_examples),
                    "examples": invalid_examples[:5],
                }
            )
        if unidentifiable:
            failures.append(
                {
                    "kind": "unidentifiable_lessons",
                    "band": band,
                    "count": len(unidentifiable),
                    "examples": unidentifiable[:5],
                }
            )

        total_demos = lessons_per_band * demos_per_lesson
        canonical_profile_hits = sum(
            count for key, count in profiles.items() if key in CANONICAL_PROFILES
        )
        band_reports[band] = {
            "lessons_checked": lessons_per_band,
            "demos_per_lesson": demos_per_lesson,
            "generated_demos": total_demos,
            "unique_inputs": len(input_hashes),
            "duplicate_inputs": total_demos - len(input_hashes),
            "identifiable_lessons": lessons_per_band - len(unidentifiable),
            "unidentifiable_lessons": unidentifiable,
            "rival_disagreement_demos": len(disagreement_demo_hashes),
            "rival_disagreements_by_name": _counter(rival_disagreement_by_name),
            "canonical_profile_hits": canonical_profile_hits,
            "start_modulo_counts": _counter(start_modulo),
            "dimensions": _counter(dimensions),
            "profiles_h_w_palette": _counter(profiles),
            "red_component_counts": _counter(blob_counts),
            "decoration_colors": _counter(decoration_colors),
            "decoration_sizes": _counter(decoration_sizes),
            "seed_formula": (
                f"{base_seed} + band_index*1000000 + lesson_index*7919"
            ),
            "sample_index_formula": "lesson_index + demo_offset",
        }

    return {
        "schema": "3ce95b466478-lesson-census-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": _sha256(generator_path),
        "generator_version": getattr(generator, "VERSION", None),
        "sampler": {
            "bands": list(band_reports),
            "lessons_per_band": lessons_per_band,
            "demos_per_lesson": demos_per_lesson,
            "base_seed": base_seed,
            "lesson_assembly": (
                "one deterministic seed per lesson; consecutive sample_index values; "
                "all cyclic starts represented"
            ),
            "output_oracle": (
                "independent size-ranking implementation in reference_probe.py, "
                "checked against all canonical pairs"
            ),
        },
        "domain_limits": {
            "advertised_exact_axes": getattr(generator, "AXES", {}),
            "validator": {
                "grid_h": "8..16",
                "grid_w": "11..16",
                "red_components": "3..5, distinct cell counts",
                "decoration": "one 4-connected component, color 3..9, size 1..3",
            },
            "scheduled_counterexample": "sample_index % 3 == 0",
            "claim_scope": (
                "finite deterministic census only; no universal induction claim"
            ),
        },
        "declared_shortcuts": sorted(shortcuts),
        "declared_rivals": rival_names,
        "canonical_pairs_checked": len(canonical),
        "canonical_shortcut_fit": shortcut_fit,
        "bands": band_reports,
        "total_generated_demos": all_generated,
        "total_unique_inputs": len(all_hashes),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, default=HOME / "generator.py")
    parser.add_argument("--lessons", type=int, default=100)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--base-seed", type=int, default=730_000)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    generator = load_generator(args.generator)
    report = audit_lessons(
        generator,
        generator_path=args.generator,
        lessons_per_band=args.lessons,
        demos_per_lesson=args.demos,
        base_seed=args.base_seed,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "out": str(args.out),
                "generator_sha256": report["generator_sha256"],
                "total_generated_demos": report["total_generated_demos"],
                "total_unique_inputs": report["total_unique_inputs"],
                "failures": len(report["failures"]),
                "bands": {
                    band: {
                        "identifiable": row["identifiable_lessons"],
                        "lessons": row["lessons_checked"],
                        "unique_inputs": row["unique_inputs"],
                        "rival_disagreement_demos": row["rival_disagreement_demos"],
                    }
                    for band, row in report["bands"].items()
                },
            },
            sort_keys=True,
        )
    )
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
