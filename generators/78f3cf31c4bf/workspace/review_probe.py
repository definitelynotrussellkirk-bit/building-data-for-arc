#!/usr/bin/env python3
"""Source-bound semantic and curriculum probe for 78f3cf31c4bf.

This is intentionally small and portable: it loads the selected sibling
``generator.py``, reads only the canonical public ledger via ``reviewer_support``,
and iterates the generator's *actual* rival registries.  It is useful after a
future edit because it does not copy a stale list of rival names.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "78f3cf31c4bf"
BANDS = ("easy", "medium", "hard")


def _load_generator():
    path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=24)
    parser.add_argument("--indices", type=int, default=12)
    args = parser.parse_args()

    gen, source = _load_generator()
    root = find_root(__file__)
    pairs = canonical_pairs(TASK_ID, root=root)
    rivals = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))
    failures: list[str] = []

    canonical_fit: dict[str, bool] = {}
    for name, rival in rivals.items():
        fit = all(rival(pair["input"]) == pair["output"] for pair in pairs)
        canonical_fit[name] = fit
        if not fit:
            failures.append(f"declared shortcut does not fit every canonical pair: {name}")

    census: dict[str, Any] = {}
    first_witness: dict[str, Any] = {}
    for band in BANDS:
        unique: set[str] = set()
        witness_counts = {name: 0 for name in witnesses}
        strict = 0
        draws = 0
        for seed in range(args.seeds):
            for index in range(args.indices):
                grid = gen.generate(seed, index, difficulty=band)
                draws += 1
                unique.add(_grid_key(grid))
                if gen.self_check(grid) != []:
                    failures.append(f"self_check failed: {band=} {seed=} {index=}")
                if gen.strict_canonical_like(grid) == []:
                    strict += 1
                for name, witness in witnesses.items():
                    if witness(grid):
                        witness_counts[name] += 1
                        first_witness.setdefault(name, {
                            "band": band,
                            "seed": seed,
                            "sample_index": index,
                            "input": grid,
                            "intended_output": gen.rule_mirror(grid),
                        })
        census[band] = {
            "draws": draws,
            "unique_inputs": len(unique),
            "strict_matches": strict,
            "witness_counts": witness_counts,
        }

    lesson_failures: list[dict[str, Any]] = []
    # Cover every starting residue more than once, including wrap-around into
    # the next six-slot schedule cycle.  The fourth pair is rotated into query.
    for band in BANDS:
        examples = []
        for index in range(args.indices + 3):
            grid = gen.generate(7000, index, difficulty=band)
            examples.append({"input": grid, "output": gen.rule_mirror(grid)})
        for start in range(args.indices):
            reasons = gen.lesson_identifiable(
                examples[start : start + gen.EXAMPLES_NEEDED],
                examples[start + gen.EXAMPLES_NEEDED],
            )
            if reasons:
                lesson_failures.append({"band": band, "start": start, "reasons": reasons})
    if lesson_failures:
        failures.append(f"{len(lesson_failures)} cyclic lesson window(s) left a rival alive")

    report = {
        "schema": "78f3cf31c4bf-review-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "canonical_pairs": len(pairs),
        "declared_rivals": sorted(rivals),
        "canonical_fit": canonical_fit,
        "census": census,
        "lesson_policy": {
            "examples_needed": gen.EXAMPLES_NEEDED,
            "seed": 7000,
            "starts_per_band": args.indices,
            "query_rotation": "three consecutive demos followed by the next generated pair",
        },
        "lesson_failures": lesson_failures,
        "first_witness": first_witness,
        "failures": failures,
        "passed": not failures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "passed": report["passed"],
        "generator_sha256": report["generator_sha256"],
        "draws": sum(row["draws"] for row in census.values()),
        "lesson_windows": len(BANDS) * args.indices,
        "failures": len(failures),
        "out": str(args.out),
    }, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
