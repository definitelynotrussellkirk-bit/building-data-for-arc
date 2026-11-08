#!/usr/bin/env python3
"""Reproduce c8d52f645999 validator ambiguity and dead texture controls."""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from reviewer_support import load_selected_generator

TASK_ID = "c8d52f645999"
EXPECTED_SOURCE_SHA256 = "bc2b6391cb0d69decff6c03d86613709e3a4062f4daa0843f14a3af541427d25"
TEXTURES = ("default", "warm", "cool", "varied")


def sha256_json(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def crop_component(grid: list[list[int]], cells: list[tuple[int, int]]) -> list[list[int]]:
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [[grid[r][c] if (r, c) in set(cells) else 0 for c in range(c0, c1 + 1)]
            for r in range(r0, r1 + 1)]


def key_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    key = grid[0][0]
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == key and (r, c) != (0, 0)
    }
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        cells: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(cells))
    return sorted(components, key=lambda cells: cells[0])


def ambiguous_input() -> list[list[int]]:
    grid = [[0] * 9 for _ in range(8)]
    grid[0][0] = 4
    # Two disconnected key-color blobs with different crops.
    for r, c in ((2, 2), (2, 3), (3, 2)):
        grid[r][c] = 4
    for r, c in ((5, 5), (5, 6), (6, 6)):
        grid[r][c] = 4
    # A lawful different-color distractor, so the current validator has no complaint.
    for r, c in ((1, 7), (2, 7), (2, 8)):
        grid[r][c] = 6
    return grid


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--racket", type=Path)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    root = Path(os.environ.get("ARCPUZZLES_HOME", Path.cwd()))
    module, source, digest = load_selected_generator(TASK_ID, root=root)
    if digest != EXPECTED_SOURCE_SHA256:
        raise SystemExit(f"unexpected source SHA-256: {digest}")

    grid = ambiguous_input()
    components = key_components(grid)
    crops = [crop_component(grid, cells) for cells in components]
    self_check = module.self_check(grid)

    texture_trials = []
    all_texture_controls_identical = True
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(8):
            outputs = {
                texture: module.generate(seed, 0, difficulty=difficulty, texture=texture)
                for texture in TEXTURES
            }
            hashes = {texture: sha256_json(output) for texture, output in outputs.items()}
            identical = len(set(hashes.values())) == 1
            all_texture_controls_identical &= identical
            texture_trials.append({
                "difficulty": difficulty,
                "seed": seed,
                "sample_index": 0,
                "hashes": hashes,
                "all_four_equal": identical,
            })

    input_path = args.out_dir / "input.json"
    input_path.write_text(json.dumps(grid, indent=2) + "\n")

    report: dict[str, Any] = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK_ID,
        "generator_path": str(source),
        "generator_sha256": digest,
        "documented_domain": "single non-corner key-color blob plus a different-color distractor",
        "counterexample_domain_status": "outside production sampler but accepted by selected self_check",
        "input": grid,
        "input_sha256": sha256_json(grid),
        "self_check_messages": self_check,
        "validator_accepts": not self_check,
        "key_component_count_after_clearing_corner": len(components),
        "key_components": [
            {"cells": [[r, c] for r, c in cells], "crop": crop}
            for cells, crop in zip(components, crops)
        ],
        "reading_order_candidate_output": crops[0],
        "alternative_key_blob_output": crops[1],
        "outputs_differ": crops[0] != crops[1],
        "texture_override_probe": {
            "textures": list(TEXTURES),
            "trial_count": len(texture_trials),
            "seed_range": "0..7 per difficulty",
            "difficulties": ["easy", "medium", "hard"],
            "all_four_outputs_identical_in_every_trial": all_texture_controls_identical,
            "trials": texture_trials,
        },
        "reproduction": {
            "cwd": "packet_root",
            "argv": [
                "python3", "review.py", "run", "python3",
                "../checks/audit/c8d52f645999/reproduce.py",
                "--out-dir", "../checks/audit/c8d52f645999",
            ],
        },
    }
    if args.racket:
        racket = json.loads(args.racket.read_text())
        report["racket_evidence_path"] = str(args.racket)
        report["racket"] = racket
        # Apply emits a list of per-input records under results for current CLI versions.
        results = racket.get("results") or racket.get("items") or []
        if results:
            actual = results[0].get("output")
            report["actual_racket_output"] = actual
            report["actual_is_reading_order_candidate"] = actual == crops[0]
            report["actual_differs_from_alternative"] = actual != crops[1]

    out = args.out_dir / ("counterexample.json" if args.racket else "probe.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(out),
        "generator_sha256": digest,
        "validator_accepts": not self_check,
        "key_components": len(components),
        "outputs_differ": crops[0] != crops[1],
        "texture_trials": len(texture_trials),
        "all_texture_controls_identical": all_texture_controls_identical,
    }, indent=2))
    if self_check or len(components) != 2 or crops[0] == crops[1] or not all_texture_controls_identical:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
