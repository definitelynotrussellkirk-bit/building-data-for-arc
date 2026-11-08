#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
import copy
import importlib
import json
from pathlib import Path
import sys
import tempfile

TASKS = ("dbee38495261", "3a3258548fa3")
ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"


def canonical_rows():
    wanted = set(TASKS)
    out = {}
    with (REPO / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") in wanted:
                out[row["task_id"]] = row
    return out


def pairs(row):
    result = list(row["train"])
    test = row["test"]
    result.extend(test if isinstance(test, list) else [test])
    return result


def ordered_route(grid, *, avoid_walls):
    out = copy.deepcopy(grid)
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in {2, 3, 4, 5, 6, 7} and value not in positions:
                positions[value] = (r, c)
    order = [2] + sorted(v for v in positions if v not in {2, 3}) + [3]
    h, w = len(grid), len(grid[0])
    for src_color, dst_color in zip(order, order[1:]):
        src, dst = positions[src_color], positions[dst_color]
        queue = deque([src])
        prev = {src: None}
        while queue and dst not in prev:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                p = (r + dr, c + dc)
                if not (0 <= p[0] < h and 0 <= p[1] < w) or p in prev:
                    continue
                if avoid_walls and grid[p[0]][p[1]] == 1:
                    continue
                prev[p] = (r, c)
                queue.append(p)
        if dst not in prev:
            continue
        path = []
        cur = dst
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        for r, c in path[1:-1]:
            if out[r][c] == 0:
                out[r][c] = 8
    return out


def complete_exact_three(grid):
    out = copy.deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            vals = [grid[r][c], grid[r][c + 1], grid[r + 1][c], grid[r + 1][c + 1]]
            nonzero = [v for v in vals if v != 0]
            if len(nonzero) == 3 and len(set(nonzero)) == 1 and 0 in vals:
                color = nonzero[0]
                for dr in (0, 1):
                    for dc in (0, 1):
                        if grid[r + dr][c + dc] == 0:
                            out[r + dr][c + dc] = color
    return out


def fill_component_bboxes(grid):
    out = copy.deepcopy(grid)
    h, w = len(grid), len(grid[0])
    seen = set()
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    p = (rr + dr, cc + dc)
                    if (0 <= p[0] < h and 0 <= p[1] < w and p not in seen
                            and grid[p[0]][p[1]] == color):
                        seen.add(p)
                        stack.append(p)
            r1 = min(rr for rr, _ in cells); r2 = max(rr for rr, _ in cells)
            c1 = min(cc for _, cc in cells); c2 = max(cc for _, cc in cells)
            for rr in range(r1, r2 + 1):
                for cc in range(c1, c2 + 1):
                    out[rr][cc] = color
    return out


def main():
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime

    rows = canonical_rows()
    with tempfile.TemporaryDirectory(prefix="audit-runtime-") as td:
        runtime = Path(td)
        prepare_runtime(Catalog(REPO), runtime, task_ids=list(TASKS))
        sys.path.insert(0, str(runtime))
        dbee = importlib.import_module("puzzle_generators.per_puzzle.dbee38495261.generator")
        corner = importlib.import_module("puzzle_generators.per_puzzle.3a3258548fa3.generator")

        dbee_pairs = pairs(rows["dbee38495261"])
        canonical_wall_aware = sum(
            ordered_route(p["input"], avoid_walls=True) == p["output"] for p in dbee_pairs
        )
        canonical_open_matches = sum(
            ordered_route(p["input"], avoid_walls=False) == p["output"] for p in dbee_pairs
        )
        canonical_selfcheck_rejections = sum(bool(dbee.self_check(p["input"])) for p in dbee_pairs)
        dbee_generated = []
        for band in ("easy", "medium", "hard"):
            for seed in range(100):
                grid = dbee.generate(seed, seed, difficulty=band)
                dbee_generated.append(grid)
        dbee_open_matches = sum(
            ordered_route(g, avoid_walls=False) == ordered_route(g, avoid_walls=True)
            for g in dbee_generated
        )

        corner_pairs = pairs(rows["3a3258548fa3"])
        canonical_exact = sum(complete_exact_three(p["input"]) == p["output"] for p in corner_pairs)
        canonical_bbox = sum(fill_component_bboxes(p["input"]) == p["output"] for p in corner_pairs)
        corner_generated = []
        for band in ("easy", "medium", "hard"):
            for seed in range(100):
                grid = corner.generate(seed, seed, difficulty=band)
                corner_generated.append(grid)
        generated_bbox = sum(
            fill_component_bboxes(g) == complete_exact_three(g) for g in corner_generated
        )
        override_equal = sum(
            corner.generate(seed, seed, difficulty="medium", n_blocks=1)
            == corner.generate(seed, seed, difficulty="medium", n_blocks=9)
            for seed in range(30)
        )
        counterexample = [[0] * 6 for _ in range(5)]
        for r, c in ((1, 1), (1, 2), (1, 3), (2, 1)):
            counterexample[r][c] = 4

        report = {
            "schema": "review-audit-reproduction-v1",
            "dbee38495261": {
                "generated_scenes": len(dbee_generated),
                "generated_with_wall_color_1": sum(
                    any(1 in row for row in g) for g in dbee_generated
                ),
                "generated_open_grid_rival_matches_rule": dbee_open_matches,
                "canonical_pairs": len(dbee_pairs),
                "canonical_wall_aware_python_matches_stored": canonical_wall_aware,
                "canonical_open_grid_rival_matches_stored": canonical_open_matches,
                "canonical_inputs_rejected_by_self_check": canonical_selfcheck_rejections,
                "first_canonical_open_rival": ordered_route(
                    dbee_pairs[0]["input"], avoid_walls=False
                ),
            },
            "3a3258548fa3": {
                "generated_scenes": len(corner_generated),
                "generated_component_bbox_shortcut_matches_rule": generated_bbox,
                "canonical_pairs": len(corner_pairs),
                "canonical_exact_python_matches_stored": canonical_exact,
                "canonical_component_bbox_shortcut_matches_stored": canonical_bbox,
                "n_blocks_1_vs_9_identical": override_equal,
                "n_blocks_override_trials": 30,
                "accepted_counterexample": counterexample,
                "counterexample_self_check": corner.self_check(counterexample),
                "counterexample_exact_output": complete_exact_three(counterexample),
                "counterexample_bbox_output": fill_component_bboxes(counterexample),
            },
        }
    out = ROOT / "checks/audits/findings.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(out)


if __name__ == "__main__":
    main()
