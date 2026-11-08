#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "017f1406edaf"


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, tuple(sorted(cells))))
    return out


def paint(grid, component):
    output = [[0 for _ in row] for row in grid]
    if component is not None:
        for r, c in component[1]:
            output[r][c] = 8
    return output


def intended(grid):
    target = sum(value == 1 for value in grid[0])
    selected = next(
        (
            comp
            for comp in components(grid)
            if comp[0] != 1
            and all(r != 0 for r, _ in comp[1])
            and len(comp[1]) == target
        ),
        None,
    )
    return paint(grid, selected)


def rival_count_blue_runs(grid):
    # Plausible shortcut: treat each contiguous blue run in row 0 as one marker.
    target = 0
    previous_blue = False
    for value in grid[0]:
        blue = value == 1
        if blue and not previous_blue:
            target += 1
        previous_blue = blue
    selected = next(
        (
            comp
            for comp in components(grid)
            if comp[0] != 1
            and all(r != 0 for r, _ in comp[1])
            and len(comp[1]) == target
        ),
        None,
    )
    return paint(grid, selected)


def main() -> int:
    root = find_root(__file__)
    gen, source, digest = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_fit = [rival_count_blue_runs(pair["input"]) == pair["output"] for pair in canonical]

    witness = None
    windows_checked = 0
    for band in ("easy", "medium", "hard"):
        for seed in range(1000):
            grids = [gen.generate(seed, i, difficulty=band) for i in range(9)]
            pairs = [{"input": grid, "output": intended(grid)} for grid in grids]
            for start in range(5):
                demos = pairs[start : start + 4]
                query = pairs[start + 4]
                windows_checked += 1
                fits = all(rival_count_blue_runs(pair["input"]) == pair["output"] for pair in demos)
                changes = rival_count_blue_runs(query["input"]) != query["output"]
                if fits and changes:
                    witness = {
                        "difficulty": band,
                        "seed": seed,
                        "start_index": start,
                        "demo_indices": list(range(start, start + 4)),
                        "query_index": start + 4,
                        "input": query["input"],
                        "python_intended_output": query["output"],
                        "rival_output": rival_count_blue_runs(query["input"]),
                        "row0_blue_cells": sum(v == 1 for v in query["input"][0]),
                        "row0_blue_runs": sum(
                            v == 1 and (i == 0 or query["input"][0][i - 1] != 1)
                            for i, v in enumerate(query["input"][0])
                        ),
                        "self_check": gen.self_check(query["input"]),
                        "demo_rival_fits": [
                            rival_count_blue_runs(pair["input"]) == pair["output"] for pair in demos
                        ],
                    }
                    break
            if witness:
                break
        if witness:
            break

    payload = {
        "schema": "arcpuzzles-audit-undeclared-rival-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": digest,
        "rule_hash": gen.RULE_HASH,
        "rival": "count contiguous blue runs in row 0 instead of blue cells",
        "canonical_pairs_fit": canonical_fit,
        "canonical_fit_count": sum(canonical_fit),
        "canonical_pair_count": len(canonical_fit),
        "production_windows_checked_until_first_witness": windows_checked,
        "witness": witness,
    }
    out = Path(__file__).with_name("undeclared-rival.json")
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if witness:
        Path(__file__).with_name("input.json").write_text(json.dumps(witness["input"]) + "\n")
        Path(__file__).with_name("rival-output.json").write_text(json.dumps(witness["rival_output"]) + "\n")
    print(json.dumps({"out": str(out), "canonical_fit": canonical_fit, "windows_checked": windows_checked, "found": witness is not None}, indent=2))
    return 0 if witness is not None and all(canonical_fit) else 1


if __name__ == "__main__":
    raise SystemExit(main())
