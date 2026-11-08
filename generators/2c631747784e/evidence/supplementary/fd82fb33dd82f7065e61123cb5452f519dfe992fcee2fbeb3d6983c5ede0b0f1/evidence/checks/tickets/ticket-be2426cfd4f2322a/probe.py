#!/usr/bin/env python3
"""One source-bound witness against row-major color reversal."""
from __future__ import annotations

import hashlib
import json
import traceback
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "2c631747784e"
TICKET_ID = "ticket-be2426cfd4f2322a"
PINNED_SOURCE_SHA256 = "3ad4bb9784a8520161d14edac52ec73de6c4d7d6dd757e287ee676e87ab10f11"
PINNED_RULE_HASH = "1b96d7f1e866"
PROBE_SEED = "5e2b9daf03c453bc8168465e975e90daed73b9d27665537ec1e20176b3f10ab5"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def grid_sha(grid: list[list[int]]) -> str:
    return digest_bytes(json.dumps(grid, separators=(",", ":")).encode())


def canonical_program() -> str:
    programs: set[str] = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(f"expected one canonical program, found {len(programs)}")
    return programs.pop()


def racket_grid(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def differing_cells(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    return [
        [r, c, a[r][c], b[r][c]]
        for r in range(len(a))
        for c in range(len(a[0]))
        if a[r][c] != b[r][c]
    ]


def main() -> int:
    report: dict[str, object] = {
        "schema": "arc-supplementary-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "type": "adversarial_witness",
        "task_id": TASK_ID,
        "consumer": "target_current_audit",
        "probe_seed": PROBE_SEED,
        "seed_derivation": "int(probe_seed[:16], 16)",
        "targeted_probe_count": 1,
        "shortcut": "reverse colors over row-major non-cyan positions instead of path order",
        "rule_hash": PINNED_RULE_HASH,
    }
    try:
        module, source_path, source_sha = load_selected_generator(TASK_ID, root=ROOT)
        if source_sha != PINNED_SOURCE_SHA256:
            raise ValueError(f"pinned source mismatch: {source_sha}")

        seed = int(PROBE_SEED[:16], 16)
        grid = module.generate(seed, 0, difficulty="medium")
        errors = module.self_check(grid, difficulty="medium")
        if errors:
            raise AssertionError(f"generated witness is not lawful: {errors}")

        program = canonical_program()
        bridge = RacketBridge()
        try:
            runtime = bridge.runtime_identity
            if runtime.get("protected") is not True:
                raise ValueError("expected protected Racket")
            reference = bridge.eval_text(f"({wrap_rule(program)} {racket_grid(grid)})")
        finally:
            bridge.close()

        mirror = module.rule_mirror(grid)
        if reference != mirror:
            raise AssertionError("generator's semantic mirror disagrees with protected Racket")
        shortcut = module.SEMANTIC_RIVALS["reverse_row_major_noncyan_cells"](grid)
        differences = differing_cells(reference, shortcut)
        path_info = module._analyze(grid)
        row_major_positions = sorted(
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value != 8
        )
        path_differs = path_info["path"] != row_major_positions and path_info["path"] != list(reversed(row_major_positions))
        witness = bool(differences) and path_differs

        report.update({
            "status": "completed" if witness else "unknown",
            "summary": (
                f"A lawful current-source path is not row-major; protected Racket differs from the "
                f"row-major reversal shortcut on {len(differences)} cells."
                if witness else
                "The single pinned input did not refute row-major reversal."
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
            "self_check": errors,
            "path_length": path_info["path_length"],
            "turn_count": path_info["turn_count"],
            "path_differs_from_row_major_in_both_directions": path_differs,
            "input": grid,
            "reference_output": reference,
            "shortcut_output": shortcut,
            "differing_cells": differences,
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
