#!/usr/bin/env python3
"""Reproduce one retained four-demo union survivor without editing the target."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK = "109a03554ed3"
HERE = Path(__file__).resolve().parent


def sha(value):
    return hashlib.sha256(value).hexdigest()


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def offsets(grid):
    """Independent four-connected component parser, using all source colors."""
    todo = {(r, c) for r, row in enumerate(grid) for c, x in enumerate(row)
            if x in {1, 2, 9}}
    components = []
    while todo:
        start = min(todo)
        todo.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in todo:
                    todo.remove(p)
                    component.add(p)
                    stack.append(p)
        components.append(component)
    answer = {}
    for color in (1, 2):
        matches = [comp for comp in components
                   if {grid[r][c] for r, c in comp} == {color, 9}]
        if len(matches) != 1:
            raise ValueError(f"Expected one pure source component for {color}")
        anchors = [(r, c) for r, c in matches[0] if grid[r][c] == 9]
        if len(anchors) != 1:
            raise ValueError("Expected one anchor in each source")
        ar, ac = anchors[0]
        answer[color] = {(r - ar, c - ac) for r, c in matches[0]
                         if grid[r][c] == color}
    return answer[2], answer[1]


def stamp(grid, cells):
    targets = [(r, c) for r, row in enumerate(grid) for c, x in enumerate(row)
               if x == 8]
    if len(targets) != 1:
        raise ValueError("Expected one cyan target")
    tr, tc = targets[0]
    result = [[0] * len(grid[0]) for _ in grid]
    for dr, dc in cells:
        r, c = tr + dr, tc + dc
        if not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
            raise ValueError("This bounded witness requires no clipping")
        result[r][c] = 3
    return result


def prepare():
    root = find_root(__file__)
    gen, source, source_sha = load_selected_generator(TASK, root=root)
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines()
            if line.strip()]
    canonical = [row for row in rows if row.get("task_id") == TASK]
    assert len(canonical) == 1
    rule = canonical[0]["program_solution"]
    identity = {
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": source_sha,
        "rule_field": "program_solution",
        "canonical_rule_text_sha256": sha(rule.encode()),
        "canonical_rule_normalized_sha256": sha(" ".join(rule.split()).encode()),
        "declares_CANONICAL_SHORTCUTS": hasattr(gen, "CANONICAL_SHORTCUTS"),
        "declares_LESSON_COMPETITORS": hasattr(gen, "LESSON_COMPETITORS"),
        "examples_needed": gen.EXAMPLES_NEEDED,
    }
    pairs = []
    for index in range(1, 6):
        grid = gen.generate(0, index, difficulty="medium")
        red, blue = offsets(grid)
        pairs.append({
            "role": "demo" if index < 5 else "query",
            "seed": 0, "sample_index": index, "difficulty": "medium",
            "overrides": {}, "input": grid,
            "self_check": gen.self_check(grid, difficulty="medium"),
            "domain": "Generated directly with normal difficulty; no input edits",
            "red_offsets": sorted(map(list, red)),
            "blue_offsets": sorted(map(list, blue)),
            "overlap_offsets": sorted(map(list, red & blue)),
            "independent_xor_output": stamp(grid, red ^ blue),
            "union_rival_output": stamp(grid, red | blue),
        })
    source_evidence = {
        "schema": "arc-audit-union-replay-v1", "task_id": TASK,
        "source_identity": identity, "pairs": pairs,
        "scope": {"seed": 0, "difficulty": "medium", "sample_indices": [1, 2, 3, 4, 5],
                  "unique_inputs": 5, "complete_lesson_windows": 1,
                  "demonstrations": 4, "queries": 1},
        "prior_finding": "review-1b19c8c442bcce16:v0001; needs_triage",
        "rival_classification": "Investigator-defined lesson competitor, not a claimed canonical shortcut",
    }
    save("source_evidence.json", source_evidence)
    save("inputs.json", [p["input"] for p in pairs])
    print(json.dumps({"generator_sha256": source_sha,
                      "overlap_counts": [len(p["overlap_offsets"]) for p in pairs],
                      "self_check_errors": [p["self_check"] for p in pairs]}))


def compare():
    witness = json.loads((HERE / "source_evidence.json").read_text())
    racket = json.loads((HERE / "racket.json").read_text())
    assert racket["generator_sha256"] == witness["source_identity"]["generator_sha256"]
    assert racket["executed_rule_hash"] == witness["source_identity"]["canonical_rule_normalized_sha256"][:12]
    assert len(racket["results"]) == len(witness["pairs"]) == 5
    for pair, result in zip(witness["pairs"], racket["results"]):
        assert result["input"] == pair["input"]
        pair["racket_output"] = result["output"]
        pair["racket_error"] = result["error"]
        pair["racket_valid_output"] = result["valid_output"]
        pair["input_sha256"] = result["input_sha256"]
        pair["racket_output_sha256"] = result["output_sha256"]
        pair["xor_matches_racket"] = pair["independent_xor_output"] == result["output"]
        pair["union_matches_racket"] = pair["union_rival_output"] == result["output"]
        pair["union_difference_cells"] = [
            [r, c, result["output"][r][c], x]
            for r, row in enumerate(pair["union_rival_output"]) for c, x in enumerate(row)
            if result["output"][r][c] != x
        ] if result["output"] is not None else None
    witness["racket_receipt"] = {k: racket[k] for k in (
        "schema", "executed_rule_hash", "catalog_rule_hash", "rule_hash_matches_catalog",
        "rule_text_sha256", "generator_sha256", "command", "cwd", "elapsed_seconds")}
    checks = {
        "all_five_validator_pass": all(p["self_check"] == [] for p in witness["pairs"]),
        "all_five_racket_valid": all(p["racket_valid_output"] and p["racket_error"] is None for p in witness["pairs"]),
        "all_five_independent_xor_match": all(p["xor_matches_racket"] for p in witness["pairs"]),
        "union_fits_four_demos": all(p["union_matches_racket"] for p in witness["pairs"][:4]),
        "union_fails_query": not witness["pairs"][4]["union_matches_racket"],
    }
    witness["checks"] = checks
    save("union_survivor_witness.json", witness)
    print(json.dumps({"checks": checks,
                      "query_difference_cells": witness["pairs"][4]["union_difference_cells"]}))
    assert all(checks.values()), "Audit outcome changed; retained results require inspection"


if __name__ == "__main__":
    {"prepare": prepare, "compare": compare}[sys.argv[1]]()
