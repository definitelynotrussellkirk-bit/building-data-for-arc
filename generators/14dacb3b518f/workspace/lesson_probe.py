#!/usr/bin/env python3
"""Source-bound rival audit for generator 14dacb3b518f.

The probe deliberately imports the generator file supplied on the command line,
hashes those exact bytes, and discovers CANONICAL_SHORTCUTS,
LESSON_COMPETITORS, and SEMANTIC_WITNESSES from that module.  It does not carry
a copied rival list.

Sampler used by default:
* 100 lessons per difficulty band.
* Four demonstrations and one query per lesson.
* Lesson n starts at schedule profile n mod the schedule length, so every cyclic
  start receives equal coverage when lesson count is a multiple of the length.
* Each lesson uses a fresh seed and five consecutive sample indices chosen so
  the requested cyclic profile start is exact.
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

TASK_ID = "14dacb3b518f"
BANDS = ("easy", "medium", "hard")


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(
        f"lesson_probe_{TASK_ID}_{hashlib.sha256(path.read_bytes()).hexdigest()[:12]}",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _find_canonical(generator_path: Path) -> Path:
    for parent in generator_path.resolve().parents:
        for relative in (
            Path("shared/data/canonical/puzzles.jsonl"),
            Path("data/canonical/puzzles.jsonl"),
        ):
            candidate = parent / relative
            if candidate.exists():
                return candidate
    raise FileNotFoundError("could not locate canonical puzzles.jsonl")


def _canonical_pairs(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [pair for split in ("train", "test") for pair in row[split]]
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _sha_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _axis_bounds(observations: list[dict[str, Any]]) -> dict[str, Any]:
    keys = sorted({key for item in observations for key in item})
    result: dict[str, Any] = {}
    for key in keys:
        values = [item[key] for item in observations if key in item]
        if values and all(isinstance(value, (int, float)) for value in values):
            result[key] = {
                "min": min(values),
                "max": max(values),
                "distinct": sorted(set(values)),
            }
        else:
            result[key] = {"distinct": sorted(set(values), key=repr)}
    return result


def run_probe(generator_path: Path, lessons_per_band: int, demos: int) -> dict[str, Any]:
    module = _load_module(generator_path)
    schedule_length = len(tuple(module.SCHEDULE_PROFILES))
    if demos < 1:
        raise ValueError("demos must be positive")
    canonical = _canonical_pairs(_find_canonical(generator_path))
    shortcuts = dict(getattr(module, "CANONICAL_SHORTCUTS", {}))
    competitors = dict(getattr(module, "LESSON_COMPETITORS", {}))
    witnesses = dict(getattr(module, "SEMANTIC_WITNESSES", {}))

    canonical_results = {}
    for name, shortcut in shortcuts.items():
        mismatches = [
            index
            for index, pair in enumerate(canonical)
            if shortcut(pair["input"]) != pair["output"]
        ]
        canonical_results[name] = {
            "pairs_checked": len(canonical),
            "mismatch_indices": mismatches,
            "fits_all": not mismatches,
        }

    band_results: dict[str, Any] = {}
    all_inputs: dict[str, list[list[int]]] = {}
    seed_offsets = {"easy": 110_000, "medium": 220_000, "hard": 330_000}

    for band in BANDS:
        unique_inputs: dict[str, list[list[int]]] = {}
        observations: list[dict[str, Any]] = []
        profile_counts: Counter[int] = Counter()
        cyclic_start_counts: Counter[int] = Counter()
        witness_draw_counts: Counter[str] = Counter()
        witness_lesson_counts: Counter[str] = Counter()
        rival_stats = {
            name: {
                "lessons": lessons_per_band,
                "demo_disagreement_lessons": 0,
                "query_disagreement_lessons": 0,
                "survives_all_demos": 0,
                "harmful_ambiguity": 0,
            }
            for name in competitors
        }
        identifiable = 0
        unidentifiable_examples: list[dict[str, Any]] = []

        for lesson_index in range(lessons_per_band):
            start_profile = lesson_index % schedule_length
            cyclic_start_counts[start_profile] += 1
            seed = seed_offsets[band] + lesson_index
            # 10*lesson_index is profile-neutral modulo five and prevents sample
            # index reuse while the small correction forces the desired start.
            sample_start = (
                10 * lesson_index + (start_profile - seed) % schedule_length
            )
            grids = []
            for offset in range(demos + 1):
                sample_index = sample_start + offset
                grid = module.generate(seed, sample_index, difficulty=band)
                errors = module.self_check(grid, difficulty=band)
                if errors:
                    raise AssertionError(
                        f"generated off-domain grid band={band} lesson={lesson_index} "
                        f"offset={offset}: {errors}"
                    )
                actual_profile = module.schedule_profile(seed, sample_index, band)
                expected_profile = (start_profile + offset) % schedule_length
                if actual_profile != expected_profile:
                    raise AssertionError(
                        f"profile mismatch: expected {expected_profile}, got {actual_profile}"
                    )
                profile_counts[actual_profile] += 1
                grids.append(grid)
                key = _grid_key(grid)
                unique_inputs.setdefault(key, grid)
                all_inputs.setdefault(key, grid)
                observations.append(module.observe_overrides(grid))
                for witness_name, witness in witnesses.items():
                    if witness(grid):
                        witness_draw_counts[witness_name] += 1

            for witness_name, witness in witnesses.items():
                if any(witness(grid) for grid in grids):
                    witness_lesson_counts[witness_name] += 1

            demos_payload = [
                {"input": grid, "output": module.rule_mirror(grid)}
                for grid in grids[:demos]
            ]
            query_payload = {
                "input": grids[demos],
                "output": module.rule_mirror(grids[demos]),
            }
            reasons = module.lesson_identifiable(demos_payload, query_payload)
            if not reasons:
                identifiable += 1
            elif len(unidentifiable_examples) < 10:
                unidentifiable_examples.append(
                    {
                        "lesson_index": lesson_index,
                        "start_profile": start_profile,
                        "seed": seed,
                        "sample_start": sample_start,
                        "reasons": reasons,
                    }
                )

            for rival_name, rival in competitors.items():
                demo_diffs = [
                    rival(demo["input"]) != demo["output"] for demo in demos_payload
                ]
                survives = not any(demo_diffs)
                query_differs = rival(query_payload["input"]) != query_payload["output"]
                stats = rival_stats[rival_name]
                stats["demo_disagreement_lessons"] += int(any(demo_diffs))
                stats["query_disagreement_lessons"] += int(query_differs)
                stats["survives_all_demos"] += int(survives)
                stats["harmful_ambiguity"] += int(survives and query_differs)

        expected_draws = lessons_per_band * (demos + 1)
        band_results[band] = {
            "lessons": lessons_per_band,
            "demos_per_lesson": demos,
            "queries_per_lesson": 1,
            "draws": expected_draws,
            "unique_inputs": len(unique_inputs),
            "duplicate_draws": expected_draws - len(unique_inputs),
            "unique_input_set_sha256": _sha_json(sorted(unique_inputs)),
            "cyclic_start_counts": {
                str(key): cyclic_start_counts[key] for key in range(schedule_length)
            },
            "profile_draw_counts": {
                str(key): profile_counts[key] for key in range(schedule_length)
            },
            "axis_domain_observed": _axis_bounds(observations),
            "identifiable_lessons": identifiable,
            "unidentifiable_lessons": lessons_per_band - identifiable,
            "unidentifiable_examples": unidentifiable_examples,
            "witness_draw_counts": {
                name: witness_draw_counts[name] for name in witnesses
            },
            "witness_lesson_counts": {
                name: witness_lesson_counts[name] for name in witnesses
            },
            "competitors": rival_stats,
        }

    return {
        "schema": "arcpuzzles-task-local-lesson-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "generator_version": module.VERSION,
        "rule_hash": module.RULE_HASH,
        "axes_declared": module.AXES,
        "schedule_profiles": list(module.SCHEDULE_PROFILES),
        "canonical_pairs": len(canonical),
        "canonical_shortcuts": canonical_results,
        "sampler": {
            "bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "demos_per_lesson": demos,
            "queries_per_lesson": 1,
            "examples_per_lesson": demos + 1,
            "cyclic_start": "lesson_index modulo schedule length",
            "seed": "band-specific offset + lesson_index",
            "sample_start": (
                "10*lesson_index + (cyclic_start - seed) modulo schedule length; "
                "then consecutive sample indices"
            ),
            "outputs": "generator.rule_mirror; Racket parity is checked separately by the battery",
        },
        "bands": band_results,
        "all_bands_unique_inputs": len(all_inputs),
        "all_bands_unique_input_set_sha256": _sha_json(sorted(all_inputs)),
        "limitations": [
            "This is an exhaustive audit of the declared deterministic five-profile lesson sampler, not universal induction over every possible ARC lesson.",
            "Rival disagreement uses the exact final generator's executable declarations; undeclared rivals are outside this report.",
            "The probe uses rule_mirror outputs. The separate authority_sync and rule_smoke stages bind that mirror to the pinned Racket authority.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generator",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "generator.py",
    )
    parser.add_argument("--lessons", type=int, default=100)
    parser.add_argument("--demos", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = run_probe(args.generator.resolve(), args.lessons, args.demos)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "out": str(args.out),
                "generator_sha256": report["generator_sha256"],
                "all_bands_unique_inputs": report["all_bands_unique_inputs"],
                "unidentifiable_by_band": {
                    band: data["unidentifiable_lessons"]
                    for band, data in report["bands"].items()
                },
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
