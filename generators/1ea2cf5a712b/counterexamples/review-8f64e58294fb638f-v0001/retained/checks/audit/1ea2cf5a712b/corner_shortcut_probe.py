#!/usr/bin/env python3
"""Show that generated matches are confined to four corner windows."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

PACKET = Path(__file__).resolve().parents[3]
REPO = PACKET / "repo"
TASK = "1ea2cf5a712b"
SOURCE = REPO / "generators" / TASK / "generator.py"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
spec = importlib.util.spec_from_file_location("audit_corner_generator", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load generator")
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)


def corner_only(grid: list[list[int]]) -> list[list[int]]:
    analysis = GEN._analyse(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    board = analysis["board"]
    template = analysis["template"]
    records: list[tuple[int, int, int, int, int]] = []
    anchors = GEN._corner_anchors(len(board), len(board[0]))
    for variant_index, variant in enumerate(GEN._rotation_variants(template)):
        height, width = len(variant), len(variant[0])
        for row, col in anchors:
            if GEN._match_at(board, variant, row, col):
                records.append((row, col, height, width, variant_index))
    return GEN._render_centers(
        analysis["height"], analysis["board_width"], GEN._record_centers(records)
    )


def centers(grid: list[list[int]]) -> list[list[int]]:
    return [[r, c] for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]


bands: dict[str, Any] = {}
representative = None
for band_index, band in enumerate(("easy", "medium", "hard")):
    total = 100
    agreements = 0
    valid = 0
    unique: set[tuple[tuple[int, ...], ...]] = set()
    noncorner_official = 0
    for offset in range(total):
        seed = 640_000 + band_index * 10_000 + offset
        sample_index = 2_000 + offset
        grid = GEN.generate(seed, sample_index, difficulty=band)
        errors = GEN.self_check(grid)
        valid += int(not errors)
        truth = GEN.rule_mirror(grid)
        rival = corner_only(grid)
        agreements += int(truth == rival)
        unique.add(tuple(tuple(row) for row in grid))
        allowed = {
            (1, 1),
            (1, len(truth[0]) - 2),
            (len(truth) - 2, 1),
            (len(truth) - 2, len(truth[0]) - 2),
        }
        noncorner_official += sum(
            value == 8 and (r, c) not in allowed
            for r, row in enumerate(truth)
            for c, value in enumerate(row)
        )
        if representative is None:
            representative = {
                "seed": seed,
                "sample_index": sample_index,
                "difficulty": band,
                "input": grid,
                "official_output": truth,
                "corner_only_output": rival,
                "official_centers": centers(truth),
            }
    bands[band] = {
        "sampler": {
            "seed_start": 640_000 + band_index * 10_000,
            "seed_stop_exclusive": 640_000 + band_index * 10_000 + total,
            "sample_index_start": 2_000,
            "sample_index_stop_exclusive": 2_000 + total,
        },
        "samples": total,
        "self_check_passes": valid,
        "unique_inputs": len(unique),
        "corner_only_agreements": agreements,
        "official_noncorner_mark_count": noncorner_official,
    }

canonical_row = None
for line in (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").open():
    row = json.loads(line)
    if row.get("task_id") == TASK:
        canonical_row = row
        break
if canonical_row is None:
    raise RuntimeError("canonical row not found")
canonical = []
for index, pair in enumerate(canonical_row["train"]):
    rival = corner_only(pair["input"])
    canonical.append(
        {
            "split": "train",
            "index": index,
            "self_check_errors": GEN.self_check(pair["input"]),
            "official_centers": centers(pair["output"]),
            "corner_only_centers": centers(rival),
            "agrees": rival == pair["output"],
            "input": pair["input"],
            "official_output": pair["output"],
            "corner_only_output": rival,
        }
    )

report = {
    "schema": "arc-audit-corner-only-shortcut-v1",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "generator_version": GEN.VERSION,
    "rule_hash": GEN.RULE_HASH,
    "hypothesis": "Search only the four 3x3 corner windows instead of sliding over the board.",
    "bands": bands,
    "canonical_train": canonical,
    "representative_generated": representative,
}
print(json.dumps(report, indent=2, sort_keys=True))
