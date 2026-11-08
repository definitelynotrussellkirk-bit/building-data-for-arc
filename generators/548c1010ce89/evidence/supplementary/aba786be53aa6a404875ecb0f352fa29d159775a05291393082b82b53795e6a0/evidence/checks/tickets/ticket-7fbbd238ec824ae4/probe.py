"""One bounded replay of the current columns-only shortcut witness.

The assignment seed identifies this ticket. The reproduction seed 727 comes
from the pinned current audit; this is an independent replay, not a fresh search.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = REPO / "generators/548c1010ce89"
sys.path.insert(0, str(REPO / "shared/runtime"))
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def sha(data):
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid):
    return sha(json.dumps(grid, separators=(",", ":")).encode())


def columns_only(grid):
    output = [row[:] for row in grid]
    for col in range(len(grid[0])):
        if all(row[col] == 0 for row in grid):
            for row in output:
                row[col] = 2
    return output


def main():
    started = time.monotonic()
    task_id = "548c1010ce89"
    source = TASK / "generator.py"
    expected_sha = "e006dcd911c368137baa9767168002b5283c172912f57597158bf4152ac0317c"
    assert sha(source.read_bytes()) == expected_sha
    assignment_path = WORK / "AUDIT_ASSIGNMENT.json"
    ticket = next(t for t in json.loads(assignment_path.read_text())["tickets"]
                  if t["ticket_id"] == "ticket-7fbbd238ec824ae4")
    assert ticket["generator_sha256"] == expected_sha
    spec = importlib.util.spec_from_file_location("peer_generator", source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    rules = set()
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            rules.add(row["program_solution"])
    assert len(rules) == 1
    rule = rules.pop()
    executed_rule_hash = sha(" ".join(rule.split()).encode())[:12]
    assert executed_rule_hash == ticket["rule_hash"] == "506bc3722b18"
    records = []
    with RacketBridge(timeout=20.0) as bridge:
        bridge.eval_text(f"(define ticket_rule {wrap_rule(rule)})")
        for index in range(4):
            grid = generator.generate(727, index, difficulty="medium")
            errors = generator.self_check(grid, difficulty="medium")
            assert errors == [], (index, errors)
            bridge.define_grid("ticket_input", grid)
            output = bridge.eval_text("(ticket_rule ticket_input)")
            rows = [i for i, row in enumerate(grid) if all(value == 0 for value in row)]
            cols = [j for j in range(len(grid[0])) if all(row[j] == 0 for row in grid)]
            intended = [[2 if r in rows or c in cols else value
                         for c, value in enumerate(row)] for r, row in enumerate(grid)]
            assert output == intended, "authority does not match stated empty-line rule"
            rival = columns_only(grid)
            differences = [[r, c] for r in range(len(grid)) for c in range(len(grid[0]))
                           if rival[r][c] != output[r][c]]
            records.append({"split": "train" if index < 3 else "test",
                            "sample_index": index, "input": grid, "output": output,
                            "rival_output": rival, "self_check": errors,
                            "scene_profile": generator.observe_overrides(grid)["scene_profile"],
                            "shape": [len(grid), len(grid[0])], "empty_rows": rows,
                            "empty_cols": cols, "input_sha256": grid_hash(grid),
                            "output_sha256": grid_hash(output), "rival_sha256": grid_hash(rival),
                            "rival_matches_authority": rival == output,
                            "differing_cells": differences})
        racket_binary = bridge.racket_binary
    assert all(row["rival_matches_authority"] for row in records[:3])
    assert not records[3]["rival_matches_authority"]
    assert sha(source.read_bytes()) == expected_sha
    elapsed = time.monotonic() - started
    assert elapsed <= 120, elapsed
    witness = {"schema": "bounded-adversarial-witness-v1", "ticket_id": ticket["ticket_id"],
               "ticket_type": ticket["type"], "task_id": task_id,
               "assignment_seed": ticket["seed"],
               "seed_use": "Ticket identity; reproduction seed comes from the same-source current audit.",
               "selection": "Independent replay of retained seed-727 finding, not a new search.",
               "seed": 727, "difficulty": "medium", "sample_indices": [0, 1, 2, 3],
               "overrides": {}, "n_train": 3, "n_test": 1,
               "source_path": str(source.relative_to(REPO)), "generator_sha256": expected_sha,
               "rule_task_id": task_id, "executed_rule_hash": executed_rule_hash,
               "rule_text_sha256": sha(rule.encode()), "rule_source": rule,
               "assignment_sha256": sha(assignment_path.read_bytes()),
               "probe_sha256": sha(Path(__file__).read_bytes()),
               "racket_binary": racket_binary,
               "racket_wrapper_sha256": sha(Path(racket_binary).read_bytes()),
               "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
               "probe_elapsed_seconds": elapsed, "targeted_probes": 1,
               "rival": "Paint all-zero columns red 2; otherwise preserve the grid.",
               "pairs": records,
               "conclusion": "All three lawful demonstrations admit the columns-only shortcut; the lawful query requires row painting too.",
               "limitations": ["One known witness replayed; no new random search, battery, or census.",
                               "No source, audit disposition, approval, or training admission was changed."]}
    (HERE / "witness.json").write_text(json.dumps(witness, separators=(",", ":")) + "\n")
    print(json.dumps({"source_sha256": expected_sha, "rule_hash": executed_rule_hash,
                      "probe_seconds": elapsed, "all_inputs_valid": True,
                      "demo_rival_matches": [r["rival_matches_authority"] for r in records[:3]],
                      "query_rival_matches": records[3]["rival_matches_authority"],
                      "query_differing_cells": len(records[3]["differing_cells"]),
                      "profiles": [r["scene_profile"] for r in records]}))


if __name__ == "__main__":
    main()
