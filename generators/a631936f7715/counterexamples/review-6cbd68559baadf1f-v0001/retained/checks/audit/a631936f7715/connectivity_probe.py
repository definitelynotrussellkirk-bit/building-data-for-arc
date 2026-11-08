#!/usr/bin/env python3
"""Audit a631936f7715's 4-connected rule against an 8-connected rival."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

PACKET_ROOT = Path(__file__).resolve().parents[3]
REPO = PACKET_ROOT / "repo"
TASK = "a631936f7715"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
BG, SRC = 7, 6
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIR8 = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0))


def components(grid, dirs):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != SRC or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            comp = []
            while stack:
                cr, cc = stack.pop()
                comp.append((cr, cc))
                for dr, dc in dirs:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == SRC and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(sorted(comp))
    return out


def solve(grid, dirs):
    h, w = len(grid), len(grid[0])
    out = [[BG for _ in range(w)] for _ in range(h)]
    for comp in components(grid, dirs):
        labels = sorted({
            grid[r + dr][c + dc]
            for r, c in comp
            for dr, dc in DIR4
            if 0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] not in (BG, SRC)
        })
        color = labels[0] if labels else SRC
        for r, c in comp:
            out[r][c] = color
    return out


def diagonal_pair_exists(grid):
    comps = components(grid, DIR4)
    owner = {cell: i for i, comp in enumerate(comps) for cell in comp}
    for (r, c), i in owner.items():
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            j = owner.get((r + dr, c + dc))
            if j is not None and j != i:
                return True
    return False


def load_generator():
    path = REPO / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod, path


def load_canonical_rows():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    rows = []
    with path.open() as f:
        for line in f:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rows.append(row)
    return rows


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    mod, gen_path = load_generator()
    rows = load_canonical_rows()
    pairs = []
    for row_index, row in enumerate(rows):
        for split in ("train", "test"):
            for pair_index, pair in enumerate(row.get(split, [])):
                pred = solve(pair["input"], DIR8)
                pairs.append({
                    "row_index": row_index,
                    "source": row.get("source"),
                    "split": split,
                    "pair_index": pair_index,
                    "input_sha256": digest(pair["input"]),
                    "eight_connected_matches_expected": pred == pair["output"],
                })

    crafted = [
        [7, 1, 7, 7, 7],
        [7, 6, 6, 7, 7],
        [7, 7, 7, 6, 2],
        [7, 7, 7, 6, 7],
        [7, 7, 7, 7, 7],
    ]
    crafted_4 = solve(crafted, DIR4)
    crafted_8 = solve(crafted, DIR8)

    diagonal_count = 0
    divergent_count = 0
    first = None
    for seed in range(600):
        grid = mod.generate(seed, 0, difficulty="easy")
        diag = diagonal_pair_exists(grid)
        out4 = solve(grid, DIR4)
        out8 = solve(grid, DIR8)
        if diag:
            diagonal_count += 1
        if out4 != out8:
            divergent_count += 1
            if first is None:
                first = {
                    "seed": seed,
                    "input": grid,
                    "self_check": mod.self_check(grid, difficulty="easy"),
                    "intended_4_connected_output": out4,
                    "rival_8_connected_output": out8,
                    "diagonal_pair_exists": diag,
                }

    result = {
        "schema": "a631936f7715-connectivity-audit-v1",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(gen_path.read_bytes()).hexdigest(),
        "canonical_rows": len(rows),
        "canonical_stored_pairs": len(pairs),
        "canonical_unique_inputs": len({p["input_sha256"] for p in pairs}),
        "eight_connected_rival_matches_all_canonical_pairs": all(p["eight_connected_matches_expected"] for p in pairs),
        "canonical_pair_results": pairs,
        "crafted_counterexample": {
            "input": crafted,
            "intended_4_connected_output": crafted_4,
            "rival_8_connected_output": crafted_8,
            "outputs_differ": crafted_4 != crafted_8,
            "self_check": mod.self_check(crafted, difficulty="easy"),
        },
        "easy_seed_probe": {
            "seeds": [0, 599],
            "sample_index": 0,
            "draws": 600,
            "diagonal_touching_distinct_4_components": diagonal_count,
            "rival_output_divergences": divergent_count,
            "first_divergence": first,
        },
    }
    out = Path(__file__).with_name("connectivity_probe.json")
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "canonical_pairs": len(pairs),
        "rival_matches_all": result["eight_connected_rival_matches_all_canonical_pairs"],
        "diagonal_count": diagonal_count,
        "divergent_count": divergent_count,
        "first_seed": None if first is None else first["seed"],
        "output": str(out),
    }, indent=2))


if __name__ == "__main__":
    main()
