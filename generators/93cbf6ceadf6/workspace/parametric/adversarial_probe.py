#!/usr/bin/env python3
"""Protected-Racket bounded self-audit for the 93cbf6ceadf6 family."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HOME = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("audit_93_prototype", HOME / "prototype.py")
if SPEC is None or SPEC.loader is None:
    raise ImportError("cannot load prototype")
prototype = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)
BASE = prototype.BASE

SETTINGS = [
    {"output_transform": value}
    for value in prototype.ALLOWED_TRANSFORMS
]


def _literal(grid) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _grid_key(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def _item_output(item) -> list[list[int]]:
    grid = [[0 for _ in range(item["width"])] for _ in range(item["height"])]
    for row, col in item["shape"]:
        grid[row][col] = item["color"]
    return grid


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)

    programs = {
        setting["output_transform"]: prototype.program_for(
            setting["output_transform"]
        )
        for setting in SETTINGS
    }
    wrapped = {name: wrap_rule(program) for name, program in programs.items()}

    audit_rows = []
    evaluation_count = 0
    odd_reading_positions = set()
    odd_shapes = set()
    odd_colors = set()
    color_multiplicities = set()
    first_object_mismatch_count = 0
    non_unique_odd_color_count = 0
    area_bbox_control_count = 0

    bridge = RacketBridge()
    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise AssertionError("self-audit requires protected Racket")

        for seed in (0, 17, 83):
            for demos in (2, 6):
                grids = prototype.sample_inputs(seed, demos + 4)
                input_keys = [_grid_key(grid) for grid in grids]
                if len(set(input_keys)) != len(input_keys):
                    raise AssertionError("duplicate visible input")

                signatures = {}
                for setting in SETTINGS:
                    transform = setting["output_transform"]
                    labels = []
                    for grid in grids:
                        expected = prototype.python_output(
                            grid, output_transform=transform
                        )
                        actual = bridge.eval_text(
                            f"({wrapped[transform]} {_literal(grid)})"
                        )
                        evaluation_count += 1
                        if actual != expected:
                            raise AssertionError(
                                "Racket/Python mismatch "
                                f"seed={seed} demos={demos} transform={transform}"
                            )
                        labels.append(actual)
                    signatures[transform] = json.dumps(
                        labels[:demos], separators=(",", ":")
                    )
                if len(set(signatures.values())) != len(SETTINGS):
                    raise AssertionError(
                        "minimum/maximum demonstrations do not identify every setting"
                    )

                for grid in grids:
                    errors = BASE.self_check(grid)
                    if errors:
                        raise AssertionError(f"base grammar violation: {errors}")
                    items = BASE._component_items(grid)
                    frequencies = Counter(item["shape"] for item in items)
                    if sorted(frequencies.values()) != [1, 2]:
                        raise AssertionError("scene does not have exact 2+1 shape multiplicity")
                    odd_index = next(
                        index for index, item in enumerate(items)
                        if frequencies[item["shape"]] == 1
                    )
                    odd = items[odd_index]
                    repeated = next(
                        item for item in items if frequencies[item["shape"]] == 2
                    )
                    odd_reading_positions.add(odd_index)
                    odd_shapes.add(odd["shape"])
                    odd_colors.add(odd["color"])
                    colors = Counter(item["color"] for item in items)
                    color_multiplicities.add(tuple(sorted(colors.values())))
                    if colors[odd["color"]] != 1:
                        non_unique_odd_color_count += 1
                    if (
                        len(odd["shape"]) == len(repeated["shape"])
                        and (odd["height"], odd["width"])
                        == (repeated["height"], repeated["width"])
                    ):
                        area_bbox_control_count += 1
                    else:
                        raise AssertionError("area/bbox control was not matched")

                    canonical = prototype.python_output(
                        grid, output_transform="identity"
                    )
                    first = _item_output(items[0])
                    if first != canonical:
                        first_object_mismatch_count += 1
                    transformed = {
                        json.dumps(
                            prototype.python_output(grid, output_transform=name),
                            separators=(",", ":"),
                        )
                        for name in prototype.ALLOWED_TRANSFORMS
                    }
                    if len(transformed) != 3:
                        raise AssertionError("untransformed-output rival survived")

                boundary = grids[-1]
                if len(boundary) != 30 or len(boundary[0]) != 30:
                    raise AssertionError("last query is not 30x30")
                if sum(cell != 0 for row in boundary for cell in row) < 60:
                    raise AssertionError("30x30 query is not content bearing")
                if not (
                    any(boundary[0])
                    and any(boundary[-1])
                    and any(row[0] for row in boundary)
                    and any(row[-1] for row in boundary)
                ):
                    raise AssertionError("30x30 query does not span all four edges")

                audit_rows.append(
                    {
                        "seed": seed,
                        "demos": demos,
                        "queries": 4,
                        "distinct_inputs": len(set(input_keys)),
                        "settings_identified": len(set(signatures.values())),
                        "boundary_shape": [30, 30],
                    }
                )
    finally:
        bridge.close()

    if odd_reading_positions != {0, 1, 2}:
        raise AssertionError("fixed-position bypass not fully refuted")
    if first_object_mismatch_count == 0:
        raise AssertionError("first-object bypass was never contradicted")
    if non_unique_odd_color_count == 0:
        raise AssertionError("unique-color bypass was never contradicted")
    if len(odd_shapes) < 8 or len(odd_colors) < 7:
        raise AssertionError("shape/color variation is too narrow")
    if color_multiplicities < {(3,), (1, 2), (1, 1, 1)}:
        raise AssertionError("color controls do not cover all intended multiplicities")

    result = {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": prototype.TASK_ID,
        "status": "passed",
        "protected_racket": True,
        "racket": identity,
        "racket_evaluations": evaluation_count,
        "program_sha256": {
            key: hashlib.sha256(value.encode()).hexdigest()
            for key, value in programs.items()
        },
        "checks": {
            "canonical_default_byte_exact": programs["identity"]
            == prototype.canonical_source(),
            "setting_independent_inputs": True,
            "minimum_and_maximum_demo_counts": [2, 6],
            "four_queries": True,
            "all_inputs_distinct": True,
            "sole_finite_setting_from_demos": True,
            "fixed_position_bypass_refuted": True,
            "first_object_bypass_refuted": True,
            "unique_color_bypass_refuted": True,
            "area_bbox_bypass_refuted": True,
            "untransformed_output_bypass_refuted": True,
            "content_bearing_30x30_query": True,
        },
        "variation": {
            "odd_reading_positions": sorted(odd_reading_positions),
            "odd_shape_count": len(odd_shapes),
            "odd_color_count": len(odd_colors),
            "color_multiplicities": [
                list(row) for row in sorted(color_multiplicities)
            ],
            "first_object_mismatches": first_object_mismatch_count,
            "non_unique_odd_color_cases": non_unique_odd_color_count,
            "matched_area_bbox_cases": area_bbox_control_count,
        },
        "cases": audit_rows,
        "limits": (
            "Finite seeds 0, 17, 83; declared three-setting family and named "
            "rivals only."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "passed",
                "racket_evaluations": evaluation_count,
                "out": str(args.out),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
