"""Replay a generated joint shortcut witness through the public Racket API.

Authoring only: canonical labels are read. Never run during a visible-only solve.
From the outer packet root, run through review.py; payload paths are relative
to WORK/repo. RESULTS.json records the exact verified invocation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK = "f68fe53c1702"
EXPECTED_INPUT = [
    [2, 0, 0, 0, 0],
    [0, 2, 2, 0, 0],
    [0, 2, 0, 0, 0],
    [0, 0, 0, 0, 0],
]
EXPECTED_OUTPUT = [
    [2, 2, 2, 0, 0],
    [2, 0, 2, 0, 0],
    [2, 2, 2, 0, 0],
    [0, 0, 0, 0, 0],
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("use a new output path to preserve previous evidence")
    root = find_root(__file__)
    source = next(p for p in (root / "generators" / TASK / "generator.py",
                              root / "puzzle_generators" / "per_puzzle" / TASK / "generator.py")
                  if p.is_file())
    spec = importlib.util.spec_from_file_location("bbox_witness_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    overrides = {"grid_h": 4, "grid_w": 5, "color": 2, "num_cells": 4}
    grid = gen.generate(117, 1, difficulty="easy", **overrides)
    assert grid == EXPECTED_INPUT, "seed replay changed; this witness is source-bound"
    assert gen.self_check(grid) == []
    pairs = canonical_pairs(TASK, root=root, labeled_only=True)
    reference = Catalog(root).apply(TASK, [grid])
    actual = reference["results"][0]["output"]
    assert reference["rule_hash_matches_catalog"]
    assert actual == EXPECTED_OUTPUT
    rivals = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        fits = sum(rival(pair["input"]) == pair["output"] for pair in pairs)
        prediction = rival(grid)
        assert fits == len(pairs), name
        assert prediction != actual, name
        rivals[name] = {"canonical_fits": fits, "canonical_pairs": len(pairs),
                        "prediction": prediction, "differs_from_racket": True}
    report = {"task_id": TASK, "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "generator_version": gen.VERSION, "seed": 117, "sample_index": 1,
              "difficulty": "easy", "overrides": overrides, "input": grid,
              "validator_findings": gen.self_check(grid), "generated_domain": True,
              "strict_canonical_findings": gen.strict_canonical_like(grid),
              "reference": reference, "rivals": rivals,
              "cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv],
              "status": "verified_generated_counterexample"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "out": str(args.out),
                      "canonical_pairs": len(pairs), "rivals_refuted": len(rivals)}))


if __name__ == "__main__":
    main()
