#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import time

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, load_selected_generator

TASK_ID = "27816160ddbd"
EXPECTED_SOURCE_SHA256 = "08e05a37107269892c399c0a12b8a05900b99d8c1630e166f3ac19b2e4b9a236"
TICKET_SEED = "e6b40ddbcf6af40f052a8ed962910f0d4cca04347a167e95592fb430f6ff1aa2"
PINNED_RULE_HASH = "3c2338ad4787"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(grid: list[list[int]]) -> list[dict]:
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    out = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        color = grid[start[0]][start[1]]
        cells = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in unseen and grid[nxt[0]][nxt[1]] == color:
                    unseen.remove(nxt)
                    cells.add(nxt)
                    queue.append(nxt)
        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        max_c = max(c for _, c in cells)
        profile = [sum(r == row for r, _ in cells) for row in range(min_r, max_r + 1)]
        out.append(
            {
                "color": color,
                "cells": sorted([list(cell) for cell in cells]),
                "size": len(cells),
                "bbox": [min_r, min_c, max_r, max_c],
                "row_profile": profile,
                "first_cell": list(min(cells)),
            }
        )
    return sorted(out, key=lambda item: tuple(item["first_cell"]))


def histogram(component: dict) -> list[list[int]]:
    profile = component["row_profile"]
    width = max(profile)
    return [[8] * count + [0] * (width - count) for count in profile]


def grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def canonical_record(root: Path) -> dict:
    found = []
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            found.append(row)
    if len(found) != 1:
        raise RuntimeError(f"expected one canonical record, found {len(found)}")
    return found[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    root = Path.cwd()
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    source_path = Path(source_path)
    assert source_sha256 == EXPECTED_SOURCE_SHA256
    assert sha256_file(source_path) == EXPECTED_SOURCE_SHA256

    record = canonical_record(root)
    program = record["program_solution"]
    callable_text = wrap_rule(program)
    seed = int(TICKET_SEED[:16], 16)
    witness = None

    with RacketBridge(max_calls_before_restart=64) as bridge:
        for difficulty in ("easy", "medium", "hard"):
            for sample_index in range(32):
                try:
                    grid = generator.generate(seed, sample_index, difficulty=difficulty)
                except ValueError:
                    continue
                comps = components(grid)
                if len(comps) < 2:
                    continue
                sizes = sorted((item["size"] for item in comps), reverse=True)
                if len(sizes) < 2 or sizes[0] == sizes[1]:
                    continue
                largest = max(comps, key=lambda item: item["size"])
                first = comps[0]
                if first["cells"] == largest["cells"]:
                    continue
                largest_output = histogram(largest)
                first_output = histogram(first)
                if largest_output == first_output:
                    continue
                canonical_output = bridge.eval_text(
                    f"({callable_text} {grid_literal(grid)})"
                )
                if canonical_output != largest_output:
                    continue
                witness = {
                    "seed": seed,
                    "ticket_seed": TICKET_SEED,
                    "sample_index": sample_index,
                    "difficulty": difficulty,
                    "input": grid,
                    "components": comps,
                    "largest_component_index": comps.index(largest),
                    "row_major_first_component_index": 0,
                    "canonical_output": canonical_output,
                    "row_major_first_rival_output": first_output,
                    "outputs_differ": canonical_output != first_output,
                }
                runtime_identity = bridge.runtime_identity
                break
            if witness is not None:
                break

    if witness is None:
        raise RuntimeError("bounded search found no lawful first-object shortcut witness")

    elapsed_seconds = time.monotonic() - started
    report = {
        "schema": "arcpuzzles-adversarial-witness-v1",
        "ticket_id": "ticket-3dc05bff0b827357",
        "type": "adversarial_witness",
        "status": "completed",
        "task_id": TASK_ID,
        "source": {
            "path": str(source_path.relative_to(root)),
            "sha256": source_sha256,
        },
        "rule": {
            "pinned_hash": PINNED_RULE_HASH,
            "program_sha256": hashlib.sha256(program.encode("utf-8")).hexdigest(),
            "runtime": runtime_identity,
        },
        "shortcut": "emit the fixed-color-8 row-profile histogram of the row-major first nonzero component instead of the unique largest component",
        "lawful_witness": witness,
        "conclusion": "The lawful generated witness rejects the first-object shortcut: canonical Racket matches the unique largest component and differs from the row-major-first rival.",
        "elapsed_seconds": elapsed_seconds,
        "limits": [
            "one pinned-seed bounded search; not a full peer battery or census",
            "does not assess the generator's already-recorded contract/prose defects",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "sample_index": witness["sample_index"],
        "difficulty": witness["difficulty"],
        "outputs_differ": witness["outputs_differ"],
        "elapsed_seconds": elapsed_seconds,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
