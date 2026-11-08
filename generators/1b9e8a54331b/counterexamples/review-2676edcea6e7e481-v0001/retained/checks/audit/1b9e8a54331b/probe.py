#!/usr/bin/env python3
"""Reproduce a blocker-free teaching window for 1b9e8a54331b."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GENERATOR = ROOT / "repo/generators/1b9e8a54331b/generator.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transform(grid, *, honor_blockers: bool):
    h, w = len(grid), len(grid[0])
    horizontal = set()
    vertical = set()
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 2:
                horizontal.add((r, c))
                for dc in (-1, 1):
                    cc = c + dc
                    while 0 <= cc < w and (not honor_blockers or grid[r][cc] != 5):
                        horizontal.add((r, cc))
                        cc += dc
            if grid[r][c] == 1:
                vertical.add((r, c))
                for dr in (-1, 1):
                    rr = r + dr
                    while 0 <= rr < h and (not honor_blockers or grid[rr][c] != 5):
                        vertical.add((rr, c))
                        rr += dr
    out = []
    for r in range(h):
        row = []
        for c in range(w):
            point = (r, c)
            if grid[r][c] == 5:
                value = 5
            elif point in horizontal and point in vertical:
                value = 6
            elif point in horizontal:
                value = 7
            elif point in vertical:
                value = 8
            else:
                value = 0
            row.append(value)
        out.append(row)
    return out


def load_generator():
    spec = importlib.util.spec_from_file_location("audited_1b9", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main():
    cases = json.loads((HERE / "cases.json").read_text())["items"]
    racket_doc = json.loads((HERE / "racket_outputs.json").read_text())
    racket = [item["output"] for item in racket_doc["results"]]
    mirror = [transform(case["input"], honor_blockers=True) for case in cases]
    rival = [transform(case["input"], honor_blockers=False) for case in cases]
    if mirror != racket:
        raise AssertionError("local authority mirror disagrees with Racket")

    matches = [guess == expected for guess, expected in zip(rival, racket)]
    query_differences = [
        [r, c, rival[-1][r][c], racket[-1][r][c]]
        for r in range(len(racket[-1]))
        for c in range(len(racket[-1][0]))
        if rival[-1][r][c] != racket[-1][r][c]
    ]

    # Reproducible ordinary-distribution census. The mirror above was checked
    # against Racket on the exact ambiguity window before using it here.
    module = load_generator()
    census = {}
    for band in ("easy", "medium", "hard"):
        unsupported = 0
        total = 300
        for sample_index in range(total):
            grid = module.generate(9001, sample_index, difficulty=band)
            intended = transform(grid, honor_blockers=True)
            shortcut = transform(grid, honor_blockers=False)
            unsupported += intended == shortcut
        census[band] = {
            "draws": total,
            "no_blocker_discrimination": unsupported,
            "rate": unsupported / total,
        }

    report = {
        "task_id": "1b9e8a54331b",
        "audited_generator_sha256": sha256(GENERATOR),
        "executed_rule_hash": racket_doc["executed_rule_hash"],
        "window": {"difficulty": "easy", "seed": 1, "sample_indices": [2, 3, 4, 5, 6]},
        "authority_mirror_matches_racket": len(racket),
        "no_blocker_rival_matches": matches,
        "four_demo_rival_fit": all(matches[:4]),
        "held_out_query_disagrees": not matches[4],
        "held_out_query_differences": query_differences,
        "ordinary_census": census,
        "conclusion": (
            "Four consecutive ordinary examples do not exercise wall stopping, so a ray-through-"
            "walls rival fits every demonstration and gives a different Racket-labelled answer "
            "on the next ordinary example. The unscheduled sampler does not guarantee blocker support."
        ),
    }
    (HERE / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
