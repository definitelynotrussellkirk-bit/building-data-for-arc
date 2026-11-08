#!/usr/bin/env python3
"""Bounded source-bound audit for the 69cab6228fdc native family."""
from __future__ import annotations

import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
from typing import Callable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HERE = Path(__file__).resolve().parent
_spec = spec_from_file_location("_family_69cab6228fdc_verify", HERE / "family.py")
family = module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(family)


def _rank(value: int) -> int:
    return 1 + ((value - 1) % 3)


def _paint_payload(grid, rank):
    stage = family.canonical_transform(grid)
    payloads = family._payloads(stage)
    out = [row[:] for row in stage]
    for r, c in payloads[_rank(rank) - 1]:
        out[r][c] = 8
    return out


def _raw_body(grid):
    return grid[3:]


def _sep(grid):
    return family._separator_col(family.canonical_transform(grid))


def _raw_source_area(grid):
    sep = _sep(grid)
    return sum(value == 1 for row in _raw_body(grid) for value in row[:sep])


def _raw_target_regions(grid):
    sep = _sep(grid)
    return len([cells for cells in family._components(_raw_body(grid), 2)
                if max(c for _, c in cells) < sep])


def _raw_target_cells(grid):
    sep = _sep(grid)
    return sum(value == 2 for row in _raw_body(grid) for value in row[:sep])


def _legend_source_col(grid):
    return grid[0].index(1) + 1


def _nonzero_count(grid):
    return sum(value != 0 for row in grid for value in row)


RIVALS: dict[str, Callable] = {
    "canonical_only": family.canonical_transform,
    "always_first": lambda grid: _paint_payload(grid, 1),
    "always_second": lambda grid: _paint_payload(grid, 2),
    "always_third": lambda grid: _paint_payload(grid, 3),
    "raw_source_component_count": lambda grid: _paint_payload(grid, family.raw_source_count(grid)),
    "raw_source_area_mod_three": lambda grid: _paint_payload(grid, _raw_source_area(grid)),
    "raw_target_region_count_mod_three": lambda grid: _paint_payload(grid, _raw_target_regions(grid)),
    "raw_target_cell_count_mod_three": lambda grid: _paint_payload(grid, _raw_target_cells(grid)),
    "grid_height_mod_three": lambda grid: _paint_payload(grid, len(grid)),
    "grid_width_mod_three": lambda grid: _paint_payload(grid, len(grid[0])),
    "legend_source_column_mod_three": lambda grid: _paint_payload(grid, _legend_source_col(grid)),
    "total_nonzero_mod_three": lambda grid: _paint_payload(grid, _nonzero_count(grid)),
}


def _racket_apply(bridge, program, grid):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def audit(seed_count: int = 32) -> dict:
    failures = []
    survivor_records = []
    rival_checks = 0
    intermediate_hist = {"1": 0, "2": 0, "3": 0}
    sizes = set()
    raw_source_hist = {}

    for seed in range(seed_count):
        for demos in (2, 3, 6):
            episode = family.build_episode(seed, "mapped_region_relay", demos, 4)
            for pair in episode["train"] + episode["test"]:
                value = family.mapped_region_count(pair["input"])
                intermediate_hist[str(value)] += 1
                raw = family.raw_source_count(pair["input"])
                raw_source_hist[str(raw)] = raw_source_hist.get(str(raw), 0) + 1
                sizes.add((len(pair["input"]), len(pair["input"][0])))
            for name, rival in RIVALS.items():
                rival_checks += 1
                fits = all(rival(pair["input"]) == pair["output"] for pair in episode["train"])
                changes_query = any(rival(pair["input"]) != pair["output"] for pair in episode["test"])
                if fits and changes_query:
                    record = {"seed": seed, "demos": demos, "rival": name}
                    failures.append(record)
                    survivor_records.append(record)

    racket_evaluations = 0
    bridge = RacketBridge()
    runtime = bridge.runtime_identity
    try:
        for seed in (0, 17):
            for mode in family.MODES:
                episode = family.build_episode(seed, mode, 3, 4)
                program = family.program_for(mode)
                for pair in episode["train"] + episode["test"]:
                    racket_evaluations += 1
                    actual = _racket_apply(bridge, program, pair["input"])
                    if actual != pair["output"]:
                        failures.append({"seed": seed, "mode": mode, "racket_mismatch": True})
        witness_episode = family.build_episode(17, "mapped_region_relay", 3, 4)
        witness = witness_episode["test"][3]
        correct = _racket_apply(bridge, family.program_for("mapped_region_relay"), witness["input"])
        wrong = _racket_apply(bridge, family.counterfactual_program(), witness["input"])
        racket_evaluations += 2
        if correct != witness["output"] or correct == wrong:
            failures.append({"counterfactual": "did_not_change_output"})
    finally:
        bridge.close()

    changed_cells = sum(
        a != b for row_a, row_b in zip(correct, wrong) for a, b in zip(row_a, row_b)
    )
    return {
        "schema": "69cab6228fdc-parametric-authoring-audit-v1",
        "task_id": family.TASK_ID,
        "seed_count": seed_count,
        "demo_counts": [2, 3, 6],
        "queries": 4,
        "episodes": seed_count * 3,
        "rival_checks": rival_checks,
        "named_rivals": sorted(RIVALS),
        "surviving_query_changing_rivals": survivor_records,
        "intermediate_histogram": intermediate_hist,
        "raw_source_component_histogram": raw_source_hist,
        "sizes": [list(size) for size in sorted(sizes)],
        "contains_30x30": (30, 30) in sizes,
        "racket_evaluations": racket_evaluations,
        "racket": {k: runtime[k] for k in (
            "schema", "backend", "protected", "binary_sha256", "prelude_sha256", "bridge_sha256"
        ) if k in runtime},
        "counterfactual": {
            "ablation": "wrong_intermediate",
            "actual_intermediate": family.mapped_region_count(witness["input"]),
            "wrong_intermediate": family.raw_source_count(witness["input"]),
            "changed_cells": changed_cells,
            "input_size": [len(witness["input"]), len(witness["input"][0])],
        },
        "failures": failures,
        "status": "pass" if not failures else "fail",
        "limits": "Finite named-rival and seed audit; not a proof of universal identifiability.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = audit(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in (
        "status", "episodes", "rival_checks", "racket_evaluations", "counterfactual", "failures"
    )}, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
