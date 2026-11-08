"""High-power, source-bound lesson audit for task 9e80ef661ecc.

This probe samples complete lessons from the reviewed generator, applies the
selected canonical Racket program to every sampled input, and scores the task's
explicit finite rival set.  It records evidence about this sampler and these
rivals only; it does not claim universal rule induction.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

from reference_probe import (
    TASK,
    canonical_pairs,
    intended_output,
    load_generator,
    racket_outputs,
)
from topology_probe import components, scene_signature, shape_signature

BANDS = ("easy", "medium", "hard")
DEMO_COUNT = 4
QUERY_COUNT = 1
STRIDE = 11
# Task-local floors for this pinned 500-input/band census, not a global policy.
MIN_SCENE_SIGNATURES = 50
MIN_OBJECT_SIGNATURES = 40


def _seed(band: str, lesson_index: int) -> int:
    digest = hashlib.sha256(f"{TASK}|source-bound-lesson-probe-v1|{band}|{lesson_index}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _digest_grid(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(generator_path: Path, lessons_per_band: int) -> dict[str, Any]:
    gen = load_generator(generator_path)
    report: dict[str, Any] = {
        "schema": "9e80ef661ecc-source-bound-lesson-probe-v2",
        "task_id": TASK,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "generator_sha256": _source_hash(generator_path),
        "probe_sha256": _source_hash(Path(__file__)),
        "topology_probe_sha256": _source_hash(Path(__file__).with_name("topology_probe.py")),
        "reference_probe_sha256": _source_hash(Path(__file__).with_name("reference_probe.py")),
        "diversity_gate": {
            "minimum_scene_signatures_per_band": MIN_SCENE_SIGNATURES,
            "minimum_object_signatures_per_band": MIN_OBJECT_SIGNATURES,
            "normalization": "object shapes modulo color, translation and D4; scenes are object multisets",
            "limitation": "Scene signatures omit contact, relative placement and palette relationships.",
        },
        "sampler": {
            "bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "demos_per_lesson": DEMO_COUNT,
            "queries_per_lesson": QUERY_COUNT,
            "sample_index_start": "lesson_index * 11",
            "within_lesson_indices": "start + 0..4",
            "seed": "sha256(task|source-bound-lesson-probe-v1|band|lesson_index)[:8]",
            "difficulty_forwarded": True,
        },
        "domain_limits": [
            "Finite audit of the generator's declared named rivals, not all possible programs.",
            "Exactly 100 independently seeded lessons per band by default; counts are empirical for this pinned sampler.",
            "The four-demo schedule deliberately covers all four profiles in each lesson, but not every lawful color/layout combination.",
            "Racket is the sampled-output authority; the independent Python oracle is checked only as supplementary parity evidence.",
        ],
        "canonical_shortcuts": {},
        "bands": {},
        "totals": {},
    }

    canonical = canonical_pairs()
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        matches = sum(rival(pair["input"]) == pair["output"] for pair in canonical)
        report["canonical_shortcuts"][name] = {
            "matches": matches,
            "pairs": len(canonical),
            "fits_all": matches == len(canonical),
        }

    total_counter = Counter()
    total_unique: set[str] = set()
    total_shapes: set[tuple] = set()
    total_scenes: set[tuple] = set()
    total_profile_counts = Counter()
    total_rivals = {
        name: Counter()
        for name in gen.LESSON_COMPETITORS
    }

    for band in BANDS:
        lesson_specs = []
        all_grids: list[list[list[int]]] = []
        for lesson_index in range(lessons_per_band):
            seed = _seed(band, lesson_index)
            start = lesson_index * STRIDE
            grids = [
                gen.generate(seed, start + offset, difficulty=band)
                for offset in range(DEMO_COUNT + QUERY_COUNT)
            ]
            lesson_specs.append({
                "lesson_index": lesson_index,
                "seed": seed,
                "sample_index": start,
                "grids": grids,
            })
            all_grids.extend(grids)

        authority_outputs = racket_outputs(all_grids)
        output_cursor = 0
        counter = Counter()
        unique_inputs: set[str] = set()
        unique_shapes: set[tuple] = set()
        unique_scenes: set[tuple] = set()
        profile_counts = Counter()
        rivals = {name: Counter() for name in gen.LESSON_COMPETITORS}
        failure_examples: list[dict[str, Any]] = []

        for spec in lesson_specs:
            grids = spec.pop("grids")
            outputs = authority_outputs[output_cursor: output_cursor + len(grids)]
            output_cursor += len(grids)
            pairs = [
                {"input": grid, "output": output}
                for grid, output in zip(grids, outputs)
            ]
            demos, query = pairs[:DEMO_COUNT], pairs[DEMO_COUNT]
            counter["lessons"] += 1

            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                counter["unidentifiable_lessons"] += 1
                if len(failure_examples) < 5:
                    failure_examples.append({
                        "type": "lesson_identifiable",
                        "replay": {k: spec[k] for k in ("lesson_index", "seed", "sample_index")},
                        "reasons": reasons,
                    })
            else:
                counter["identifiable_lessons"] += 1

            for pair in pairs:
                grid, authority = pair["input"], pair["output"]
                counter["inputs"] += 1
                digest = _digest_grid(grid)
                unique_inputs.add(digest)
                unique_scenes.add(scene_signature(grid))
                unique_shapes.update(shape_signature(o["cells"]) for o in components(grid))
                profile = gen.observe_overrides(grid).get("profile")
                profile_counts[str(profile)] += 1
                strict_errors = gen.strict_canonical_like(grid)
                counter["strict_failures"] += bool(strict_errors)
                counter["python_oracle_mismatches"] += intended_output(grid) != authority
                counter["generator_mirror_mismatches"] += gen.rule_mirror(grid) != authority

            for name, rival in gen.LESSON_COMPETITORS.items():
                demo_matches = [rival(pair["input"]) == pair["output"] for pair in demos]
                query_matches = rival(query["input"]) == query["output"]
                rivals[name]["demo_grid_matches"] += sum(demo_matches)
                rivals[name]["demo_grid_disagreements"] += len(demo_matches) - sum(demo_matches)
                rivals[name]["query_matches"] += query_matches
                rivals[name]["query_disagreements"] += not query_matches
                if all(demo_matches):
                    rivals[name]["lessons_survived_all_demos"] += 1
                    if not query_matches:
                        rivals[name]["survived_then_failed_query"] += 1
                else:
                    rivals[name]["lessons_refuted_by_demos"] += 1

        counter["unique_inputs"] = len(unique_inputs)
        counter["duplicate_inputs"] = counter["inputs"] - counter["unique_inputs"]
        counter["raw_grid_uniqueness"] = len(unique_inputs)
        counter["normalized_scene_topology_uniqueness"] = len(unique_scenes)
        counter["normalized_object_shape_uniqueness"] = len(unique_shapes)
        counter["diversity_gate_failures"] = int(len(unique_scenes) < MIN_SCENE_SIGNATURES) + int(len(unique_shapes) < MIN_OBJECT_SIGNATURES)
        report["bands"][band] = {
            "counts": dict(counter),
            "profile_counts": dict(sorted(profile_counts.items())),
            "rivals": {name: dict(stats) for name, stats in rivals.items()},
            "failure_examples": failure_examples,
        }
        total_counter.update(counter)
        total_unique.update(unique_inputs)
        total_shapes.update(unique_shapes)
        total_scenes.update(unique_scenes)
        total_profile_counts.update(profile_counts)
        for name, stats in rivals.items():
            total_rivals[name].update(stats)

    # Recompute union-sensitive uniqueness rather than summing per-band values.
    total_counter["unique_inputs"] = len(total_unique)
    total_counter["duplicate_inputs"] = total_counter["inputs"] - len(total_unique)
    total_counter["raw_grid_uniqueness"] = len(total_unique)
    total_counter["normalized_scene_topology_uniqueness"] = len(total_scenes)
    total_counter["normalized_object_shape_uniqueness"] = len(total_shapes)
    report["totals"] = {
        "counts": dict(total_counter),
        "profile_counts": dict(sorted(total_profile_counts.items())),
        "rivals": {name: dict(stats) for name, stats in total_rivals.items()},
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=Path(__file__).resolve().parents[1] / "generator.py")
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.lessons_per_band < 100:
        parser.error("assignment evidence requires at least 100 lessons per band")
    generator_path = args.generator.resolve()
    report = audit(generator_path, args.lessons_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    summary = {
        "generator_sha256": report["generator_sha256"],
        "lessons": report["totals"]["counts"].get("lessons"),
        "inputs": report["totals"]["counts"].get("inputs"),
        "unique_inputs": report["totals"]["counts"].get("unique_inputs"),
        "unidentifiable_lessons": report["totals"]["counts"].get("unidentifiable_lessons", 0),
        "strict_failures": report["totals"]["counts"].get("strict_failures", 0),
        "normalized_scene_topology_uniqueness": report["totals"]["counts"]["normalized_scene_topology_uniqueness"],
        "normalized_object_shape_uniqueness": report["totals"]["counts"]["normalized_object_shape_uniqueness"],
        "diversity_gate_failures": report["totals"]["counts"].get("diversity_gate_failures", 0),
        "python_oracle_mismatches": report["totals"]["counts"].get("python_oracle_mismatches", 0),
        "rival_survivors": {
            name: stats.get("lessons_survived_all_demos", 0)
            for name, stats in report["totals"]["rivals"].items()
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    failures = (
        summary["unidentifiable_lessons"]
        + summary["strict_failures"]
        + summary["python_oracle_mismatches"]
        + summary["diversity_gate_failures"]
        + report["totals"]["counts"].get("generator_mirror_mismatches", 0)
        + sum(summary["rival_survivors"].values())
    )
    return int(failures != 0)


if __name__ == "__main__":
    raise SystemExit(main())
