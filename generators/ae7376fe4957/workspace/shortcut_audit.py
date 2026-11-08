#!/usr/bin/env python3
"""Audit declared shortcut rivals and lesson-query rotations for ae7376fe4957.

The tool deliberately reads rival declarations from the generator instead of
copying a name list.  It reports which shortcuts fit all canonical pairs, finds
one generated refutation per declared shortcut, and checks every query position
in deterministic four-pair lesson windows.
"""
from __future__ import annotations

import argparse
import importlib
import json
from typing import Any

from reviewer_support import canonical_pairs, find_root


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.ae7376fe4957.generator"
)
BANDS = ("easy", "medium", "hard")


def _pair(grid: list[list[int]]) -> dict[str, Any]:
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def _rival_prediction(rival, grid):
    try:
        return {"status": "ok", "output": rival(grid)}
    except Exception as exc:  # Audit output should retain rival failures.
        return {
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }


def audit(*, seed_count: int = 16, start_count: int = 48) -> dict[str, Any]:
    """Return a JSON-serializable shortcut and rotation audit report."""
    if seed_count < 1 or start_count < 1:
        raise ValueError("seed_count and start_count must both be positive")

    root = find_root(__file__)
    canonical = canonical_pairs(GEN.TASK_ID, root=root)
    shortcuts = dict(GEN.CANONICAL_SHORTCUTS)

    canonical_results: dict[str, Any] = {}
    canonical_fitting: list[str] = []
    for name, rival in shortcuts.items():
        pair_results = []
        fits = True
        for index, pair in enumerate(canonical):
            prediction = _rival_prediction(rival, pair["input"])
            matches = prediction.get("output") == pair["output"]
            pair_results.append(
                {
                    "pair_index": index,
                    "status": prediction["status"],
                    "matches": matches,
                    **({"error": prediction["error"]} if "error" in prediction else {}),
                }
            )
            fits = fits and prediction["status"] == "ok" and matches
        canonical_results[name] = {"fits_all": fits, "pairs": pair_results}
        if fits:
            canonical_fitting.append(name)

    generated_refutations: dict[str, Any] = {name: None for name in shortcuts}
    sample_limit = start_count + GEN.EXAMPLES_NEEDED
    for band in BANDS:
        for seed in range(seed_count):
            for sample_index in range(sample_limit):
                grid = GEN.generate(seed, sample_index, difficulty=band)
                official = GEN.rule_mirror(grid)
                for name, rival in shortcuts.items():
                    if generated_refutations[name] is not None:
                        continue
                    prediction = _rival_prediction(rival, grid)
                    if prediction["status"] == "ok" and prediction["output"] != official:
                        generated_refutations[name] = {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "input": grid,
                            "official_output": official,
                            "rival_output": prediction["output"],
                        }
                if all(generated_refutations.values()):
                    break
            if all(generated_refutations.values()):
                break
        if all(generated_refutations.values()):
            break

    rotation_failures: list[dict[str, Any]] = []
    rotations_checked = 0
    lesson_size = GEN.EXAMPLES_NEEDED + 1
    for band in BANDS:
        for seed in range(seed_count):
            for start in range(start_count):
                pairs = [
                    _pair(GEN.generate(seed, index, difficulty=band))
                    for index in range(start, start + lesson_size)
                ]
                for query_index, query in enumerate(pairs):
                    demos = [
                        pair for index, pair in enumerate(pairs) if index != query_index
                    ]
                    findings = GEN.lesson_identifiable(demos, query)
                    rotations_checked += 1
                    if findings:
                        rotation_failures.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "findings": findings,
                                "train_indices": [
                                    index
                                    for index in range(lesson_size)
                                    if index != query_index
                                ],
                                "query": query,
                            }
                        )

    return {
        "schema": "ae7376fe4957-shortcut-audit-v1",
        "task_id": GEN.TASK_ID,
        "generator_version": GEN.VERSION,
        "declared_rule_hash": GEN.RULE_HASH,
        "declared_shortcuts": list(shortcuts),
        "canonical_pair_count": len(canonical),
        "canonical_results": canonical_results,
        "canonical_fitting_shortcuts": canonical_fitting,
        "generated_refutations": generated_refutations,
        "rotation_policy": "hold out each pair once from ordered four-pair windows",
        "seed_count": seed_count,
        "start_count_per_band": start_count,
        "rotations_checked": rotations_checked,
        "rotation_failures": rotation_failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=16, help="seeds per band")
    parser.add_argument(
        "--starts", type=int, default=48, help="lesson starts per seed and band"
    )
    parser.add_argument("--out", help="write JSON to this path instead of stdout")
    args = parser.parse_args()

    report = audit(seed_count=args.seeds, start_count=args.starts)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        print(text, end="")
    return 1 if report["rotation_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
