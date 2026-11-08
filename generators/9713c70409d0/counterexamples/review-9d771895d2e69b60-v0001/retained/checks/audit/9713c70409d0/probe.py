#!/usr/bin/env python3
"""Reproduce the row-then-column versus column-then-row curriculum gap."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from collections import defaultdict
from pathlib import Path

from reviewer_support import canonical_pairs

TASK = "9713c70409d0"
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ["ARCPUZZLES_HOME"]).resolve()
SOURCE = ROOT / "generators" / TASK / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def points_by_color(grid):
    result = defaultdict(set)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                result[color].add((r, c))
    return dict(result)


def row_close(cells):
    by_row = defaultdict(list)
    for r, c in cells:
        by_row[r].append(c)
    return {(r, c) for r, cols in by_row.items() for c in range(min(cols), max(cols) + 1)}


def col_close(cells):
    by_col = defaultdict(list)
    for r, c in cells:
        by_col[c].append(r)
    return {(r, c) for c, rows in by_col.items() for r in range(min(rows), max(rows) + 1)}


def matrix(grid, close_fn):
    points = points_by_color(grid)
    colors = sorted(points)
    occupied = {color: close_fn(points[color]) for color in colors}
    return [
        [5 if i == j else (8 if occupied[a] & occupied[b] else 0)
         for j, b in enumerate(colors)]
        for i, a in enumerate(colors)
    ]


def intended(grid):
    return matrix(grid, lambda cells: col_close(row_close(cells)))


def column_then_row_rival(grid):
    return matrix(grid, lambda cells: row_close(col_close(cells)))


def main() -> int:
    gen = load_generator()
    canon = canonical_pairs(TASK, root=ROOT)
    canonical = []
    for index, pair in enumerate(canon):
        actual = intended(pair["input"])
        rival = column_then_row_rival(pair["input"])
        canonical.append({
            "pair": index,
            "intended_matches_label": actual == pair["output"],
            "rival_matches_label": rival == pair["output"],
            "rival_agrees_with_intended": rival == actual,
        })

    draws = []
    aggregate = {"draws": 0, "rival_agrees": 0, "self_check_errors": 0}
    for band_i, band in enumerate(("easy", "medium", "hard")):
        for index in range(80):
            seed = 973000 + band_i * 1000 + index
            grid = gen.generate(seed, index, difficulty=band)
            agree = column_then_row_rival(grid) == intended(grid)
            errors = gen.self_check(grid)
            draws.append({
                "band": band,
                "seed": seed,
                "sample_index": index,
                "profile": gen.observe_overrides(grid)["scene_profile"],
                "rival_agrees": agree,
                "self_check": errors,
            })
            aggregate["draws"] += 1
            aggregate["rival_agrees"] += int(agree)
            aggregate["self_check_errors"] += int(bool(errors))

    witness = json.loads((HERE / "witness_input.json").read_text())
    witness_result = {
        "self_check": gen.self_check(witness),
        "strict_canonical_like": gen.strict_canonical_like(witness),
        "intended": intended(witness),
        "generator_rule_mirror": gen.rule_mirror(witness),
        "rival": column_then_row_rival(witness),
        "disagrees": intended(witness) != column_then_row_rival(witness),
    }
    result = {
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "canonical_pairs": canonical,
        "canonical_rival_matches": sum(r["rival_matches_label"] for r in canonical),
        "canonical_pair_count": len(canonical),
        "generated_aggregate": aggregate,
        "witness": witness_result,
        "scope": "240 production draws: 80 per explicit difficulty; finite evidence only",
    }
    (HERE / "probe.json").write_text(json.dumps({"result": result, "draws": draws}, indent=2) + "\n")
    (HERE / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
