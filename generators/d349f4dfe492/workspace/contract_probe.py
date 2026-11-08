#!/usr/bin/env python3
"""Source-bound contract and curriculum probe for d349f4dfe492.

Run from the repository root (or anywhere inside the packet):

    python3 generators/d349f4dfe492/workspace/contract_probe.py \
        --out ../checks/contract-probe.json

The probe does not invoke the private Racket authority.  It checks the Python
mirror against all canonical pairs, proves the complete advertised exact-axis
Cartesian product is constructible, verifies every cyclic three-demo window
against the generator's *actual declared rivals*, and reports distribution
coverage.  A nonzero exit means at least one reproducible contract failed.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "d349f4dfe492"
HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
sys.path.insert(0, str(REPO / "src"))

from reviewer_support import canonical_pairs  # noqa: E402


def load_generator():
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--lesson-starts", type=int, default=30)
    parser.add_argument("--distribution-draws", type=int, default=100)
    args = parser.parse_args()

    gen = load_generator()
    failures: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "schema": "d349f4dfe492-contract-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "failures": failures,
    }

    # Canonical parity and canonical-shortcut calibration.
    canonical = canonical_pairs(TASK_ID, root=REPO)
    canonical_rows = []
    for index, pair in enumerate(canonical):
        source = copy.deepcopy(pair["input"])
        row = {
            "index": index,
            "split": pair["split"],
            "shape": [len(source), len(source[0])],
            "self_check": gen.self_check(source),
            "strict": gen.strict_canonical_like(source),
            "mirror_matches": gen.rule_mirror(source) == pair["output"],
            "input_immutable": source == pair["input"],
            "shortcut_matches": {
                name: rival(source) == pair["output"]
                for name, rival in gen.CANONICAL_SHORTCUTS.items()
            },
        }
        canonical_rows.append(row)
        if row["self_check"] or row["strict"] or not row["mirror_matches"] or not row["input_immutable"]:
            failures.append({"kind": "canonical_parity", "index": index, "detail": row})
        missed = [name for name, matched in row["shortcut_matches"].items() if not matched]
        if missed:
            failures.append({"kind": "misdeclared_canonical_shortcut", "index": index, "rivals": missed})
    report["canonical"] = canonical_rows

    # Exhaust the full advertised exact-axis Cartesian product in every band.
    axis_failures = []
    axis_draws = 0
    for difficulty in (None, "easy", "medium", "hard"):
        for h in range(7, 19):
            for w in range(7, 19):
                for n_seeds in range(1, 6):
                    axis_draws += 1
                    options = {"grid_h": h, "grid_w": w, "n_seeds": n_seeds}
                    try:
                        grid = gen.generate(
                            seed=100_000 + axis_draws,
                            sample_index=axis_draws,
                            difficulty=difficulty,
                            **options,
                        )
                        observed = gen.observe_overrides(grid)
                        errors = gen.self_check(grid)
                        if observed != options or errors:
                            axis_failures.append(
                                {
                                    "difficulty": difficulty,
                                    "options": options,
                                    "observed": observed,
                                    "errors": errors,
                                }
                            )
                    except Exception as exc:  # keep exact reproducer
                        axis_failures.append(
                            {
                                "difficulty": difficulty,
                                "options": options,
                                "exception": repr(exc),
                            }
                        )
    if axis_failures:
        failures.append({"kind": "axis_cartesian_product", "count": len(axis_failures)})
    report["axis_cartesian_product"] = {
        "draws": axis_draws,
        "failures": axis_failures,
    }

    # Every cyclic lesson start must refute the actual declared competitors.
    lesson_rows = []
    for difficulty in ("easy", "medium", "hard"):
        for start in range(args.lesson_starts):
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(
                    seed=200_000 + start * 100 + offset,
                    sample_index=start + offset,
                    difficulty=difficulty,
                )
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                seed=300_000 + start,
                sample_index=start + gen.EXAMPLES_NEEDED,
                difficulty=difficulty,
            )
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            reasons = gen.lesson_identifiable(demos, query)
            survivors = [
                name
                for name, rival in gen.LESSON_COMPETITORS.items()
                if all(rival(pair["input"]) == pair["output"] for pair in demos)
            ]
            profiles = [
                gen.schedule_profile(0, start + offset, difficulty=difficulty)
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            row = {
                "difficulty": difficulty,
                "start": start,
                "profiles": profiles,
                "reasons": reasons,
                "surviving_rivals": survivors,
            }
            lesson_rows.append(row)
            if reasons or survivors:
                failures.append({"kind": "lesson_window", "detail": row})
    report["lesson_windows"] = {
        "count": len(lesson_rows),
        "rows": lesson_rows,
    }

    # Distribution coverage with exact denominators and unique-input counts.
    distribution = {}
    for difficulty in ("easy", "medium", "hard"):
        profile_counts: Counter[str] = Counter()
        seed_counts: Counter[int] = Counter()
        clipped = 0
        repeated = 0
        strict = 0
        unique = set()
        witness_counts: Counter[str] = Counter()
        for index in range(args.distribution_draws):
            grid = gen.generate(400_000 + index, index, difficulty=difficulty)
            unique.add(frozen(grid))
            profile = gen.schedule_profile(400_000 + index, index, difficulty=difficulty)
            profile_counts[profile] += 1
            seeds = gen._seed_cells(grid)
            seed_counts[len(seeds)] += 1
            h, w = len(grid), len(grid[0])
            if any(r in (0, h - 1) or c in (0, w - 1) for r, c, _ in seeds):
                clipped += 1
            colors = [value for _r, _c, value in seeds]
            if len(set(colors)) < len(colors):
                repeated += 1
            if not gen.strict_canonical_like(grid):
                strict += 1
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                if witness(grid):
                    witness_counts[name] += 1
        distribution[difficulty] = {
            "draws": args.distribution_draws,
            "unique_inputs": len(unique),
            "profiles": dict(sorted(profile_counts.items())),
            "seed_counts": {str(k): v for k, v in sorted(seed_counts.items())},
            "clipped": clipped,
            "repeated_colors": repeated,
            "strict": strict,
            "witness_counts": dict(sorted(witness_counts.items())),
        }
        if strict != args.distribution_draws:
            failures.append({"kind": "strict_fraction", "difficulty": difficulty, "strict": strict})
        missing_profiles = set(gen.SCHEDULE_PROFILES) - set(profile_counts)
        if missing_profiles:
            failures.append({"kind": "profile_coverage", "difficulty": difficulty, "missing": sorted(missing_profiles)})
        missing_witnesses = [name for name, count in witness_counts.items() if count == 0]
        if missing_witnesses:
            failures.append({"kind": "witness_coverage", "difficulty": difficulty, "missing": missing_witnesses})
    report["distribution"] = distribution

    # Reproducibility/freshness/global-RNG guard.
    random.seed(918273)
    before = random.getstate()
    first = gen.generate(41, 17, difficulty="hard")
    after = random.getstate()
    second = gen.generate(41, 17, difficulty="hard")
    freshness = {
        "global_rng_unchanged": before == after,
        "deterministic": first == second,
        "fresh_outer": first is not second,
        "fresh_rows": all(a is not b for a, b in zip(first, second)),
    }
    report["reproducibility"] = freshness
    if not all(freshness.values()):
        failures.append({"kind": "reproducibility", "detail": freshness})

    report["passed"] = not failures
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")

    if failures:
        print(f"FAIL: {len(failures)} contract failure(s)", file=sys.stderr)
        return 1
    print(
        f"PASS: canonical={len(canonical)} axis_draws={axis_draws} "
        f"lesson_windows={len(lesson_rows)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
