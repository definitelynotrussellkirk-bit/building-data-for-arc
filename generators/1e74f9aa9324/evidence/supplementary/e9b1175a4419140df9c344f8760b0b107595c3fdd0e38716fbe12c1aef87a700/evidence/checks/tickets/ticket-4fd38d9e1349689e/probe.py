#!/usr/bin/env python3
"""One bounded adversarial witness for generator 1e74f9aa9324."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TICKET_ID = "ticket-4fd38d9e1349689e"
TASK_ID = "1e74f9aa9324"
EXPECTED_GENERATOR_SHA256 = "839df7863b053e392bff17a586bac17487907fc228ddc3a43ca3d3af71d257bf"
EXPECTED_RULE_HASH = "d37150574f6e"
PROBE_SEED = "af4dfa0860085fd89056021d318b3af276bc8690914c837cdff98f14d1e1eaf8"
_MAPPING = {2: 2, 3: 4, 4: 3, 8: 1}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_program(root: Path) -> str:
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    return row["program_solution"]
    raise KeyError(TASK_ID)


def rule_application(source: str, grid: Any) -> str:
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    )
    return f"({wrap_rule(source)} '({rows}))"


def move_code_but_preserve_decoys(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-equivalent shortcut: move col-0 codes, but retain distractors."""
    output = copy.deepcopy(grid)
    for row in output:
        code = row[0]
        row[0] = 0
        target = _MAPPING.get(code)
        if target is not None and target < len(row):
            row[target] = code
    return output


def main() -> None:
    repo = find_root(__file__)
    generator, source_path, digest = load_selected_generator(TASK_ID, root=repo)
    if digest != EXPECTED_GENERATOR_SHA256:
        raise SystemExit(
            f"pinned generator mismatch: expected {EXPECTED_GENERATOR_SHA256}, got {digest}"
        )
    if getattr(generator, "RULE_HASH", None) != EXPECTED_RULE_HASH:
        raise SystemExit("pinned rule hash mismatch")

    canonical = canonical_pairs(TASK_ID, root=repo, variant=0)
    canonical_matches = []
    for pair in canonical:
        shortcut = move_code_but_preserve_decoys(pair["input"])
        matches = shortcut == pair["output"]
        canonical_matches.append({
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "matches": matches,
        })
        if not matches:
            raise AssertionError("shortcut is not canonical-equivalent on the pinned variant")

    seed = int(PROBE_SEED[:16], 16)
    sample_index = int(PROBE_SEED[16:24], 16) % 10000
    recipe = {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": "medium",
        "overrides": {"grid_h": 10, "grid_w": 10, "texture": "one_per_row"},
    }
    witness_input = generator.generate(
        seed,
        sample_index,
        difficulty=recipe["difficulty"],
        **recipe["overrides"],
    )
    validation_errors = generator.self_check(
        witness_input,
        difficulty=recipe["difficulty"],
        meta=recipe["overrides"],
    )
    if validation_errors:
        raise AssertionError(f"generated witness is not lawful: {validation_errors}")
    observed = generator.observe_overrides(witness_input)
    if observed != recipe["overrides"]:
        raise AssertionError(f"override realization mismatch: {observed}")

    program = canonical_program(repo)
    with RacketBridge(timeout=30, max_calls_before_restart=None) as bridge:
        authoritative = bridge.eval_text(rule_application(program, witness_input))
    mirror = generator.rule_mirror(witness_input)
    if authoritative != mirror:
        raise AssertionError("Python mirror disagrees with canonical Racket authority")

    shortcut = move_code_but_preserve_decoys(witness_input)
    if shortcut == authoritative:
        raise AssertionError("adversarial shortcut unexpectedly agrees on witness")
    differing_cells = [
        {"row": r, "column": c, "authority": authoritative[r][c], "shortcut": shortcut[r][c]}
        for r in range(len(authoritative))
        for c in range(len(authoritative[0]))
        if authoritative[r][c] != shortcut[r][c]
    ]
    if len(differing_cells) != len(witness_input):
        raise AssertionError(
            "one_per_row witness should expose exactly one retained distractor per row"
        )
    if not all(row["authority"] == 0 and row["shortcut"] != 0 for row in differing_cells):
        raise AssertionError("differences are not precisely preserved distractors")

    report = {
        "schema": "arcpuzzles-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "status": "completed",
        "source_binding": {
            "generator_path": str(source_path.relative_to(repo)),
            "generator_sha256": digest,
            "rule_hash": EXPECTED_RULE_HASH,
            "rule_source_sha256": sha256_bytes(program.encode("utf-8")),
        },
        "shortcut": {
            "name": "move_code_but_preserve_decoys",
            "claim": (
                "Apply the correct column-0 lookup but leave every other nonzero input cell in place."
            ),
            "plausibility": (
                "All four canonical pairs contain no distractors, so this shortcut matches every "
                "canonical label while omitting the rule's erasure behavior."
            ),
            "canonical_pairs_checked": len(canonical_matches),
            "canonical_matches": canonical_matches,
        },
        "witness": {
            "recipe": recipe,
            "input": witness_input,
            "authoritative_output": authoritative,
            "shortcut_output": shortcut,
            "differing_cells": differing_cells,
            "validation": {
                "self_check": "passed",
                "observed_overrides": observed,
                "racket_matches_python_mirror": True,
                "shortcut_disagrees": True,
            },
        },
        "assessment": {
            "finding": False,
            "summary": (
                "A lawful one-decoy-per-row input separates the canonical-equivalent "
                "move-but-preserve shortcut in all 10 rows. The generator already schedules "
                "decoy textures and validates erasure, so this witness supports the current "
                "no-issue audit rather than exposing a new defect."
            ),
        },
        "limits": [
            "One source-bound witness was constructed; no peer battery or distribution census was run.",
            "The result rejects this shortcut only and is not a universal identifiability proof.",
        ],
    }
    out_path = Path(__file__).with_name("witness.json")
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ticket_id": TICKET_ID,
        "status": "completed",
        "canonical_pairs_matched": len(canonical_matches),
        "differing_cells": len(differing_cells),
        "output": str(out_path),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
