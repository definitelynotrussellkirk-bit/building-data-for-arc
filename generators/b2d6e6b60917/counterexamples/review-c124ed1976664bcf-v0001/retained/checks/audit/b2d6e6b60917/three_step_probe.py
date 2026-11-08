"""Reproduce a three-copy-cap lesson ambiguity for b2d6e6b60917."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs

TASK_ID = "b2d6e6b60917"
HERE = Path(__file__).resolve().parent
ROOT = Path.cwd().resolve()
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
BAND = "easy"
SEED = 0
START = 1


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}_three_step", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    gen = load_generator()
    pairs = []
    for sample_index in range(START, START + gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(SEED, sample_index, difficulty=BAND)
        intended = gen.rule_mirror(grid)
        rival = gen._render(grid, steps=range(1, 4))
        pairs.append({
            "sample_index": sample_index,
            "profile": gen.schedule_profile(SEED, sample_index, BAND),
            "input": grid,
            "mirror_output": intended,
            "rival_output": rival,
            "rival_matches": rival == intended,
            "self_check": gen.self_check(grid, difficulty=BAND),
        })

    inputs = [pair["input"] for pair in pairs]
    (HERE / "lesson_inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")
    (HERE / "three_step_rival_outputs.json").write_text(
        json.dumps([pair["rival_output"] for pair in pairs], indent=2) + "\n"
    )
    (HERE / "mirror_outputs.json").write_text(
        json.dumps([pair["mirror_output"] for pair in pairs], indent=2) + "\n"
    )

    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    canonical_matches = sum(
        gen._render(pair["input"], steps=range(1, 4)) == pair["output"]
        for pair in canonical
    )

    racket_path = HERE / "three_step_racket.json"
    racket_record = json.loads(racket_path.read_text()) if racket_path.exists() else None
    racket_outputs = (
        [row["output"] for row in racket_record["results"]]
        if racket_record is not None else None
    )
    mirror_outputs = [pair["mirror_output"] for pair in pairs]
    rival_outputs = [pair["rival_output"] for pair in pairs]
    differing_cells = []
    if racket_outputs:
        for pair_index, (actual, rival) in enumerate(zip(racket_outputs, rival_outputs)):
            for r in range(len(actual)):
                for c in range(len(actual[0])):
                    if actual[r][c] != rival[r][c]:
                        differing_cells.append(
                            [pair_index, r, c, actual[r][c], rival[r][c]]
                        )

    evidence = {
        "schema": "arcpuzzles-audit-three-step-cap-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "rival": "apply the correct source/direction/stride rule but stop after ray step 3",
        "canonical_matches": f"{canonical_matches}/{len(canonical)}",
        "lesson": {
            "difficulty": BAND,
            "seed": SEED,
            "sample_indices": [pair["sample_index"] for pair in pairs],
            "profiles": [pair["profile"] for pair in pairs],
            "policy": "first 3 consecutive pairs are demonstrations; fourth is query",
            "demo_matches": [pair["rival_matches"] for pair in pairs[:3]],
            "query_matches": pairs[3]["rival_matches"],
            "self_check_errors": [pair["self_check"] for pair in pairs],
        },
        "racket": {
            "present": racket_record is not None,
            "generator_sha256": racket_record.get("generator_sha256") if racket_record else None,
            "rule_hash_matches_catalog": racket_record.get("rule_hash_matches_catalog") if racket_record else None,
            "all_outputs_valid": (
                all(row["valid_output"] and row["error"] is None for row in racket_record["results"])
                if racket_record else None
            ),
            "matches_python_mirror": racket_outputs == mirror_outputs if racket_outputs else None,
        },
        "query_differing_cells": [row for row in differing_cells if row[0] == 3],
        "finding": (
            "The named rival is not in LESSON_COMPETITORS. It fits every canonical pair and all three "
            "demonstrations in this lawful generated lesson, but predicts a different query output."
        ),
    }
    (HERE / "three_step_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
