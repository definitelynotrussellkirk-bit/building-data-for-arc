#!/usr/bin/env python3
"""Audit d48ec0001283 for an undeclared all-same-row shortcut."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
GENERATOR = WORK / "repo/generators/d48ec0001283/generator.py"
CANONICAL = WORK / "repo/shared/data/canonical/puzzles.jsonl"
OUT_DIR = Path(__file__).resolve().parent
SEED = 480031


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_d48", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rival_all_same_row(grid: list[list[int]]) -> list[list[int]]:
    """Fill extrema when a row has >=2 markers and all have one color."""
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        entries = [(c, value) for c, value in enumerate(row) if value != 0]
        if len(entries) >= 2 and len({value for _, value in entries}) == 1:
            left, color = entries[0]
            right = entries[-1][0]
            for c in range(left, right + 1):
                out[r][c] = color
    return out


def canonical_pairs() -> list[dict]:
    for line in CANONICAL.read_text().splitlines():
        task = json.loads(line)
        if task.get("task_id") == "d48ec0001283":
            test = task.get("test")
            tests = test if isinstance(test, list) else [test]
            return [*task.get("train", []), *[p for p in tests if p]]
    raise RuntimeError("canonical task not found")


def main() -> None:
    module = load_generator()
    pairs = canonical_pairs()
    canonical_matches = sum(
        rival_all_same_row(pair["input"]) == pair["output"] for pair in pairs
    )

    bands: dict[str, dict[str, int]] = {}
    for band in ("easy", "medium", "hard"):
        generated = 0
        self_check_passed = 0
        rival_matches = 0
        for sample_index in range(300):
            grid = module.generate(SEED, sample_index, difficulty=band)
            generated += 1
            self_check_passed += not module.self_check(grid)
            actual = module.rule_mirror(grid)
            rival_matches += rival_all_same_row(grid) == actual
        bands[band] = {
            "generated": generated,
            "self_check_passed": self_check_passed,
            "rival_matches": rival_matches,
        }

    # Two ordinary active rows plus one same-color three-marker row.  The latter
    # is where the authority's exact-two condition differs from the shortcut.
    witness = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 0, 2, 0, 2, 0, 0],
        [5, 0, 0, 0, 5, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 7, 0, 0, 0, 7, 0, 0],
    ]
    authority_mirror = module.rule_mirror(witness)
    rival = rival_all_same_row(witness)
    validator_errors = module.self_check(witness)
    differing_cells = [
        [r, c, authority_mirror[r][c], rival[r][c]]
        for r in range(len(witness))
        for c in range(len(witness[0]))
        if authority_mirror[r][c] != rival[r][c]
    ]

    report = {
        "task_id": "d48ec0001283",
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "seed": SEED,
        "sample_indices": [0, 299],
        "canonical_pairs": len(pairs),
        "canonical_rival_matches": canonical_matches,
        "bands": bands,
        "ordinary_total": sum(v["generated"] for v in bands.values()),
        "ordinary_rival_matches": sum(v["rival_matches"] for v in bands.values()),
        "witness": {
            "validator_errors": validator_errors,
            "belongs_to_current_generator_domain": not validator_errors,
            "authority_mirror_output": authority_mirror,
            "rival_output": rival,
            "differing_cells": differing_cells,
        },
    }
    (OUT_DIR / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
    (OUT_DIR / "input.json").write_text(json.dumps(witness, indent=2) + "\n")
    (OUT_DIR / "rival_output.json").write_text(
        json.dumps({"rival": "fill_all_same_marker_rows", "output": rival}, indent=2)
        + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
