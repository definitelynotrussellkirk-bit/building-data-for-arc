"""Findings-only source-bound control audit; execute through run_with_racket.py."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog

TASK_ID = "2587fd13e366"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit" / TASK_ID
GENERATOR = ROOT / "generators" / TASK_ID / "generator.py"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_target():
    spec = importlib.util.spec_from_file_location("audited_generator", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def boxes(module, grid):
    result = []
    for cells in module._blue_components(grid):
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        result.append([min(rs), min(cs), max(rs), max(cs)])
    return result


def main():
    module = load_target()
    task = Catalog().get(TASK_ID)
    rule = task["variants"][0]["program_solution"]
    assert all(row["program_solution"] == rule for row in task["variants"])
    source = {
        "generator_path": str(GENERATOR.relative_to(ROOT)),
        "generator_sha256": sha(GENERATOR.read_bytes()),
        "generator_version": module.VERSION,
        "canonical_rule_exact_utf8_sha256": sha(rule.encode()),
        "canonical_rule_whitespace_normalized_sha256": sha(" ".join(rule.split()).encode()),
        "catalog_rule_hash": task["rule_hash"],
        "canonical_rule": rule,
        "current_notes_sha256": sha((GENERATOR.parent / "notes.md").read_bytes()),
        "current_audit_unresolved": task["audit_unresolved"],
    }
    base = dict(grid_h=22, grid_w=22, rect_size_kind="large", position_bias="spread")
    requests = [
        ("A1_count_not_honored", 2, dict(base, n_rects=5)),
        ("A1_center_fallback", 0, dict(base, n_rects=3, position_bias="center")),
        ("A2_valid_single_rectangle_rejected", 0, dict(base, n_rects=1)),
    ]
    cases = []
    for case_id, seed, overrides in requests:
        grid = module.generate(seed, 0, difficulty="hard", **overrides)
        bbs = boxes(module, grid)
        errors = module.self_check(grid, difficulty="hard")
        cases.append({
            "case_id": case_id,
            "seed": seed,
            "sample_index": 0,
            "difficulty": "hard",
            "overrides": overrides,
            "input": grid,
            "actual_rectangle_bboxes_inclusive": bbs,
            "actual_rectangle_count": len(bbs),
            "actual_rectangle_sizes": [[r2-r1+1,c2-c1+1] for r1,c1,r2,c2 in bbs],
            "self_check_errors": errors,
            "declared_axis_values_valid": True,
            "rectangular_grid_colors_0_and_1_only": bool(grid) and all(len(row)==22 and all(type(v) is int and v in (0,1) for v in row) for row in grid),
            "requested_count_honored": len(bbs) == overrides["n_rects"],
            "requested_large_sizes_honored": all(5 <= r2-r1+1 <= 7 and 5 <= c2-c1+1 <= 7 for r1,c1,r2,c2 in bbs),
            "rival_output": None,
            "rival_status": "not_applicable_control_contract_findings",
        })
    capacity_overrides = dict(base, n_rects=5)
    capacity_grid = module.generate(0, 0, difficulty="hard", **capacity_overrides)
    capacity_boxes = boxes(module, capacity_grid)
    canonical_validation = []
    for index, pair in enumerate(task["variants"][0]["train"]):
        grid = [[int(v) for v in row] for row in pair["input"]]
        canonical_validation.append({"variant":0,"split":"train","pair_index":index,"self_check_errors":module.self_check(grid)})
    report = {
        "task_id": TASK_ID,
        "review_id": "review-bc0c45d2cb547c41",
        "source": source,
        "findings": [
            {"id":"A1","severity":"medium","kind":"override_contract","summary":"Valid requested rectangle counts and sizes are silently weakened. A spread request for five large rectangles returns four despite available capacity; centered requests fall back to two 3x3 rectangles. Both pass self_check."},
            {"id":"A2","severity":"medium","kind":"generator_validator_contract","summary":"AXES advertises n_rects=1 as valid and generate explicitly supports it, but self_check rejects the returned single solid large rectangle."},
        ],
        "cases": cases,
        "capacity_control": {"seed":0,"sample_index":0,"difficulty":"hard","overrides":capacity_overrides,"actual_rectangle_bboxes_inclusive":capacity_boxes,"actual_rectangle_count":len(capacity_boxes),"self_check_errors":module.self_check(capacity_grid)},
        "canonical_train_self_check": canonical_validation,
        "limits": "Focused control checks only. No semantic label disagreement claimed; no full battery or distribution census run. No generator, rule, notes, or task tests changed.",
    }
    assert source["generator_sha256"] == "565e9b65d09b913a54e3ebd4b5f5608e04dd7aeffbaf4d78b829dfa6c2cb2afb"
    assert len(capacity_boxes) == 5
    assert cases[0]["actual_rectangle_count"] == 4 and cases[0]["self_check_errors"] == []
    assert cases[1]["actual_rectangle_sizes"] == [[3,3],[3,3]] and cases[1]["self_check_errors"] == []
    assert cases[2]["actual_rectangle_count"] == 1 and cases[2]["self_check_errors"] == ["normal path should show at least 2 blue rectangles, found 1"]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "input.json").write_text(json.dumps({"inputs":[case["input"] for case in cases]},separators=(",",":"))+"\n")
    (OUT / "witness.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"task_id":TASK_ID,"source":{k:v for k,v in source.items() if k!="canonical_rule"},"cases":[{k:v for k,v in row.items() if k!="input"} for row in cases],"capacity_control":report["capacity_control"],"canonical_train_self_check":canonical_validation},indent=2))


if __name__ == "__main__":
    main()
