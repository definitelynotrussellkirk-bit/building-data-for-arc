#!/usr/bin/env python3
"""Source-bound semantic contract probe for generator 7147e98f8173.

Run from any packet/repository layout with the reviewer runtime on PYTHONPATH:

    python3 generators/7147e98f8173/workspace/probe_contract.py --seed 915

The probe does not consult private query labels.  It materializes the generator's
own labelled lessons with its independent Python rule mirror, checks every query
holdout against the declared lesson hook, and verifies that every declared rival
is refuted somewhere in the sampled curriculum.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root, load_selected_generator

TASK_ID = "7147e98f8173"
BANDS = ("easy", "medium", "hard")


def probe(*, seed: int = 915) -> dict[str, Any]:
    """Return a compact, JSON-serializable contract report; raise on source errors."""
    root = find_root(__file__)
    gen, source_path, source_sha = load_selected_generator(TASK_ID, root=root)

    failures: list[dict[str, Any]] = []
    rival_refutations: dict[str, int] = {name: 0 for name in gen.LESSON_COMPETITORS}
    band_counts: dict[str, int] = {}
    rotations_checked = 0

    for band in BANDS:
        pairs = []
        for sample_index in range(gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(seed, sample_index, difficulty=band)
            errors = gen.self_check(grid, difficulty=band)
            if errors:
                failures.append(
                    {
                        "band": band,
                        "sample_index": sample_index,
                        "kind": "self_check",
                        "reasons": errors,
                    }
                )
            observed = gen.observe_overrides(grid)
            if not observed:
                failures.append(
                    {
                        "band": band,
                        "sample_index": sample_index,
                        "kind": "unobservable_axes",
                    }
                )
            output = gen.rule_mirror(grid)
            pairs.append({"input": grid, "output": output})
            for name, rival in gen.LESSON_COMPETITORS.items():
                if rival(grid) != output:
                    rival_refutations[name] += 1

        band_counts[band] = len(pairs)
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            reasons = gen.lesson_identifiable(demos, query)
            rotations_checked += 1
            if reasons:
                failures.append(
                    {
                        "band": band,
                        "query_index": query_index,
                        "kind": "lesson_identifiability",
                        "reasons": reasons,
                    }
                )

    missing_refutations = sorted(name for name, count in rival_refutations.items() if count == 0)
    if missing_refutations:
        failures.append({"kind": "unrefuted_rivals", "names": missing_refutations})

    return {
        "schema": "arc-generator-contract-probe-v1",
        "task_id": TASK_ID,
        "generator_path": Path(source_path).relative_to(root).as_posix(),
        "generator_sha256": source_sha,
        "seed": seed,
        "bands": band_counts,
        "examples_per_lesson": gen.EXAMPLES_NEEDED,
        "queries_per_band": gen.EXAMPLES_NEEDED + 1,
        "lesson_rotations_checked": rotations_checked,
        "lesson_failures": failures,
        "rival_refutation_counts": rival_refutations,
        "rivals_refuted": sorted(name for name, count in rival_refutations.items() if count > 0),
        "status": "pass" if not failures else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=915)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = probe(seed=args.seed)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
