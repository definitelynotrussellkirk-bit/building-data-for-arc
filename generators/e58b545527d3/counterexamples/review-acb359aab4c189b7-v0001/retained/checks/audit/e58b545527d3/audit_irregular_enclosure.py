#!/usr/bin/env python3
"""Source-bound audit for rectangular-frame teaching support in e58b545527d3."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator, normalize_grid

TASK_ID = "e58b545527d3"


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def rectangular_frame_only(grid):
    """Plausible shortcut: fill interiors of axis-aligned color-8 frames.

    Frames are detected independently rather than as connected color-8
    components, because distinct valid frames can touch and therefore merge
    into one connected component in the canonical examples.
    """
    out = copy.deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for r0 in range(h - 2):
        for r1 in range(r0 + 2, h):
            for c0 in range(w - 2):
                for c1 in range(c0 + 2, w):
                    border = (
                        [(r0, c) for c in range(c0, c1 + 1)]
                        + [(r1, c) for c in range(c0, c1 + 1)]
                        + [(r, c0) for r in range(r0 + 1, r1)]
                        + [(r, c1) for r in range(r0 + 1, r1)]
                    )
                    if any(grid[r][c] != 8 for r, c in border):
                        continue
                    seeds = {
                        grid[r][c]
                        for r in range(r0 + 1, r1)
                        for c in range(c0 + 1, c1)
                        if grid[r][c] not in (0, 8)
                    }
                    if len(seeds) != 1:
                        continue
                    color = next(iter(seeds))
                    for r in range(r0 + 1, r1):
                        for c in range(c0 + 1, c1):
                            if out[r][c] == 0:
                                out[r][c] = color
    return out


def irregular_witness():
    grid = [[0] * 9 for _ in range(8)]
    boundary = set()
    boundary.update((1, c) for c in range(2, 7))
    boundary.update((r, 6) for r in range(1, 7))
    boundary.update((6, c) for c in range(2, 7))
    boundary.update({(5, 2), (5, 1), (4, 1), (3, 1), (2, 1), (2, 2)})
    for r, c in boundary:
        grid[r][c] = 8
    grid[3][3] = 4
    return grid


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    root = find_root(__file__)
    generator, source, generator_sha = load_selected_generator(TASK_ID, root=root)
    catalog = Catalog(root)

    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_checks = [
        {
            "index": index,
            "matches": rectangular_frame_only(pair["input"]) == pair["output"],
            "input": pair["input"],
            "expected": pair["output"],
            "rival_output": rectangular_frame_only(pair["input"]),
        }
        for index, pair in enumerate(canonical)
    ]
    if not canonical_checks or not all(row["matches"] for row in canonical_checks):
        raise AssertionError("rectangular-frame rival does not fit all canonical labels")

    generated = []
    grids = []
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            grid = normalize_grid(generator.generate(seed, 0, difficulty=band))
            grids.append(grid)
            generated.append({"difficulty": band, "seed": seed, "sample_index": 0})
    applied = catalog.apply(TASK_ID, grids, timeout=180)
    for row, receipt, grid in zip(generated, applied["results"], grids, strict=True):
        row["reference_output"] = receipt["output"]
        row["rival_output"] = rectangular_frame_only(grid)
        row["matches"] = row["rival_output"] == row["reference_output"]
    if not all(row["matches"] for row in generated):
        raise AssertionError("finite generated sample refuted the rectangular-frame rival")

    witness = irregular_witness()
    witness_apply = catalog.apply(TASK_ID, [witness], timeout=180)
    authoritative = witness_apply["results"][0]["output"]
    rival_output = rectangular_frame_only(witness)
    if authoritative == rival_output:
        raise AssertionError("irregular witness did not distinguish the executable rule")

    report = {
        "schema": "arcpuzzles-adversarial-audit-v1",
        "task_id": TASK_ID,
        "finding": "canonical-and-generator-supported rectangular-frame shortcut misses the executable rule's irregular enclosed regions",
        "classification": "teaching_support_gap_outside_documented_rectangular_generator_domain",
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": generator_sha,
        "generator_version": generator.VERSION,
        "command": [sys.executable, *sys.argv],
        "cwd": str(Path.cwd()),
        "canonical_pairs_checked": len(canonical_checks),
        "canonical_rival_matches": sum(row["matches"] for row in canonical_checks),
        "generated_scope": {
            "bands": ["easy", "medium", "hard"],
            "seeds": [0, 19],
            "sample_index": 0,
            "count": len(generated),
            "rival_matches": sum(row["matches"] for row in generated),
        },
        "reference_identity": {
            key: applied.get(key)
            for key in ("generator_sha256", "executed_rule_hash", "rule_text_sha256", "rule_hash_matches_catalog")
        },
        "witness": {
            "domain": "executable rule domain; outside the documented rectangular-frame generator distribution",
            "input": witness,
            "authoritative_output": authoritative,
            "rival_output": rival_output,
            "different": authoritative != rival_output,
            "reference_execution": witness_apply,
        },
        "canonical_checks": canonical_checks,
        "generated_checks": generated,
        "limitations": [
            "The witness is not claimed to belong to the current documented rectangular-frame generator domain.",
            "The finite generated check covers 60 inputs, not every seed/sample index.",
            "The finding is a semantic teaching/support gap, not a bad canonical label claim.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "out": str(args.out), "canonical": len(canonical_checks),
        "generated": len(generated), "witness_differs": True,
        "generator_sha256": generator_sha,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
