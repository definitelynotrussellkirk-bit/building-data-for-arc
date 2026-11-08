#!/usr/bin/env python3
"""Task-local rival audit with every cyclic query start in the 5-position schedule.

This complements the shared lesson census.  The census samples production lessons,
but it does not rotate every deterministic schedule position into the query slot.
This probe checks all five starts, all three explicit difficulty bands, and the
actual rival declarations exported by the selected generator.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_ID = "515cca15a0b7"
BANDS = ("easy", "medium", "hard")
CYCLIC_STARTS = (0, 1, 2, 3, 4)
TRAIN_COUNT = 3
TEST_COUNT = 1


def _grid_digest(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _same_grid(left: Any, right: Any) -> bool:
    return left == right


def _source_hash(module: Any) -> str:
    return hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()


def audit(generator: Any, canonical_pairs: list[dict[str, Any]], *, seed_count: int = 20) -> dict[str, Any]:
    """Return a deterministic, JSON-serializable semantic audit report."""
    if seed_count < 1:
        raise ValueError("seed_count must be positive")

    canonical_results: dict[str, dict[str, Any]] = {}
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        pair_rows = []
        for pair_index, pair in enumerate(canonical_pairs):
            matches = _same_grid(rival(pair["input"]), pair["output"])
            pair_rows.append({"pair_index": pair_index, "matches": matches})
        canonical_results[name] = {
            "pairs": len(pair_rows),
            "fits_all": all(row["matches"] for row in pair_rows),
            "results": pair_rows,
        }

    competitor_counts = {
        name: {
            "lessons": 0,
            "refuted_by_training": 0,
            "ambiguous": 0,
            "survived_all": 0,
        }
        for name in generator.LESSON_COMPETITORS
    }
    unique_inputs: set[str] = set()
    lesson_rows = []

    for band_index, band in enumerate(BANDS):
        for seed_offset in range(seed_count):
            seed = 410_000 + band_index * 10_000 + seed_offset
            for start in CYCLIC_STARTS:
                grids = [
                    generator.generate(seed, start + offset, difficulty=band)
                    for offset in range(TRAIN_COUNT + TEST_COUNT)
                ]
                answers = [generator.rule_mirror(grid) for grid in grids]
                unique_inputs.update(_grid_digest(grid) for grid in grids)
                lesson_result = {
                    "band": band,
                    "seed": seed,
                    "start": start,
                    "sample_indices": list(range(start, start + TRAIN_COUNT + TEST_COUNT)),
                    "layouts": [generator.observe_overrides(grid)["layout"] for grid in grids],
                    "rivals": {},
                }
                for name, rival in generator.LESSON_COMPETITORS.items():
                    rival_answers = [rival(grid) for grid in grids]
                    fits_training = all(
                        _same_grid(rival_answers[index], answers[index])
                        for index in range(TRAIN_COUNT)
                    )
                    matches_query = _same_grid(rival_answers[-1], answers[-1])
                    row = competitor_counts[name]
                    row["lessons"] += 1
                    if not fits_training:
                        outcome = "refuted_by_training"
                    elif matches_query:
                        outcome = "survived_all"
                    else:
                        outcome = "ambiguous"
                    row[outcome] += 1
                    lesson_result["rivals"][name] = {
                        "fits_training": fits_training,
                        "matches_query": matches_query,
                        "outcome": outcome,
                    }
                lesson_rows.append(lesson_result)

    witness_seed = 919_003
    witness_index = 1  # dense position in the production schedule
    witness_band = "hard"
    witness_input = generator.generate(witness_seed, witness_index, difficulty=witness_band)
    intended_output = generator.rule_mirror(witness_input)
    rival_output = generator.CANONICAL_SHORTCUTS["keep_two_nearest"](witness_input)
    if rival_output == intended_output:
        raise AssertionError("expected dense witness to refute keep_two_nearest")

    all_identifiable = all(
        row["ambiguous"] == 0 and row["survived_all"] == 0
        for row in competitor_counts.values()
    )
    return {
        "schema": "arc-task-cyclic-semantic-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": _source_hash(generator),
        "policy": {
            "bands": list(BANDS),
            "seed_count_per_band": seed_count,
            "train": TRAIN_COUNT,
            "test": TEST_COUNT,
            "schedule_period": 5,
            "starts": list(CYCLIC_STARTS),
            "assembly": "four consecutive production sample indices; first three demonstrations, fourth query",
        },
        "canonical_pairs": len(canonical_pairs),
        "canonical_shortcuts": canonical_results,
        "canonical_shortcuts_fit_all_pairs": all(
            row["fits_all"] for row in canonical_results.values()
        ),
        "cyclic_starts": list(CYCLIC_STARTS),
        "lessons": len(lesson_rows),
        "instance_draws": len(lesson_rows) * (TRAIN_COUNT + TEST_COUNT),
        "unique_inputs": len(unique_inputs),
        "competitors": competitor_counts,
        "all_lessons_identifiable": all_identifiable,
        "strongest_shortcut_witness": {
            "shortcut": "keep_two_nearest",
            "difficulty": witness_band,
            "seed": witness_seed,
            "sample_index": witness_index,
            "overrides": {},
            "layout": generator.observe_overrides(witness_input)["layout"],
            "input": witness_input,
            "intended_output": intended_output,
            "rival_output": rival_output,
        },
        "lessons_detail": lesson_rows,
        "limits": (
            "Finite evidence over declared rivals and the production five-position schedule; "
            "it is not a proof against undeclared hypotheses."
        ),
    }


def _load_generator(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(f"semantic_probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=20, help="seed blocks per difficulty band")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    from reviewer_support import canonical_pairs, find_root

    generator_path = Path(__file__).resolve().parents[1] / "generator.py"
    generator = _load_generator(generator_path)
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    report = audit(generator, pairs, seed_count=args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        f"lessons={report['lessons']} unique_inputs={report['unique_inputs']} "
        f"identifiable={report['all_lessons_identifiable']} out={args.out}"
    )
    return 0 if report["all_lessons_identifiable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
