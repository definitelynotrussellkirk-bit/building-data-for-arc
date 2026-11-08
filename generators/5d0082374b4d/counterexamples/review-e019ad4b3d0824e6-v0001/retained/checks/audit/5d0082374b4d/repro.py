#!/usr/bin/env python3
"""Reproduce the marker-preservation teaching ambiguity without private runners.

Run from the packet's outer root (use fresh output paths on a repeat):

    WORK/.venv/bin/python review.py run ../.venv/bin/python \
      ../checks/audit/5d0082374b4d/repro.py prepare
    WORK/.venv/bin/python review.py run ../.venv/bin/python -m arcpuzzles \
      apply 5d0082374b4d --check-generator-domain \
      --input ../checks/audit/5d0082374b4d/inputs.json \
      --out ../checks/audit/5d0082374b4d/authority.json
    WORK/.venv/bin/python review.py run ../.venv/bin/python -m arcpuzzles \
      generate 5d0082374b4d --count 1 --seed 136 --difficulty easy --test 1 \
      --out ../checks/audit/5d0082374b4d/production.jsonl
    WORK/.venv/bin/python review.py run ../.venv/bin/python \
      ../checks/audit/5d0082374b4d/repro.py verify

The rival independently detects 4-connected color-1 frames and fills zero
interior cells with alternating stripes, preserving the colored input keys.
The first three generated inputs have only even interior widths, so their
answers cannot distinguish that rival from overwriting every interior cell.
The fourth input has odd interior widths and separates the rules.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "5d0082374b4d"
SOURCE_SHA256 = "f24326c752e2a0e3d1d38282d5f9da862a7c6e6889a600dcb7ce71f8bc289314"
SEED = 136
MINIMAL_INPUT = [
    [1, 1, 1, 1, 1],
    [1, 2, 0, 3, 1],
    [1, 0, 0, 0, 1],
    [1, 1, 1, 1, 1],
]
MINIMAL_EXPECTED = [
    [1, 1, 1, 1, 1],
    [1, 2, 3, 2, 1],
    [1, 2, 3, 2, 1],
    [1, 1, 1, 1, 1],
]


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def frame_bounds(grid):
    """Independent monochrome component parser; no generator helpers."""
    remaining = {
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
        if value == 1
    }
    bounds = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for adjacent in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if adjacent in remaining:
                    remaining.remove(adjacent)
                    component.add(adjacent)
                    stack.append(adjacent)
        r1, r2 = min(r for r, _ in component), max(r for r, _ in component)
        c1, c2 = min(c for _, c in component), max(c for _, c in component)
        perimeter = {
            (r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)
        }
        if component == perimeter and r2 - r1 >= 2 and c2 - c1 >= 2:
            bounds.append((r1, c1, r2, c2))
    return sorted(bounds)


def stripe_solution(grid, *, preserve_markers):
    """Fill stripes; the alternative differs only in preserving colored keys."""
    output = [[1 if value == 1 else 0 for value in row] for row in grid]
    for r1, c1, r2, c2 in frame_bounds(grid):
        left = grid[r1 + 1][c1 + 1]
        right = grid[r1 + 1][c2 - 1]
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                value = left if (c - c1 - 1) % 2 == 0 else right
                if preserve_markers and grid[r][c] not in (0, 1):
                    value = grid[r][c]
                output[r][c] = value
    return output


def differences(expected, actual):
    return [
        {"row": r, "column": c, "expected": value, "rival": actual[r][c]}
        for r, row in enumerate(expected) for c, value in enumerate(row)
        if value != actual[r][c]
    ]


def prepare(folder, generator, source_hash, repo_root):
    draws = [generator.generate(SEED, index, difficulty="easy") for index in range(4)]
    assert all(generator.self_check(grid) == [] for grid in draws)
    assert generator.self_check(MINIMAL_INPUT) == []
    assert stripe_solution(MINIMAL_INPUT, preserve_markers=False) == MINIMAL_EXPECTED
    assert stripe_solution(MINIMAL_INPUT, preserve_markers=True) != MINIMAL_EXPECTED
    canonical = canonical_pairs(TASK_ID, root=repo_root)
    assert len(canonical) == 5
    row = next(
        json.loads(line)
        for line in (repo_root / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )
    metadata = {
        "task_id": TASK_ID, "generator_sha256": source_hash,
        "generator_version": generator.VERSION, "declared_rule_hash": generator.RULE_HASH,
        "canonical_program_sha256": hashlib.sha256(row["program_solution"].encode()).hexdigest(),
        "seed": SEED, "difficulty": "easy", "sample_indices": list(range(4)),
        "input_roles": ["demo_0", "demo_1", "demo_2", "query", "minimal", *[
            f"canonical_{item['split']}_{item['pair_index']}" for item in canonical
        ]],
        "generated_features": [generator.semantic_features(grid) for grid in draws],
        "minimal_self_check": generator.self_check(MINIMAL_INPUT),
        "canonical": canonical,
        "lesson_contract_declarations": {
            name: hasattr(generator, name)
            for name in ("EXAMPLES_NEEDED", "LESSON_COMPETITORS", "SEMANTIC_RIVALS", "lesson_identifiable")
        },
    }
    folder.mkdir(parents=True, exist_ok=True)
    write(folder / "inputs.json", {"inputs": draws + [MINIMAL_INPUT] + [p["input"] for p in canonical]})
    write(folder / "prepared.json", metadata)
    print(json.dumps({"prepared_inputs": 10, "seed": SEED, "generator_sha256": source_hash}))


def verify(folder, generator, source_hash):
    prepared = read(folder / "prepared.json")
    authority = read(folder / "authority.json")
    inputs = read(folder / "inputs.json")["inputs"]
    production = json.loads((folder / "production.jsonl").read_text().splitlines()[0])
    assert source_hash == prepared["generator_sha256"] == authority["generator_sha256"]
    assert source_hash == production["provenance"]["generator_sha256"]
    assert authority["executed_rule_hash"] == production["executed_rule_hash"] == generator.RULE_HASH
    # apply reports the lowered callable hash; generation retains rule! source.
    # Bind like-for-like source text here and retain both identities below.
    assert hashlib.sha256(production["program"].encode()).hexdigest() == prepared["canonical_program_sha256"]
    rows = authority["results"]
    assert len(rows) == len(inputs) == 10
    assert all(row["input"] == grid for row, grid in zip(rows, inputs))
    assert all(row["output"] is not None for row in rows)
    assert all(generator.self_check(grid) == [] for grid in inputs)
    assert [pair["input"] for pair in production["train"] + production["test"]] == inputs[:4]
    assert len(production["train"]) == 3 and len(production["test"]) == 1
    assert [pair["output"] for pair in production["train"] + production["test"]] == [row["output"] for row in rows[:4]]
    assert all(
        stripe_solution(grid, preserve_markers=False) == row["output"]
        for grid, row in zip(inputs, rows)
    )
    assert all(
        generator.expected_output(grid) == row["output"]
        for grid, row in zip(inputs, rows)
    )
    assert all(
        row["output"] == pair["output"]
        for row, pair in zip(rows[5:], prepared["canonical"])
    )
    rival_outputs = [stripe_solution(grid, preserve_markers=True) for grid in inputs]
    matches = [row["output"] == rival for row, rival in zip(rows, rival_outputs)]
    assert matches[:4] == [True, True, True, False]
    assert rows[4]["output"] == MINIMAL_EXPECTED and not matches[4]
    report = {
        "schema": "arc.audit-marker-preservation.v1",
        "task_id": TASK_ID, "generator_sha256": source_hash,
        "executed_rule_hash": authority["executed_rule_hash"],
        "rule_text_sha256": authority["rule_text_sha256"],
        "rule_text_hash_scope": "lowered callable executed by public apply",
        "canonical_program_sha256": prepared["canonical_program_sha256"],
        "verdict": "REPRODUCED_TEACHING_AMBIGUITY",
        "independently_rerun": True,
        "inherited_context": "GNOTE-001240 recognizes the overwrite distinction; the seed136 lesson counterexample is a new independent reproduction.",
        "rule_output_mismatches": 0,
        "canonical_pairs_checked_with_racket": 5,
        "total_racket_inputs_checked": 10,
        "production": {
            "seed": SEED, "difficulty": "easy", "train_count": 3, "query_count": 1,
            "sample_indices": production["sample_indices"],
            "lesson_check": production.get("lesson_check"),
            "rejections": production["rejections"],
            "rival_fits_each_demonstration": matches[:3],
            "rival_fits_query": matches[3],
            "inner_widths": [facts["inner_widths"] for facts in prepared["generated_features"]],
            "query_answers_used_as_demonstrations": False,
            "query_differences": differences(rows[3]["output"], rival_outputs[3]),
            "query_input": inputs[3], "query_racket_output": rows[3]["output"],
            "query_rival_output": rival_outputs[3],
        },
        "minimal": {
            "shape": [4, 5], "self_check": generator.self_check(inputs[4]),
            "scope": "Smallest admitted single frame exposing the overwrite branch; normal draws have larger canvases and two or three frames.",
            "input": inputs[4], "racket_output": rows[4]["output"],
            "rival_output": rival_outputs[4],
            "differences": differences(rows[4]["output"], rival_outputs[4]),
        },
        "lesson_contract_declarations": prepared["lesson_contract_declarations"],
        "limits": [
            "One deterministic default-distribution episode and one validator-lawful reduction; no prevalence estimate.",
            "The rival is independently introduced by this audit, not declared by the generator.",
            "No general Racket correctness failure was found; this finding concerns what the demonstrations identify.",
            "No target source, rule, notes or approval edits; no full battery rerun.",
        ],
    }
    write(folder / "finding.json", report)
    write(folder / "minimal-witness.json", report["minimal"])
    print(json.dumps({
        "verdict": report["verdict"], "source_sha256": source_hash,
        "executed_rule_hash": authority["executed_rule_hash"],
        "production_rival_match": matches[:4],
        "query_difference_cells": len(report["production"]["query_differences"]),
        "minimal_difference_cells": len(report["minimal"]["differences"]),
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "verify"))
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    repo_root = find_root(__file__)
    generator, source, source_hash = load_selected_generator(TASK_ID, root=repo_root)
    assert source_hash == SOURCE_SHA256, f"audited source changed: {source_hash}"
    if args.action == "prepare":
        prepare(args.out, generator, source_hash, repo_root)
    else:
        verify(args.out, generator, source_hash)


if __name__ == "__main__":
    main()
