#!/usr/bin/env python3
"""Protected-Racket bounded self-audit for the 99d71aabd753 family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HOME = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("audit_99_prototype", HOME / "prototype.py")
if SPEC is None or SPEC.loader is None:
    raise ImportError("cannot load prototype")
prototype = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)

SETTINGS = [
    {"alignment": alignment, "measure": measure}
    for alignment in prototype.ALLOWED_ALIGNMENTS
    for measure in prototype.ALLOWED_MEASURES
]


def _literal(grid) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _grid_key(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)

    programs = {
        json.dumps(setting, sort_keys=True): prototype.program_for(
            setting["measure"], setting["alignment"]
        )
        for setting in SETTINGS
    }
    wrapped = {key: wrap_rule(program) for key, program in programs.items()}
    audit_rows = []
    all_profiles = set()
    all_first_cells = set()
    evaluation_count = 0
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
                    setting_key = json.dumps(setting, sort_keys=True)
                    labels = []
                    for grid in grids:
                        expected = prototype.python_output(
                            grid,
                            measure=setting["measure"],
                            alignment=setting["alignment"],
                        )
                        actual = bridge.eval_text(
                            f"({wrapped[setting_key]} {_literal(grid)})"
                        )
                        evaluation_count += 1
                        if actual != expected:
                            raise AssertionError(
                                f"Racket/Python mismatch seed={seed} demos={demos} setting={setting}"
                            )
                        labels.append(actual)
                    signatures[setting_key] = json.dumps(labels[:demos], separators=(",", ":"))
                if len(set(signatures.values())) != len(SETTINGS):
                    raise AssertionError("minimum/maximum demonstrations do not identify every setting")

                for grid in grids:
                    object_values = sorted(prototype.component_counts(grid).values(), reverse=True)
                    cell_values = sorted(prototype.cell_counts(grid).values(), reverse=True)
                    all_profiles.add(tuple(object_values))
                    nonzero = [
                        (r, c)
                        for r, row in enumerate(grid)
                        for c, value in enumerate(row)
                        if value != 0
                    ]
                    all_first_cells.add(min(nonzero))
                    if not any(a - b > 1 for a, b in zip(object_values, object_values[1:])):
                        raise AssertionError("rank-step shortcut survived")
                    official = prototype.python_output(grid, measure="objects", alignment="right")
                    if prototype.rank_step_output(grid) == official:
                        raise AssertionError("rank-step rival matched official output")
                    if official == prototype.python_output(grid, measure="cells", alignment="right"):
                        raise AssertionError("object/cell measures aliased")
                boundary = grids[-1]
                if len(boundary) != 30 or len(boundary[0]) != 30:
                    raise AssertionError("last query is not 30x30")
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

    if len(all_profiles) < 5:
        raise AssertionError("fixed-profile bypass not sufficiently challenged")
    if len(all_first_cells) < 5:
        raise AssertionError("fixed-location bypass not sufficiently challenged")

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
            "canonical_default_byte_exact": programs[
                json.dumps({"alignment": "right", "measure": "objects"}, sort_keys=True)
            ] == prototype.canonical_source(),
            "setting_independent_inputs": True,
            "minimum_and_maximum_demo_counts": [2, 6],
            "four_queries": True,
            "all_inputs_distinct": True,
            "sole_finite_setting_from_demos": True,
            "rank_step_bypass_refuted": True,
            "object_cell_alias_refuted": True,
            "fixed_profile_bypass_refuted": True,
            "fixed_location_bypass_refuted": True,
            "content_bearing_30x30_query": True,
        },
        "object_profiles": [list(row) for row in sorted(all_profiles)],
        "cases": audit_rows,
        "limits": "Finite seeds 0, 17, 83; declared four-setting family and named rivals only.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "racket_evaluations": evaluation_count, "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
