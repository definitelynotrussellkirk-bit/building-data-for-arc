#!/usr/bin/env python3
"""Task-local executable rival probe for 39fd645f21c6.

The shared semantic gate samples production lessons but does not rotate every
pair into the query position.  This helper complements it by:

* checking each declared canonical shortcut against every canonical pair;
* finding a concrete generated counterexample for every declared rival; and
* testing all four cyclic query rotations of deterministic four-pair lessons.

Run from the repository through the packet wrapper, for example:

    python3 run_with_racket.py python3 \
      generators/39fd645f21c6/workspace/probe_shortcuts.py \
      --lessons-per-band 100 --out ../checks/shortcut-probe.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

from src.core.canonical_pairs import load_task_pairs

TASK_ID = "39fd645f21c6"
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CANONICAL_PATH = _REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
_GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
_SPEC = importlib.util.spec_from_file_location("probe_39fd645f21c6", _GENERATOR_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load generator from {_GENERATOR_PATH}")
GEN = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GEN)


def _pair(grid: list[list[int]]) -> dict[str, Any]:
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def _same(left: Any, right: Any) -> bool:
    return left == right


def run(lessons_per_band: int) -> dict[str, Any]:
    canonical = load_task_pairs(TASK_ID, _CANONICAL_PATH)
    canonical_shortcuts: dict[str, Any] = {}
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        matches = [
            _same(shortcut(pair["input"]), pair["output"])
            for pair in canonical
        ]
        canonical_shortcuts[name] = {
            "matches": matches,
            "fits_all": all(matches),
            "pair_count": len(matches),
        }

    counterexamples: dict[str, Any] = {}
    rotation_failures: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()
    rotations_checked = 0
    lessons_checked = 0

    for band_index, band in enumerate(("easy", "medium", "hard")):
        for lesson_index in range(lessons_per_band):
            seed = 390_000 + 10_000 * band_index + lesson_index
            start = 4 * lesson_index
            pairs = [
                _pair(GEN.generate(seed, start + offset, difficulty=band))
                for offset in range(4)
            ]
            lessons_checked += 1
            for pair_offset, pair in enumerate(pairs):
                unique_inputs.add(json.dumps(pair["input"], separators=(",", ":")))
                truth = pair["output"]
                for name, rival in GEN.SEMANTIC_RIVALS.items():
                    rival_output = rival(pair["input"])
                    if name not in counterexamples and not _same(rival_output, truth):
                        counterexamples[name] = {
                            "difficulty": band,
                            "seed": seed,
                            "sample_index": start + pair_offset,
                            "observables": GEN.semantic_observables(pair["input"]),
                            "input": pair["input"],
                            "authoritative_mirror_output": truth,
                            "rival_output": rival_output,
                        }

            for query_index in range(4):
                query = pairs[query_index]
                demos = pairs[query_index + 1 :] + pairs[:query_index]
                rotations_checked += 1
                reasons = GEN.lesson_identifiable(demos, query)
                survivors = [
                    name
                    for name, rival in GEN.LESSON_COMPETITORS.items()
                    if all(_same(rival(demo["input"]), demo["output"]) for demo in demos)
                ]
                if reasons or survivors:
                    rotation_failures.append(
                        {
                            "difficulty": band,
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "query_index": query_index,
                            "reasons": reasons,
                            "survivors": survivors,
                        }
                    )

    missing_counterexamples = sorted(set(GEN.SEMANTIC_RIVALS) - set(counterexamples))
    return {
        "task_id": TASK_ID,
        "generator_version": GEN.VERSION,
        "rule_hash": GEN.RULE_HASH,
        "lessons_per_band": lessons_per_band,
        "lessons_checked": lessons_checked,
        "rotations_checked": rotations_checked,
        "unique_inputs": len(unique_inputs),
        "canonical_shortcuts": canonical_shortcuts,
        "rival_counterexamples": counterexamples,
        "missing_rival_counterexamples": missing_counterexamples,
        "rotation_failure_count": len(rotation_failures),
        "rotation_failures": rotation_failures[:20],
        "passed": (
            not missing_counterexamples
            and not rotation_failures
            and all(item["fits_all"] for item in canonical_shortcuts.values())
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.lessons_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "passed": report["passed"],
        "lessons_checked": report["lessons_checked"],
        "rotations_checked": report["rotations_checked"],
        "unique_inputs": report["unique_inputs"],
        "missing_rival_counterexamples": report["missing_rival_counterexamples"],
        "rotation_failure_count": report["rotation_failure_count"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
