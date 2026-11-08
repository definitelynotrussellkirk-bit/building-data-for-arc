"""Source-bound, findings-only audit; run prepare, the recorded CLIs, then verify.

All paths are confined to this audit directory except read-only target imports.
The local-neighbor rival reads the original grid once; it never iterates fills.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "22d736100571"
SOURCE = REPO / "generators" / TASK / "generator.py"
PIN = "67378d6b4be7a0d84490fdc90a8bb4e94a09e75854eb9ee6b1cfdb3ae7f768b6"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def load(name):
    return json.loads((HERE / name).read_text())


def neighbor_rival(grid):
    """Fill every original zero immediately flanked by red on either axis."""
    h, w = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            horizontal = 0 < c < w - 1 and grid[r][c - 1] == grid[r][c + 1] == 2
            vertical = 0 < r < h - 1 and grid[r - 1][c] == grid[r + 1][c] == 2
            if grid[r][c] == 0 and (horizontal or vertical):
                output[r][c] = 2
    return output


def target_module():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == PIN, "Audited source changed"
    sys.path.insert(0, str(REPO / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("audit_target_22d736100571", SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def prepare():
    module = target_module()
    canonical = None
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            assert canonical is None, "Unexpected duplicate canonical record"
            canonical = row
    assert canonical is not None
    rule = canonical["program_solution"]
    labeled = list(canonical["train"])
    tests = canonical["test"]
    labeled += tests if isinstance(tests, list) else [tests]
    labeled = [pair for pair in labeled if "output" in pair]
    grids = [module.generate(0, i, difficulty="easy") for i in range(4)]
    save("input.json", grids[3])
    save("generated_inputs.json", grids)
    save("rival-output.json", neighbor_rival(grids[3]))
    cases = []
    for overrides in ({"grid_h": 4}, {"n_spans": 1},
                      {"texture": "no_gap", "grid_h": 8, "grid_w": 9},
                      {"texture": "no_spans"}):
        case = {"seed": 0, "sample_index": 0, "difficulty": "easy", "overrides": overrides}
        try:
            grid = module.generate(0, 0, difficulty="easy", **overrides)
            case["outcome"] = {"status": "returned", "shape": [len(grid), len(grid[0])],
                               "self_check": module.self_check(grid, difficulty="easy"), "grid": grid}
        except Exception as exc:
            case["outcome"] = {"status": "raised", "type": type(exc).__name__, "message": str(exc)}
        cases.append(case)
    report = {
        "schema": "arcpuzzles-focused-audit-v1", "task_id": TASK,
        "status": "prepared_pending_racket", "source_sha256": PIN,
        "rule_text_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "rule_hash": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12],
        "canonical_record_sha256": digest(canonical),
        "replay": {"seed": 0, "sample_index": 0, "difficulty": "easy", "overrides": {},
                   "n_train": 3, "n_test": 1, "expected_accepted_indices": [0, 1, 2, 3]},
        "self_check": [module.self_check(grid, difficulty="easy") for grid in grids],
        "canonical_rival_fits": [neighbor_rival(pair["input"]) == pair["output"] for pair in labeled],
        "canonical_labeled_pair_count": len(labeled),
        "rival": "Fill original zeros immediately flanked by 2 horizontally or vertically, in one simultaneous pass.",
        "rival_predictions": [neighbor_rival(grid) for grid in grids],
        "prior_lead": {"return_id": "review-01a6511d9d35145b:v0001", "resolution": "needs_triage",
                       "source_matches": True, "newly_remeasured_override_cases": cases},
        "limits": ["A single fixed-seed ordered production lesson is tested; no frequency estimate or all-band claim.",
                   "The rival is an auditor-supplied candidate, not a declared generator hook.",
                   "Canonical fit uses the five saved labeled canonical pairs; reference outputs for the generated lesson are obtained separately through Racket."]}
    save("repro.json", report)
    print(json.dumps({"status": report["status"], "rule_hash": report["rule_hash"],
                      "canonical_rival_fits": report["canonical_rival_fits"], "self_check": report["self_check"]}))


def verify():
    target_module()
    report, receipt, grids = load("repro.json"), load("racket.json"), load("generated_inputs.json")
    lessons = [json.loads(line) for line in (HERE / "lesson.jsonl").read_text().splitlines() if line.strip()]
    assert len(lessons) == 1
    lesson = lessons[0]
    pairs = lesson["train"] + lesson["test"]
    assert len(lesson["train"]) == 3 and len(lesson["test"]) == 1
    assert [pair["input"] for pair in pairs] == grids
    assert receipt["generator_sha256"] == PIN == lesson["provenance"]["generator_sha256"]
    assert receipt["executed_rule_hash"] == report["rule_hash"] == lesson["provenance"]["rule_hash"]
    assert receipt["rule_hash_matches_catalog"]
    assert receipt["results"][0]["input"] == grids[3]
    assert receipt["results"][0]["output"] == pairs[3]["output"]
    comparisons = [neighbor_rival(pair["input"]) == pair["output"] for pair in pairs]
    assert comparisons == [True, True, True, False], comparisons
    assert all(report["canonical_rival_fits"]) and report["self_check"] == [[], [], [], []]
    output, rival = pairs[3]["output"], neighbor_rival(grids[3])
    differences = [{"row": r, "column": c, "reference": output[r][c], "rival": rival[r][c]}
                   for r in range(len(output)) for c in range(len(output[0])) if output[r][c] != rival[r][c]]
    assert differences == [{"row": 2, "column": 7, "reference": 0, "rival": 2}]
    save("output.json", output)
    report.update({"status": "reproduced_teaching_ambiguity", "production_rival_fits": comparisons,
                   "query_differences": differences, "sampling": lesson.get("sampling"),
                   "production_lesson_check": lesson.get("lesson_check"),
                   "reference_generator_domain": receipt["results"][0].get("generator_domain"),
                   "executed_rule_text_sha256": receipt["rule_text_sha256"],
                   "racket_receipt_sha256": hashlib.sha256((HERE / "racket.json").read_bytes()).hexdigest(),
                   "lesson_sha256": hashlib.sha256((HERE / "lesson.jsonl").read_bytes()).hexdigest()})
    save("repro.json", report)
    save("counterexample.json", {
        "schema": "arcpuzzles-audit-counterexample-v1", "task_id": TASK,
        "finding_id": "A22-local-neighbor-teaching", "status": report["status"],
        "generator_sha256": PIN, "rule_hash": receipt["executed_rule_hash"],
        "executed_rule_text_sha256": receipt["rule_text_sha256"],
        "query_replay": {"seed": 0, "sample_index": 3, "difficulty": "easy", "overrides": {}},
        "lesson_replay": report["replay"], "input": grids[3], "racket_output": output,
        "rival_output": rival, "rival_description": report["rival"],
        "differing_cells": differences, "validator": report["reference_generator_domain"],
        "demonstration_rival_fits": comparisons[:3], "canonical_rival_fits": report["canonical_rival_fits"],
        "production_accepted_indices": [p["sample_index"] for p in lesson["sampling"]["accepted_pairs"]],
        "production_rejections": lesson["sampling"]["rejections"],
        "reference_command": {"cwd": "packet_root", "actual_cwd": str(WORK), "payload_cwd": str(REPO),
                              "argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
                                       "--input", "../checks/audit/22d736100571/input.json", "--check-generator-domain",
                                       "--out", "../checks/audit/22d736100571/racket.json"]}})
    print(json.dumps({"status": report["status"], "production_rival_fits": comparisons,
                      "query_differences": differences, "sampling": report["sampling"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "verify"))
    phase = parser.parse_args().phase
    prepare() if phase == "prepare" else verify()
