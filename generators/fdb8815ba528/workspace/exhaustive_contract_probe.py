#!/usr/bin/env python3
"""Exhaustively verify every declared exact-axis combination.

This is reviewer tooling, not production code. It independently observes the
returned grid, checks the public validator, compares the production mirror with
an independent oracle, and records replayable failures.
"""
from __future__ import annotations

import argparse
from itertools import product
import json
from pathlib import Path
from typing import Any

from reference_probe import load_generator, observe, oracle


def run(generator_path: str | None, seeds: int) -> dict[str, Any]:
    gen = load_generator(generator_path)
    bands = (None, "easy", "medium", "hard")
    failures: list[dict[str, Any]] = []
    total = 0
    for band, profile, n_blobs, relation, edge, palette, seed in product(
        bands,
        gen.SCENE_PROFILES,
        gen.N_BLOBS,
        gen.COLOR_RELATIONS,
        gen.EDGE_MODES,
        gen.PALETTE_KINDS,
        range(seeds),
    ):
        requested = {
            "scene_profile": profile,
            "n_blobs": n_blobs,
            "color_relation": relation,
            "edge_mode": edge,
            "palette_kind": palette,
        }
        total += 1
        try:
            grid = gen.generate(seed, seed + 7, difficulty=band, **requested)
            errors = gen.self_check(grid, meta={"overrides": requested})
            observed = observe(grid)
            independent = oracle(grid)
            mirrored = gen.rule_mirror(grid)
            if errors or observed != requested or independent != mirrored or independent == grid:
                failures.append({
                    "difficulty": band,
                    "seed": seed,
                    "sample_index": seed + 7,
                    "requested": requested,
                    "observed": observed,
                    "self_check_errors": errors,
                    "oracle_matches_rule_mirror": independent == mirrored,
                    "nontrivial": independent != grid,
                    "input": grid,
                })
        except Exception as exc:  # retained as replay evidence
            failures.append({
                "difficulty": band,
                "seed": seed,
                "sample_index": seed + 7,
                "requested": requested,
                "exception": f"{type(exc).__name__}: {exc}",
            })
    return {
        "schema": "fdb8815ba528-exhaustive-contract-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "seeds_per_combination": seeds,
        "total_cases": total,
        "failure_count": len(failures),
        "passed": not failures,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", help="optional generator.py under test")
    parser.add_argument("--seeds", type=int, default=6)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run(args.generator, args.seeds)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(json.dumps({k: result[k] for k in ("total_cases", "failure_count", "passed")}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
