from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, load_selected_generator

TASK_ID = "74d1cf8c8502"


def components8(grid):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 6}
    found = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    point = (r + dr, c + dc)
                    if point in remaining:
                        remaining.remove(point)
                        component.add(point)
                        queue.append(point)
        found.append(sorted(component))
    return found


def bbox(cells):
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def rival_8_connected(grid):
    out = [row[:] for row in grid]
    for cells in components8(grid):
        r1, c1, r2, c2 = bbox(cells)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if r in (r1, r2) or c in (c1, c2):
                    out[r][c] = 2
    return out


def witness():
    grid = [[0] * 12 for _ in range(10)]
    for r, c in ((2, 2), (2, 3), (3, 3), (4, 4), (4, 5), (5, 4)):
        grid[r][c] = 6
    return grid


def grid_sha(grid):
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    gen, source, source_sha = load_selected_generator(TASK_ID, root=root)
    canonical = []
    for pair in canonical_pairs(TASK_ID, root=root):
        prediction = rival_8_connected(pair["input"])
        canonical.append({
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "matches": prediction == pair["output"],
            "input_sha256": grid_sha(pair["input"]),
        })

    generated = []
    for band in ("easy", "medium", "hard"):
        matches = 0
        unique = set()
        for sample_index in range(200):
            grid = gen.generate(90210, sample_index, difficulty=band)
            unique.add(grid_sha(grid))
            matches += rival_8_connected(grid) == gen.rule_mirror(grid)
        generated.append({
            "difficulty": band,
            "seed": 90210,
            "sample_indices": [0, 199],
            "matches": matches,
            "total": 200,
            "unique_inputs": len(unique),
        })

    grid = witness()
    intended = gen.rule_mirror(grid)
    rival = rival_8_connected(grid)
    diffs = [
        {"row": r, "column": c, "intended": intended[r][c], "rival": rival[r][c]}
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if intended[r][c] != rival[r][c]
    ]
    report = {
        "schema": "74d1cf8c8502-connectivity-audit-v2",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "rival": "Merge diagonal contacts into 8-connected magenta objects, then outline each merged bounding box.",
        "canonical_fit": {
            "matches": sum(row["matches"] for row in canonical),
            "total": len(canonical),
            "records": canonical,
        },
        "generated_fit": generated,
        "witness": {
            "input": grid,
            "input_sha256": grid_sha(grid),
            "self_check_errors": gen.self_check(grid),
            "intended_python": intended,
            "rival_output": rival,
            "four_connected_components": len(gen._six_components(grid)),
            "eight_connected_components": len(components8(grid)),
            "differing_cells": diffs,
        },
        "limits": [
            "The witness is lawful for the canonical Racket rule but outside the generator validator because the boxes lack its extra moat restriction.",
            "Generated-fit coverage is 200 indices per band at one seed, not exhaustive over all seeds.",
        ],
    }
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (out.parent / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    (out.parent / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")
    print(json.dumps({
        "generator_sha256": source_sha,
        "canonical_fit": f"{report['canonical_fit']['matches']}/{report['canonical_fit']['total']}",
        "generated_fit": {row['difficulty']: f"{row['matches']}/{row['total']}" for row in generated},
        "self_check_errors": report["witness"]["self_check_errors"],
        "four_components": report["witness"]["four_connected_components"],
        "eight_components": report["witness"]["eight_connected_components"],
        "differing_cells": len(diffs),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
