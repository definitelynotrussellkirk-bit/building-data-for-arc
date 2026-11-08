#!/usr/bin/env python3
"""Finite, source-bound curriculum probe for generator 76aff6297765.

This authoring tool checks three independent claims:

* every declared canonical shortcut really fits every canonical pair;
* every cyclic lesson/query rotation refutes every declared competitor; and
* each generated grid alone exposes all four occupancy relations, leaving only
  the intended one-hot Boolean truth table.

It uses the Python diagnostic mirror and canonical labels.  The repository's
Racket-backed battery and lesson census remain the output authority.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable, Sequence

from reviewer_support import canonical_pairs, find_root


TASK_ID = "76aff6297765"


def _load_generator():
    """Load the staged module, falling back to the sibling source tree."""
    try:
        return importlib.import_module(
            f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
        )
    except ModuleNotFoundError:
        generator_path = Path(__file__).resolve().parents[1] / "generator.py"
        spec = importlib.util.spec_from_file_location(
            f"arcpuzzles_generator_{TASK_ID}", generator_path
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load generator from {generator_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


GEN = _load_generator()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _state(top: int, bottom: int) -> int:
    if top == 0 and bottom == 0:
        return 0
    if top == 0:
        return 1
    if bottom == 0:
        return 2
    return 3


def _truth_table_output(grid: list[list[int]], mask: int) -> list[list[int]]:
    info = GEN._analysis(grid)
    if info.get("errors"):
        raise ValueError("invalid task grid: " + "; ".join(info["errors"]))
    return [
        [
            8
            if mask & (1 << _state(info["top"][row][col], info["bottom"][row][col]))
            else 0
            for col in range(info["panel_w"])
        ]
        for row in range(info["panel_h"])
    ]


def _pair(seed: int, sample_index: int, difficulty: str) -> dict[str, object]:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def _scene_kind(grid: list[list[int]]) -> str:
    info = GEN._analysis(grid)
    if GEN.strict_canonical_like(grid) == []:
        return "canonical_anchor"
    if info["top_color"] == info["bot_color"]:
        return "same_foreground"
    return "distinct_broad"


def run_probe(
    *,
    seeds: Sequence[int] = (0, 31, 91),
    difficulties: Sequence[str] = ("easy", "medium", "hard"),
) -> dict[str, object]:
    generator_path = Path(GEN.__file__).resolve()
    root = find_root(__file__)
    canonical = canonical_pairs(TASK_ID, root=root)

    canonical_fit_matrix: dict[str, list[bool]] = {}
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        canonical_fit_matrix[name] = [
            rival(pair["input"]) == pair["output"] for pair in canonical
        ]
    actual_fits = sorted(
        name for name, results in canonical_fit_matrix.items() if all(results)
    )
    declared_fits = sorted(GEN.CANONICAL_SHORTCUTS)

    errors: list[dict[str, object]] = []
    period = len(GEN.SCHEDULE_PROFILES)
    windows_checked = 0
    rotations_checked = 0
    ambiguous_rotations = 0
    competitor_checks = 0
    grids_checked = 0
    non_unique_truth_tables = 0
    row_major_collisions = 0

    for difficulty in difficulties:
        for seed in seeds:
            for start in range(period):
                windows_checked += 1
                pairs = [
                    _pair(seed, start + offset, difficulty)
                    for offset in range(period)
                ]
                kinds = [_scene_kind(pair["input"]) for pair in pairs]
                expected_kinds = {
                    "canonical_anchor": 2,
                    "same_foreground": 2,
                    "distinct_broad": 2,
                }
                observed_kinds = {
                    kind: kinds.count(kind) for kind in expected_kinds
                }
                if observed_kinds != expected_kinds:
                    errors.append(
                        {
                            "kind": "schedule_profile_counts",
                            "difficulty": difficulty,
                            "seed": seed,
                            "start": start,
                            "observed": observed_kinds,
                            "expected": expected_kinds,
                        }
                    )

                for pair_index, pair in enumerate(pairs):
                    grids_checked += 1
                    grid = pair["input"]
                    expected = pair["output"]
                    fitting_masks = [
                        mask
                        for mask in range(16)
                        if _truth_table_output(grid, mask) == expected
                    ]
                    if fitting_masks != [1]:
                        non_unique_truth_tables += 1
                        errors.append(
                            {
                                "kind": "truth_table_not_unique",
                                "difficulty": difficulty,
                                "seed": seed,
                                "sample_index": start + pair_index,
                                "fitting_masks": fitting_masks,
                            }
                        )
                    if GEN._rival_count_only_row_major(grid) == expected:
                        row_major_collisions += 1
                        errors.append(
                            {
                                "kind": "row_major_count_collision",
                                "difficulty": difficulty,
                                "seed": seed,
                                "sample_index": start + pair_index,
                            }
                        )

                for query_index, query in enumerate(pairs):
                    rotations_checked += 1
                    demos = [
                        pair for index, pair in enumerate(pairs) if index != query_index
                    ]
                    hook_reasons = GEN.lesson_identifiable(demos, query)
                    survivors = []
                    for name, rival in GEN.LESSON_COMPETITORS.items():
                        competitor_checks += 1
                        if all(
                            rival(demo["input"]) == demo["output"] for demo in demos
                        ):
                            survivors.append(name)
                    if hook_reasons or survivors:
                        ambiguous_rotations += 1
                        errors.append(
                            {
                                "kind": "ambiguous_rotation",
                                "difficulty": difficulty,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "hook_reasons": hook_reasons,
                                "survivors": survivors,
                            }
                        )

    if declared_fits != actual_fits:
        errors.append(
            {
                "kind": "canonical_shortcut_declaration_mismatch",
                "declared": declared_fits,
                "actual": actual_fits,
            }
        )

    return {
        "schema": "arcpuzzles-relation-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": _sha256(generator_path),
        "rule_hash": GEN.RULE_HASH,
        "seeds": list(seeds),
        "difficulties": list(difficulties),
        "canonical": {
            "pairs_checked": len(canonical),
            "declared_fits": declared_fits,
            "actual_fits": actual_fits,
            "declared_matches_actual": declared_fits == actual_fits,
            "fit_matrix": canonical_fit_matrix,
        },
        "schedule": {
            "profiles": list(GEN.SCHEDULE_PROFILES),
            "demonstrations": GEN.EXAMPLES_NEEDED,
            "windows_checked": windows_checked,
            "rotations_checked": rotations_checked,
            "competitor_checks": competitor_checks,
            "ambiguous_rotations": ambiguous_rotations,
        },
        "relations": {
            "grids_checked": grids_checked,
            "truth_tables_per_grid": 16,
            "non_unique_truth_tables": non_unique_truth_tables,
            "row_major_collisions": row_major_collisions,
        },
        "errors": errors[:100],
        "error_count": len(errors),
        "passed": not errors,
        "limitations": [
            "Finite checks cover only the supplied seeds, bands, schedule starts, declared rivals, and 16 pointwise occupancy truth tables.",
            "Python rule_mirror is diagnostic; Racket-backed checks remain authoritative.",
        ],
    }


def write_report(report: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def _parse_csv_ints(value: str) -> tuple[int, ...]:
    result = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    if not result:
        raise argparse.ArgumentTypeError("provide at least one integer seed")
    return result


def _parse_csv_strings(value: str) -> tuple[str, ...]:
    result = tuple(part.strip() for part in value.split(",") if part.strip())
    if not result:
        raise argparse.ArgumentTypeError("provide at least one difficulty")
    return result


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=_parse_csv_ints, default=(0, 31, 91))
    parser.add_argument(
        "--difficulties",
        type=_parse_csv_strings,
        default=("easy", "medium", "hard"),
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = run_probe(seeds=args.seeds, difficulties=args.difficulties)
    write_report(report, args.out)
    print(json.dumps({
        "passed": report["passed"],
        "windows_checked": report["schedule"]["windows_checked"],
        "rotations_checked": report["schedule"]["rotations_checked"],
        "grids_checked": report["relations"]["grids_checked"],
        "error_count": report["error_count"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
