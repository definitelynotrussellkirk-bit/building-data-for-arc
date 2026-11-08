#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge

ROOT = Path(__file__).resolve().parents[3] / "repo"
TASK = "61a55c0c7ee8"
GEN_PATH = ROOT / "generators" / TASK / "generator.py"
CANON = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
OUT = Path(__file__).with_name("report.json")


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GEN_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    for line in CANON.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row["program_solution"]
    raise RuntimeError("canonical rule missing")


def components(grid: list[list[int]], max_row: int) -> list[list[tuple[int, int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(max_row) for c in range(w) if grid[r][c] != 0}
    out = []
    while unseen:
        start = min(unseen)
        stack = [start]
        unseen.remove(start)
        comp = []
        while stack:
            r, c = stack.pop()
            comp.append((r, c, grid[r][c]))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                q = (r + dr, c + dc)
                if q in unseen:
                    unseen.remove(q)
                    stack.append(q)
        out.append(sorted(comp))
    return sorted(out, key=lambda c: (-len(c), c))


def intended_role_aware(grid: list[list[int]]) -> tuple[list[list[int]], dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    legend_cols = [c for c in range(w) if grid[h - 2][c] or grid[h - 1][c]][:3]
    mapping = {grid[h - 2][c]: grid[h - 1][c] for c in legend_cols}
    comps = components(grid, h - 2)
    template = next(c for c in comps if len(c) > 1 and any(v != 9 for _, _, v in c))
    template_pos = {(r, c) for r, c, _ in template}
    anchors = [
        (r, c)
        for comp in comps
        for r, c, v in comp
        if v == 9 and (r, c) not in template_pos
    ]
    r0 = min(r for r, _, _ in template)
    c0 = min(c for _, c, _ in template)
    out = [[0 for _ in range(w)] for _ in range(h)]
    for ar, ac in anchors:
        for r, c, v in template:
            rr, cc = ar + r - r0, ac + c - c0
            if not (0 <= rr < h and 0 <= cc < w):
                raise RuntimeError("role-aware stamp left grid")
            out[rr][cc] = mapping[v]
    return out, {
        "legend_columns": legend_cols,
        "mapping": {str(k): v for k, v in sorted(mapping.items())},
        "template": template,
        "true_anchors": anchors,
        "false_anchor_cells_inside_template": [(r, c) for r, c, v in template if v == 9],
    }


def diff_cells(a, b):
    return [
        [r, c, a[r][c], b[r][c]]
        for r in range(len(a))
        for c in range(len(a[0]))
        if a[r][c] != b[r][c]
    ]


def main() -> int:
    gen = load_generator()
    draws = []
    collision_count = 0
    candidate = None
    for seed in range(100):
        for sample_index in range(6):
            grid = gen.generate(seed, sample_index, difficulty=None)
            h, w = len(grid), len(grid[0])
            legend_cols = [c for c in range(w) if grid[h - 2][c] or grid[h - 1][c]][:3]
            srcs = [grid[h - 2][c] for c in legend_cols]
            collided = 9 in srcs
            collision_count += int(collided)
            draws.append({"seed": seed, "sample_index": sample_index, "source_colors": srcs, "reserved_9_collision": collided})
            if collided and candidate is None:
                try:
                    intended, inferred = intended_role_aware(grid)
                except Exception:
                    continue
                if inferred["true_anchors"] and inferred["false_anchor_cells_inside_template"]:
                    candidate = (seed, sample_index, grid, intended, inferred)
    assert candidate is not None
    seed, sample_index, grid, intended, inferred = candidate

    program = canonical_program()
    bridge = RacketBridge(timeout=30)
    try:
        stripped = program.strip()
        if not (stripped.startswith("(rule!") and stripped.endswith(")")):
            raise RuntimeError("canonical program is not a single rule! form")
        callable_text = f"(lambda (g) {stripped[len('(rule!'):-1].strip()})"
        bridge.eval_text(f"(define __audit_rule {callable_text})")
        bridge.define_grid("__audit_input", grid)
        exact = bridge.eval_text("(__audit_rule __audit_input)")
        runtime = bridge.runtime_identity
    finally:
        bridge.shutdown()

    diffs = diff_cells(exact, intended)
    report = {
        "schema": "arc-audit-role-collision-v1",
        "task_id": TASK,
        "status": "defect_reproduced",
        "finding": "reserved anchor color 9 is sampled as a template source color",
        "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
        "canonical_rule_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "sampled_draws": len(draws),
        "draws_with_source_color_9": collision_count,
        "collision_rate": collision_count / len(draws),
        "reproduction": {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": None,
            "input": grid,
            "validator_issues": gen.self_check(grid, difficulty=None),
            "belongs_to_documented_generator_domain": True,
            **inferred,
            "exact_racket_output": exact,
            "role_aware_documented_output": intended,
            "differing_cells": diffs,
            "differing_cell_count": len(diffs),
        },
        "mechanism": {
            "generator": "src_pool contains 9, while 9 is also the hard-coded anchor marker",
            "canonical_rule": "all color-9 cells above the legend are anchors and all color-9 cells are excluded from the template",
            "effect": "template 9s become false anchors and disappear from the template stamped at genuine anchors",
        },
        "racket_runtime": runtime,
        "limitations": ["Finite census over 600 deterministic draws; exact rate is schedule-dependent."],
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "sampled_draws", "draws_with_source_color_9", "collision_rate")}, indent=2))
    print(json.dumps({"seed": seed, "sample_index": sample_index, "diffs": len(diffs)}, indent=2))
    return 0 if diffs else 1


if __name__ == "__main__":
    raise SystemExit(main())
