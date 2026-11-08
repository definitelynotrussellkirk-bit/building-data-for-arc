#!/usr/bin/env python3
"""One source-bound nearest-pair shortcut witness for ticket-293346737d9702bc."""
from __future__ import annotations

import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.generic.concepts.extraction import _program_body
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TICKET_ID = "ticket-293346737d9702bc"
TASK_ID = "3f26d45b9f51"
TICKET_SEED = "4160d90086bdfffce3aec3ae6db384f62d6736545cb4fddf8050a663271a9061"
EXPECTED_SOURCE_SHA256 = "1bd4448f9ff51545858cb402a42521bd7238925667727911e797a8259ee06f5a"
RIVAL_NAME = "nearest_pair_only"


def canonical_program(root: Path) -> str:
    for raw in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(raw)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise RuntimeError(f"canonical program missing for {TASK_ID}")


def differing_pixels(left: list[list[int]], right: list[list[int]]) -> list[dict[str, int]]:
    return [
        {"row": row, "col": col, "intended": left[row][col], "rival": right[row][col]}
        for row in range(len(left))
        for col in range(len(left[0]))
        if left[row][col] != right[row][col]
    ]


def main() -> int:
    root = find_root(__file__)
    module, source_path, actual_sha256 = load_selected_generator(TASK_ID, root=root)
    rival = module.SEMANTIC_RIVALS[RIVAL_NAME]
    canonical = canonical_pairs(TASK_ID, root=root)
    canonical_fit = [rival(pair["input"]) == pair["output"] for pair in canonical]

    derived_seed = int(TICKET_SEED[:16], 16)
    sample_index = int(TICKET_SEED[16:24], 16) % 10_000
    call = {
        "seed": derived_seed,
        "sample_index": sample_index,
        "difficulty": "medium",
        "K": 8,
        "n_colors": 3,
    }
    grid = module.generate(
        derived_seed,
        sample_index,
        difficulty="medium",
        K=8,
        n_colors=3,
    )
    self_errors = module.self_check(grid)
    strict_errors = module.strict_canonical_like(grid)
    has_three_collinear = module._w_three_collinear(grid)
    intended_python = module._solve_python(grid)
    rival_output = rival(grid)

    program = canonical_program(root)
    with RacketBridge() as bridge:
        bridge.define_grid("g", grid)
        intended_racket = bridge.eval_text(_program_body(program))
        runtime_identity = bridge.runtime_identity

    diffs = differing_pixels(intended_racket, rival_output)
    coarse_cells = sorted({(row["row"] // 3, row["col"] // 3) for row in diffs})
    witness_holds = bool(
        actual_sha256 == EXPECTED_SOURCE_SHA256
        and all(canonical_fit)
        and self_errors == []
        and strict_errors == []
        and has_three_collinear
        and intended_python == intended_racket
        and rival_output != intended_racket
        and diffs
    )
    report = {
        "schema": "arcpuzzles-ticket-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "rule_hash": module.RULE_HASH,
        "ticket_seed": TICKET_SEED,
        "seed_derivation": "seed=int(ticket_seed[:16],16); sample_index=int(ticket_seed[16:24],16)%10000",
        "source": {
            "path": str(source_path.relative_to(root)),
            "expected_sha256": EXPECTED_SOURCE_SHA256,
            "actual_sha256": actual_sha256,
            "matches": actual_sha256 == EXPECTED_SOURCE_SHA256,
        },
        "shortcut": {
            "name": RIVAL_NAME,
            "description": "On each occupied row or column, connect only the closest adjacent same-color marker pair.",
            "canonical_pair_fit": canonical_fit,
            "fits_all_canonical_pairs": all(canonical_fit),
        },
        "witness": {
            "call": call,
            "observe_overrides": module.observe_overrides(grid),
            "self_check": self_errors,
            "strict_canonical_like": strict_errors,
            "has_three_collinear_markers": has_three_collinear,
            "input": grid,
            "intended_output_racket": intended_racket,
            "intended_output_python_matches_racket": intended_python == intended_racket,
            "rival_output": rival_output,
            "differing_pixel_count": len(diffs),
            "differing_pixels": diffs,
            "differing_coarse_cells": [list(cell) for cell in coarse_cells],
        },
        "racket_runtime_identity": runtime_identity,
        "conclusion": {
            "witness_holds": witness_holds,
            "summary": (
                "The nearest-pair-only shortcut fits every canonical pair but leaves part of the "
                "min-to-max interval blank on this lawful three-collinear-marker scene."
            ),
        },
    }
    out = Path(__file__).with_name("result.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ticket_id": TICKET_ID, "witness_holds": witness_holds, "difference_pixels": len(diffs), "result": str(out)}, sort_keys=True))
    return 0 if witness_holds else 1


if __name__ == "__main__":
    raise SystemExit(main())
