#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_pairs

TASK = "c4d63d8b4567"
HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3] / "repo"
GEN_PATH = ROOT / "generators" / TASK / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_c4", GEN_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def repeated_horizontal_only(grid):
    """Plausible wrong rule: repeated colors may fire horizontally, never vertically."""
    source = [list(row) for row in grid]
    out = [row[:] for row in source]
    h, w = len(source), len(source[0])
    counts = Counter(value for row in source for value in row if value)
    colors = list(counts)
    for r in range(h):
        for color in colors:
            cols = [c for c in range(w) if source[r][c] == color]
            if len(cols) == 2:
                lo, hi = min(cols), max(cols)
                if all(source[r][c] == 0 for c in range(lo + 1, hi)):
                    for c in range(lo, hi + 1):
                        out[r][c] = color
    for c in range(w):
        for color in colors:
            if counts[color] != 2:
                continue
            rows = [r for r in range(h) if source[r][c] == color]
            if len(rows) == 2:
                lo, hi = min(rows), max(rows)
                if all(source[r][c] == 0 for r in range(lo + 1, hi)):
                    for r in range(lo, hi + 1):
                        out[r][c] = color
    return out


def main():
    gen = load_generator()
    counterexample = json.loads((HERE / "input.json").read_text())
    authority = json.loads((HERE / "racket.json").read_text())["results"][0]["output"]

    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    canonical_matches = sum(
        repeated_horizontal_only(pair["input"]) == pair["output"] for pair in canonical
    )

    generated_total = generated_matches = vertical_repeated = horizontal_repeated = 0
    for band in ("easy", "medium", "hard"):
        for seed in range(50):
            for index in range(4):
                grid = gen.generate(seed, index, difficulty=band)
                intended = gen.rule_mirror(grid)
                generated_total += 1
                generated_matches += repeated_horizontal_only(grid) == intended
                analysis = gen._analyze(grid)
                for record in analysis.get("repeated") or []:
                    horizontal_repeated += record["orientation"] == "H"
                    vertical_repeated += record["orientation"] == "V"

    rival_output = repeated_horizontal_only(counterexample)
    report = {
        "schema": "c4d63d8b4567-vertical-repetition-shortcut-audit-v1",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "rival": "apply the normal rule, but for colors repeated globally only allow horizontal pairs",
        "canonical": {"pairs": len(canonical), "rival_matches": canonical_matches},
        "generated": {
            "bands": ["easy", "medium", "hard"],
            "seeds": "0..49",
            "sample_indices": "0..3",
            "cases": generated_total,
            "rival_matches": generated_matches,
            "horizontal_repeated_records": horizontal_repeated,
            "vertical_repeated_records": vertical_repeated,
        },
        "counterexample": {
            "input": counterexample,
            "self_check": gen.self_check(counterexample),
            "authority_output": authority,
            "rival_output": rival_output,
            "outputs_differ": authority != rival_output,
            "different_cells": [
                [r, c, authority[r][c], rival_output[r][c]]
                for r in range(len(authority))
                for c in range(len(authority[0]))
                if authority[r][c] != rival_output[r][c]
            ],
        },
    }
    (HERE / "vertical_repetition_probe.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if (
        canonical_matches == len(canonical)
        and generated_matches == generated_total
        and vertical_repeated == 0
        and authority != rival_output
        and not report["counterexample"]["self_check"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
