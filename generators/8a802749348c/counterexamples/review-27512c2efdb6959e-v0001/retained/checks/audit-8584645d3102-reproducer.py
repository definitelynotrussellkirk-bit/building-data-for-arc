#!/usr/bin/env python3
"""Independent, read-only audit reproducer for generator 8584645d3102."""
from __future__ import annotations

import json
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
sys.path.insert(0, str(REPO / "shared" / "tools"))

from generator_module_loader import load_module_from_path  # noqa: E402

TASK = "8584645d3102"
GEN_PATH = REPO / "generators" / TASK / "generator.py"
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def canonical_record() -> dict:
    with CANONICAL.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise RuntimeError(f"task {TASK} missing from canonical ledger")


def seed_positions(grid):
    reds, greens = [], []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 2:
                reds.append((r, c))
            elif value == 3:
                greens.append((r, c))
    return reds, greens


def shortest_path_summary(grid) -> dict:
    reds, greens = seed_positions(grid)
    if len(reds) != 1 or len(greens) != 1:
        return {"distance": None, "path_count_capped_at_2": 0}
    start, goal = reds[0], greens[0]
    h, w = len(grid), len(grid[0])
    dist = {start: 0}
    ways = {start: 1}
    q = deque([start])
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] == 5:
                continue
            nxt = (nr, nc)
            nd = dist[(r, c)] + 1
            if nxt not in dist:
                dist[nxt] = nd
                ways[nxt] = ways[(r, c)]
                q.append(nxt)
            elif dist[nxt] == nd:
                ways[nxt] = min(2, ways[nxt] + ways[(r, c)])
    return {
        "distance": dist.get(goal),
        "path_count_capped_at_2": ways.get(goal, 0),
    }


def main() -> None:
    gen = load_module_from_path(f"audit_{TASK}", GEN_PATH)
    canonical = canonical_record()
    canonical_cases = list(canonical["train"]) + [canonical["test"]]
    canonical_checks = []
    for index, case in enumerate(canonical_cases):
        errors = gen.self_check(case["input"])
        canonical_checks.append({
            "case": f"train[{index}]" if index < len(canonical["train"]) else "test[0]",
            "accepted": not errors,
            "errors": errors,
        })

    samples = []
    ambiguous = 0
    unreachable = 0
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(30):
            grid = gen.generate(seed, 0, difficulty=difficulty)
            paths = shortest_path_summary(grid)
            if paths["path_count_capped_at_2"] >= 2:
                ambiguous += 1
            if paths["path_count_capped_at_2"] == 0:
                unreachable += 1
            samples.append({
                "difficulty": difficulty,
                "seed": seed,
                **paths,
                "grid": grid if paths["path_count_capped_at_2"] >= 2 and not any(
                    row.get("grid") for row in samples
                ) else None,
            })

    first_ambiguous = next(row for row in samples if row["path_count_capped_at_2"] >= 2)
    no_seeds = gen.generate(0, 0, texture="no_seeds")
    multiple_seeds = gen.generate(0, 0, texture="multiple_seeds")
    wall_low = gen.generate(0, 0, difficulty="easy", wall_pct=0.0)
    wall_high = gen.generate(0, 0, difficulty="easy", wall_pct=0.4)
    unknown = gen.generate(0, 0, difficulty="easy", typo_axis="ignored")
    ordinary = gen.generate(0, 0, difficulty="easy")

    report = {
        "schema": "arcpuzzles-independent-audit-v1",
        "task_id": TASK,
        "generator_version": gen.VERSION,
        "generator_path": str(GEN_PATH.relative_to(ROOT)),
        "canonical_title": canonical.get("title"),
        "canonical_written_solution": canonical.get("written_solution"),
        "canonical_case_count": len(canonical_checks),
        "canonical_rejected_count": sum(not row["accepted"] for row in canonical_checks),
        "canonical_checks": canonical_checks,
        "sample_count": len(samples),
        "ambiguous_shortest_path_count": ambiguous,
        "unreachable_count": unreachable,
        "first_ambiguous": first_ambiguous,
        "degenerates": {
            "no_seeds_self_check": gen.self_check(no_seeds),
            "multiple_seeds_self_check": gen.self_check(multiple_seeds),
            "invalid_single_cell_self_check": gen.self_check([[9]]),
        },
        "override_contract": {
            "wall_pct_0_equals_0_4": wall_low == wall_high,
            "unknown_override_equals_ordinary": unknown == ordinary,
        },
    }
    out = ROOT / "checks" / "audit-8584645d3102-reproducer.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "canonical_rejected": report["canonical_rejected_count"],
        "ambiguous": ambiguous,
        "sample_count": len(samples),
        "unreachable": unreachable,
        "no_seeds_self_check": report["degenerates"]["no_seeds_self_check"],
        "invalid_single_cell_self_check": report["degenerates"]["invalid_single_cell_self_check"],
        **report["override_contract"],
        "output": str(out),
    }, indent=2))


if __name__ == "__main__":
    main()
