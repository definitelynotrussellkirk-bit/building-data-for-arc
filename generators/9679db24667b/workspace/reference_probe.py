#!/usr/bin/env python3
"""Independent row-rule and curriculum probe for task 9679db24667b.

This tool deliberately does not call the generator's ``rule_mirror``, row
analysis helpers, witness predicates, or hard-coded rival-name lists.  It can be
copied with a staged runtime and used to check canonical parity, generated
structure, declared shortcut fit, competitor refutation, cyclic lesson starts,
and query rotations.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "9679db24667b"
HOME = Path(__file__).resolve().parents[1]


def _normalized_copy(grid) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be nonempty")
    rows = []
    width = None
    for row in grid:
        if not isinstance(row, (list, tuple)) or not row:
            raise ValueError("rows must be nonempty")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError("grid must be rectangular")
        copied = list(row)
        if any(type(value) is not int or not 0 <= value <= 9 for value in copied):
            raise ValueError("cells must be integer ARC colors 0..9")
        rows.append(copied)
    return rows


def classify_rows(grid) -> list[dict[str, Any]]:
    """Describe each row using only the public pixels."""
    rows = _normalized_copy(grid)
    result = []
    for index, row in enumerate(rows):
        companions = [value for value in row if value not in (0, 9)]
        colors = sorted(set(companions))
        nines = row.count(9)
        if not colors and not nines:
            kind = "blank"
        elif len(colors) == 1 and nines:
            kind = "qualifying"
        elif not colors and nines:
            kind = "nine_only"
        elif len(colors) >= 2 and nines:
            kind = "multi_color_marker"
        else:
            kind = "color_without_marker"
        result.append(
            {
                "row": index,
                "kind": kind,
                "nines": nines,
                "colors": colors,
                "companion_counts": dict(sorted(Counter(companions).items())),
            }
        )
    return result


def independent_oracle(grid) -> list[list[int]]:
    """Apply the written row predicate without importing generator helpers."""
    source = _normalized_copy(grid)
    output = deepcopy(source)
    for fact in classify_rows(source):
        if fact["kind"] != "qualifying":
            continue
        replacement = fact["colors"][0]
        row_index = fact["row"]
        output[row_index] = [
            replacement if value == 9 else value
            for value in source[row_index]
        ]
    return output


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("generator_9679db24667b_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pair(grid) -> dict[str, Any]:
    return {"input": deepcopy(grid), "output": independent_oracle(grid)}


def audit(generator_path: Path, samples_per_band: int) -> dict[str, Any]:
    module = _load_generator(generator_path)
    canonical = canonical_pairs(TASK_ID, root=find_root(__file__))
    canonical_mismatches = [
        {
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
        }
        for pair in canonical
        if independent_oracle(pair["input"]) != pair["output"]
    ]

    bands: dict[str, Any] = {}
    generated_grids: list[list[list[int]]] = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts = Counter()
        unique = set()
        for index in range(samples_per_band):
            grid = module.generate(30_000 + 1_000 * band_index, index, difficulty=band)
            generated_grids.append(grid)
            facts = classify_rows(grid)
            counts["samples"] += 1
            counts["oracle_changed"] += independent_oracle(grid) != grid
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["canonical_profile"] += not any(
                fact["kind"] in {"nine_only", "multi_color_marker"}
                for fact in facts
            )
            counts["teaching_profile"] += any(fact["kind"] == "nine_only" for fact in facts)
            counts["multiple_nines"] += any(
                fact["kind"] == "qualifying" and fact["nines"] >= 2
                for fact in facts
            )
            counts["repeated_companion"] += any(
                fact["kind"] == "qualifying"
                and sum(fact["companion_counts"].values()) >= 2
                for fact in facts
            )
            unique.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
        counts["unique_inputs"] = len(unique)
        bands[band] = dict(counts)

    declared_shortcuts = dict(getattr(module, "CANONICAL_SHORTCUTS", {}))
    shortcut_fit = {
        name: all(solver(pair["input"]) == pair["output"] for pair in canonical)
        for name, solver in declared_shortcuts.items()
    }

    competitors = dict(getattr(module, "LESSON_COMPETITORS", {}))
    teaching = [
        grid
        for grid in generated_grids
        if any(fact["kind"] == "nine_only" for fact in classify_rows(grid))
    ]
    competitor_refuted = {
        name: any(solver(grid) != independent_oracle(grid) for grid in teaching)
        for name, solver in competitors.items()
    }

    lesson_failures = []
    profiles = tuple(getattr(module, "SCHEDULE_PROFILES", ()))
    cycle = max(1, len(profiles))
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(2 * cycle):
            seed = 70_000 + 1_000 * band_index + start
            lesson = [
                _pair(module.generate(seed, index, difficulty=band))
                for index in range(start, start + 4)
            ]
            for held_out in range(4):
                demos = [pair for index, pair in enumerate(lesson) if index != held_out]
                reasons = module.lesson_identifiable(demos, lesson[held_out])
                if reasons:
                    lesson_failures.append(
                        {
                            "band": band,
                            "start": start,
                            "held_out": held_out,
                            "reasons": reasons,
                        }
                    )

    generator_sha = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    return {
        "schema": "9679db24667b-independent-probe-v1",
        "task_id": TASK_ID,
        "generator_version": getattr(module, "VERSION", None),
        "generator_sha256": generator_sha,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical": {
            "pairs": len(canonical),
            "oracle_mismatches": canonical_mismatches,
            "declared_shortcut_fit": shortcut_fit,
        },
        "samples_per_band": samples_per_band,
        "bands": bands,
        "competitor_refuted_by_teaching_profile": competitor_refuted,
        "rotation_probe": {
            "cycle_length": cycle,
            "starts_per_band": 2 * cycle,
            "rotations_checked": 3 * 2 * cycle * 4,
            "failures": lesson_failures,
        },
        "limitations": [
            "The Python oracle is independent supplementary evidence; the repository Racket authority remains final.",
            "Finite declared-rival checks do not prove uniqueness against every possible hypothesis.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generator",
        type=Path,
        default=Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")),
    )
    parser.add_argument("--samples-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.samples_per_band < 1:
        parser.error("--samples-per-band must be positive")

    report = audit(args.generator.resolve(), args.samples_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    failed = bool(
        report["canonical"]["oracle_mismatches"]
        or not all(report["canonical"]["declared_shortcut_fit"].values())
        or not all(report["competitor_refuted_by_teaching_profile"].values())
        or report["rotation_probe"]["failures"]
        or any(values["self_check_errors"] for values in report["bands"].values())
    )
    print(
        json.dumps(
            {
                "generator_version": report["generator_version"],
                "canonical": report["canonical"],
                "bands": report["bands"],
                "competitor_refuted_by_teaching_profile": report[
                    "competitor_refuted_by_teaching_profile"
                ],
                "rotation_probe": report["rotation_probe"],
                "status": "FAIL" if failed else "PASS",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
