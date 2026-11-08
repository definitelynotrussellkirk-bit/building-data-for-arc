#!/usr/bin/env python3
"""Source-bound canonical-shortcut probe for task 603bd7fff5df."""
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "603bd7fff5df"
RIVAL_NAME = "side_endpoint_eights"


def differing_cells(left, right):
    rows = max(len(left), len(right))
    out = []
    for r in range(rows):
        left_row = left[r] if r < len(left) else None
        right_row = right[r] if r < len(right) else None
        width = max(len(left_row or []), len(right_row or []))
        for c in range(width):
            lv = left_row[c] if left_row is not None and c < len(left_row) else None
            rv = right_row[c] if right_row is not None and c < len(right_row) else None
            if lv != rv:
                out.append([r, c, lv, rv])
    return out


def main() -> int:
    here = Path(__file__).resolve().parent
    root = find_root(__file__)
    gen, source, source_sha = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_fit = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        canonical_fit[name] = [
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "fits": rival(pair["input"]) == pair["output"],
            }
            for pair in canonical
        ]
    rival = gen.CANONICAL_SHORTCUTS[RIVAL_NAME]
    witness = None
    for band in ("easy", "medium", "hard"):
        for seed in (31, 707, 1234):
            for sample_index in range(36):
                grid = gen.generate(seed, sample_index, difficulty=band)
                intended = gen.rule_mirror(grid)
                rival_output = rival(grid)
                if rival_output != intended:
                    witness = {
                        "seed": seed,
                        "sample_index": sample_index,
                        "difficulty": band,
                        "overrides": {},
                        "input": grid,
                        "intended_python_mirror": intended,
                        "rival_output": rival_output,
                        "differing_cells": differing_cells(intended, rival_output),
                        "self_check": gen.self_check(grid),
                        "observed_overrides": gen.observe_overrides(grid),
                    }
                    break
            if witness:
                break
        if witness:
            break
    if witness is None:
        raise RuntimeError(f"no disagreement found for {RIVAL_NAME}")
    report = {
        "schema": "603bd7fff5df-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_source": str(source.relative_to(root)),
        "generator_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "rival": RIVAL_NAME,
        "canonical_pair_count": len(canonical),
        "canonical_shortcut_fit": canonical_fit,
        "all_declared_shortcuts_fit_all_canonical_pairs": all(
            row["fits"] for rows in canonical_fit.values() for row in rows
        ),
        "witness": witness,
    }
    (here / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
    (here / "input.json").write_text(json.dumps({"input": witness["input"]}, indent=2) + "\n")
    print(json.dumps({
        "generator_sha256": source_sha,
        "rival": RIVAL_NAME,
        "canonical_pairs": len(canonical),
        "all_declared_shortcuts_fit_all_canonical_pairs": report["all_declared_shortcuts_fit_all_canonical_pairs"],
        "recipe": {k: witness[k] for k in ("seed", "sample_index", "difficulty", "overrides")},
        "input_shape": [len(witness["input"]), len(witness["input"][0])],
        "intended_shape": [len(witness["intended_python_mirror"]), len(witness["intended_python_mirror"][0])],
        "rival_shape": [len(witness["rival_output"]), len(witness["rival_output"][0])],
        "differing_cells": len(witness["differing_cells"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
