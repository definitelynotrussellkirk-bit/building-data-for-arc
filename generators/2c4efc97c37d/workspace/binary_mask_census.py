#!/usr/bin/env python3
"""Bounded adversarial census for task 2c4efc97c37d binary-mask teaching.

The probe is independent of the production generator's geometry helpers.  It
checks exact override recovery, both palette-topology schedules, the isolated
color-9 witness, all registered shortcut disagreements, and output parity with
the independent onion oracle.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from typing import Any

import onion_probe as probe


def _is_isolated_nine(grid: list[list[int]]) -> bool:
    positions = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    ]
    if len(positions) != 1:
        return False
    row, col = positions[0]
    height, width = len(grid), len(grid[0])
    return all(
        not (0 <= row + dr < height and 0 <= col + dc < width)
        or grid[row + dr][col + dc] == 0
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
    )


def _topology_details(grid: list[list[int]]) -> dict[str, Any]:
    components = probe.components(grid)
    depths = [probe.onion_depth(cells) for cells in components]
    color_sets = [
        tuple(sorted({grid[row][col] for row, col in cells}))
        for cells in components
    ]
    if any(len(colors) > 1 for colors in color_sets):
        mode = "mixed"
    else:
        values = [colors[0] for colors in color_sets]
        mode = "reused" if len(values) != len(set(values)) else "unique"

    by_color: dict[int, list[int]] = defaultdict(list)
    for colors, depth in zip(color_sets, depths):
        if len(colors) == 1:
            by_color[colors[0]].append(depth)
    repeated_depths = [values for values in by_color.values() if len(values) > 1]
    return {
        "mode": mode,
        "color_sets": color_sets,
        "depths": depths,
        "repeated_depths": repeated_depths,
    }


def _cases(full: bool):
    if not full:
        common = {
            "seed": 27182,
            "difficulty": None,
            "grid_h": 9,
            "grid_w": 25,
            "object_count": 3,
            "max_depth": 3,
            "irregular_count": 2,
        }
        for sample_index in (0, 1):
            yield {**common, "sample_index": sample_index}
        return

    for (
        seed,
        difficulty,
        grid_h,
        grid_w,
        object_count,
        max_depth,
        irregular_count,
        sample_index,
    ) in product(
        (17, 27182),
        (None, "easy", "medium", "hard"),
        (9, 18),
        (25, 30),
        (3, 4),
        (2, 4),
        (1, 3),
        (0, 1),
    ):
        yield {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "grid_h": grid_h,
            "grid_w": grid_w,
            "object_count": object_count,
            "max_depth": max_depth,
            "irregular_count": irregular_count,
        }


def run_census(*, full: bool = True) -> dict[str, Any]:
    gen = probe.load_generator()
    failures: list[dict[str, Any]] = []
    topology_counts: Counter[str] = Counter()
    band_counts: Counter[str] = Counter()
    cases = list(_cases(full))

    for index, case in enumerate(cases):
        overrides = {
            name: case[name]
            for name in ("grid_h", "grid_w", "object_count", "max_depth", "irregular_count")
        }
        try:
            grid = gen.generate(
                case["seed"],
                case["sample_index"],
                difficulty=case["difficulty"],
                **overrides,
            )
            errors = gen.self_check(grid)
            observed = gen.observe_overrides(grid)
            intended = probe.intended_output(grid)
            topology = _topology_details(grid)
            expected_mode = ("reused", "mixed")[case["sample_index"] % 2]
            rival_outputs = {
                "bbox_rectangle_depth": probe.bbox_shortcut_output(grid),
                "color_partition_depth": probe.color_partition_output(grid),
                "nonzero_foreground_depth": probe.nonzero_output(grid),
            }
            checks = {
                "self_check": not errors,
                "override_recovery": observed == overrides,
                "rule_mirror": gen.rule_mirror(grid) == intended,
                "isolated_nine": _is_isolated_nine(grid),
                "scheduled_topology": topology["mode"] == expected_mode,
                "all_rivals_disagree": all(value != intended for value in rival_outputs.values()),
                "registered_rivals_match_probe": all(
                    gen.SEMANTIC_RIVALS[name](grid) == value
                    for name, value in rival_outputs.items()
                ),
                "reused_depths_differ": (
                    expected_mode != "reused"
                    or (
                        len(topology["repeated_depths"]) == 1
                        and len(set(topology["repeated_depths"][0])) == 2
                    )
                ),
                "mixed_component_present": (
                    expected_mode != "mixed"
                    or sum(len(colors) > 1 for colors in topology["color_sets"]) == 1
                ),
            }
            failed = [name for name, passed in checks.items() if not passed]
            if failed:
                failures.append(
                    {
                        "case_index": index,
                        "case": case,
                        "failed_checks": failed,
                        "self_check_errors": errors,
                        "observed": observed,
                        "topology": topology,
                        "intended": intended,
                        "rivals": rival_outputs,
                    }
                )
            topology_counts[topology["mode"]] += 1
            band_counts[str(case["difficulty"])] += 1
        except Exception as exc:  # retained as bounded diagnostic evidence
            failures.append(
                {
                    "case_index": index,
                    "case": case,
                    "exception": f"{type(exc).__name__}: {exc}",
                }
            )

    source = Path(gen.__file__).resolve()
    return {
        "schema": "arcpuzzles-binary-mask-census-v1",
        "task_id": probe.TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": sha256(source.read_bytes()).hexdigest(),
        "full": full,
        "case_count": len(cases),
        "topology_counts": dict(sorted(topology_counts.items())),
        "band_counts": dict(sorted(band_counts.items())),
        "failures": failures,
        "passed": not failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="run two representative cases")
    parser.add_argument("--out", type=Path, help="optional JSON report path")
    args = parser.parse_args(argv)
    report = run_census(full=not args.quick)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
