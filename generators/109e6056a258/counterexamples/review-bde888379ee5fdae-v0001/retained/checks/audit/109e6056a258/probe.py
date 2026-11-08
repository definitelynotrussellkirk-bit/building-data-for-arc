"""Reproduce ignored exact key controls without editing the target generator.

Run prepare through the packet wrapper, execute supported Racket apply on
input.json, then run summarize through the wrapper. No private runner imports.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK = "109e6056a258"
HERE = Path(__file__).resolve().parent
SEED = "audit-op-tf-exact-controls"
INDEX = 0
DIFFICULTY = "medium"
REQUESTS = [{"op_key": 1, "tf_key": 1}, {"op_key": 5, "tf_key": 6}]


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def prepare():
    root = find_root(__file__)
    gen, source, source_hash = load_selected_generator(TASK, root=root)
    rows = [json.loads(s) for s in canonical_path(root).read_text().splitlines()
            if s.strip() and json.loads(s).get("task_id") == TASK]
    assert len(rows) == 1
    row = rows[0]
    program_hash = hashlib.sha256(row["program_solution"].encode()).hexdigest()
    draws = [gen.generate(SEED, INDEX, difficulty=DIFFICULTY, **request)
             for request in REQUESTS]
    observed = [{"op_key": grid[0][0], "tf_key": grid[0][-1]} for grid in draws]
    validator = [gen.self_check(grid, difficulty=DIFFICULTY) for grid in draws]
    assert draws[0] == draws[1], "Exact-control defect no longer reproduced"
    assert all(not errors for errors in validator), validator
    counterfactuals = []
    for request in REQUESTS:
        grid = [r[:] for r in draws[0]]
        grid[0][0] = request["op_key"]
        grid[0][-1] = request["tf_key"]
        assert not gen.self_check(grid, difficulty=DIFFICULTY)
        counterfactuals.append(grid)
    # Three Racket inputs: the actual draw, then identical geometry with each
    # requested key pair written literally. These retain valid domain shapes.
    inputs = [draws[0], *counterfactuals]
    write("input.json", inputs)
    record = {
        "schema": "arcpuzzles-audit-exact-key-controls-v1",
        "task_id": TASK,
        "phase": "audit-final-unchanged-source",
        "generator_path": str(source.relative_to(root)),
        "generator_sha256": source_hash,
        "canonical_rule_sha256": program_hash,
        "canonical_rule_hash": program_hash[:12],
        "seed": SEED,
        "sample_indices": [INDEX],
        "difficulty": DIFFICULTY,
        "requested_overrides": REQUESTS,
        "observed_corner_keys": observed,
        "identical_draw_pair_count": 1,
        "paired_draw_denominator": 1,
        "unique_generated_input_count": len({grid_hash(g) for g in draws}),
        "generated_inputs_validator_errors": validator,
        "request_mismatch_count": sum(a != b for a,b in zip(REQUESTS, observed)),
        "request_count": len(REQUESTS),
        "input_order": ["actual generated input", "honour requested op=1 tf=1 on same geometry", "honour requested op=5 tf=6 on same geometry"],
        "inputs": inputs,
        "input_sha256": [grid_hash(g) for g in inputs],
        "counterfactual_validator_errors": [gen.self_check(g, difficulty=DIFFICULTY) for g in counterfactuals],
        "counterfactual_domain": "Only corner keys changed to declared legal values; sizes, shapes, separation, positions and shape colors are unchanged from one accepted generated input.",
        "existing_finding": "Confirms unresolved review-78fdee0a9f8452e7:v0001 on the same source hash; this is not a newly discovered defect.",
        "scope": "One fixed seed/sample pair and two key-only interventions; no random census or all-branch correctness claim.",
        "canonical_pairs_read": sum(len(row.get(k, [])) for k in ("train", "test")),
        "target_tests_present": (root / "generators" / TASK / "tests").is_dir(),
    }
    write("audit_record.json", record)
    print(json.dumps({k:record[k] for k in ["generator_sha256", "canonical_rule_hash", "observed_corner_keys", "identical_draw_pair_count", "request_mismatch_count"]}))


def summarize():
    record = json.loads((HERE / "audit_record.json").read_text())
    racket = json.loads((HERE / "racket.json").read_text())
    root = find_root(__file__)
    _, _, source_hash = load_selected_generator(TASK, root=root)
    assert source_hash == record["generator_sha256"] == racket["generator_sha256"]
    assert racket["executed_rule_hash"] == record["canonical_rule_hash"]
    assert racket["rule_hash_matches_catalog"] is True
    rows = racket["results"]
    assert len(rows) == 3
    assert [r["input"] for r in rows] == record["inputs"]
    assert all(r["valid_output"] and r["error"] is None for r in rows)
    actual = rows[0]["output"]
    rivals = [r["output"] for r in rows[1:]]
    assert all(out != actual for out in rivals), "Chosen key controls must matter on this witness"
    assert rivals[0] != rivals[1]
    record.update({
        "executed_rule_text_sha256": racket["rule_text_sha256"],
        "actual_racket_output": actual,
        "rival_definition": "Apply the actual canonical Racket rule to the same generated geometry with each requested legal corner-key pair written literally.",
        "rival_outputs": [{"requested_overrides": request, "output": output}
                          for request,output in zip(REQUESTS,rivals)],
        "racket_valid_output_count": len(rows),
        "racket_case_denominator": len(rows),
        "racket_command": racket["command"],
        "racket_cwd_relative_to_WORK": "repo",
        "racket_evidence": "checks/audit/109e6056a258/racket.json",
        "conclusion": "Existing exact-control defect reproduced: both requests are ignored; both corresponding lawful interventions change the reference output.",
    })
    write("audit_record.json", record)
    print(json.dumps({"reproduced": True, "actual_keys": record["observed_corner_keys"],
                      "actual_output": actual, "honour_requested_keys_outputs": rivals,
                      "racket_valid_cases": len(rows), "source_unchanged": True}))


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("action", choices=["prepare", "summarize"])
    a=p.parse_args()
    {"prepare":prepare,"summarize":summarize}[a.action]()
