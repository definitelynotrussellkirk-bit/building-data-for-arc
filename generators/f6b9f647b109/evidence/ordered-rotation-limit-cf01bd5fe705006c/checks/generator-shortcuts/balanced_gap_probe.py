#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "f6b9f647b109"
BANDS = (None, "easy", "medium", "hard")
DRAWS_PER_BAND = 100


def endpoints(grid):
    red = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
    blue = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1)
    return red, blue


def is_balanced(grid) -> bool:
    red, blue = endpoints(grid)
    return abs(red[0] - blue[0]) == abs(red[1] - blue[1])


def balanced_unsupported_rival(generator, grid):
    """Fit all visible-dominant cases; leave balanced cases unchanged."""
    if is_balanced(grid):
        return [row[:] for row in grid]
    return generator.rule_mirror(grid)


def canonical_program(root: Path) -> str:
    programs = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                programs.append(row["program_solution"])
    unique = set(programs)
    if len(unique) != 1:
        raise RuntimeError(f"expected one unique canonical program, found {len(unique)}")
    return unique.pop()


def execute(bridge: RacketBridge, program: str, grid):
    body = strip_rule_wrapper(program)
    if body.lstrip().startswith("(lambda"):
        bridge.define_grid("shortcut_input", grid)
        return bridge.eval_text(f"({body} shortcut_input)")
    bridge.define_grid("g", grid)
    return bridge.eval_text(body)


def main() -> int:
    root = find_root(__file__)
    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    program = canonical_program(root)

    canonical_train = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for variant_index, line in enumerate(handle):
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            for pair_index, pair in enumerate(row.get("train", [])):
                canonical_train.append({
                    "variant_index": variant_index,
                    "content_hash": row.get("content_hash"),
                    "pair_index": pair_index,
                    "balanced": is_balanced(pair["input"]),
                    "rival_matches": balanced_unsupported_rival(generator, pair["input"]) == pair["output"],
                })

    generated_balanced = []
    generated_mismatches = []
    for band in BANDS:
        for sample_index in range(DRAWS_PER_BAND):
            grid = generator.generate(271828, sample_index, difficulty=band)
            if is_balanced(grid):
                generated_balanced.append({"difficulty": band, "sample_index": sample_index})
            if balanced_unsupported_rival(generator, grid) != generator.rule_mirror(grid):
                generated_mismatches.append({"difficulty": band, "sample_index": sample_index})

    witness = [[0] * 6 for _ in range(6)]
    witness[1][1] = 2
    witness[4][4] = 1
    with RacketBridge() as bridge:
        authority_output = execute(bridge, program, witness)
    mirror_output = generator.rule_mirror(witness)
    rival_output = balanced_unsupported_rival(generator, witness)

    evidence = {
        "schema": "arcpuzzles-generator-shortcut-evidence-v1",
        "task_id": TASK_ID,
        "source_path": str(source_path),
        "source_sha256": source_sha,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "shortcut": "perform the ordered path only when one coordinate gap is strictly dominant; leave balanced-gap inputs unchanged",
        "canonical_demonstrations": {
            "count": len(canonical_train),
            "balanced_count": sum(row["balanced"] for row in canonical_train),
            "rival_match_count": sum(row["rival_matches"] for row in canonical_train),
            "records": canonical_train,
        },
        "generated_support_probe": {
            "bands": list(BANDS),
            "draws_per_band": DRAWS_PER_BAND,
            "draws": len(BANDS) * DRAWS_PER_BAND,
            "balanced_count": len(generated_balanced),
            "rival_mismatch_count": len(generated_mismatches),
            "balanced_examples": generated_balanced[:5],
            "mismatch_examples": generated_mismatches[:5],
        },
        "counterexample": {
            "input": witness,
            "self_check": generator.self_check(witness),
            "authority_output": authority_output,
            "python_mirror_output": mirror_output,
            "rival_output": rival_output,
            "authority_matches_mirror": authority_output == mirror_output,
            "authority_differs_from_rival": authority_output != rival_output,
        },
        "generator_emits_counterexample_class": False,
        "reason": "ordinary generation declares only row|column major_axis and deliberately samples unequal gaps",
    }

    if not canonical_train or not all(row["rival_matches"] and not row["balanced"] for row in canonical_train):
        raise AssertionError("shortcut did not fit every canonical demonstration")
    if generated_balanced or generated_mismatches:
        raise AssertionError("ordinary generated support unexpectedly refuted the shortcut")
    if generator.self_check(witness):
        raise AssertionError("balanced witness is not in the public validator domain")
    if authority_output != mirror_output or authority_output == rival_output:
        raise AssertionError("balanced witness did not distinguish the shortcut")

    out = Path(__file__).with_name("balanced_gap_evidence.json")
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "reproduced",
        "canonical_demonstrations_matched": len(canonical_train),
        "generated_draws_matched": len(BANDS) * DRAWS_PER_BAND,
        "counterexample_refutes_shortcut": True,
        "evidence": str(out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
