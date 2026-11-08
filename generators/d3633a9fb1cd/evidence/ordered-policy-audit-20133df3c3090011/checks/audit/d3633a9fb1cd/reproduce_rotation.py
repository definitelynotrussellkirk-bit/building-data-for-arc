#!/usr/bin/env python3
"""Reproduce a source-bound arbitrary-query-rotation hole for d3633a9fb1cd."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import find_root, load_selected_generator

TASK = "d3633a9fb1cd"
SEED = 3226059948
DIFFICULTY = "easy"
SAMPLE_INDICES = [1, 2, 3, 4]
ROTATED_QUERY_INDEX = 2
RIVALS = ("component_manhattan", "tie_break_low_color")


def _sha_grid(grid) -> str:
    raw = json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("choose a new output file")

    root = find_root(__file__)
    module, source, source_sha = load_selected_generator(TASK, root=root)
    grids = [module.generate(SEED, index, difficulty=DIFFICULTY) for index in SAMPLE_INDICES]
    checks = [module.self_check(grid, difficulty=DIFFICULTY) for grid in grids]
    assert all(not errors for errors in checks), checks

    applied = Catalog(root).apply(TASK, grids, timeout=120)
    assert applied["rule_hash_matches_catalog"] is True
    pairs = []
    for sample_index, row in zip(SAMPLE_INDICES, applied["results"]):
        assert row["output"] is not None
        pairs.append({
            "sample_index": sample_index,
            "input": row["input"],
            "output": row["output"],
            "input_sha256": _sha_grid(row["input"]),
        })

    competitors = module.LESSON_COMPETITORS
    missing = [name for name in RIVALS if name not in competitors]
    assert not missing, missing

    production_demos, production_query = pairs[:3], pairs[3]
    production = {}
    for name in RIVALS:
        fn = competitors[name]
        demo_fit = [fn(pair["input"]) == pair["output"] for pair in production_demos]
        query_prediction = fn(production_query["input"])
        production[name] = {
            "demo_fit": demo_fit,
            "fits_all_demos": all(demo_fit),
            "query_differs": query_prediction != production_query["output"],
        }
        assert not (all(demo_fit) and query_prediction != production_query["output"])

    rotated_query = pairs[ROTATED_QUERY_INDEX]
    rotated_demos = [pair for index, pair in enumerate(pairs) if index != ROTATED_QUERY_INDEX]
    rotation = {}
    for name in RIVALS:
        fn = competitors[name]
        demo_fit = [fn(pair["input"]) == pair["output"] for pair in rotated_demos]
        query_prediction = fn(rotated_query["input"])
        rotation[name] = {
            "demo_sample_indices": [pair["sample_index"] for pair in rotated_demos],
            "demo_fit": demo_fit,
            "fits_all_demos": all(demo_fit),
            "query_sample_index": rotated_query["sample_index"],
            "query_expected": rotated_query["output"],
            "query_prediction": query_prediction,
            "query_differs": query_prediction != rotated_query["output"],
        }
        assert all(demo_fit)
        assert query_prediction != rotated_query["output"]

    report = {
        "schema": "arcpuzzles-audit-rotation-reproducer-v1",
        "task_id": TASK,
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": source_sha,
        "seed": SEED,
        "difficulty": DIFFICULTY,
        "sample_indices": SAMPLE_INDICES,
        "production_query_index": 3,
        "rotated_query_index": ROTATED_QUERY_INDEX,
        "self_checks": checks,
        "executed_rule_hash": applied["executed_rule_hash"],
        "rule_text_sha256": applied["rule_text_sha256"],
        "rule_hash_matches_catalog": applied["rule_hash_matches_catalog"],
        "production": production,
        "rotation": rotation,
        "pairs": pairs,
        "classification": (
            "ordered production lesson is identifiable for the declared rivals; "
            "holding out sample_index 3 instead leaves both declared rivals alive"
        ),
        "limits": (
            "One exact 3-demo/1-query lesson and one query rotation; the separate "
            "100-per-band census measures prevalence. No target source was edited."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": str(args.out),
        "generator_sha256": source_sha,
        "production_ambiguous": any(
            row["fits_all_demos"] and row["query_differs"] for row in production.values()
        ),
        "rotation_ambiguous_rivals": [
            name for name, row in rotation.items()
            if row["fits_all_demos"] and row["query_differs"]
        ],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
