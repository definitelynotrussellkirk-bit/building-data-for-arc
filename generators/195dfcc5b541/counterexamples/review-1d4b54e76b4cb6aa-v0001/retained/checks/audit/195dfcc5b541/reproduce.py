"""Reproduce the overlap-order shortcut for audit target 195dfcc5b541."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK_ID = "195dfcc5b541"
GENERATOR = REPO / "generators" / TASK_ID / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_195dfcc5b541", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        record = json.loads(line)
        if record.get("task_id") == TASK_ID:
            test = record["test"] if isinstance(record["test"], list) else [record["test"]]
            return record["train"] + test
    raise RuntimeError("canonical task missing")


def candidate_matches(gen, grid):
    height, width = len(grid), len(grid[0])
    matches = []
    for component in gen._components_8(grid, 8):
        base = gen._norm(component)
        rotations = gen._rotations(base)
        variants = [(0, shape) for shape in rotations]
        variants.extend((1, gen._reflect(shape)) for shape in rotations)
        for flip_rank, shape in variants:
            shape_h, shape_w = gen._bbox(shape)
            for row0 in range(height - shape_h + 1):
                for col0 in range(width - shape_w + 1):
                    cells = tuple((row0 + row, col0 + col) for row, col in shape)
                    if all(grid[row][col] == 3 for row, col in cells):
                        # Match the authority's prepend enumeration before sorting.
                        matches.insert(0, (flip_rank, row0, col0, cells))
    return matches


def rightmost_first_rival(gen, grid):
    """Greedy non-overlap matching, but break same-row ties right-to-left."""
    matches = candidate_matches(gen, grid)
    matches.sort(key=lambda item: (item[0], item[1], -item[2]))
    output = deepcopy(grid)
    used = set()
    for _, _, _, cells in matches:
        if used.intersection(cells):
            continue
        used.update(cells)
        for row, col in cells:
            output[row][col] = 8
    return output


def main():
    gen = load_generator()
    pairs = canonical_pairs()
    canonical_fits = [rightmost_first_rival(gen, pair["input"]) == pair["output"] for pair in pairs]

    generated_total = 0
    generated_fits = 0
    for band in (None, "easy", "medium", "hard"):
        for index in range(40):
            grid = gen.generate(10000 + index, index * 17, difficulty=band)
            generated_total += 1
            generated_fits += rightmost_first_rival(gen, grid) == gen._intended_rule(grid)

    overrides = {"grid_h": 11, "grid_w": 17, "shape_variant": 0, "copy_count": 2}
    base = gen.generate(0, 0, **overrides)
    block = { (row, col) for row in range(2) for col in range(4) }
    assert all(base[row][col] not in (3, 8) for row, col in gen._halo(block, 11, 17))
    grid = deepcopy(base)
    for row, col in block:
        grid[row][col] = 3

    intended = gen._intended_rule(grid)
    rival = rightmost_first_rival(gen, grid)
    differing = [
        {"row": row, "col": col, "intended": intended[row][col], "rival": rival[row][col]}
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if intended[row][col] != rival[row][col]
    ]
    report = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "rival": "same matcher and greedy non-overlap policy, but same-row candidates are ordered right-to-left instead of left-to-right",
        "canonical_labeled_pairs": {"fits": sum(canonical_fits), "total": len(canonical_fits), "per_pair": canonical_fits},
        "ordinary_generated_samples": {"fits": generated_fits, "total": generated_total, "bands": [None, "easy", "medium", "hard"], "samples_per_band": 40},
        "counterexample": {
            "base_seed": 0,
            "base_sample_index": 0,
            "base_overrides": overrides,
            "mutation": "replace clean top-left 2x4 background block (rows 0..1, cols 0..3) with color 3",
            "validator_errors": gen.self_check(grid),
            "documented_generator_domain": False,
            "domain_note": "validator-clean and canonical-rule-lawful, but deliberately outside the ordinary sampler's one-cell-isolated-copy distribution",
            "differing_cells": differing,
        },
    }
    assert canonical_fits == [True] * 5
    assert generated_fits == generated_total
    assert report["counterexample"]["validator_errors"] == []
    assert intended != rival

    (HERE / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    (HERE / "python-intended.json").write_text(json.dumps(intended, indent=2) + "\n")
    (HERE / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")
    (HERE / "observation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
