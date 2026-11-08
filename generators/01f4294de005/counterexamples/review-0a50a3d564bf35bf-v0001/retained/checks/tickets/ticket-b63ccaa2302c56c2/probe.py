#!/usr/bin/env python3
"""Bounded morphology-shortcut probe for ticket-b63ccaa2302c56c2."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TICKET_ID = "ticket-b63ccaa2302c56c2"
TASK_ID = "01f4294de005"
PINNED_SOURCE_SHA256 = "591671957b7f51cc484c0a8bbd4a1100d79a7365184faeb9b8feb0558c76df5f"
RULE_HASH = "813a9887f202"
PROBE_SEED = "06c69f889ee974b9b3486cf933ad74adcbf4ff1363d1c73cf36e26986f5125a5"


def json_hash(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    root = find_root(__file__)
    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    if source_sha != PINNED_SOURCE_SHA256:
        raise RuntimeError(f"source hash drift: {source_sha}")

    seed_base = int(PROBE_SEED[:16], 16) % 1_000_000_000
    samples = []
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        for offset in range(8):
            seed = seed_base + band_index * 10_000 + offset
            sample_index = band_index * 8 + offset
            grid = generator.generate(seed, sample_index, difficulty=difficulty)
            samples.append(
                {
                    "difficulty": difficulty,
                    "seed": seed,
                    "sample_index": sample_index,
                    "height": len(grid),
                    "width": len(grid[0]),
                    "row_1_blank": all(value == 0 for value in grid[1]),
                    "self_check": generator.self_check(grid),
                    "input_sha256": json_hash(grid),
                }
            )

    candidates = [
        pair
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True)
        if any(value != 0 for value in pair["input"][1])
        and generator.self_check(pair["input"]) == []
    ]
    if not candidates:
        raise RuntimeError("no lawful canonical witness with nonzero row 1")
    pair = candidates[0]
    witness = {
        "variant": pair["variant"],
        "split": pair["split"],
        "pair_index": pair["pair_index"],
        "row_1_nonzero_cells": [
            [1, column, value]
            for column, value in enumerate(pair["input"][1])
            if value != 0
        ],
        "self_check": generator.self_check(pair["input"]),
        "input": pair["input"],
        "output": pair["output"],
        "input_sha256": json_hash(pair["input"]),
        "output_sha256": json_hash(pair["output"]),
    }

    result = {
        "schema": "arc-supplementary-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "task_id": TASK_ID,
        "source": {
            "path": source_path.relative_to(root).as_posix(),
            "sha256": source_sha,
        },
        "rule_hash": RULE_HASH,
        "probe_seed": PROBE_SEED,
        "shortcut": (
            "Treat the first all-zero row as a structural separator and infer that "
            "the legend is everything above it, rather than learning that the "
            "legend is specifically row 0."
        ),
        "generated_probe": {
            "sample_count": len(samples),
            "row_1_blank_count": sum(row["row_1_blank"] for row in samples),
            "all_self_checks_passed": all(not row["self_check"] for row in samples),
            "samples": samples,
        },
        "lawful_witness": witness,
        "finding": (
            "The separator shortcut is supported by all 24 bounded generated "
            "samples but refuted by a self-check-valid canonical input with body "
            "cells immediately below the legend. This independently reproduces "
            "the current unresolved morphology audit on the pinned source."
        ),
    }
    out = Path(__file__).with_name("result.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": "finding",
        "generated": len(samples),
        "row_1_blank": result["generated_probe"]["row_1_blank_count"],
        "witness": witness["input_sha256"],
        "result": str(out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
