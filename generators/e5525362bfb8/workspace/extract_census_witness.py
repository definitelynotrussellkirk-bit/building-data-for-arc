"""Extract and replay a small, already Racket-labelled network counterexample.

Run through run_with_racket.py / review.py run from this review packet. This
does not invoke a Python label oracle or consult any solve episode answers.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root

TASK = "e5525362bfb8"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = find_root(__file__)
    source = next(p for p in (
        root / "generators" / TASK / "generator.py",
        root / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
    ) if p.is_file())
    spec = importlib.util.spec_from_file_location("witness_generator", source)
    gen = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gen
    spec.loader.exec_module(gen)
    census = json.loads(args.census.read_text())
    if census["task_id"] != TASK or census["generator_sha256"] != digest(source):
        raise ValueError("census and current generator source do not match")
    candidates = []
    for lesson_index, lesson in enumerate(census["lessons"]):
        instance = lesson["instance"]
        for accepted in instance["sampling"]["accepted_pairs"]:
            pair = instance[accepted["split"]][accepted["pair_index"]]
            if gen.observe_overrides(pair["input"])["scene"] == "network":
                area = len(pair["input"]) * len(pair["input"][0])
                candidates.append((area, lesson_index, accepted["sample_index"], accepted, pair))
    _, lesson_index, sample_index, accepted, pair = min(candidates, key=lambda x: x[:3])
    lesson = census["lessons"][lesson_index]
    grid, actual = pair["input"], pair["output"]
    replay = gen.generate(lesson["seed"], sample_index, difficulty=lesson["band"])
    if replay != grid or gen.self_check(grid):
        raise ValueError("recorded input failed exact regeneration or validation")
    labelled = canonical_pairs(TASK, root=root, labeled_only=True)
    canonical_fit, declarations = {}, {}
    for contract in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        for name, rival in getattr(gen, contract).items():
            prediction = rival(grid)
            differences = [[r, c] for r, row in enumerate(actual)
                           for c, value in enumerate(row) if prediction[r][c] != value]
            if not differences:
                raise ValueError(f"selected witness does not refute {contract}:{name}")
            declarations[f"{contract}:{name}"] = {
                "rival_output": prediction, "different_cells": differences,
            }
            fits = sum(rival(p["input"]) == p["output"] for p in labelled)
            canonical_fit[f"{contract}:{name}"] = {"fits": fits, "pairs": len(labelled)}
            if contract == "CANONICAL_SHORTCUTS" and fits != len(labelled):
                raise ValueError(f"declared canonical shortcut {name} does not fit all labels")
    record = {
        "task_id": TASK, "generator_version": gen.VERSION,
        "generator_sha256": digest(source), "declared_rule_hash": gen.RULE_HASH,
        "rule_source_sha256": census["rule_source_sha256"],
        "authority": "selected Racket labels retained by lesson-census; reused without relabelling",
        "census_sha256": digest(args.census), "census_path": "checks/lesson-census.json",
        "lesson_index": lesson_index, "instance_sha256": lesson["instance_sha256"],
        "accepted_pair": accepted, "seed": lesson["seed"], "sample_index": sample_index,
        "difficulty": lesson["band"], "overrides": {}, "input": grid,
        "actual_racket_output": actual, "self_check": [], "exact_regeneration": True,
        "observed_axes": gen.observe_overrides(grid), "canonical_rival_fit": canonical_fit,
        "rivals": declarations,
        "scope": "One lawful generated network; seven distinct rivals, aliased in three contracts.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({k: record[k] for k in ("generator_sha256", "seed", "sample_index", "difficulty", "observed_axes")}))


if __name__ == "__main__":
    main()
