#!/usr/bin/env python3
"""One bounded shortcut witness probe for generator 0ae119475d57."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "0ae119475d57"
EXPECTED_SHA256 = "42967d2de4dc05ab714039499533e569aa8cb5c62b02449bbb8e88638f43c83b"
PROBE_SEED_HEX = "90057ab120fcdb52c6970abb2376524a2285f6ddae7dd342edc554253ee9a3bd"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    started = time.monotonic()
    root = find_root(__file__)
    module, source, digest = load_selected_generator(TASK_ID, root=root)
    if digest != EXPECTED_SHA256:
        raise AssertionError(f"source drift: {digest}")
    rival = module.CANONICAL_SHORTCUTS["upper_wins_overlap"]
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_matches = [rival(pair["input"]) == pair["output"] for pair in canonical]

    seed = int(PROBE_SEED_HEX[:16], 16) % (2**63)
    sample_index = int(PROBE_SEED_HEX[16:24], 16) % 4
    grid = module.generate(seed, sample_index, difficulty="hard", grid_w=4)
    diagnostics = module.self_check(grid)
    truth = module.rule_mirror(grid)
    rival_output = rival(grid)
    differences = [
        [row, col, truth[row][col], rival_output[row][col]]
        for row in range(len(truth))
        for col in range(len(truth[0]))
        if truth[row][col] != rival_output[row][col]
    ]
    witness = module.SEMANTIC_WITNESSES["true_overlap_lower_wins"](grid)
    completed = all(canonical_matches) and not diagnostics and witness and bool(differences)
    result = {
        "schema": "arcpuzzles-ticket-adversarial-witness-v1",
        "ticket_id": "ticket-45cfd7795e5052d8",
        "type": "adversarial_witness",
        "task_id": TASK_ID,
        "source_path": str(source.relative_to(root)),
        "source_sha256": digest,
        "rule_hash": module.RULE_HASH,
        "probe_seed": PROBE_SEED_HEX,
        "elapsed_minutes": round((time.monotonic() - started) / 60, 6),
        "shortcut": "upper_wins_overlap",
        "canonical_pairs_checked": len(canonical),
        "canonical_pairs_matched": sum(canonical_matches),
        "generated_call": {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": "hard",
            "grid_w": 4,
        },
        "self_check": diagnostics,
        "witness_true_overlap_lower_wins": witness,
        "difference_count": len(differences),
        "differences": differences,
        "input": grid,
        "intended_output": truth,
        "shortcut_output": rival_output,
        "status": "completed" if completed else "unknown",
        "summary": (
            "The upper-wins-on-overlap shortcut fits every labeled canonical pair "
            "but is refuted by this lawful generated overlap, where the lower-panel "
            "color must win."
            if completed
            else "The bounded probe did not establish the intended witness."
        ),
        "limits": [
            "One generated witness and one declared shortcut were inspected.",
            "No peer source was modified and no census or full battery was run.",
        ],
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
