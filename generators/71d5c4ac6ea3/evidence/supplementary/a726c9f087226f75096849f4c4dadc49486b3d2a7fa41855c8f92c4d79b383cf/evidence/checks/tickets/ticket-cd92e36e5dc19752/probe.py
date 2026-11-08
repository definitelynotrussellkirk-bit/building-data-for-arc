#!/usr/bin/env python3
"""One bounded witness for the fixed-two-seeds shortcut in 71d5c4ac6ea3."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator


TICKET_ID = "ticket-cd92e36e5dc19752"
TASK_ID = "71d5c4ac6ea3"
PINNED_SHA256 = "e70ca9f847fc4919d7cba9fa328eec429f34aea56d6a9fe99facc6a0d5e9c11f"
PINNED_RULE_HASH = "ed3afc80127d"
PROBE_SEED_HEX = "39b12ffc766d4627b4d440c22ab7e6bb1c291872f75cefad902d6712bc6d9ac9"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def sha_json(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def task_row():
    matches = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            matches.append(row)
    if len(matches) != 1:
        raise RuntimeError(f"expected one canonical task row, found {len(matches)}")
    return matches[0]


def official_pairs(row):
    test = row["test"]
    return list(row["train"]) + (test if isinstance(test, list) else [test])


def fixed_two_seed_shortcut(grid):
    height, width = len(grid), len(grid[0])
    anchor = sorted(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    )[0]
    offsets = [
        (row - anchor[0], col - anchor[1])
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    ]
    seeds = sorted(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    )
    output = [[0 for _ in range(width)] for _ in range(height)]
    for seed_row, seed_col in seeds[:2]:
        for delta_row, delta_col in offsets:
            row, col = seed_row + delta_row, seed_col + delta_col
            if 0 <= row < height and 0 <= col < width:
                output[row][col] = 8
    return output


def main() -> int:
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    if source_sha256 != PINNED_SHA256:
        raise RuntimeError(f"source drift: {source_sha256} != {PINNED_SHA256}")
    row = task_row()
    normalized_rule_hash = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode("utf-8")
    ).hexdigest()
    if not normalized_rule_hash.startswith(PINNED_RULE_HASH):
        raise RuntimeError(
            f"rule drift: {normalized_rule_hash} does not start with {PINNED_RULE_HASH}"
        )
    pairs = official_pairs(row)
    official_seed_counts = [
        sum(value == 2 for values in pair["input"] for value in values)
        for pair in pairs
    ]
    shortcut_survives_official = all(
        fixed_two_seed_shortcut(pair["input"]) == pair["output"]
        for pair in pairs
    )

    numeric_seed = int(PROBE_SEED_HEX[:16], 16)
    witness = generator.generate(
        numeric_seed,
        0,
        difficulty="hard",
        n_seeds=3,
    )
    seed_cells = sorted(
        (r, c)
        for r, values in enumerate(witness)
        for c, value in enumerate(values)
        if value == 2
    )
    if len(seed_cells) != 3:
        raise RuntimeError(f"probe failed to realize exactly three seeds: {seed_cells}")
    self_check = generator.self_check(witness)
    if self_check:
        raise RuntimeError(f"generated witness is not lawful: {self_check}")

    with RacketBridge(timeout=30) as bridge:
        bridge.define_grid("__ticket_input", witness)
        canonical_output = bridge.eval_text(
            f"({wrap_rule(row['program_solution'])} __ticket_input)"
        )
        runtime_identity = bridge.runtime_identity
    shortcut_output = fixed_two_seed_shortcut(witness)
    if canonical_output == shortcut_output:
        raise RuntimeError("three-seed witness did not refute fixed-two-seed shortcut")
    differing_cells = [
        [r, c]
        for r, (left_row, right_row) in enumerate(
            zip(canonical_output, shortcut_output, strict=True)
        )
        for c, (left, right) in enumerate(zip(left_row, right_row, strict=True))
        if left != right
    ]

    report = {
        "schema": "arcpuzzles-adversarial-witness-v1",
        "status": "completed",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "probe_seed_hex": PROBE_SEED_HEX,
        "numeric_seed": numeric_seed,
        "sample_index": 0,
        "shortcut": "extract all offsets but stamp them only at the first two row-major color-2 seeds",
        "why_plausible": (
            "all official training/query inputs contain exactly two seeds, so a fixed-two-target "
            "implementation reproduces every official output"
        ),
        "source": {
            "path": str(Path(source_path).relative_to(ROOT)),
            "sha256": source_sha256,
            "version": generator.VERSION,
            "rule_hash": PINNED_RULE_HASH,
            "normalized_rule_sha256": normalized_rule_hash,
        },
        "official_pair_count": len(pairs),
        "official_seed_counts": official_seed_counts,
        "shortcut_matches_every_official_pair": shortcut_survives_official,
        "witness": {
            "difficulty": "hard",
            "overrides": {"n_seeds": 3},
            "self_check": self_check,
            "seed_cells": [list(cell) for cell in seed_cells],
            "input": witness,
            "canonical_racket_output": canonical_output,
            "fixed_two_seed_shortcut_output": shortcut_output,
            "input_sha256": sha_json(witness),
            "canonical_output_sha256": sha_json(canonical_output),
            "shortcut_output_sha256": sha_json(shortcut_output),
            "differing_cells": differing_cells,
            "refutes_shortcut": canonical_output != shortcut_output,
        },
        "racket_runtime": {
            key: value
            for key, value in runtime_identity.items()
            if not key.endswith("_path")
        },
        "limitations": [
            "One deterministic generated witness was checked; this is not a generator-wide census.",
            "The witness refutes one concrete shortcut, not every alternative hypothesis.",
        ],
    }
    out = HERE / "witness.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "official_seed_counts": official_seed_counts,
                "shortcut_survives_official": shortcut_survives_official,
                "witness_seed_count": len(seed_cells),
                "differing_cell_count": len(differing_cells),
                "out": str(out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
