#!/usr/bin/env python3
"""Bounded authoring audit for the 70205357c60a native parametric family."""
from __future__ import annotations

import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
from typing import Callable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HERE = Path(__file__).resolve().parent
_spec = spec_from_file_location("_family_70205357c60a_verify", HERE / "family.py")
family = module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(family)


def _paint_payload(grid, rank):
    stage = family.canonical_transform(grid)
    sep = family._separator_col(grid)
    payloads = [cells for cells in family._components(stage, 3) if cells[0][1] > sep]
    rank = max(1, min(3, rank))
    out = [row[:] for row in stage]
    for r, c in payloads[rank - 1]:
        out[r][c] = 8
    return out


def _main_component(grid):
    sep = family._separator_col(grid)
    large = [cells for cells in family._components(grid, 5)
             if max(c for _, c in cells) < sep and len(cells) >= 9]
    if len(large) != 1:
        raise ValueError("expected one large controller")
    return large[0]


def _bbox_rank(grid, axis):
    cells = _main_component(grid)
    if axis == "width":
        rank = max(c for _, c in cells) - min(c for _, c in cells) - 1
    else:
        rank = max(r for r, _ in cells) - min(r for r, _ in cells) - 1
    return _paint_payload(grid, rank)


def _all_component_rank(grid):
    sep = family._separator_col(grid)
    count = len([cells for cells in family._components(grid, 5)
                 if max(c for _, c in cells) < sep])
    return _paint_payload(grid, count)


def _raw_cell_mod(grid):
    sep = family._separator_col(grid)
    count = sum(value == 5 for row in grid for value in row[:sep])
    return _paint_payload(grid, 1 + ((count - 1) % 3))


RIVALS: dict[str, Callable] = {
    "canonical_only": family.canonical_transform,
    "always_first": lambda grid: _paint_payload(grid, 1),
    "always_second": lambda grid: _paint_payload(grid, 2),
    "always_third": lambda grid: _paint_payload(grid, 3),
    "raw_large_component_count": lambda grid: _paint_payload(grid, 1),
    "controller_width_minus_two": lambda grid: _bbox_rank(grid, "width"),
    "controller_height_minus_two": lambda grid: _bbox_rank(grid, "height"),
    "all_raw_5_components": _all_component_rank,
    "raw_5_cell_count_mod_three": _raw_cell_mod,
}


def _racket_apply(bridge, program, grid):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def audit(seed_count: int = 32) -> dict:
    failures = []
    rival_checks = 0
    survivor_records = []
    intermediate_hist = {"1": 0, "2": 0, "3": 0}
    sizes = set()
    boundary_contacts = 0

    for seed in range(seed_count):
        for demos in (2, 3, 6):
            episode = family.build_episode(seed, "interior_count_relay", demos, 4)
            for pair in episode["train"] + episode["test"]:
                value = family.interior_count(pair["input"])
                intermediate_hist[str(value)] += 1
                h, w = len(pair["input"]), len(pair["input"][0])
                sizes.add((h, w))
                if any(pair["input"][r][c] for r, c in
                       [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]):
                    boundary_contacts += 1
            for name, rival in RIVALS.items():
                rival_checks += 1
                fits = all(rival(pair["input"]) == pair["output"] for pair in episode["train"])
                changes_query = any(rival(pair["input"]) != pair["output"] for pair in episode["test"])
                if fits and changes_query:
                    failures.append({"seed": seed, "demos": demos, "rival": name})
                    survivor_records.append({"seed": seed, "demos": demos, "rival": name})

    racket_evaluations = 0
    bridge = RacketBridge()
    try:
        runtime = bridge.runtime_identity
        for seed in (0, 17):
            for mode in family.MODES:
                episode = family.build_episode(seed, mode, 3, 4)
                program = family.program_for(mode)
                for pair in episode["train"] + episode["test"]:
                    racket_evaluations += 1
                    actual = _racket_apply(bridge, program, pair["input"])
                    if actual != pair["output"]:
                        failures.append({"seed": seed, "mode": mode, "racket_mismatch": True})
        witness_episode = family.build_episode(0, "interior_count_relay", 3, 4)
        witness = next(pair for pair in witness_episode["test"] if family.interior_count(pair["input"]) != 1)
        correct = _racket_apply(bridge, family.program_for("interior_count_relay"), witness["input"])
        wrong = _racket_apply(bridge, family.counterfactual_program(), witness["input"])
        racket_evaluations += 2
        if correct == wrong or correct != witness["output"]:
            failures.append({"counterfactual": "did_not_change_output"})
    finally:
        bridge.close()

    return {
        "schema": "70205357c60a-parametric-authoring-audit-v1",
        "task_id": family.TASK_ID,
        "seed_count": seed_count,
        "demo_counts": [2, 3, 6],
        "queries": 4,
        "episodes": seed_count * 3,
        "rival_checks": rival_checks,
        "named_rivals": sorted(RIVALS),
        "surviving_query_changing_rivals": survivor_records,
        "intermediate_histogram": intermediate_hist,
        "sizes": [list(size) for size in sorted(sizes)],
        "contains_30x30": (30, 30) in sizes,
        "corner_boundary_contacts": boundary_contacts,
        "racket_evaluations": racket_evaluations,
        "racket": {k: runtime[k] for k in ("schema", "backend", "protected", "binary_sha256", "prelude_sha256", "bridge_sha256") if k in runtime},
        "counterfactual": {
            "ablation": "wrong_intermediate",
            "actual_intermediate": family.interior_count(witness["input"]),
            "wrong_intermediate": 1,
            "changed_cells": sum(a != b for ra, rb in zip(correct, wrong) for a, b in zip(ra, rb)),
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
    print(json.dumps({k: report[k] for k in ("status", "episodes", "rival_checks", "racket_evaluations", "failures")}, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
