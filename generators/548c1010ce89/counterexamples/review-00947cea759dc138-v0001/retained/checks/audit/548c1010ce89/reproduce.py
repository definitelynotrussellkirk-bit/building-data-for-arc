#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "548c1010ce89"
SEED = 727
DIFFICULTY = "medium"
INDICES = range(4)


def digest(value):
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def columns_only(grid):
    h, w = len(grid), len(grid[0])
    empty_cols = {c for c in range(w) if all(grid[r][c] == 0 for r in range(h))}
    return [[2 if c in empty_cols else grid[r][c] for c in range(w)] for r in range(h)]


def main():
    here = Path(__file__).resolve()
    repo = find_root(here)
    module, source, source_sha256 = load_selected_generator(TASK_ID, root=repo)
    cases = []
    inputs = []
    for index in INDICES:
        grid = module.generate(SEED, index, difficulty=DIFFICULTY)
        errors = module.self_check(grid, difficulty=DIFFICULTY)
        info = module._analysis(grid)
        authority = module.rule_mirror(grid)
        rival = columns_only(grid)
        cases.append({
            "sample_index": index,
            "role": "demonstration" if index < 3 else "query",
            "scene_profile": info["scene_profile"],
            "shape": [len(grid), len(grid[0])],
            "empty_rows": list(info["empty_rows"]),
            "empty_cols": list(info["empty_cols"]),
            "self_check_errors": errors,
            "input": grid,
            "authority_output": authority,
            "columns_only_rival_output": rival,
            "rival_matches_authority": rival == authority,
            "input_sha256": digest(grid),
            "authority_sha256": digest(authority),
            "rival_sha256": digest(rival),
        })
        inputs.append(grid)
    report = {
        "schema": "audit-reproduction/1",
        "finding_id": "548-columns-only-schedule",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(repo)),
        "generator_sha256": source_sha256,
        "rule_hash": module.RULE_HASH,
        "seed": SEED,
        "difficulty": DIFFICULTY,
        "sample_indices": list(INDICES),
        "lesson_policy": "indices 0..2 demonstrations; index 3 query",
        "rival_rule": "paint every all-zero column red 2; preserve every other cell",
        "all_inputs_pass_target_validator": all(not c["self_check_errors"] for c in cases),
        "all_demonstrations_fit_rival": all(c["rival_matches_authority"] for c in cases[:3]),
        "query_disagrees_with_rival": not cases[3]["rival_matches_authority"],
        "cases": cases,
    }
    target = here.parent
    (target / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
    (target / "counterexample.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in (
        "generator_sha256", "all_inputs_pass_target_validator",
        "all_demonstrations_fit_rival", "query_disagrees_with_rival")}, indent=2))
    for case in cases:
        print(case["sample_index"], case["scene_profile"], case["shape"],
              case["empty_rows"], case["empty_cols"], case["rival_matches_authority"])
    return 0 if (report["all_inputs_pass_target_validator"]
                 and report["all_demonstrations_fit_rival"]
                 and report["query_disagrees_with_rival"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
