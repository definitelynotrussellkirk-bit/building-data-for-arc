#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import canonical_pairs, load_selected_generator  # noqa: E402

TASK = "b3c48865ed63"
OUT = HERE.parent
GEN, SOURCE, DIGEST = load_selected_generator(TASK, root=REPO)
Grid = list[list[int]]


def components(grid: Grid, color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = [start]
        comp: list[tuple[int, int]] = []
        while queue:
            r, c = queue.pop()
            comp.append((r, c))
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    queue.append((nr, nc))
        result.append(comp)
    return result


def prepare(grid: Grid) -> tuple[Grid, int, list[list[tuple[int, int]]]]:
    out = [row[:] for row in grid]
    target = out[0][0]
    out[0][0] = 0
    return out, target, components(out, target) if target else []


def topological_rule(grid: Grid) -> Grid:
    out, target, comps = prepare(grid)
    for comp in comps:
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        solid = set(comp)
        exterior: set[tuple[int, int]] = set()
        q: deque[tuple[int, int]] = deque()
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if (r in (r0, r1) or c in (c0, c1)) and (r, c) not in solid:
                    exterior.add((r, c)); q.append((r, c))
        while q:
            r, c = q.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if r0 <= nr <= r1 and c0 <= nc <= c1 and (nr, nc) not in solid and (nr, nc) not in exterior:
                    exterior.add((nr, nc)); q.append((nr, nc))
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if (r, c) not in solid and (r, c) not in exterior:
                    out[r][c] = target
    return out


def bbox_fill_rival(grid: Grid) -> Grid:
    out, target, comps = prepare(grid)
    for comp in comps:
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        for r in range(min(rs), max(rs) + 1):
            for c in range(min(cs), max(cs) + 1):
                if out[r][c] == 0:
                    out[r][c] = target
    return out


def witness() -> Grid:
    g = [[0 for _ in range(16)] for _ in range(14)]
    target = 4
    g[0][0] = target
    # A 5x5 target ring with a three-cell arm. The ring has a true hole,
    # while the enlarged component bounding box also contains exterior-connected space.
    for r in range(3, 8):
        for c in range(3, 8):
            if r in (3, 7) or c in (3, 7):
                g[r][c] = target
    for c in range(8, 11):
        g[3][c] = target
    # Non-target ring must stay hollow.
    for r in range(10, 13):
        for c in range(12, 15):
            if r in (10, 12) or c in (12, 14):
                g[r][c] = 6
    return g


handmade = witness()
assert GEN.self_check(handmade) == []
expected = topological_rule(handmade)
rival = bbox_fill_rival(handmade)
assert expected != rival
# The true 3x3 hole fills, but exterior-connected cells in the arm-expanded bbox stay empty.
assert all(expected[r][c] == 4 for r in range(4, 7) for c in range(4, 7))
assert expected[4][8] == 0 and rival[4][8] == 4
assert expected[11][13] == 0  # distractor remains hollow

generated: list[dict] = []
inputs: list[Grid] = [handmade]
for band_index, band in enumerate(("easy", "medium", "hard")):
    for index in range(10):
        seed = 730_000 + band_index * 10_000 + index
        grid = GEN.generate(seed, index, difficulty=band)
        py = topological_rule(grid)
        rv = bbox_fill_rival(grid)
        generated.append({
            "seed": seed,
            "sample_index": index,
            "difficulty": band,
            "self_check_errors": GEN.self_check(grid),
            "rival_matches_python_rule": rv == py,
        })
        inputs.append(grid)
assert all(row["self_check_errors"] == [] for row in generated)
assert all(row["rival_matches_python_rule"] for row in generated)

pairs = canonical_pairs(TASK, root=REPO)
canonical_matches = sum(bbox_fill_rival(row["input"]) == row["output"] for row in pairs)

(OUT / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
record = {
    "schema": "arcpuzzles-audit-probe-preapply-v1",
    "task_id": TASK,
    "generator_sha256": DIGEST,
    "source_path": str(SOURCE.relative_to(REPO)),
    "witness": {
        "input_index": 0,
        "self_check_errors": GEN.self_check(handmade),
        "python_topological_output": expected,
        "rival_output": rival,
        "separating_cell": [4, 8],
        "construction": "target 5x5 ring plus connected top arm; true hole and exterior-connected bbox space coexist",
    },
    "generated_census": {
        "plan": "10 draws in each of easy, medium, hard; seed=730000+10000*band_index+sample_index",
        "total": len(generated),
        "rival_matches_python_rule": sum(row["rival_matches_python_rule"] for row in generated),
        "rows": generated,
    },
    "canonical_census": {
        "total": len(pairs),
        "rival_matches_labels": canonical_matches,
    },
    "rival_name": "fill_every_background_cell_in_each_target_component_bbox",
    "apply_command": {
        "cwd": "WORK",
        "argv": [
            "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
            "--input", f"../checks/audit/{TASK}/input.json", "--check-generator-domain",
            "--out", f"../checks/audit/{TASK}/racket.json",
        ],
    },
}
(OUT / "probe-preapply.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "task_id": TASK,
    "generator_sha256": DIGEST,
    "generated_rival_fit": f"{len(generated)}/{len(generated)}",
    "canonical_rival_fit": f"{canonical_matches}/{len(pairs)}",
    "witness_rival_differs": True,
}, sort_keys=True))
