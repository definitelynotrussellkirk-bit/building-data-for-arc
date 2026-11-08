"""Replay one source-bound peer learnability finding with protected Racket labels.

Run from outer packet: WORK/.venv/bin/python review.py run python3
../checks/0e4861d08306/probe.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

TASK = "0e4861d08306"
EXPECTED = "79ba403364de6a3378f7bc57bfdf32ae7f3b0db06be50ba387443f09dfc59622"
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1] / "repo"
RUNTIME = ROOT / "shared/runtime"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]

from reviewer_support import load_selected_generator
from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _real_evaluator


def all_red_seeds(grid):
    """Independent rival: flood from every red seed along red/blue adjacency."""
    result = [row[:] for row in grid]
    seen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2}
    pending = list(seen)
    while pending:
        r, c = pending.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = r + dr, c + dc
            if (0 <= rr < len(grid) and 0 <= cc < len(grid[0])
                    and (rr, cc) not in seen and grid[rr][cc] in (1, 2)):
                seen.add((rr, cc))
                pending.append((rr, cc))
    for r, c in seen:
        if result[r][c] == 1:
            result[r][c] = 3
    return result


def main():
    source = ROOT / f"generators/{TASK}/generator.py"
    # Check exact source bytes before importing or sampling the generator.
    actual = hashlib.sha256(source.read_bytes()).hexdigest()
    assert actual == EXPECTED, ("source changed; finding must be retriaged", actual)
    module, selected_path, selected_digest = load_selected_generator(TASK, root=ROOT)
    assert selected_path.resolve() == source.resolve() and selected_digest == actual
    catalog = Catalog(ROOT)
    metadata = catalog.describe(TASK)
    variants = catalog._variants()[metadata.get("rule_task_id", TASK)]
    programs = {v["program_solution"] for v in variants}
    assert len(programs) == 1
    program = programs.pop()
    rule_hash = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()
    assert rule_hash == "351d458c75d227ab22cc1a53dd493fb3a29142742a72aa2f457729af2aa1c2f5"
    apply, runtime_identity, bridge = _real_evaluator(RUNTIME)
    cases = []
    try:
        for sample_index in (1, 2, 3, 4):
            grid = module.generate(0, sample_index, difficulty="easy")
            assert module.self_check(grid) == []
            output = apply(program, grid)
            assert isinstance(output, list) and output == module.rule_mirror(grid)
            rival = all_red_seeds(grid)
            differences = [[r, c] for r, row in enumerate(output)
                           for c, value in enumerate(row) if rival[r][c] != value]
            cases.append({"sample_index": sample_index, "input": grid,
                          "output": output, "rival_output": rival,
                          "profile": module.canonical_profile_signature(grid),
                          "difference_cells": differences})
    finally:
        bridge.close()
    assert [c["profile"] for c in cases] == ["authored"] * 3 + ["generalized"]
    assert all(not c["difference_cells"] for c in cases[:3])
    assert cases[3]["difference_cells"] == [[4, 4], [4, 5], [4, 6], [5, 4], [5, 5]]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == actual
    witness = {
        "schema": "bounded-peer-learnability-witness-v1", "task_id": TASK,
        "status": "finding_reproduced", "source": source.relative_to(ROOT).as_posix(),
        "source_sha256": actual, "canonical_rule_sha256": rule_hash,
        "generator_declared_rule_hash": module.RULE_HASH,
        "declared_rule_hash_matches_catalog": module.RULE_HASH == rule_hash[:12],
        "source_unchanged": True, "runtime_identity": runtime_identity,
        "recipe": {"seed": 0, "difficulty": "easy", "demo_sample_indexes": [1, 2, 3],
                   "query_sample_index": 4, "overrides": {}},
        "rival": "Flood from every red seed through 4-connected red/blue cells",
        "demo_fit": [True, True, True], "query_disagrees": True,
        "query_difference_cells": cases[3]["difference_cells"],
        "public": {"train": [{"input": c["input"], "output": c["output"]}
                              for c in cases[:3]], "test": [{"input": cases[3]["input"]}]},
        "private": {"cases": cases, "canonical_program": program},
        "limits": "One retained raw generator lesson recipe, four protected Racket reference calls, "
                  "one independent Python rival. No export-materializer replay, distribution estimate, "
                  "full battery, universal learnability claim, production repair, or acceptance change.",
    }
    (OUT / "witness.json").write_text(json.dumps(witness, separators=(",", ":")) + "\n")
    summary = {k: witness[k] for k in ("task_id", "status", "source_sha256", "recipe",
                                     "demo_fit", "query_disagrees", "query_difference_cells", "limits")}
    (OUT / "result.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
