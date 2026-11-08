#!/usr/bin/env python3
"""Source-bound lesson census for generator 48732ebd41f9.

This probe is intentionally task-local and independent of the selected Racket
source.  It imports the final generator by file path, uses an independent
largest-area-zero-rectangle oracle, iterates the generator's *actual* declared
rivals/witnesses, and checks 100 four-demo lessons per difficulty band while
covering every cyclic schedule start equally.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "48732ebd41f9"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
GENERATOR_PATH = HERE.parent / "generator.py"
CANONICAL_PATH = REPO / "shared/data/canonical/puzzles.jsonl"
TARGET_PATH = REPO / "shared/data/base/solutions/training/3eda0437__48732ebd41f9.json"
BANDS = ("easy", "medium", "hard")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location(
        f"task_{TASK_ID}_semantic_probe", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict[str, Any]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"canonical row missing for {TASK_ID}")


def all_pairs(row: dict[str, Any]) -> list[dict[str, Any]]:
    return [pair for split in ("train", "test") for pair in row[split]]


def zero_rectangles(grid: list[list[int]]) -> list[tuple[int, int, int, int, int]]:
    """Independent mirror of the public row-band candidate scan."""
    height, width = len(grid), len(grid[0])
    found: list[tuple[int, int, int, int, int]] = []
    for top in range(height):
        valid = [True] * width
        for bottom in range(top, height):
            for col in range(width):
                valid[col] = valid[col] and grid[bottom][col] == 0
            rect_h = bottom - top + 1
            if rect_h < 2:
                continue
            start = None
            for col in range(width + 1):
                if col < width and valid[col]:
                    if start is None:
                        start = col
                elif start is not None:
                    found.append((top, start, bottom, col - 1, rect_h * (col - start)))
                    start = None
    return found


def official_output(grid: list[list[int]]) -> list[list[int]]:
    rectangles = zero_rectangles(grid)
    if not rectangles:
        raise ValueError("no height>=2 zero rectangle")
    max_area = max(rect[4] for rect in rectangles)
    top, left, bottom, right, _area = next(
        rect for rect in rectangles if rect[4] == max_area
    )
    output = deepcopy(grid)
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            if output[row][col] == 0:
                output[row][col] = 6
    return output


def freeze(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def run_census(lessons_per_band: int) -> tuple[dict[str, Any], list[str]]:
    if lessons_per_band < 100 or lessons_per_band % 4:
        raise ValueError("--lessons-per-band must be a multiple of 4 and at least 100")

    gen = load_generator()
    row = canonical_row()
    pairs = all_pairs(row)
    canonical_profiles = sorted({profile(pair["input"]) for pair in pairs})
    errors: list[str] = []

    canonical_checks: dict[str, Any] = {
        "pair_count": len(pairs),
        "profiles": [list(item) for item in canonical_profiles],
        "independent_oracle_matches": 0,
        "generator_mirror_matches": 0,
        "rival_fits_all_pairs": {},
    }
    for pair in pairs:
        expected = pair["output"]
        if official_output(pair["input"]) == expected:
            canonical_checks["independent_oracle_matches"] += 1
        else:
            errors.append("independent oracle disagrees with a canonical pair")
        if gen.rule_mirror(pair["input"]) == expected:
            canonical_checks["generator_mirror_matches"] += 1
        else:
            errors.append("generator mirror disagrees with a canonical pair")

    for name, rival in gen.SEMANTIC_RIVALS.items():
        fit_vector = [rival(pair["input"]) == pair["output"] for pair in pairs]
        canonical_checks["rival_fits_all_pairs"][name] = {
            "fits": sum(fit_vector),
            "total": len(fit_vector),
            "fits_all": all(fit_vector),
        }

    report: dict[str, Any] = {
        "schema": "48732ebd41f9-semantic-probe-v1",
        "task_id": TASK_ID,
        "source_binding": {
            "generator_path": str(GENERATOR_PATH.relative_to(REPO)),
            "generator_sha256": sha256(GENERATOR_PATH),
            "canonical_path": str(CANONICAL_PATH.relative_to(REPO)),
            "canonical_sha256": sha256(CANONICAL_PATH),
            "selected_target_path": str(TARGET_PATH.relative_to(REPO)),
            "selected_target_sha256": sha256(TARGET_PATH),
            "declared_rule_hash": gen.RULE_HASH,
            "generator_version": gen.VERSION,
        },
        "sampler": {
            "bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "demos_per_lesson": gen.EXAMPLES_NEEDED,
            "queries_per_lesson": 1,
            "cyclic_starts": list(range(gen.EXAMPLES_NEEDED)),
            "lessons_per_start_per_band": lessons_per_band // gen.EXAMPLES_NEEDED,
            "seed_formula": "910000 + band_index*100000 + start*10000 + lesson_index",
            "sample_index_formula": "start + lesson_index*EXAMPLES_NEEDED + offset",
            "difficulty_argument": "band name",
            "axes": gen.AXES,
            "schedule_profiles": list(gen.SCHEDULE_PROFILES),
        },
        "canonical": canonical_checks,
        "bands": {},
    }

    for band_index, band in enumerate(BANDS):
        unique_inputs: set[str] = set()
        profile_counts: dict[str, int] = {}
        witness_draw_counts = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        rival_stats = {
            name: {
                "demo_disagreements": 0,
                "query_disagreements": 0,
                "lessons_refuted_by_demo": 0,
                "unresolved_lessons_that_change_query": 0,
            }
            for name in gen.LESSON_COMPETITORS
        }
        invalid_draws = 0
        observation_failures = 0
        mirror_disagreements = 0
        canonical_profile_draws = 0
        lessons_seen = 0

        per_start = lessons_per_band // gen.EXAMPLES_NEEDED
        for start in range(gen.EXAMPLES_NEEDED):
            for lesson_index in range(per_start):
                seed = 910000 + band_index * 100000 + start * 10000 + lesson_index
                base_index = start + lesson_index * gen.EXAMPLES_NEEDED
                demos: list[dict[str, list[list[int]]]] = []
                generated: list[list[list[int]]] = []
                for offset in range(gen.EXAMPLES_NEEDED):
                    grid = gen.generate(seed, base_index + offset, difficulty=band)
                    generated.append(grid)
                    output = official_output(grid)
                    demos.append({"input": grid, "output": output})
                query_grid = gen.generate(
                    seed ^ 0x5A5A5A,
                    base_index + gen.EXAMPLES_NEEDED,
                    difficulty=band,
                )
                query = {"input": query_grid, "output": official_output(query_grid)}
                generated.append(query_grid)
                lessons_seen += 1

                for grid in generated:
                    unique_inputs.add(freeze(grid))
                    key = "/".join(map(str, profile(grid)))
                    profile_counts[key] = profile_counts.get(key, 0) + 1
                    canonical_profile_draws += int(profile(grid) in canonical_profiles)
                    if gen.self_check(grid):
                        invalid_draws += 1
                    try:
                        observed = gen.observe_overrides(grid)
                        regenerated = gen.generate(
                            seed,
                            base_index,
                            difficulty=band,
                            **observed,
                        )
                        if gen.observe_overrides(regenerated) != observed:
                            observation_failures += 1
                    except Exception:
                        observation_failures += 1
                    if gen.rule_mirror(grid) != official_output(grid):
                        mirror_disagreements += 1
                    for name, witness in gen.SEMANTIC_WITNESSES.items():
                        witness_draw_counts[name] += int(bool(witness(grid)))

                for name, rival in gen.LESSON_COMPETITORS.items():
                    demo_vector = [
                        rival(item["input"]) != item["output"] for item in demos
                    ]
                    query_differs = rival(query["input"]) != query["output"]
                    rival_stats[name]["demo_disagreements"] += sum(demo_vector)
                    rival_stats[name]["query_disagreements"] += int(query_differs)
                    rival_stats[name]["lessons_refuted_by_demo"] += int(any(demo_vector))
                    rival_stats[name]["unresolved_lessons_that_change_query"] += int(
                        not any(demo_vector) and query_differs
                    )

        total_draws = lessons_seen * (gen.EXAMPLES_NEEDED + 1)
        band_report = {
            "lessons": lessons_seen,
            "draws": total_draws,
            "unique_inputs": len(unique_inputs),
            "canonical_profile_draws": canonical_profile_draws,
            "invalid_draws": invalid_draws,
            "observation_failures": observation_failures,
            "independent_vs_generator_mirror_disagreements": mirror_disagreements,
            "profile_counts": dict(sorted(profile_counts.items())),
            "witness_draw_counts": witness_draw_counts,
            "rivals": rival_stats,
        }
        report["bands"][band] = band_report

        if lessons_seen != lessons_per_band:
            errors.append(f"{band}: expected {lessons_per_band} lessons, got {lessons_seen}")
        if invalid_draws:
            errors.append(f"{band}: {invalid_draws} generated draws failed self_check")
        if observation_failures:
            errors.append(f"{band}: {observation_failures} override observations failed")
        if mirror_disagreements:
            errors.append(f"{band}: {mirror_disagreements} mirror/oracle disagreements")
        for name, stats in rival_stats.items():
            if stats["lessons_refuted_by_demo"] != lessons_seen:
                errors.append(
                    f"{band}: rival {name} refuted in "
                    f"{stats['lessons_refuted_by_demo']}/{lessons_seen} lessons"
                )
            if stats["unresolved_lessons_that_change_query"]:
                errors.append(
                    f"{band}: rival {name} unresolved in "
                    f"{stats['unresolved_lessons_that_change_query']} lessons"
                )

    report["verdict"] = "pass" if not errors else "fail"
    report["errors"] = errors
    return report, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report, errors = run_census(args.lessons_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": report["verdict"],
        "generator_sha256": report["source_binding"]["generator_sha256"],
        "bands": {
            band: {
                "lessons": data["lessons"],
                "unique_inputs": data["unique_inputs"],
                "canonical_profile_draws": data["canonical_profile_draws"],
            }
            for band, data in report["bands"].items()
        },
        "errors": errors,
        "out": str(args.out),
    }, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
