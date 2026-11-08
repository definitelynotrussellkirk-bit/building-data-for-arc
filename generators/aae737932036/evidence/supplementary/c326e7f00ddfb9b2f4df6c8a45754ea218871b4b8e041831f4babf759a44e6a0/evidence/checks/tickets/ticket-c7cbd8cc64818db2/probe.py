from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "aae737932036"
EXPECTED_SOURCE_SHA256 = "976a9e1496e37af6b4e4e03ee06480998cc283c97b5f67fae84b7f81ea8f7f71"
EXPECTED_RULE_HASH = "f01a570f8a9d"
PROBE_SEED = "b6d6eda13c940e27fc2597d8b5a2495d190370be1bb59221fccc7104c14a62f0"


def global_column_pack_skipping_ones(grid):
    """Plausible shortcut: use the whole column, preserving but ignoring 1-walls."""
    out = copy.deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for c in range(w):
        markers = [grid[r][c] for r in range(h) if grid[r][c] not in (0, 1)]
        slots = [r for r in range(h) if grid[r][c] != 1]
        for r in slots:
            out[r][c] = 0
        for r, color in zip(slots[-len(markers):], markers):
            out[r][c] = color
    return out


def canonical_program(root: Path) -> str:
    programs = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"expected one canonical program, found {len(programs)}")
    return programs.pop()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = find_root(__file__)
    generator, source, source_sha = load_selected_generator(TASK_ID, root=root)
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source drift: {source_sha}")
    program = canonical_program(root)
    program_sha = hashlib.sha256(program.encode()).hexdigest()
    normalized_rule_hash = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
    if normalized_rule_hash != EXPECTED_RULE_HASH:
        raise RuntimeError(f"rule drift: {normalized_rule_hash}")

    # Deterministic lawful witness selected from the pinned probe seed: an
    # interior 1-wall separates two markers from the bottom floor.
    witness = [[0 for _ in range(8)] for _ in range(8)]
    witness[-1] = [1] * 8
    witness[4][3] = 1
    witness[0][3] = 2
    witness[1][3] = 3
    witness[0][1] = 4
    witness[3][1] = 5
    self_check = generator.self_check(witness)
    if self_check:
        raise AssertionError(self_check)

    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in witness) + ")"
    with RacketBridge() as bridge:
        canonical = bridge.eval_text(f"({wrap_rule(program)} {literal})")
        runtime = bridge.runtime_identity
    rival = global_column_pack_skipping_ones(witness)
    differing = [
        {"row": r, "column": c, "canonical": canonical[r][c], "shortcut": rival[r][c]}
        for r in range(len(witness))
        for c in range(len(witness[0]))
        if canonical[r][c] != rival[r][c]
    ]
    if not differing:
        raise AssertionError("witness failed to distinguish the shortcut")

    result = {
        "schema": "arcpuzzles-adversarial-witness-v1",
        "ticket_id": "ticket-c7cbd8cc64818db2",
        "type": "adversarial_witness",
        "task_id": TASK_ID,
        "probe_seed": PROBE_SEED,
        "source": str(source.relative_to(root)),
        "source_sha256": source_sha,
        "rule_sha256": program_sha,
        "rule_hash": normalized_rule_hash,
        "shortcut": "global_column_pack_skipping_ones",
        "shortcut_description": "preserve 1-cells but pack all markers into the lowest non-1 cells of the whole column, ignoring interior walls as segment boundaries",
        "self_check_errors": self_check,
        "input": witness,
        "canonical_output": canonical,
        "shortcut_output": rival,
        "differing_cells": differing,
        "observation": "The two markers in column 3 remain above the interior wall under the canonical segment-local rule, but cross below it under the shortcut.",
        "runtime_identity": runtime,
        "limits": "One constructed lawful witness; no prevalence or lesson-schedule estimate.",
    }
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"differing_cells": len(differing), "protected": runtime.get("protected")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
