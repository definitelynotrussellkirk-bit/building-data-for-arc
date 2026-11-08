#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

TASK_ID = "2534c7164e36"
EXPECTED_SOURCE_SHA256 = "eab765a3418f667520bfac6419a2730a4666dcb1e3fb54508c5cc117ef051ac5"


def sha_json(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = Path.cwd().resolve()
    for path in (root / "shared" / "runtime", root / "src"):
        sys.path.insert(0, str(path))

    from arc_repl.racket_bridge import RacketBridge  # noqa: PLC0415
    from puzzle_generators.rule_wrap import wrap_rule  # noqa: PLC0415
    from reviewer_support import (  # noqa: PLC0415
        canonical_pairs,
        canonical_path,
        load_selected_generator,
    )

    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    exact_source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if source_sha256 != exact_source_sha256 or exact_source_sha256 != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("source binding mismatch")

    programs = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise RuntimeError(f"expected one canonical program, found {len(programs)}")
    program = next(iter(programs))

    canonical = canonical_pairs(TASK_ID, root=root)

    def linked_only_rival(grid):
        analysis = module._analyze(grid)
        if analysis["errors"]:
            raise ValueError("invalid rival input")
        if analysis["facts"]["family"] == "linked":
            return module._priority_output(grid)
        return [[0] * 4 for _ in range(4)]

    canonical_matches = [
        linked_only_rival(pair["input"]) == pair["output"] for pair in canonical
    ]

    witness = module.generate(
        0,
        0,
        difficulty="medium",
        scene_family="generalized",
    )
    analysis = module._analyze(witness)
    mirror_output = module.rule_mirror(witness)
    rival_output = linked_only_rival(witness)
    function = wrap_rule(program)
    datum = "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in witness
    ) + ")"
    with RacketBridge(max_calls_before_restart=8) as bridge:
        racket_output = bridge.eval_text(f"({function} '{datum})")
        runtime_identity = bridge.runtime_identity

    differing_cells = [
        [row, col]
        for row in range(4)
        for col in range(4)
        if racket_output[row][col] != rival_output[row][col]
    ]
    payload = {
        "schema": "arcpuzzles-supplementary-adversarial-witness-v1",
        "ticket_id": "ticket-5f774277e8b5eea5",
        "task_id": TASK_ID,
        "source_path": str(source_path.relative_to(root)),
        "source_sha256": exact_source_sha256,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "canonical_pair_occurrences": len(canonical),
        "linked_only_rival_matches_all_canonical_occurrences": all(canonical_matches),
        "shortcut": (
            "Apply the correct overlay only to linked/published geometry; return a "
            "blank 4x4 output for generalized geometry."
        ),
        "witness": {
            "generation": {
                "seed": 0,
                "sample_index": 0,
                "difficulty": "medium",
                "scene_family": "generalized",
            },
            "self_check": module.self_check(witness),
            "observed_overrides": module.observe_overrides(witness),
            "masks": list(analysis["facts"]["masks"]),
            "input": witness,
            "input_sha256": sha_json(witness),
            "racket_output": racket_output,
            "racket_output_sha256": sha_json(racket_output),
            "mirror_matches_racket": mirror_output == racket_output,
            "rival_output": rival_output,
            "rival_output_sha256": sha_json(rival_output),
            "differing_cells": differing_cells,
        },
        "runtime_identity": {
            key: (Path(value).name if key.endswith("_path") and isinstance(value, str) else value)
            for key, value in runtime_identity.items()
        },
        "finding": False,
        "summary": (
            "The linked-only shortcut fits every canonical occurrence but is refuted "
            f"on a lawful generalized witness at {len(differing_cells)}/16 cells; "
            "the current generator already supplies the separating family."
        ),
        "scope": "All canonical occurrences plus one generated witness and one Racket execution; no seed census.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
