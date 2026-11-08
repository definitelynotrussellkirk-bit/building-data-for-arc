#!/usr/bin/env python3
"""Reproduce the generic_extraction_gen3 audit on the pinned packet source."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PACKET_ROOT = Path(__file__).resolve().parents[3]
RUNTIME = PACKET_ROOT / "repo/shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
SOURCE = PACKET_ROOT / "repo/generators/generic_extraction_gen3/generator.py"
OUT = Path(__file__).with_name("reproduced.json")
EXPECTED_SHA256 = "87a544108eb4521319ec3d1f909ae6029bae02071d5d0477d7f9ff22e95e7664"


def load_module():
    spec = importlib.util.spec_from_file_location("generic_extraction_gen3_audit", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bbox_of_signal(grid: list[list[int]], noise: int) -> tuple[int, int, int, int]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value not in (0, noise)]
    if not cells:
        raise ValueError("no signal")
    return min(r for r, _ in cells), max(r for r, _ in cells), min(c for _, c in cells), max(c for _, c in cells)


def corner_rect(grid: list[list[int]], ca: int, cb: int) -> tuple[int, int, int, int]:
    h, w = len(grid), len(grid[0])
    candidates: list[tuple[int, int, int, int, int]] = []
    for r0 in range(h - 1):
        for r1 in range(r0 + 1, h):
            for c0 in range(w - 1):
                if grid[r0][c0] != ca or grid[r1][c0] != cb:
                    continue
                for c1 in range(c0 + 1, w):
                    if grid[r0][c1] == cb and grid[r1][c1] == ca:
                        candidates.append(((r1 - r0 + 1) * (c1 - c0 + 1), r0, r1, c0, c1))
    if not candidates:
        raise ValueError("no A,B/B,A corner rectangle")
    _, r0, r1, c0, c1 = max(candidates)
    return r0, r1, c0, c1


def rival(grid: list[list[int]], noise: int, mapping: dict[int, int], ca: int, cb: int) -> list[list[int]]:
    r0, r1, c0, c1 = corner_rect(grid, ca, cb)
    return [
        [0 if value == noise else mapping.get(value, value) for value in row[c0 : c1 + 1]]
        for row in grid[r0 : r1 + 1]
    ]


def main() -> int:
    sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if sha != EXPECTED_SHA256:
        raise RuntimeError(f"source hash mismatch: {sha}")
    gen = load_module()
    totals = Counter()
    first: dict[str, Any] | None = None
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(100):
            task = gen.generate_task(seed, difficulty=difficulty)
            noise = int(task["meta"]["noise"])
            mapping = {int(k): int(v) for k, v in task["meta"]["mapping"].items()}
            ca, cb = tuple(mapping)
            totals["tasks"] += 1
            for pair_index, pair in enumerate(task["train"] + task["test"]):
                grid = pair["input"]
                output = pair["output"]
                totals["pairs"] += 1
                r0, r1, c0, c1 = bbox_of_signal(grid, noise)
                if (grid[r0][c0], grid[r0][c1], grid[r1][c0], grid[r1][c1]) == (ca, cb, cb, ca):
                    totals["fixed_corner_pairs"] += 1
                counts = Counter(value for row in grid for value in row if value != 0)
                if counts[noise] == max(counts.values()):
                    totals["noise_most_frequent_pairs"] += 1
                prediction = rival(grid, noise, mapping, ca, cb)
                if prediction == output:
                    totals["rival_matches_pairs"] += 1
                if first is None and difficulty == "easy" and seed == 0 and pair_index == 0:
                    modified = [row[:] for row in grid]
                    modified[0][0] = ca
                    intended = gen._apply(modified, noise, mapping)
                    rival_output = rival(modified, noise, mapping, ca, cb)
                    program = task["program"]
                    first = {
                        "difficulty": difficulty,
                        "seed": seed,
                        "pair_index": pair_index,
                        "noise": noise,
                        "mapping": mapping,
                        "program": program,
                        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                        "added_signal_cell": [0, 0],
                        "input": modified,
                        "intended_output": intended,
                        "rival_output": rival_output,
                        "outputs_differ": intended != rival_output,
                        "input_sha256": hashlib.sha256(json.dumps(modified, separators=(",", ":")).encode()).hexdigest(),
                        "intended_output_sha256": hashlib.sha256(json.dumps(intended, separators=(",", ":")).encode()).hexdigest(),
                        "rival_output_sha256": hashlib.sha256(json.dumps(rival_output, separators=(",", ":")).encode()).hexdigest(),
                        "validator_status": "not_applicable: target exposes no self_check",
                        "generator_domain": "outside sampler: a signal color was added beyond the forced-corner rectangle",
                    }
    report = {
        "schema": "arc-audit-reproducer-v1",
        "target": "generic_extraction_gen3",
        "source_sha256": sha,
        "seed_range": {"per_band": "0..99", "bands": ["easy", "medium", "hard"]},
        "probe": dict(totals),
        "rival": "Select the largest A,B/B,A corner rectangle, erase the most-frequent noise color inside it, recolor A/B, and ignore same-colored signal outside it.",
        "classification": "suspected teaching shortcut / domain restriction",
        "counterexample": first,
        "supported_apply": {
            "status": "unsupported",
            "reason": "arcpuzzles apply requires a per-puzzle generator with a resolvable canonical rule",
            "evidence": "checks/audit/generic_extraction_gen3/apply.log",
        },
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    expected = 1494
    ok = (
        totals["tasks"] == 300
        and totals["pairs"] == expected
        and totals["fixed_corner_pairs"] == expected
        and totals["noise_most_frequent_pairs"] == expected
        and totals["rival_matches_pairs"] == expected
        and first is not None
        and first["outputs_differ"]
    )
    print(json.dumps({"status": "pass" if ok else "fail", **report["probe"]}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
