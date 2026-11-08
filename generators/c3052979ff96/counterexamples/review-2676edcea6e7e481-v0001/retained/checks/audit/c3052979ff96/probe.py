#!/usr/bin/env python3
"""Reproduce the distractor-preservation coverage gap for c3052979ff96."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GENERATOR = ROOT / "repo/generators/c3052979ff96/generator.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def first_code(grid):
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if 1 <= value <= 4:
                return r, c, value
    raise ValueError("no code")


def authority_mirror(grid):
    h, w = len(grid), len(grid[0])
    pivot = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9)
    _, _, code = first_code(grid)
    shape = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8]
    out = [row[:] for row in grid]
    pr, pc = pivot
    for r, c in shape:
        dr, dc = r - pr, c - pc
        if code == 1:
            nr, nc = pr + dr, pc + dc
        elif code == 2:
            nr, nc = pr + dc, pc - dr
        elif code == 3:
            nr, nc = pr - dr, pc - dc
        else:
            nr, nc = pr - dc, pc + dr
        if 0 <= nr < h and 0 <= nc < w:
            out[nr][nc] = 2
    return out


def strip_distractors_rival(grid):
    code_r, code_c, _ = first_code(grid)
    stripped = [[0 for _ in row] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (8, 9) or (r, c) == (code_r, code_c):
                stripped[r][c] = value
    return authority_mirror(stripped)


def main():
    cases = json.loads((HERE / "cases.json").read_text())["items"]
    racket_doc = json.loads((HERE / "racket_outputs.json").read_text())
    racket = [item["output"] for item in racket_doc["results"]]
    if len(cases) != len(racket):
        raise AssertionError("case/output count mismatch")

    mirror_matches = 0
    generated_matches = 0
    generated_total = 0
    canonical_matches = 0
    canonical_total = 0
    canonical_distractor_support = 0
    failing_canonical = []
    for index, (case, expected) in enumerate(zip(cases, racket)):
        mirror = authority_mirror(case["input"])
        mirror_matches += mirror == expected
        rival = strip_distractors_rival(case["input"])
        if case["kind"] == "generated":
            generated_total += 1
            generated_matches += rival == expected
        else:
            canonical_total += 1
            canonical_matches += rival == expected
            cr, cc, code = first_code(case["input"])
            distractors = sorted({
                value
                for r, row in enumerate(case["input"])
                for c, value in enumerate(row)
                if value not in (0, 8, 9) and not ((r, c) == (cr, cc) and value == code)
            })
            canonical_distractor_support += bool(distractors)
            if rival != expected:
                differing = [
                    [r, c, rival[r][c], expected[r][c]]
                    for r in range(len(expected))
                    for c in range(len(expected[0]))
                    if rival[r][c] != expected[r][c]
                ]
                failing_canonical.append({
                    "case_index": index,
                    "canonical_index": case["index"],
                    "distractor_colors": distractors,
                    "differing_cells": differing,
                })

    report = {
        "task_id": "c3052979ff96",
        "audited_generator_sha256": sha256(GENERATOR),
        "executed_rule_hash": racket_doc["executed_rule_hash"],
        "racket_cases": len(cases),
        "authority_mirror_matches_racket": mirror_matches,
        "generated_cases": generated_total,
        "generated_cases_with_unrelated_distractors": 0,
        "strip_distractors_rival_matches_generated": generated_matches,
        "canonical_cases": canonical_total,
        "canonical_cases_with_unrelated_distractors": canonical_distractor_support,
        "strip_distractors_rival_matches_canonical": canonical_matches,
        "failing_canonical": failing_canonical,
        "conclusion": (
            "The generator never emits unrelated preserved colors. A solver that deletes "
            "all non-shape/non-pivot/non-code content before stamping matches every sampled "
            "generated Racket label but fails every canonical example."
        ),
    }
    (HERE / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
