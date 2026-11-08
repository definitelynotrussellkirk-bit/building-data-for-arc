"""Independent task-local semantic probes. Run from the extracted packet root.

This script reads only the selected canonical task. Python predictions here are
diagnostic rival hypotheses, not substitutes for the retained Racket authority.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
from collections import deque
from pathlib import Path

TASK_ID = "547c45a21db1"
DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIRS8 = DIRS4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))


def canonical(repo):
    rows = []
    for line in (repo / "shared/data/canonical/puzzles.jsonl").open():
        obj = json.loads(line)
        if obj.get("task_id") == TASK_ID:
            rows.append((obj, hashlib.sha256(line.encode()).hexdigest()))
    assert len(rows) == 1, len(rows)
    row, row_hash = rows[0]
    pairs = []
    for split in ("train", "test"):
        source = row[split]
        source = [source] if isinstance(source, dict) else source
        for index, pair in enumerate(source):
            pairs.append((split, index, pair))
    return row, row_hash, pairs


def support(grid):
    return {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v in (1, 2, 3)}


def seed(grid, color):
    return next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color)


def distances(grid, start, diagonal=False, diagonal_cost=1.0):
    points = support(grid)
    found = {start: 0.0}
    queue = [(0.0, start)]
    for_pop = DIRS8 if diagonal else DIRS4
    while queue:
        dist, at = heapq.heappop(queue)
        if dist > found[at]:
            continue
        for dr, dc in for_pop:
            nxt = (at[0] + dr, at[1] + dc)
            weight = diagonal_cost if dr and dc else 1.0
            cost = dist + weight
            if nxt in points and cost < found.get(nxt, math.inf):
                found[nxt] = cost
                heapq.heappush(queue, (cost, nxt))
    return found


def recolor(grid, d2, d3):
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 1:
                delta = d2[(r, c)] - d3[(r, c)]
                out[r][c] = 2 if delta < -1e-8 else 3 if delta > 1e-8 else 4
    return out


def bfs4(grid):
    return recolor(grid, distances(grid, seed(grid, 2)), distances(grid, seed(grid, 3)))


def bfs8(grid):
    return recolor(grid, distances(grid, seed(grid, 2), True), distances(grid, seed(grid, 3), True))


def diagonal_euclidean(grid):
    return recolor(grid, distances(grid, seed(grid, 2), True, math.sqrt(2)),
                   distances(grid, seed(grid, 3), True, math.sqrt(2)))


def direct_metric(grid, metric):
    seeds = [seed(grid, value) for value in (2, 3)]
    dists = []
    for point in seeds:
        one = {}
        for at in support(grid):
            delta = abs(at[0] - point[0]), abs(at[1] - point[1])
            one[at] = sum(delta) if metric == "manhattan" else max(delta) if metric == "chebyshev" else sum(x*x for x in delta)
        dists.append(one)
    return recolor(grid, *dists)


def raster_seed_order(grid):
    ends = sorted([seed(grid, 2), seed(grid, 3)])
    return recolor(grid, distances(grid, ends[0]), distances(grid, ends[1]))


def path_order(grid):
    points = support(grid)
    prev = None
    cur = seed(grid, 2)
    path = []
    while cur is not None:
        path.append(cur)
        options = [p for dr, dc in DIRS4 if (p := (cur[0]+dr, cur[1]+dc)) in points and p != prev]
        assert len(options) <= 1, "requires a simple induced path with endpoint seeds"
        prev, cur = cur, options[0] if options else None
    assert len(path) == len(points)
    return path


def turn_penalty(grid, penalty):
    path = path_order(grid)
    turns = [i for i in range(1, len(path)-1)
             if (path[i][0]-path[i-1][0], path[i][1]-path[i-1][1]) !=
                (path[i+1][0]-path[i][0], path[i+1][1]-path[i][1])]
    d2 = {p: i + penalty * sum(t < i for t in turns) for i, p in enumerate(path)}
    d3 = {p: len(path)-1-i + penalty * sum(t > i for t in turns) for i, p in enumerate(path)}
    return recolor(grid, d2, d3)


RIVALS = {
    "manhattan": lambda g: direct_metric(g, "manhattan"),
    "euclidean_squared": lambda g: direct_metric(g, "euclidean"),
    "chebyshev": lambda g: direct_metric(g, "chebyshev"),
    "bfs8": bfs8,
    "diagonal_euclidean": diagonal_euclidean,
    "raster_seed_order": raster_seed_order,
    "turn_penalty_half": lambda g: turn_penalty(g, 0.5),
    "turn_discount_half": lambda g: turn_penalty(g, -0.5),
    "turn_penalty_one": lambda g: turn_penalty(g, 1.0),
}


def mismatch(a, b):
    return [[r, c, a[r][c], b[r][c]] for r in range(len(a)) for c in range(len(a[0])) if a[r][c] != b[r][c]]


def make_path(points, shape=(5, 7), red_at_start=True):
    grid = [[0]*shape[1] for _ in range(shape[0])]
    for r, c in points:
        grid[r][c] = 1
    a, b = (2, 3) if red_at_start else (3, 2)
    grid[points[0][0]][points[0][1]] = a
    grid[points[-1][0]][points[-1][1]] = b
    return grid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path("repo"))
    parser.add_argument("--out", type=Path, default=Path("checks/semantic-review/analysis.json"))
    args = parser.parse_args()
    row, row_hash, pairs = canonical(args.repo)
    report = {
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256((args.repo/f"generators/{TASK_ID}/generator.py").read_bytes()).hexdigest(),
        "rule_sha256": hashlib.sha256(row["program_solution"].encode()).hexdigest(),
        "canonical_line_sha256": row_hash,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical_profiles": [],
        "rival_canonical_fit": {},
        "witnesses": [],
    }
    for split, index, pair in pairs:
        g = pair["input"]
        pts = support(g)
        report["canonical_profiles"].append({"split": split, "index": index,
            "shape": [len(g), len(g[0])], "palette": sorted({v for row in g for v in row}),
            "path_length": len(pts), "ones": sum(v == 1 for row in g for v in row),
            "seed2": seed(g, 2), "seed3": seed(g, 3),
            "bfs4_differences": mismatch(bfs4(g), pair["output"]),
            "path": path_order(g)})
    for name, fn in RIVALS.items():
        entries = [{"split": split, "index": index,
                    "differences": mismatch(fn(pair["input"]), pair["output"])}
                   for split, index, pair in pairs]
        report["rival_canonical_fit"][name] = {"fits_all": all(not e["differences"] for e in entries), "pairs": entries}
    witnesses = {
        "unequal_l_4": make_path([(1,1),(1,2),(1,3),(2,3)]),
        "asymmetric_u_7_reversed_order": make_path([(2,1),(3,1),(3,2),(3,3),(2,3),(1,3),(0,3)]),
        "asymmetric_u_8_reversed_order": make_path([(3,1),(4,1),(4,2),(4,3),(3,3),(2,3),(1,3),(0,3)]),
        "canonical_query_swapped_seeds": [[3 if v == 2 else 2 if v == 3 else v for v in line] for line in pairs[-1][2]["input"]],
    }
    for name, grid in witnesses.items():
        expected = bfs4(grid)
        report["witnesses"].append({"name": name, "input": grid, "python_bfs4_diagnostic_output": expected,
            "rivals": {name: {"output": fn(grid), "differences": mismatch(fn(grid), expected)} for name, fn in RIVALS.items()}})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+"\n")
    (args.out.parent / "authority_inputs.json").write_text(json.dumps(list(witnesses.values()))+"\n")
    print(json.dumps({"output": str(args.out), "source_sha256": report["generator_sha256"],
        "canonical_fit": {name: result["fits_all"] for name,result in report["rival_canonical_fit"].items()},
        "witness_refutations": {w["name"]: [name for name, result in w["rivals"].items() if result["differences"]]
                                 for w in report["witnesses"]}}, indent=2))


if __name__ == "__main__":
    main()
