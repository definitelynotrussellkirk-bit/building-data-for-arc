#!/usr/bin/env python3
"""Regenerate the retained canonical-shortcut counterexample bundle."""
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "1e26763a6f70"
SEED = 20261012
SAMPLE_INDEX = 1
DIFFICULTY = "medium"


def main() -> int:
    root = find_root(__file__)
    gen, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    canon = canonical_pairs(TASK_ID, root=root)
    canonical_fit = {
        name: all(rival(pair["input"]) == pair["output"] for pair in canon)
        for name, rival in gen.CANONICAL_SHORTCUTS.items()
    }
    if not all(canonical_fit.values()):
        raise AssertionError(f"declared shortcut no longer fits canonicals: {canonical_fit}")

    grid = gen.generate(SEED, SAMPLE_INDEX, difficulty=DIFFICULTY)
    intended = gen.rule_mirror(grid)
    rival_outputs = {
        name: rival(grid) for name, rival in gen.CANONICAL_SHORTCUTS.items()
    }
    surviving = [name for name, output in rival_outputs.items() if output == intended]
    if surviving:
        raise AssertionError(f"counterexample failed to refute: {surviving}")

    payload = {
        "schema": "arcpuzzles-generator-counterexample-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "seed": SEED,
        "sample_index": SAMPLE_INDEX,
        "difficulty": DIFFICULTY,
        "schedule_profile": gen.schedule_profile(SEED, SAMPLE_INDEX, DIFFICULTY),
        "canonical_pairs_checked": len(canon),
        "canonical_shortcut_fit": canonical_fit,
        "input": grid,
        "intended_output": intended,
        "rival_outputs": rival_outputs,
        "purpose": (
            "Both declared shortcuts fit every labeled canonical pair but differ "
            "from the intended rule on this generated rich scene."
        ),
    }
    output = source_path.parent / "counterexamples" / "canonical-shortcuts.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(output)
    print(json.dumps({
        "generator_sha256": source_sha,
        "profile": payload["schedule_profile"],
        "canonical_shortcuts": sorted(rival_outputs),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
