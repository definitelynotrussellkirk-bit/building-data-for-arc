#!/usr/bin/env python3
"""One source-bound witness against a main-diagonal-only shortcut."""
from __future__ import annotations

import hashlib
import json
import traceback
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "2b12b664738d"
TICKET_ID = "ticket-498a78bb80efd78d"
PINNED_SOURCE_SHA256 = "fdf62f9ce90a3bb339209790ea2b8533b8d56a9c25bed48003036a8c157cd2cb"
PINNED_RULE_HASH = "e1a9213544fb"
PROBE_SEED = "61c3aee60cfc541991ca0849bddfd26a25f1e9bf8747c1f2444f2600061fdde7"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def grid_sha(grid) -> str:
    return digest_bytes(json.dumps(grid, separators=(",", ":")).encode())


def canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"expected one canonical program, found {len(programs)}")
    return programs.pop()


def racket_grid(grid) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def complete_all_diagonal_pairs(grid):
    output = [row[:] for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if a != 0 and a == e and b == 0 and d == 0:
                output[r][c + 1] = output[r + 1][c] = a
            if b != 0 and b == d and a == 0 and e == 0:
                output[r][c] = output[r + 1][c + 1] = b
    return output


def main_diagonal_only_shortcut(grid):
    output = [row[:] for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if a != 0 and a == e and b == 0 and d == 0:
                output[r][c + 1] = output[r + 1][c] = a
    return output


def main() -> int:
    report = {
        "schema": "arc-supplementary-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "type": "adversarial_witness",
        "task_id": TASK_ID,
        "consumer": "target_current_audit",
        "probe_seed": PROBE_SEED,
        "seed_derivation": "int(probe_seed[:16], 16)",
        "targeted_probe_count": 1,
        "shortcut": "complete same-color main-diagonal pairs but ignore anti-diagonal pairs",
        "rule_hash": PINNED_RULE_HASH,
    }
    try:
        module, source_path, source_sha = load_selected_generator(TASK_ID, root=ROOT)
        if source_sha != PINNED_SOURCE_SHA256:
            raise ValueError(f"pinned source mismatch: {source_sha}")
        seed = int(PROBE_SEED[:16], 16)
        grid = module.generate(seed, 0, difficulty="medium")
        self_check = module.self_check(grid, difficulty="medium")
        if self_check:
            raise AssertionError(f"generated witness is not lawful: {self_check}")
        blocks = module._diag_blocks(grid)
        orientations = [row[3] for row in blocks]

        program = canonical_program()
        bridge = RacketBridge()
        try:
            runtime = bridge.runtime_identity
            if runtime.get("protected") is not True:
                raise ValueError("expected protected Racket")
            reference = bridge.eval_text(f"({wrap_rule(program)} {racket_grid(grid)})")
        finally:
            bridge.close()

        mirror = complete_all_diagonal_pairs(grid)
        if reference != mirror:
            raise AssertionError("independent full-rule mirror disagrees with Racket")
        shortcut = main_diagonal_only_shortcut(grid)
        differing = [
            [r, c, reference[r][c], shortcut[r][c]]
            for r in range(len(grid))
            for c in range(len(grid[0]))
            if reference[r][c] != shortcut[r][c]
        ]
        witness = bool(differing)
        report.update({
            "status": "completed" if witness else "unknown",
            "summary": (
                f"A lawful current-source input contains {orientations.count('anti')} anti-diagonal block(s); "
                f"protected Racket differs from the main-diagonal-only shortcut on {len(differing)} cells."
                if witness else
                "The single pinned input did not refute the main-diagonal-only shortcut."
            ),
            "source": {"path": str(source_path.relative_to(ROOT)), "sha256": source_sha},
            "program_sha256": digest_bytes(program.encode()),
            "runtime": {
                "backend": runtime.get("backend"),
                "protected": runtime.get("protected"),
                "binary_sha256": runtime.get("binary_sha256"),
                "evaluations": 1,
            },
            "actual_seed": seed,
            "sample_index": 0,
            "difficulty": "medium",
            "self_check": self_check,
            "blocks": [{"row": r, "col": c, "color": color, "orientation": orientation}
                       for r, c, color, orientation in blocks],
            "input": grid,
            "reference_output": reference,
            "shortcut_output": shortcut,
            "differing_cells": differing,
            "input_sha256": grid_sha(grid),
            "reference_output_sha256": grid_sha(reference),
            "shortcut_output_sha256": grid_sha(shortcut),
            "limitations": [
                "One pinned seed/sample and one declared shortcut only; no peer battery or distribution claim.",
                "This witness supports teaching coverage; it does not approve or modify the peer generator.",
            ],
        })
    except Exception as exc:
        report.update({
            "status": "unknown",
            "summary": f"Bounded probe could not establish a witness: {type(exc).__name__}: {exc}",
            "error": traceback.format_exc(),
        })
    (HERE / "witness.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report.get(k) for k in ("ticket_id", "status", "summary")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
