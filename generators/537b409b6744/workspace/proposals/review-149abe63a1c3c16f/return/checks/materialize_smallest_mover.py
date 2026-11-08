#!/usr/bin/env python3
"""Materialize the exact canonical-fitting smallest-mover counterexample."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "537b409b6744"
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
TASK_DIR = ROOT / "generators" / TASK_ID


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def changed_cells(left, right):
    return [
        [row, column]
        for row in range(len(left))
        for column in range(len(left[0]))
        if left[row][column] != right[row][column]
    ]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--counterexample", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(argv)

    probe = load_module(
        "shortcut_reference_probe", TASK_DIR / "workspace" / "reference_probe.py"
    )
    prototype = load_module(
        "shortcut_parametric_helpers",
        TASK_DIR / "workspace" / "parametric" / "prototype.py",
    )

    replay = {
        "seed": 1,
        "sample_index": 17,
        "overrides": {
            "grid_h": 10,
            "grid_w": 10,
            "direction": "down",
            "mover_span": 2,
            "mover_depth": 2,
            "wall_extra": 2,
            "wall_depth": 3,
            "gap": 1,
            "distractor_kind": "solid",
        },
    }
    grid = GEN.generate(replay["seed"], replay["sample_index"], **replay["overrides"])
    candidates = probe.ranked_candidates(grid)
    intended_python = GEN._rule_output(grid)
    shortcut_output = probe.smallest_candidate_output(grid)
    if shortcut_output != GEN.CANONICAL_SHORTCUTS["smallest_mover"](grid):
        raise AssertionError("independent probe disagrees with declared shortcut")
    if intended_python == shortcut_output:
        raise AssertionError("selected witness does not distinguish the shortcut")

    source = prototype.canonical_program()
    bridge = RacketBridge(timeout=60, max_calls_before_restart=32)
    try:
        intended_racket = bridge.eval_text(prototype._application(source, grid))
        runtime_identity = bridge.runtime_identity
    finally:
        bridge.shutdown()
    if intended_racket != intended_python:
        raise AssertionError("canonical Racket output disagrees with Python oracle")

    canonical_rows = []
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        actual = GEN.CANONICAL_SHORTCUTS["smallest_mover"](pair["input"])
        canonical_rows.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "fits": actual == pair["output"],
            }
        )
    if not all(row["fits"] for row in canonical_rows):
        raise AssertionError("smallest_mover does not fit every labeled canonical pair")

    candidate_rows = [
        {
            "rank": index,
            "gap": candidate["gap"],
            "direction": candidate["direction"],
            "mover_color": candidate["mover"]["color"],
            "mover_size": candidate["mover"]["size"],
            "wall_color": candidate["wall"]["color"],
            "wall_size": candidate["wall"]["size"],
        }
        for index, candidate in enumerate(candidates)
    ]
    record = {
        "schema": "arcpuzzles-shortcut-counterexample-v1",
        "task_id": TASK_ID,
        "shortcut": "smallest_mover",
        "description": (
            "Choose the qualifying candidate with the smallest mover area, "
            "breaking ties by the canonical nearest-gap ranking."
        ),
        "replay": replay,
        "input": grid,
        "intended_output": intended_racket,
        "shortcut_output": shortcut_output,
        "racket_intended_matches_python": intended_racket == intended_python,
        "outputs_differ": intended_racket != shortcut_output,
        "candidate_summary": candidate_rows,
        "intended_changed_cells": changed_cells(grid, intended_racket),
        "shortcut_changed_cells": changed_cells(grid, shortcut_output),
        "canonical_fit": {
            "labeled_pairs": len(canonical_rows),
            "fits_all": all(row["fits"] for row in canonical_rows),
            "pairs": canonical_rows,
        },
        "bindings": {
            "generator_path": str(GENERATOR_PATH),
            "generator_sha256": GENERATOR_SHA256,
            "reference_probe_sha256": sha256_bytes(
                (TASK_DIR / "workspace" / "reference_probe.py").read_bytes()
            ),
            "canonical_program_sha256": sha256_bytes(source.encode("utf-8")),
            "canonical_rule_hash": GEN.RULE_HASH,
        },
        "racket_runtime": runtime_identity,
        "command": sys.argv,
        "cwd": os.getcwd(),
    }

    for path in (args.counterexample, args.evidence):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "counterexample": str(args.counterexample),
                "evidence": str(args.evidence),
                "canonical_pairs_fit": len(canonical_rows),
                "candidate_sizes": [row["mover_size"] for row in candidate_rows],
                "outputs_differ": True,
                "evidence_sha256": sha256_bytes(args.evidence.read_bytes()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
