#!/usr/bin/env python3
"""Audit marker-location support for generator 819d58220317."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, load_selected_generator

TASK = "819d58220317"


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def components(grid, color):
    h, w = len(grid), len(grid[0])
    left = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result = []
    while left:
        start = min(left); left.remove(start); todo = [start]; comp = {start}
        while todo:
            r, c = todo.pop()
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                p = (r+dr, c+dc)
                if p in left:
                    left.remove(p); comp.add(p); todo.append(p)
        result.append(comp)
    return result


def bounds(comp):
    rows = [r for r, _ in comp]; cols = [c for _, c in comp]
    return min(rows), min(cols), max(rows), max(cols)


def frames(grid):
    boxes = [bounds(comp) for comp in components(grid, 4)]
    boxes.sort(key=lambda b: (-((b[2]-b[0]+1)*(b[3]-b[1]+1)), b))
    return boxes


def apply_rank(grid, rank):
    out = copy.deepcopy(grid)
    boxes = frames(grid)
    if not 1 <= rank <= len(boxes):
        return out
    r0, c0, r1, c1 = boxes[rank-1]
    inner = boxes[rank] if rank < len(boxes) else None
    for r in range(r0+1, r1):
        for c in range(c0+1, c1):
            if inner is not None:
                ir0, ic0, ir1, ic1 = inner
                if ir0 <= r <= ir1 and ic0 <= c <= ic1:
                    continue
            if out[r][c] == 0:
                out[r][c] = 8
    return out


def intended(grid):
    return apply_rank(grid, sum(v == 2 for row in grid for v in row))


def border_only_rival(grid):
    h, w = len(grid), len(grid[0])
    rank = sum(
        grid[r][c] == 2
        for r in range(h)
        for c in range(w)
        if r in (0, h-1) or c in (0, w-1)
    )
    return apply_rank(grid, rank)


def differences(a, b):
    return [[r, c, a[r][c], b[r][c]] for r in range(len(a)) for c in range(len(a[0])) if a[r][c] != b[r][c]]


def all_red_on_border(grid):
    h, w = len(grid), len(grid[0])
    red = [(r, c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 2]
    return bool(red) and all(r in (0,h-1) or c in (0,w-1) for r,c in red)


def move_one_marker_off_border(grid, outer):
    h, w = len(grid), len(grid[0])
    r0, c0, r1, c1 = outer
    red = [(r, c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 2]
    candidates = [
        (r, c)
        for r in range(1, h-1)
        for c in range(1, w-1)
        if grid[r][c] == 0 and not (r0 <= r <= r1 and c0 <= c <= c1)
    ]
    if len(red) < 2 or not candidates:
        return None
    witness = copy.deepcopy(grid)
    old = red[0]; new = candidates[0]
    witness[old[0]][old[1]] = 0
    witness[new[0]][new[1]] = 2
    return witness, old, new


def run(root: Path, per_band: int) -> tuple[dict, dict]:
    gen, source, source_sha = load_selected_generator(TASK, root=root)
    pairs = canonical_pairs(TASK, root=root, labeled_only=True)
    canonical_rows = []
    for pair in pairs:
        grid = pair["input"]
        canonical_rows.append({
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "all_red_on_border": all_red_on_border(grid),
            "rival_matches": border_only_rival(grid) == pair["output"],
        })

    generated = []
    witness_record = None
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(per_band):
            seed = 8190000 + band_index * 100000 + index
            grid = gen.generate(seed, index, difficulty=band)
            truth = gen.rule_mirror(grid)
            generated.append({
                "band": band,
                "seed": seed,
                "sample_index": index,
                "all_red_on_border": all_red_on_border(grid),
                "rival_matches": border_only_rival(grid) == truth,
            })

    for seed in range(1000):
        grid = gen.generate(
            seed,
            0,
            difficulty="hard",
            grid_h=30,
            grid_w=30,
            n_frames=3,
            rank=2,
            marker_layout="single_side",
        )
        profile = gen.semantic_profile(grid)
        moved = move_one_marker_off_border(grid, profile["outer_bounds"])
        if moved is None:
            continue
        witness, old, new = moved
        findings = gen.self_check(witness)
        if findings:
            continue
        truth = gen.rule_mirror(witness)
        rival = border_only_rival(witness)
        if truth != rival:
            witness_record = {
                "generation": {
                    "seed": seed,
                    "sample_index": 0,
                    "difficulty": "hard",
                    "overrides": {
                        "grid_h": 30,
                        "grid_w": 30,
                        "n_frames": 3,
                        "rank": 2,
                        "marker_layout": "single_side",
                    },
                },
                "mutation": {"moved_border_marker_from": list(old), "to_off_border_outside_frame": list(new)},
                "validator_errors": findings,
                "input": witness,
                "intended_output": truth,
                "border_only_rival_output": rival,
                "differing_cells": differences(truth, rival),
                "input_sha256": digest(witness),
                "intended_sha256": digest(truth),
                "rival_sha256": digest(rival),
            }
            break
    if witness_record is None:
        raise RuntimeError("failed to construct an off-border lawful witness")

    report = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK,
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": source_sha,
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "canonical": {
            "pairs": len(pairs),
            "all_red_on_border": sum(row["all_red_on_border"] for row in canonical_rows),
            "border_only_rival_matches": sum(row["rival_matches"] for row in canonical_rows),
            "rows": canonical_rows,
        },
        "generated": {
            "draws": len(generated),
            "all_red_on_border": sum(row["all_red_on_border"] for row in generated),
            "border_only_rival_matches": sum(row["rival_matches"] for row in generated),
            "per_band": per_band,
        },
        "witness": witness_record,
        "conclusion": (
            "All canonical and sampled generated markers lie on the grid perimeter, so a solver can count only border red cells. "
            "The selected rule counts red cells anywhere, and self_check accepts off-perimeter markers outside the outer frame; the retained witness separates the rules."
        ),
    }
    return report, {"inputs": [witness_record["input"]]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--per-band", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    args = parser.parse_args()
    report, inputs = run(args.root.resolve(), args.per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.inputs.write_text(json.dumps(inputs, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "generator_sha256": report["generator_sha256"],
        "canonical": report["canonical"],
        "generated": report["generated"],
        "witness_differences": len(report["witness"]["differing_cells"]),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
