#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, load_selected_generator

TASK_ID = "0fce75f9162a"
EXPECTED_SOURCE = "1d052a6b65320bdb645cce0fc5576a3f3a86bb442c6872cd3310cca8cf792e40"
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def global_shift_to_top(grid):
    height, width = len(grid), len(grid[0])
    occupied = [(r, c, grid[r][c]) for r in range(height) for c in range(width) if grid[r][c] != 0]
    shift = min(r for r, _c, _v in occupied)
    out = [[0] * width for _ in range(height)]
    for row, col, value in occupied:
        out[row - shift][col] = value
    return out


def canonical_program():
    values = set()
    with canonical_path(REPO).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                values.add(row["program_solution"])
    if len(values) != 1:
        raise ValueError("expected one canonical program")
    return values.pop()


def main():
    module, source, source_sha = load_selected_generator(TASK_ID, root=REPO)
    if source_sha != EXPECTED_SOURCE:
        raise ValueError(f"peer source drift: {source_sha}")
    grid = module.generate(5, 0, difficulty="medium", texture="blobs_share_cols")
    self_check = module.self_check(grid, difficulty="medium")
    program = canonical_program()
    with RacketBridge(timeout=15.0) as bridge:
        if bridge.runtime_identity.get("protected") is not True:
            raise ValueError("protected Racket required")
        actual = bridge.eval_text(f"({wrap_rule(program)} {literal(grid)})")
        racket_identity = {k: bridge.runtime_identity[k] for k in ("backend", "protected", "binary_sha256", "prelude_sha256")}
    rival = global_shift_to_top(grid)
    baseline = module.generate(17, 0, difficulty="easy")
    ignored = module.generate(17, 0, difficulty="easy", n_blobs=1)
    report = {
        "schema": "arcpuzzles-peer-bounded-finding-v1",
        "task_id": TASK_ID,
        "status": "finding",
        "generator_path": str(source.relative_to(REPO)),
        "generator_sha256": source_sha,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "racket": racket_identity,
        "finding": "The advertised blobs_share_cols texture violates the task's disjoint-column invariant, yet generate returns it and self_check accepts it. Protected Racket then overwrites colliding independently shifted blobs. The advertised n_blobs=1 override is also ignored in the easy band.",
        "case": {
            "call": {"seed": 5, "sample_index": 0, "difficulty": "medium", "overrides": {"texture": "blobs_share_cols"}},
            "input": grid,
            "input_sha256": digest(grid),
            "self_check": self_check,
            "actual_racket_output": actual,
            "actual_output_sha256": digest(actual),
            "plausible_rival": "shift the complete foreground upward by its global top row",
            "rival_output": rival,
            "rival_output_sha256": digest(rival),
            "outputs_differ": actual != rival,
        },
        "override_probe": {
            "call": {"seed": 17, "sample_index": 0, "difficulty": "easy", "overrides": {"n_blobs": 1}},
            "baseline_equals_override": baseline == ignored,
            "realized_nonzero_colors": len({v for row in ignored for v in row if v}),
            "self_check": module.self_check(ignored, difficulty="easy"),
        },
        "recommended_repair": "Remove/reject degenerate textures that violate declared invariants; make n_blobs an exact honored control in every band; strengthen self_check to reject overlapping blob column ranges and invalid requested counts.",
        "limits": "One retained texture case and one override case on exact current source; not a full generator battery.",
    }
    if self_check or actual == rival or baseline != ignored:
        raise ValueError("expected peer defect did not reproduce exactly")
    out = HERE / "finding.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "finding", "path": str(out.relative_to(WORK)), "source_sha256": source_sha, "racket_output_differs_from_rival": actual != rival, "n_blobs_override_ignored": baseline == ignored}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
