#!/usr/bin/env python3
"""Enumerate every legal joint override across all bands and schedule profiles."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("e51349aef7b1_controls", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def frozen(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def run(seed: int) -> dict[str, Any]:
    bands = (None, "easy", "medium", "hard")
    failures: list[dict[str, Any]] = []
    unique: set[tuple[tuple[int, ...], ...]] = set()
    coverage = {
        "bands": set(),
        "panel_n": set(),
        "c_cells": set(),
        "palette_id": set(),
        "profiles": set(),
    }
    cases = 0
    for band in bands:
        for panel_n in (5, 6):
            for c_cells in range(4, 9):
                for palette_id in range(5):
                    for profile in range(GEN.LESSON_SCHEDULE_PERIOD):
                        cases += 1
                        grid = GEN.generate(
                            seed,
                            profile,
                            difficulty=band,
                            panel_n=panel_n,
                            c_cells=c_cells,
                            palette_id=palette_id,
                        )
                        unique.add(frozen(grid))
                        expected = {
                            "panel_n": panel_n,
                            "c_cells": c_cells,
                            "palette_id": palette_id,
                        }
                        observed = GEN.observe_overrides(grid)
                        problems = []
                        if observed != expected:
                            problems.append({"observed": observed, "expected": expected})
                        problems.extend(GEN.self_check(grid, difficulty=band))
                        problems.extend(GEN.strict_canonical_like(grid))
                        if GEN.rule_mirror(grid) != GEN._output_for_code(
                            grid, GEN._matching_codes(*GEN._split_panels(grid)[:2])[0]
                        ):
                            problems.append("rule mirror disagrees with first cropped match")
                        if problems:
                            failures.append({
                                "band": band,
                                "panel_n": panel_n,
                                "c_cells": c_cells,
                                "palette_id": palette_id,
                                "profile": profile,
                                "problems": problems,
                            })
                        coverage["bands"].add("default" if band is None else band)
                        coverage["panel_n"].add(panel_n)
                        coverage["c_cells"].add(c_cells)
                        coverage["palette_id"].add(palette_id)
                        coverage["profiles"].add(profile)

    invalid_cases = (
        {"panel_n": 4}, {"panel_n": 7}, {"panel_n": True},
        {"c_cells": 3}, {"c_cells": 9}, {"c_cells": 4.0},
        {"palette_id": -1}, {"palette_id": 5}, {"palette_id": "2"},
        {"unknown_axis": 1}, {"transform": 2},
    )
    invalid_rejected = 0
    invalid_failures = []
    for kwargs in invalid_cases:
        try:
            GEN.generate(seed, 0, **kwargs)
        except (TypeError, ValueError):
            invalid_rejected += 1
        else:
            invalid_failures.append(kwargs)

    serial_coverage = {key: sorted(values, key=str) for key, values in coverage.items()}
    passed = not failures and not invalid_failures and cases == 800
    return {
        "schema": "e51349aef7b1-control-probe-v1",
        "generator_sha256": hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest(),
        "seed": seed,
        "cases_checked": cases,
        "expected_cases": 800,
        "unique_inputs": len(unique),
        "coverage": serial_coverage,
        "invalid_cases_checked": len(invalid_cases),
        "invalid_cases_rejected": invalid_rejected,
        "invalid_failures": invalid_failures,
        "failures": failures,
        "passed": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=811)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run(args.seed)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(json.dumps({
        "passed": report["passed"],
        "cases_checked": report["cases_checked"],
        "unique_inputs": report["unique_inputs"],
        "invalid_cases_rejected": report["invalid_cases_rejected"],
        "failures": len(report["failures"]),
        "invalid_failures": report["invalid_failures"],
        "coverage": report["coverage"],
    }, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
