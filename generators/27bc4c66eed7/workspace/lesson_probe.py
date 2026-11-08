#!/usr/bin/env python3
"""Source-bound lesson census for task 27bc4c66eed7.

The probe imports the selected generator bytes directly, iterates the generator's
actual semantic declarations, verifies each declared canonical shortcut against
all usable public pairs, and inspects overlapping five-demo lesson schedules at
all cyclic start residues.  It does not claim universal induction; its finite
sampler and domain limits are serialized with the result.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

TASK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_DIR.parents[1]
GENERATOR_PATH = TASK_DIR / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_27bc4c66eed7_lesson_probe", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs(task_id: str) -> list[dict[str, list[list[int]]]]:
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return [*row.get("train", []), *row.get("test", [])]
    raise RuntimeError(f"canonical row {task_id} not found")


def _freeze(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _grid_profile(grid) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({cell for row in grid for cell in row})


def _shared_row(gen, grid) -> bool:
    rows = [row for row, *_ in gen._horizontal_runs(grid)]
    return len(rows) != len(set(rows))


def run_census(per_band: int = 100) -> dict[str, Any]:
    gen = _load_generator()
    source = GENERATOR_PATH.read_bytes()
    generator_sha = hashlib.sha256(source).hexdigest()
    canonical = _canonical_pairs(gen.TASK_ID)
    canonical_profiles = sorted({_grid_profile(pair["input"]) for pair in canonical})

    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))
    canonical_shortcuts: dict[str, Any] = {}
    failures: list[str] = []
    for name, shortcut in shortcuts.items():
        mismatches = [
            index
            for index, pair in enumerate(canonical)
            if shortcut(pair["input"]) != pair["output"]
        ]
        canonical_shortcuts[name] = {
            "usable_pairs": len(canonical),
            "fits_all": not mismatches,
            "mismatch_indices": mismatches,
        }
        if mismatches:
            failures.append(
                f"declared canonical shortcut {name!r} misses pairs {mismatches}"
            )

    bands: dict[str, Any] = {}
    # Each lesson uses five consecutive demonstration indices and the next query.
    # Starts 0..per_band-1 cover every modulo-5 schedule residue equally when
    # per_band is a multiple of five. A distinct deterministic seed per lesson
    # broadens layout/color coverage while preserving the real generate() path.
    for band_index, band in enumerate(("easy", "medium", "hard")):
        inputs: set[tuple[tuple[int, ...], ...]] = set()
        profile_counts: Counter[str] = Counter()
        witness_counts: Counter[str] = Counter()
        rival_demo_refutations: Counter[str] = Counter()
        rival_query_disagreements: Counter[str] = Counter()
        run_count_hist: Counter[int] = Counter()
        run_length_hist: Counter[int] = Counter()
        color_hist: Counter[int] = Counter()
        shared_rows = 0
        repeated_color_grids = 0
        singleton_grids = 0
        even_grids = 0
        canonical_profile_grids = 0
        strict_rejections = 0
        lesson_hook_failures = 0
        surviving_lessons: dict[str, int] = {name: 0 for name in competitors}

        for lesson_index in range(per_band):
            seed = 27_000_000 + band_index * 1_000_000 + lesson_index
            start = lesson_index
            grids = [
                gen.generate(seed, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            pairs = [
                {"input": grid, "output": gen.apply_rule(grid)} for grid in grids
            ]
            demos = pairs[: gen.EXAMPLES_NEEDED]
            query = pairs[gen.EXAMPLES_NEEDED]

            if callable(getattr(gen, "lesson_identifiable", None)):
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    lesson_hook_failures += 1
                    if lesson_hook_failures <= 5:
                        failures.append(
                            f"{band} lesson {lesson_index} not identifiable: {reasons}"
                        )

            for name, competitor in competitors.items():
                demo_refuted = any(
                    competitor(pair["input"]) != pair["output"] for pair in demos
                )
                if demo_refuted:
                    rival_demo_refutations[name] += 1
                else:
                    surviving_lessons[name] += 1
                if competitor(query["input"]) != query["output"]:
                    rival_query_disagreements[name] += 1

            for offset, grid in enumerate(grids):
                inputs.add(_freeze(grid))
                profile = gen.schedule_profile(seed, start + offset, band)
                profile_counts[str(profile)] += 1
                runs = gen._horizontal_runs(grid)
                run_count_hist[len(runs)] += 1
                lengths = [end - begin + 1 for _, begin, end, _ in runs]
                run_length_hist.update(lengths)
                color_hist.update(color for *_, color in runs)
                shared_rows += int(_shared_row(gen, grid))
                repeated = len({color for *_, color in runs}) < len(runs)
                repeated_color_grids += int(repeated)
                singleton_grids += int(any(length == 1 for length in lengths))
                even_grids += int(any(length % 2 == 0 for length in lengths))
                canonical_profile_grids += int(
                    _grid_profile(grid) in set(canonical_profiles)
                )
                strict_rejections += int(bool(gen.strict_canonical_like(grid)))
                for name, predicate in witnesses.items():
                    witness_counts[name] += int(bool(predicate(grid)))

        for name, survivors in surviving_lessons.items():
            if survivors:
                failures.append(
                    f"{band}: competitor {name!r} survives {survivors}/{per_band} lessons"
                )
        if strict_rejections:
            failures.append(
                f"{band}: strict validator rejects {strict_rejections} generated grids"
            )

        total_grids = per_band * (gen.EXAMPLES_NEEDED + 1)
        bands[band] = {
            "lessons": per_band,
            "demos_per_lesson": gen.EXAMPLES_NEEDED,
            "generated_grid_occurrences": total_grids,
            "unique_inputs": len(inputs),
            "start_residue_histogram": {
                str(residue): sum(
                    1 for lesson_index in range(per_band) if lesson_index % 5 == residue
                )
                for residue in range(5)
            },
            "schedule_profile_occurrences": dict(sorted(profile_counts.items())),
            "witness_occurrences": dict(sorted(witness_counts.items())),
            "rival_demo_refutations": dict(sorted(rival_demo_refutations.items())),
            "rival_query_disagreements": dict(sorted(rival_query_disagreements.items())),
            "rival_surviving_lessons": surviving_lessons,
            "lesson_hook_failures": lesson_hook_failures,
            "strict_rejections": strict_rejections,
            "canonical_profile_occurrences": canonical_profile_grids,
            "shared_row_occurrences": shared_rows,
            "repeated_color_occurrences": repeated_color_grids,
            "singleton_occurrences": singleton_grids,
            "even_length_occurrences": even_grids,
            "run_count_histogram": {str(k): v for k, v in sorted(run_count_hist.items())},
            "run_length_histogram": {str(k): v for k, v in sorted(run_length_hist.items())},
            "run_color_histogram": {str(k): v for k, v in sorted(color_hist.items())},
        }

    return {
        "schema": "27bc4c66eed7-lesson-census-v1",
        "task_id": gen.TASK_ID,
        "generator_sha256": generator_sha,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "sampler": {
            "bands": ["easy", "medium", "hard"],
            "lessons_per_band": per_band,
            "seed_formula": "27000000 + band_index*1000000 + lesson_index",
            "lesson_start_sample_index": "lesson_index",
            "demo_indices": "start..start+4",
            "query_index": "start+5",
            "all_cyclic_schedule_starts": True,
            "outputs": "generator.apply_rule Python mirror; separately authority-bound by official rule_smoke/authority_sync",
        },
        "domain_limits": {
            "grid_h": "5..7",
            "grid_w": "7..10",
            "n_runs": "2..5",
            "run_lengths": "1..5; run_length override 0 denotes mixed",
            "colors": "foreground 1..9, background 0",
            "claim": "finite census only; no universal induction claim",
        },
        "canonical_profiles": [list(profile) for profile in canonical_profiles],
        "declared_shortcuts": sorted(shortcuts),
        "declared_competitors": sorted(competitors),
        "declared_witnesses": sorted(witnesses),
        "canonical_shortcut_checks": canonical_shortcuts,
        "bands": bands,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run_census(args.per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "generator_sha256": report["generator_sha256"],
        "bands": {
            band: {
                "lessons": stats["lessons"],
                "unique_inputs": stats["unique_inputs"],
                "survivors": stats["rival_surviving_lessons"],
                "witnesses": stats["witness_occurrences"],
            }
            for band, stats in report["bands"].items()
        },
        "failures": report["failures"],
    }, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
