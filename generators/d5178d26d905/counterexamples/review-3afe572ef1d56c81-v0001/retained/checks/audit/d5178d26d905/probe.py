#!/usr/bin/env python3
"""Reproduce the yellow-count-order teaching ambiguity on current source."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs

TASK = "d5178d26d905"
ROOT = Path.cwd()
GEN_PATH = ROOT / "generators" / TASK / "generator.py"
OUT = ROOT.parent / "checks" / "audit" / TASK / "evidence.json"

spec = importlib.util.spec_from_file_location("audit_d517", GEN_PATH)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)


def yellow_count_order(grid):
    """Wrong but plausible: rank special reference rows by yellow density."""
    info = gen._facts(grid)
    reference = info["reference"]
    line_columns = info["reference_line_columns"]
    line_colors = info["line_colors"]
    fills = info["fills"]
    retention = info["retention"]
    ranked_rows = sorted(
        info["reference_special_indexes"],
        key=lambda row: (sum(value == 4 for value in reference[row]), row),
    )
    special_lookup = {row: index for index, row in enumerate(ranked_rows)}
    output = [[0 for _ in row] for row in reference]
    for row_index in range(len(reference)):
        special_index = special_lookup.get(row_index)
        if special_index is None:
            for column, color in zip(line_columns, line_colors):
                output[row_index][column] = color
            continue
        output[row_index] = [fills[special_index]] * len(reference[row_index])
        for line_index, column in enumerate(line_columns):
            if retention[special_index][line_index]:
                output[row_index][column] = line_colors[line_index]
    return output


def differences(left, right):
    return [
        [r, c, left[r][c], right[r][c]]
        for r in range(len(left))
        for c in range(len(left[0]))
        if left[r][c] != right[r][c]
    ]


seed = 0
start = 7
difficulty = "medium"
grids = [gen.generate(seed, start + offset, difficulty=difficulty) for offset in range(4)]
receipt = Catalog(ROOT).apply(TASK, grids, reference="canonical", timeout=180)
authority_outputs = [item["output"] for item in receipt["results"]]
mirror_outputs = [gen.rule_mirror(grid) for grid in grids]
assert mirror_outputs == authority_outputs
rival_outputs = [yellow_count_order(grid) for grid in grids]
assert rival_outputs[:3] == authority_outputs[:3]
assert rival_outputs[3] != authority_outputs[3]

pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
canonical_fit = sum(yellow_count_order(pair["input"]) == pair["output"] for pair in pairs)
assert canonical_fit == len(pairs)

demos = [
    {"input": grid, "output": output}
    for grid, output in zip(grids[:3], authority_outputs[:3])
]
query = {"input": grids[3], "output": authority_outputs[3]}
infos = [gen._facts(grid) for grid in grids]
report = {
    "schema": "arc-audit-reproduction-v1",
    "task_id": TASK,
    "finding": "yellow-count-order rival survives demos and changes query",
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "rule_hash_declared": gen.RULE_HASH,
    "receipt_rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
    "seed": seed,
    "difficulty": difficulty,
    "sample_indices": list(range(start, start + 4)),
    "profiles": [gen.schedule_profile(seed, start + i, difficulty) for i in range(4)],
    "self_check": [gen.self_check(grid) for grid in grids],
    "strict_check": [gen.strict_canonical_like(grid) for grid in grids],
    "canonical_pairs_fit": canonical_fit,
    "canonical_pairs_total": len(pairs),
    "declared_lesson_hook_reasons": gen.lesson_identifiable(demos, query),
    "reference_special_rows": [info["reference_special_indexes"] for info in infos],
    "reference_special_yellow_counts": [
        [sum(value == 4 for value in info["reference"][row])
         for row in info["reference_special_indexes"]]
        for info in infos
    ],
    "rival_fits_demonstrations": [
        rival_outputs[i] == authority_outputs[i] for i in range(3)
    ],
    "query_diff_cells": differences(authority_outputs[3], rival_outputs[3]),
    "lesson": [
        {
            "sample_index": start + i,
            "input": grids[i],
            "authority_output": authority_outputs[i],
            "rival_output": rival_outputs[i],
        }
        for i in range(4)
    ],
}
OUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({
    "canonical_fit": f"{canonical_fit}/{len(pairs)}",
    "demo_fit": report["rival_fits_demonstrations"],
    "query_diff_cells": len(report["query_diff_cells"]),
    "lesson_hook_reasons": report["declared_lesson_hook_reasons"],
    "out": str(OUT),
}))
