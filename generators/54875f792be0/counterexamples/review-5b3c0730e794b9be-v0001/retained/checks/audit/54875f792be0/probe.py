#!/usr/bin/env python3
"""Bounded findings-only probe; labels come only from public Catalog execution."""
from __future__ import annotations
from collections import deque
import hashlib
import json
from pathlib import Path
from arcpuzzles import Catalog

OUT = Path(__file__).resolve().parent
TASK = "54875f792be0"


def components(grid):
    seen = set()
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0 or (r, c) in seen:
                continue
            cells = {(r, c)}
            seen.add((r, c))
            todo = [(r, c)]
            while todo:
                rr, cc = todo.pop()
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if (0 <= nr < len(grid) and 0 <= nc < len(row)
                            and grid[nr][nc] == color and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        cells.add((nr, nc))
                        todo.append((nr, nc))
            yield color, cells


def area_rival(grid):
    """Retain non-solid components of size >=8, ignoring exact borders."""
    output = [[0] * len(grid[0]) for _ in grid]
    for color, cells in components(grid):
        height = max(r for r, _ in cells) - min(r for r, _ in cells) + 1
        width = max(c for _, c in cells) - min(c for _, c in cells) + 1
        if 8 <= len(cells) < height * width:
            for r, c in cells:
                output[r][c] = color
    return output


def hole_rival(grid):
    """Retain components enclosing any 4-connected hole, ignoring shape."""
    output = [[0] * len(grid[0]) for _ in grid]
    for color, cells in components(grid):
        r1, r2 = min(r for r, _ in cells)-1, max(r for r, _ in cells)+1
        c1, c2 = min(c for _, c in cells)-1, max(c for _, c in cells)+1
        outside = {(r1, c1)}
        todo = deque(outside)
        while todo:
            r, c = todo.popleft()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if (r1 <= p[0] <= r2 and c1 <= p[1] <= c2
                        and p not in cells and p not in outside):
                    outside.add(p)
                    todo.append(p)
        if any((r,c) not in cells and (r,c) not in outside
               for r in range(r1,r2+1) for c in range(c1,c2+1)):
            for r, c in cells:
                output[r][c] = color
    return output


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def main():
    catalog = Catalog()
    row = catalog.get(TASK)
    source = catalog.root / row["generator"]
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    variants = row["variants"]
    canonical = [pair for variant in variants for split in ("train", "test")
                 for pair in variant[split]]
    save("canonical_pairs.json", canonical)
    witnesses = {
        "missing_corner_3x4": [[0,2,2,2],[2,0,0,2],[2,2,2,2]],
        "nonrectangular_enclosed_ring_3x4": [[0,2,2,2],[2,2,0,2],[2,2,2,2]],
        "complete_frame_3x4_control": [[2,2,2,2],[2,0,0,2],[2,2,2,2]],
    }
    applied = catalog.apply(TASK, list(witnesses.values()), timeout=60)
    save("reference_witnesses.json", applied)
    measured = []
    for (name, grid), result in zip(witnesses.items(), applied["results"], strict=True):
        measured.append({"name": name, "input": grid, "reference_output": result["output"],
                         "area_rival_output": area_rival(grid),
                         "hole_rival_output": hole_rival(grid),
                         "area_rival_matches": area_rival(grid) == result["output"],
                         "hole_rival_matches": hole_rival(grid) == result["output"]})
    episodes = []
    fit = []
    for difficulty in ("easy", "medium", "hard"):
        generated = catalog.generate(TASK, seed=54875, count=1, difficulty=difficulty,
                                     n_train=3, n_test=1, allow_unapproved=True, timeout=60)
        episodes.extend(generated)
        episode = generated[0]
        pairs = episode.get("train", []) + episode.get("test", [])
        fit.append({"difficulty": difficulty, "seed": 54875, "pairs": len(pairs),
                    "area_rival_matches": sum(area_rival(p["input"]) == p["output"] for p in pairs),
                    "hole_rival_matches": sum(hole_rival(p["input"]) == p["output"] for p in pairs)})
    save("generated_episodes.json", episodes)
    after = hashlib.sha256(source.read_bytes()).hexdigest()
    summary = {"task_id": TASK, "generator_sha256": before,
               "source_unchanged": before == after, "rule_hash": row["rule_hash"],
               "rule_text_sha256": applied["rule_text_sha256"],
               "executed_rule_hash": applied["executed_rule_hash"],
               "canonical_pairs": len(canonical),
               "canonical_area_rival_matches": sum(area_rival(p["input"]) == p["output"] for p in canonical),
               "canonical_hole_rival_matches": sum(hole_rival(p["input"]) == p["output"] for p in canonical),
               "generated_fit": fit, "witnesses": measured,
               "scope": "3 hand-made actual canonical Racket checks and 3 episodes (12 pairs); no battery."}
    save("summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
