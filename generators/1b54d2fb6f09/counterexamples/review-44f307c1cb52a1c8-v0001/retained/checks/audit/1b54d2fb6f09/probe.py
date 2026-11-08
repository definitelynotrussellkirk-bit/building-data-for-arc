"""Findings-only audit of a source-bound missing two-cell segment boundary.

From WORK:
  PYTHONPATH=repo/src:repo/shared/runtime python checks/audit/1b54d2fb6f09/probe.py prepare
  python run_with_racket.py python -m arcpuzzles apply 1b54d2fb6f09 --input ../checks/audit/1b54d2fb6f09/input.json --out ../checks/audit/1b54d2fb6f09/racket.json
  PYTHONPATH=repo/src:repo/shared/runtime python checks/audit/1b54d2fb6f09/probe.py summarize

The rival is independent audit code. Only the public Racket receipt supplies
new authoritative labels. No generator, rule, canonical data or tests are edited.
"""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK = "1b54d2fb6f09"
BASE = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def write(name, value):
    (BASE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def skip_length_two_segments(grid):
    """Plausible nearby rule: cyan endpoints only for segments of length >=3."""
    h, w = len(grid), len(grid[0])
    seen = set()
    out = deepcopy(grid)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 2 or (r, c) in seen:
                continue
            todo = deque([(r, c)])
            seen.add((r, c))
            component = []
            while todo:
                row, col = todo.popleft()
                component.append((row, col))
                for nr, nc in ((row - 1, col), (row + 1, col),
                               (row, col - 1), (row, col + 1)):
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 2
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            if len(component) < 3:
                continue
            rows = {p[0] for p in component}
            cols = {p[1] for p in component}
            if len(rows) == 1 or len(cols) == 1:
                for row, col in (min(component), max(component)):
                    out[row][col] = 8
    return out


def materialize_witness():
    grid = [[0] * 10 for _ in range(9)]
    # Two straight red segments; one four-cell bent red negative control.
    red = ((1, 1), (1, 2), (1, 6), (2, 6), (3, 6), (4, 6),
           (6, 1), (7, 1), (8, 1), (8, 2))
    for row, col in red:
        grid[row][col] = 2
    for col in (6, 7, 8):
        grid[6][col] = 3
    expected = deepcopy(grid)
    for row, col in ((1, 1), (1, 2), (1, 6), (4, 6)):
        expected[row][col] = 8
    return grid, expected


def load_target():
    root = find_root(Path("repo"))
    source = root / "generators" / TASK / "generator.py"
    actual_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    assignment = json.loads(Path("AUDIT_ASSIGNMENT.json").read_text())
    target, = [item for item in assignment["targets"] if item["task_id"] == TASK]
    assert actual_hash == target["generator_sha256"]
    spec = importlib.util.spec_from_file_location("audit_generator", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    description = Catalog(root).describe(TASK)
    programs = []
    for line in (root / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            programs.append(row["program_solution"])
    assert len(set(programs)) == 1
    return root, module, {
        "task_id": TASK,
        "audit_packet_id": assignment["packet_id"],
        "generator_sha256": actual_hash,
        "catalog_rule_hash": description["rule_hash"],
        "canonical_program_text_sha256": hashlib.sha256(programs[0].encode()).hexdigest(),
        "approval_reasons_at_audit": description["approval_reasons"],
    }


def prepare():
    root, gen, identity = load_target()
    grids, cases = [], []
    canonical = canonical_pairs(TASK, root=root, labeled_only=True)
    for pair in canonical:
        grids.append(pair["input"])
        rival = skip_length_two_segments(pair["input"])
        cases.append({
            "kind": "canonical", "variant": pair["variant"], "split": pair["split"],
            "pair_index": pair["pair_index"], "input_sha256": digest(pair["input"]),
            "self_check": gen.self_check(pair["input"]),
            "strict_canonical_like": gen.strict_canonical_like(pair["input"]),
            "rival_output": rival, "canonical_output": pair["output"],
            "rival_fits_stored_label": rival == pair["output"],
        })
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(4):
            grid = gen.generate(0, sample_index, difficulty=difficulty)
            grids.append(grid)
            cases.append({
                "kind": "generated", "seed": 0, "sample_index": sample_index,
                "difficulty": difficulty, "overrides": {},
                "input_sha256": digest(grid), "self_check": gen.self_check(grid),
                "strict_canonical_like": gen.strict_canonical_like(grid),
                "observed_axes": gen.observe_overrides(grid),
                "rival_output": skip_length_two_segments(grid),
            })
    grid, expected = materialize_witness()
    grids.append(grid)
    cases.append({
        "kind": "handmade_domain_witness", "input_sha256": digest(grid),
        "construction": "9x10, horizontal red length2, vertical red length4, four-cell bent red, green length3 line",
        "seed": None, "sample_index": None, "overrides": None,
        "self_check": gen.self_check(grid),
        "strict_canonical_like": gen.strict_canonical_like(grid),
        "observed_axes": gen.observe_overrides(grid),
        "rival_output": skip_length_two_segments(grid),
        "hand_written_expected_output": expected,
    })
    assert all(not case["self_check"] and not case["strict_canonical_like"] for case in cases)
    write("input.json", grids)
    write("prepared.json", {"identity": identity, "rival_name": "skip_length_two_segments",
                           "cases": cases, "case_count": len(cases)})
    print(json.dumps({"prepared_cases": len(cases), "canonical": len(canonical),
                      "generated": 12, "handmade": 1, "identity": identity}, indent=2))


def summarize():
    _, _, current_identity = load_target()
    prepared = json.loads((BASE / "prepared.json").read_text())
    assert prepared["identity"] == current_identity
    receipt = json.loads((BASE / "racket.json").read_text())
    assert receipt["generator_sha256"] == current_identity["generator_sha256"]
    assert receipt["rule_hash_matches_catalog"] is True
    assert len(receipt["results"]) == prepared["case_count"]
    assert all(row["error"] is None for row in receipt["results"])
    cases = []
    for case, actual in zip(prepared["cases"], receipt["results"]):
        result = dict(case)
        result["actual_racket_output"] = actual["output"]
        result["actual_output_sha256"] = actual["output_sha256"]
        result["rival_matches_racket"] = case["rival_output"] == actual["output"]
        if "canonical_output" in case:
            assert case["canonical_output"] == actual["output"]
        if "hand_written_expected_output" in case:
            assert case["hand_written_expected_output"] == actual["output"]
        cases.append(result)
    canonical = [case for case in cases if case["kind"] == "canonical"]
    generated = [case for case in cases if case["kind"] == "generated"]
    witness, = [case for case in cases if case["kind"] == "handmade_domain_witness"]
    assert all(case["rival_matches_racket"] for case in canonical + generated)
    assert not witness["rival_matches_racket"]
    witness_grid = json.loads((BASE / "input.json").read_text())[-1]
    witness["input"] = witness_grid
    witness["differing_cells"] = [
        {"row": r, "col": c, "rival": witness["rival_output"][r][c],
         "racket": witness["actual_racket_output"][r][c]}
        for r in range(len(witness_grid)) for c in range(len(witness_grid[0]))
        if witness["rival_output"][r][c] != witness["actual_racket_output"][r][c]
    ]
    report = {
        "schema": "arcpuzzles-target-audit-counterexample-v1",
        "classification": "reproduced_domain_coverage_defect",
        "identity": current_identity,
        "reference_identity": {key: receipt.get(key) for key in (
            "catalog_rule_hash", "executed_rule_hash", "rule_text_sha256",
            "rule_hash_matches_catalog", "generator_sha256")},
        "rival_name": prepared["rival_name"],
        "canonical_rival_fit": {"matching": len(canonical), "total": len(canonical)},
        "sampled_generated_rival_fit": {"matching": len(generated), "total": len(generated)},
        "coverage_argument": (
            "The selected construction requests minimum segment length4 for its first straight "
            "component and minimum3 for every later one, keeps red components4-separated, "
            "uses a bent nonstraight negative control, and has no length override. Thus every "
            "successfully generated ordinary input lacks the lawful length2 branch."
        ),
        "witness": witness,
        "cases": cases,
        "target_source_modified": False,
        "target_rule_modified": False,
        "existing_metadata_audit_resolution": "unchanged_needs_triage",
    }
    write("counterexample.json", report)
    print(json.dumps({"classification": report["classification"],
                      "canonical_fit": report["canonical_rival_fit"],
                      "generated_fit": report["sampled_generated_rival_fit"],
                      "witness_differing_cells": witness["differing_cells"],
                      "identity": current_identity}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "summarize"))
    args = parser.parse_args()
    globals()[args.action]()
