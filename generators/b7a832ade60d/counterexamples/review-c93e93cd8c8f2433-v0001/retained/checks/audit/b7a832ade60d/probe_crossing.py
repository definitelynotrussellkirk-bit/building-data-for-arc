from __future__ import annotations

import hashlib
import importlib.util
import sys
import json
from pathlib import Path

TASK_ID = "b7a832ade60d"
ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / "checks" / "audit" / TASK_ID
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
spec = importlib.util.spec_from_file_location(
    f"audit_{TASK_ID}_generator",
    REPO / "generators" / TASK_ID / "generator.py",
)
assert spec is not None and spec.loader is not None
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)


def documented_stop_on_painted(grid: list[list[int]]) -> list[list[int]]:
    """Implement the behavior promised by SUMMARY: prior ray pixels block."""
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value in (0, 5):
                continue
            if r == 0:
                dr, dc = 1, 0
            elif r == h - 1:
                dr, dc = -1, 0
            elif c == 0:
                dr, dc = 0, 1
            elif c == w - 1:
                dr, dc = 0, -1
            else:
                continue
            rr, cc = r + dr, c + dc
            while 0 <= rr < h and 0 <= cc < w and out[rr][cc] == 0:
                out[rr][cc] = value
                rr += dr
                cc += dc
    return out


def active_edges(grid: list[list[int]]) -> set[str]:
    h, w = len(grid), len(grid[0])
    edges: set[str] = set()
    if any(grid[0][c] not in (0, 5) for c in range(1, w - 1)):
        edges.add("top")
    if any(grid[h - 1][c] not in (0, 5) for c in range(1, w - 1)):
        edges.add("bottom")
    if any(grid[r][0] not in (0, 5) for r in range(1, h - 1)):
        edges.add("left")
    if any(grid[r][w - 1] not in (0, 5) for r in range(1, h - 1)):
        edges.add("right")
    return edges


def border_colors(grid: list[list[int]]) -> set[int]:
    h, w = len(grid), len(grid[0])
    return {
        grid[r][c]
        for r in range(h)
        for c in range(w)
        if (r in (0, h - 1) or c in (0, w - 1))
        and grid[r][c] not in (0, 5)
    }


def main() -> None:
    grid = json.loads((AUDIT / "input.json").read_text())
    racket = json.loads((AUDIT / "racket.json").read_text())
    actual = racket["results"][0]["output"]
    rival = documented_stop_on_painted(grid)
    differences = [
        {"row": r, "col": c, "racket": actual[r][c], "documented": rival[r][c]}
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if actual[r][c] != rival[r][c]
    ]

    sample_count = 200
    coverage_histogram: dict[str, int] = {}
    all_four = 0
    distinct_color_failures = 0
    selfcheck_failures = 0
    examples = []
    for seed in range(sample_count):
        sample = GEN.generate(seed, 0, difficulty="medium")
        edges = tuple(sorted(active_edges(sample)))
        key = ",".join(edges) or "none"
        coverage_histogram[key] = coverage_histogram.get(key, 0) + 1
        all_four += int(len(edges) == 4)
        distinct_color_failures += int(len(border_colors(sample)) < 2)
        errors = GEN.self_check(sample)
        selfcheck_failures += int(bool(errors))
        if len(examples) < 5 and len(edges) < 4:
            examples.append(
                {
                    "seed": seed,
                    "sample_index": 0,
                    "edges": list(edges),
                    "border_colors": sorted(border_colors(sample)),
                    "self_check": errors,
                    "input": sample,
                }
            )

    generator_path = REPO / "generators" / TASK_ID / "generator.py"
    report = {
        "schema": "arc-generator-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "rule_hash": racket["executed_rule_hash"],
        "crossing_counterexample": {
            "input": grid,
            "self_check_errors": GEN.self_check(grid),
            "racket_output": actual,
            "documented_stop_on_painted_output": rival,
            "different_cells": differences,
            "interpretation": (
                "The Racket rule tests the original input while extending each ray, "
                "so the later horizontal ray crosses and overwrites the earlier vertical "
                "ray. The SUMMARY says a prior ray tip should block it."
            ),
        },
        "ordinary_medium_sample": {
            "seed_range": [0, sample_count - 1],
            "sample_index": 0,
            "denominator": sample_count,
            "all_four_edges": all_four,
            "fewer_than_four_edges": sample_count - all_four,
            "distinct_border_color_failures": distinct_color_failures,
            "self_check_failures": selfcheck_failures,
            "edge_set_histogram": coverage_histogram,
            "first_undercovered_examples": examples,
        },
    }
    (AUDIT / "rival.json").write_text(
        json.dumps(
            {
                "task_id": TASK_ID,
                "rival": "documented_stop_on_prior_ray_pixels",
                "output": rival,
                "different_cells": differences,
            },
            indent=2,
        )
        + "\n"
    )
    (AUDIT / "probe_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["crossing_counterexample"], indent=2))
    print(json.dumps(report["ordinary_medium_sample"], indent=2))


if __name__ == "__main__":
    main()
