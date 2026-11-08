"""Source-bound, findings-only audit; invokes no private runtime helpers."""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import importlib.util
import json
import os
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK_ID = "e5030f1df7fa"
HERE = Path(__file__).resolve().parent


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def isolated_component_rival(grid):
    """Fill only yellow components that are exactly one eight-cell 3x3 ring."""
    out = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 4}
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    queue.append(point)
        if len(component) != 8:
            continue
        top = min(r for r, c in component)
        left = min(c for r, c in component)
        border = {(top + dr, left + dc) for dr in range(3) for dc in range(3)
                  if (dr, dc) != (1, 1)}
        if component == border and grid[top + 1][left + 1] == 0:
            out[top + 1][left + 1] = 2
    return out


def identity_and_generator():
    root = find_root(os.environ["ARCPUZZLES_HOME"])
    puzzle = Catalog().get(TASK_ID)
    source = root / puzzle["generator"]
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    assert source_sha == puzzle["generator_sha256"]
    spec = importlib.util.spec_from_file_location("audit_e5030f1df7fa_generator", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return root, module, {
        "task_id": TASK_ID,
        "generator_version": module.VERSION,
        "generator_path": puzzle["generator"],
        "generator_sha256": source_sha,
        "rule_hash": puzzle["rule_hash"],
        "source_phase": "unchanged audit source",
        "declared_canonical_shortcuts": getattr(module, "CANONICAL_SHORTCUTS", None),
        "declared_lesson_competitors": getattr(module, "LESSON_COMPETITORS", None),
    }


def prepare():
    root, generator, identity = identity_and_generator()
    pairs = canonical_pairs(TASK_ID, root=root)
    cases = []
    grids = []
    for pair in pairs:
        grids.append(pair["input"])
        cases.append({
            "input_index": len(grids) - 1,
            "kind": "canonical",
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "difficulty": None,
            "self_check_errors": generator.self_check(pair["input"]),
            "canonical_output": pair["output"],
        })
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            grid = generator.generate(seed, 0, difficulty=band)
            grids.append(grid)
            cases.append({
                "input_index": len(grids) - 1,
                "kind": "generated",
                "seed": seed,
                "sample_index": 0,
                "difficulty": band,
                "overrides": {},
                "self_check_errors": generator.self_check(grid, difficulty=band),
            })
    write_json("input.json", grids)
    write_json("cases.json", {**identity, "cases": cases})
    print(json.dumps({**identity, "input_count": len(grids),
                      "canonical_count": len(pairs), "generated_count": len(grids) - len(pairs),
                      "self_check_failures": [c for c in cases if c["self_check_errors"]]}, indent=2))


def compare():
    _, _, identity = identity_and_generator()
    cases_file = json.loads((HERE / "cases.json").read_text())
    assert cases_file["generator_sha256"] == identity["generator_sha256"]
    assert cases_file["rule_hash"] == identity["rule_hash"]
    grids = json.loads((HERE / "input.json").read_text())
    reference = json.loads((HERE / "racket.json").read_text())
    # The supported apply command supplies the executed source/rule identity.
    assert reference["generator_sha256"] == identity["generator_sha256"]
    assert reference["executed_rule_hash"] == identity["rule_hash"]
    assert reference["rule_hash_matches_catalog"] is True
    identity["rule_text_sha256"] = reference["rule_text_sha256"]
    assert all(row["valid_output"] and row["error"] is None for row in reference["results"])
    outputs = [row["output"] for row in reference["results"]]
    assert len(outputs) == len(grids) == len(cases_file["cases"])
    cases = []
    witnesses = []
    for case, grid, actual in zip(cases_file["cases"], grids, outputs):
        rival = isolated_component_rival(grid)
        errors = [{"row": r, "column": c, "racket": actual[r][c], "rival": rival[r][c]}
                  for r in range(len(grid)) for c in range(len(grid[0])) if actual[r][c] != rival[r][c]]
        row = {**case, "rival_matches_racket": not errors,
               "different_cells": errors}
        if "canonical_output" in row:
            row["racket_matches_canonical"] = actual == row.pop("canonical_output")
        cases.append(row)
        if errors:
            witnesses.append({**identity, **row, "input": grid,
                              "actual_racket_output": actual, "rival_output": rival,
                              "domain": "Canonical and validator-accepted; outside the generator's isolated-ring support.",
                              "reference_command": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK_ID,
                                                    "--input", "../checks/audit/e5030f1df7fa/input.json",
                                                    "--out", "../checks/audit/e5030f1df7fa/racket.json"],
                              "reference_command_cwd": "packet_root (WORK)",
                              "effective_payload_cwd": "repo"})
    generated = [c for c in cases if c["kind"] == "generated"]
    canonical = [c for c in cases if c["kind"] == "canonical"]
    summary = {
        **identity,
        "rival": "Fill centers only of yellow 4-connected components whose entire component is an eight-cell 3x3 ring.",
        "generated_inputs": len(generated),
        "generated_unique_inputs": len({json.dumps(grids[c["input_index"]]) for c in generated}),
        "generated_rival_matches": sum(c["rival_matches_racket"] for c in generated),
        "generated_self_check_passes": sum(not c["self_check_errors"] for c in generated),
        "generated_seed_range": [0, 7],
        "generated_sample_index": 0,
        "generated_difficulties": ["easy", "medium", "hard"],
        "generated_overrides": {},
        "canonical_pairs": len(canonical),
        "canonical_racket_matches": sum(c["racket_matches_canonical"] for c in canonical),
        "canonical_rival_matches": sum(c["rival_matches_racket"] for c in canonical),
        "canonical_self_check_passes": sum(not c["self_check_errors"] for c in canonical),
        "witness_count": len(witnesses),
        "cases": cases,
    }
    write_json("probe.json", summary)
    write_json("witness.json", witnesses)
    print(json.dumps({key: value for key, value in summary.items() if key != "cases"}, indent=2))
    assert len(witnesses) == 1
    assert witnesses[0]["split"] == "train" and witnesses[0]["pair_index"] == 2
    assert summary["canonical_racket_matches"] == 5
    assert summary["generated_rival_matches"] == summary["generated_self_check_passes"] == 24


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "compare"))
    args = parser.parse_args()
    prepare() if args.mode == "prepare" else compare()
