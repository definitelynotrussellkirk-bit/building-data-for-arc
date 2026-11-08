#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from reviewer_support import canonical_pairs, load_selected_generator

TASK_ID = "33fcd12e6b89"


def object_cells(grid):
    return [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 3, 4)]


def normalized_shape(grid):
    cells = object_cells(grid)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def whitelist_rival(grid, allowed_shapes):
    shape = normalized_shape(grid)
    if shape not in allowed_shapes:
        return copy.deepcopy(grid)
    out = copy.deepcopy(grid)
    p3 = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3)
    p4 = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 4)
    dr, dc = p4[0] - p3[0], p4[1] - p3[1]
    for r, c in object_cells(grid):
        out[r][c] = 0
    for r, c in object_cells(grid):
        out[r + dr][c + dc] = grid[r][c]
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--racket", type=Path, required=True)
    parser.add_argument("--rival", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd()
    gen, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    counterexample = json.loads(args.input.read_text())
    racket_receipt = json.loads(args.racket.read_text())

    allowed_shapes = {
        tuple(sorted(shape))
        for shape in gen._SHAPES
    }
    sampled_shapes = set()
    sample_failures = []
    total = 0
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(150):
            grid = gen.generate(20261023, index, difficulty=difficulty)
            total += 1
            sampled_shapes.add(normalized_shape(grid))
            rival = whitelist_rival(grid, allowed_shapes)
            # The generator's own intended geometry can be computed directly.
            p3 = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3)
            p4 = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 4)
            dr, dc = p4[0] - p3[0], p4[1] - p3[1]
            intended = copy.deepcopy(grid)
            for r, c in object_cells(grid):
                intended[r][c] = 0
            for r, c in object_cells(grid):
                intended[r + dr][c + dc] = grid[r][c]
            if rival != intended:
                sample_failures.append({"difficulty": difficulty, "sample_index": index})

    # The public ARC task has two labelled demonstrations and one labelled
    # query in the canonical data.  Shortcut fit is assessed on demonstrations;
    # the query is retained separately as a possible discriminator.
    labeled_pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_fit = [
        whitelist_rival(pair["input"], allowed_shapes) == pair["output"]
        for pair in labeled_pairs[:2]
    ]
    canonical_query_fit = (
        whitelist_rival(labeled_pairs[2]["input"], allowed_shapes) == labeled_pairs[2]["output"]
        if len(labeled_pairs) > 2 else None
    )

    rival_output = whitelist_rival(counterexample, allowed_shapes)
    args.rival.write_text(json.dumps(rival_output, indent=2) + "\n")
    actual_output = racket_receipt.get("output")
    if actual_output is None and "results" in racket_receipt:
        rows = racket_receipt["results"]
        actual_output = rows[0].get("output") if isinstance(rows, list) and rows else None
    if actual_output is None and "outputs" in racket_receipt:
        outputs = racket_receipt["outputs"]
        actual_output = outputs[0] if isinstance(outputs, list) and outputs else None
    result = {
        "schema": "arcpuzzles-audit-fixed-shape-rival-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": source_sha,
        "rule_hash": "4151627dc5c7",
        "allowed_normalized_shapes": [list(map(list, shape)) for shape in sorted(allowed_shapes)],
        "generated_sample_count": total,
        "generated_unique_shapes": [list(map(list, shape)) for shape in sorted(sampled_shapes)],
        "generated_rival_mismatches": sample_failures,
        "canonical_demonstration_fit": canonical_fit,
        "canonical_query_fit": canonical_query_fit,
        "counterexample": {
            "input": counterexample,
            "normalized_shape": list(map(list, normalized_shape(counterexample))),
            "shape_is_whitelisted": normalized_shape(counterexample) in allowed_shapes,
            "self_check": gen.self_check(counterexample),
            "racket_output": actual_output,
            "rival_output": rival_output,
            "outputs_disagree": actual_output != rival_output,
        },
        "reproduced": (
            all(canonical_fit)
            and not sample_failures
            and normalized_shape(counterexample) not in allowed_shapes
            and gen.self_check(counterexample) == []
            and actual_output is not None
            and actual_output != rival_output
        ),
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"reproduced": result["reproduced"], "samples": total, "generator_sha256": source_sha}))
    return 0 if result["reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
