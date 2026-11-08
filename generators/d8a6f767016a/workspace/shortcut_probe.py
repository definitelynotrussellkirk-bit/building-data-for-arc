#!/usr/bin/env python3
"""Reproduce the component-size shortcut and its exact counterexample.

This is diagnostic code, never label authority. Labels remain the canonical
Racket rule. Optionally pass the JSON emitted by `arcpuzzles apply` to bind the
hand-made counterexample to the executed authority.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_ID = "d8a6f767016a"


def exact_input() -> list[list[int]]:
    grid = [[0] * 11 for _ in range(9)]
    for r in range(4):
        for c in range(5):
            if r in (0, 3) or c in (0, 4):
                grid[r][c] = 8  # 14 cells, one enclosed region
    for r in range(6, 9):
        for c in range(8, 11):
            if r in (6, 8) or c in (8, 10):
                grid[r][c] = 8  # 8 cells, one enclosed region
    return grid


def digest(value) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--racket-result", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--per-band", type=int, default=100)
    args = parser.parse_args()

    root = find_root(__file__)
    try:
        gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
    except ModuleNotFoundError:
        source = root / "generators" / TASK_ID / "generator.py"
        spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", source)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load generator from {source}")
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    train = [pair for pair in pairs if pair["split"] == "train"]
    test = [pair for pair in pairs if pair["split"] == "test"]

    grid = exact_input()
    mirror = gen.rule_mirror(grid)
    rival = gen._rival_canonical_size_bins(grid)
    racket_output = None
    racket_meta = None
    if args.racket_result:
        payload = json.loads(args.racket_result.read_text())
        racket_output = payload["results"][0]["output"]
        racket_meta = {
            key: payload.get(key)
            for key in ("reference", "executed_rule_hash", "rule_text_sha256", "generator_sha256")
        }
        if racket_output != mirror:
            raise SystemExit("Python mirror disagrees with executed canonical Racket output")

    rates = {}
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(args.per_band):
            sample = gen.generate(90_000 + index, index, difficulty=band)
            hits += int(gen._witness_size_shortcut_counterexample(sample))
        rates[band] = {"hits": hits, "draws": args.per_band}

    report = {
        "schema": "d8a6f767016a-shortcut-probe-v1",
        "shortcut": "component-size bins: <=12->1, 13..17->3, 18..25->2, >=26->4",
        "canonical_training_fit": {
            "fit": sum(gen._rival_canonical_size_bins(p["input"]) == p["output"] for p in train),
            "pairs": len(train),
        },
        "canonical_test_fit": {
            "fit": sum(gen._rival_canonical_size_bins(p["input"]) == p["output"] for p in test),
            "pairs": len(test),
        },
        "counterexample": {
            "input": grid,
            "input_sha256": digest(grid),
            "intended_output": racket_output or mirror,
            "rival_output": rival,
            "disagrees": rival != (racket_output or mirror),
            "component_stats": [
                {"cells": len(cells), "holes": gen._count_holes(cells)}
                for cells in gen._objects4(grid)
            ],
            "racket": racket_meta,
        },
        "ordinary_generator_witness_rate": rates,
        "limits": [
            "Finite checks against one named rival do not prove unique induction.",
            "The Python mirror is diagnostic; canonical Racket remains label authority.",
        ],
    }
    if report["canonical_training_fit"]["fit"] != len(train):
        raise SystemExit("shortcut no longer fits all canonical training demonstrations")
    if not report["counterexample"]["disagrees"]:
        raise SystemExit("counterexample did not distinguish the shortcut")
    if any(row["hits"] != row["draws"] for row in rates.values()):
        raise SystemExit("ordinary generator missed the required shortcut witness")

    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
