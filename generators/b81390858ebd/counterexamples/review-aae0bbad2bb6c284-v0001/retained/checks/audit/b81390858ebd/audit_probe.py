#!/usr/bin/env python3
"""Independent shortcut census for audit target b81390858ebd.

This deliberately does not import private runner functions.  It imports only the
public generator module, reimplements the ARC rule and the proposed rival, and
writes reproducible JSON evidence beside this script.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
RUNTIME = REPO / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))

TASK = "b81390858ebd"
GENERATOR_PATH = REPO / "generators" / TASK / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"

Grid = list[list[int]]
Cell = tuple[int, int]


def sha256_json(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_canonical() -> dict:
    with CANONICAL_PATH.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise KeyError(TASK)


def components(grid: Grid) -> list[tuple[int, list[Cell]]]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    out: list[tuple[int, list[Cell]]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[Cell] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, sorted(cells)))
    return out


def contact_degrees(grid: Grid, comps: list[tuple[int, list[Cell]]]) -> list[int]:
    owner = {cell: i for i, (_, cells) in enumerate(comps) for cell in cells}
    h, w = len(grid), len(grid[0])
    neighbors = [set() for _ in comps]
    for i, (_, cells) in enumerate(comps):
        for r, c in cells:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    j = owner.get((nr, nc))
                    if j is not None and j != i:
                        neighbors[i].add(j)
    return [len(s) for s in neighbors]


def render_component(cells: Iterable[Cell]) -> Grid:
    cells = sorted(cells)
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    cell_set = set(cells)
    return [
        [8 if (r, c) in cell_set else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def intended_rule(grid: Grid) -> Grid:
    comps = components(grid)
    degrees = contact_degrees(grid, comps)
    best = min(
        range(len(comps)),
        key=lambda i: (-degrees[i], -len(comps[i][1]), min(comps[i][1])),
    )
    return render_component(comps[best][1])


def largest_top_left_rival(grid: Grid) -> Grid:
    comps = components(grid)
    best = min(range(len(comps)), key=lambda i: (-len(comps[i][1]), min(comps[i][1])))
    return render_component(comps[best][1])


def component_summary(grid: Grid) -> list[dict]:
    comps = components(grid)
    degrees = contact_degrees(grid, comps)
    rows = []
    for i, (color, cells) in enumerate(comps):
        rows.append(
            {
                "index": i,
                "color": color,
                "size": len(cells),
                "degree": degrees[i],
                "top_left": list(min(cells)),
                "cells": [list(x) for x in cells],
            }
        )
    return rows


def canonical_pairs(row: dict) -> list[tuple[Grid, Grid, str]]:
    pairs = [(p["input"], p["output"], f"train[{i}]") for i, p in enumerate(row["train"])]
    test = row.get("test")
    if isinstance(test, dict) and "output" in test:
        pairs.append((test["input"], test["output"], "test[0]"))
    elif isinstance(test, list):
        pairs.extend((p["input"], p["output"], f"test[{i}]") for i, p in enumerate(test) if "output" in p)
    return pairs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws-per-band", type=int, default=200)
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("probe.json"))
    args = parser.parse_args()

    generator = load_generator()
    canonical = load_canonical()

    canonical_rows = []
    for inp, expected, label in canonical_pairs(canonical):
        intended = intended_rule(inp)
        rival = largest_top_left_rival(inp)
        canonical_rows.append(
            {
                "label": label,
                "expected_sha256": sha256_json(expected),
                "intended_matches_expected": intended == expected,
                "rival_matches_expected": rival == expected,
                "components": component_summary(inp),
            }
        )

    bands = [None, "easy", "medium", "hard"]
    generated = {}
    examples = []
    for band_index, band in enumerate(bands):
        counts = {
            "draws": 0,
            "self_check_clean": 0,
            "intended_equals_rival": 0,
            "target_is_unique_largest_component": 0,
            "generator_errors": 0,
        }
        for i in range(args.draws_per_band):
            seed = 8_130_000 + band_index * 100_000 + i
            try:
                grid = generator.generate(seed, i, difficulty=band)
            except Exception as exc:  # retained as evidence, not hidden
                counts["generator_errors"] += 1
                if len(examples) < 10:
                    examples.append({"difficulty": band, "seed": seed, "sample_index": i, "error": repr(exc)})
                continue
            counts["draws"] += 1
            if not generator.self_check(grid, difficulty=band):
                counts["self_check_clean"] += 1
            comps = components(grid)
            degrees = contact_degrees(grid, comps)
            target = min(
                range(len(comps)),
                key=lambda j: (-degrees[j], -len(comps[j][1]), min(comps[j][1])),
            )
            sizes = [len(cells) for _, cells in comps]
            if sizes.count(sizes[target]) == 1 and sizes[target] == max(sizes):
                counts["target_is_unique_largest_component"] += 1
            if intended_rule(grid) == largest_top_left_rival(grid):
                counts["intended_equals_rival"] += 1
            if len(examples) < 4:
                examples.append(
                    {
                        "difficulty": band,
                        "seed": seed,
                        "sample_index": i,
                        "grid": grid,
                        "components": component_summary(grid),
                        "output": intended_rule(grid),
                    }
                )
        generated["default" if band is None else band] = counts

    # Task-lawful counterexample that current generation/self_check excludes:
    # a 3-cell degree-3 hub and an isolated 4-cell distractor.
    counterexample: Grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 7, 7, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 7, 7, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 3, 0, 4, 0, 0, 0, 0],
        [0, 0, 0, 0, 2, 2, 2, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 6, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    intended_counterexample = intended_rule(counterexample)
    rival_counterexample = largest_top_left_rival(counterexample)

    report = {
        "schema": "b81390858ebd-independent-audit-v1",
        "task_id": TASK,
        "generator_version": getattr(generator, "VERSION", None),
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "rival": {
            "name": "largest_component_then_top_left",
            "definition": "Select the largest same-color 4-connected component, breaking ties by top-left position; crop its bbox and recolor its cells to 8.",
        },
        "canonical": {
            "pairs": len(canonical_rows),
            "intended_matches": sum(r["intended_matches_expected"] for r in canonical_rows),
            "rival_matches": sum(r["rival_matches_expected"] for r in canonical_rows),
            "rows": canonical_rows,
        },
        "generated": generated,
        "generated_totals": {
            key: sum(v[key] for v in generated.values())
            for key in next(iter(generated.values()))
        },
        "counterexample": {
            "input": counterexample,
            "components": component_summary(counterexample),
            "intended_mirror_output": intended_counterexample,
            "rival_output": rival_counterexample,
            "disagrees": intended_counterexample != rival_counterexample,
            "generator_self_check_errors": generator.self_check(counterexample, difficulty=None),
            "input_sha256": sha256_json(counterexample),
            "intended_output_sha256": sha256_json(intended_counterexample),
            "rival_output_sha256": sha256_json(rival_counterexample),
        },
        "sample_generated_examples": examples,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    args.out.with_name("counterexample-input.json").write_text(json.dumps(counterexample, indent=2) + "\n")
    args.out.with_name("counterexample-rival-output.json").write_text(json.dumps(rival_counterexample, indent=2) + "\n")

    print(json.dumps({
        "canonical_rival_matches": f"{report['canonical']['rival_matches']}/{report['canonical']['pairs']}",
        "generated_rival_matches": f"{report['generated_totals']['intended_equals_rival']}/{report['generated_totals']['draws']}",
        "generated_unique_largest": f"{report['generated_totals']['target_is_unique_largest_component']}/{report['generated_totals']['draws']}",
        "counterexample_disagrees": report["counterexample"]["disagrees"],
        "counterexample_self_check_errors": report["counterexample"]["generator_self_check_errors"],
        "out": str(args.out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
