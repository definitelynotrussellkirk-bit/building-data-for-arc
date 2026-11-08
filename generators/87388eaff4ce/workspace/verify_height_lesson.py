#!/usr/bin/env python3
"""Reproducible semantic probe for the 87388eaff4ce lesson contract.

This tool is deliberately source-bound: it imports the selected generator,
iterates whatever witnesses/rivals it currently declares, verifies the local
mirror on every labeled canonical pair, and checks a fixed generated census.
Pass ``--run-racket`` to compare the same inputs with the protected authority.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]
ROOT = next(
    parent for parent in HERE.parents
    if (parent / "shared" / "runtime" / "reviewer_support.py").exists()
)
RUNTIME = ROOT / "shared" / "runtime"
SRC = ROOT / "src"
for path in (str(SRC), str(RUNTIME)):
    if path not in sys.path:
        sys.path.insert(0, path)

from reviewer_support import canonical_pairs  # noqa: E402

TASK_ID = "87388eaff4ce"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"height_lesson_probe_{TASK_ID}", TASK_DIR / "generator.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load selected generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def counterexample_grid() -> list[list[int]]:
    grid = [[0] * 12 for _ in range(9)]
    for r in range(4):
        grid[1 + r][8] = 5
    for r, c in ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)):
        grid[1 + r][1 + c] = 9
    for r, c in ((0, 0), (0, 1), (1, 0), (1, 1)):
        grid[6 + r][4 + c] = 2
    return grid


def build_report(*, run_racket: bool = False) -> dict[str, Any]:
    gen = _load_generator()
    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    canonical_rows = []
    for pair in canonical:
        mirror = gen.rule_mirror(pair["input"])
        canonical_rows.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "self_check": gen.self_check(pair["input"]),
                "mirror_exact": mirror == pair["output"],
            }
        )

    generated_rows = []
    for band in ("easy", "medium", "hard"):
        for index in range(24):
            grid = gen.generate(873_000 + index, index, difficulty=band)
            intended = gen.rule_mirror(grid)
            witness_results = {
                name: bool(predicate(grid))
                for name, predicate in gen.SEMANTIC_WITNESSES.items()
            }
            rival_results = {
                name: rival(grid) != intended
                for name, rival in gen.SEMANTIC_RIVALS.items()
            }
            generated_rows.append(
                {
                    "band": band,
                    "sample_index": index,
                    "profile": gen.schedule_profile(873_000 + index, index, band),
                    "input_dims": [len(grid), len(grid[0])],
                    "output_dims": [len(intended), len(intended[0])],
                    "lawful": gen.self_check(grid, difficulty=band) == [],
                    "witnesses": witness_results,
                    "rivals_disagree": rival_results,
                }
            )

    witness = counterexample_grid()
    witness_intended = gen.rule_mirror(witness)
    witness_rivals = {
        name: {
            "disagrees": rival(witness) != witness_intended,
            "output": rival(witness),
        }
        for name, rival in gen.SEMANTIC_RIVALS.items()
    }

    report: dict[str, Any] = {
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "canonical": {
            "pairs": canonical_rows,
            "all_self_check": all(not row["self_check"] for row in canonical_rows),
            "all_mirror_exact": all(row["mirror_exact"] for row in canonical_rows),
        },
        "generated": {
            "rows": generated_rows,
            "all_lawful": all(row["lawful"] for row in generated_rows),
            "all_witnesses_fire": all(
                all(row["witnesses"].values()) for row in generated_rows
            ),
            "every_declared_rival_refuted": all(
                all(row["rivals_disagree"].values()) for row in generated_rows
            ),
            "unique_inputs": len(
                {json.dumps(row, sort_keys=True) for row in generated_rows}
            ),
        },
        "counterexample": {
            "input": witness,
            "self_check": gen.self_check(witness),
            "intended": witness_intended,
            "rivals": witness_rivals,
            "intended_differs_from_every_declared_rival": all(
                item["disagrees"] for item in witness_rivals.values()
            ),
        },
    }

    if run_racket:
        from arcpuzzles import Catalog

        grids = [pair["input"] for pair in canonical]
        grids.append(witness)
        grids.extend(
            gen.generate(873_000 + index, index, difficulty="medium")
            for index in range(8)
        )
        applied = Catalog().apply(TASK_ID, grids, timeout=180)
        report["racket"] = {
            "rule_hash_matches_catalog": applied["rule_hash_matches_catalog"],
            "all_valid": all(
                item["valid_output"] and item["error"] is None
                for item in applied["results"]
            ),
            "all_match_mirror": all(
                item["output"] == gen.rule_mirror(item["input"])
                for item in applied["results"]
                if item["output"] is not None
            ),
            "results": applied["results"],
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-racket", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(run_racket=args.run_racket)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    ok = (
        report["canonical"]["all_self_check"]
        and report["canonical"]["all_mirror_exact"]
        and report["generated"]["all_lawful"]
        and report["generated"]["all_witnesses_fire"]
        and report["generated"]["every_declared_rival_refuted"]
        and report["counterexample"]["intended_differs_from_every_declared_rival"]
    )
    if args.run_racket:
        ok = ok and report["racket"]["all_valid"] and report["racket"]["all_match_mirror"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
