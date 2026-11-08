"""Check public-apply labels and retain exact, source-bound audit findings."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator


TASK = "7d970a1ea99b"
OUT = Path(__file__).resolve().parent


def read(name):
    return json.loads((OUT / name).read_text())


def main():
    report = read("probe_report.json")
    cases = read("reference_cases.json")
    applied = read("racket.json")
    _, _, current_hash = load_selected_generator(TASK, root=find_root(__file__))
    assert current_hash == report["sources"]["generator_sha256"] == applied["generator_sha256"]
    assert applied["reference"] == "canonical" and applied["rule_hash_matches_catalog"]
    assert len(cases) == len(applied["results"]) == 12
    verification = []
    for index, (case, result) in enumerate(zip(cases, applied["results"], strict=True)):
        grid = case["input"]
        assert result["input"] == grid and result["index"] == index
        assert result["valid_output"] and result["error"] is None
        output = result["output"]
        expected_overlay = [[grid[c][r] if grid[c][r] != 0 else grid[r][c]
                             for c in range(len(grid))] for r in range(len(grid))]
        assert output == expected_overlay
        overwritten = [{"row": r, "column": c, "input_color": grid[r][c], "output_color": output[r][c]}
                       for r in range(len(grid)) for c in range(len(grid))
                       if grid[r][c] and grid[r][c] != output[r][c]]
        canonical_match = None
        if "expected_output" in case:
            canonical_match = output == case["expected_output"]
            assert canonical_match
        verification.append({"index": index, "kind": case["kind"],
                             "canonical_match": canonical_match,
                             "nonzero_input_cells_overwritten": overwritten,
                             "output_is_symmetric": all(output[r][c] == output[c][r] for r in range(len(grid)) for c in range(len(grid))),
                             "output_equals_input": output == grid})
    assert report["prior_reproduction"]["matches_retained_counterexample"]
    assert report["prior_reproduction"]["self_check_errors"] == []
    assert verification[0]["nonzero_input_cells_overwritten"] == [
        {"row": 2, "column": 3, "input_color": 2, "output_color": 4},
        {"row": 3, "column": 2, "input_color": 4, "output_color": 2},
    ]
    by_name = {row["name"]: row for row in report["override_cases"]}
    for name in ("legal_side_4", "legal_side_16", "legal_n_cells_1", "legal_n_cells_12"):
        assert by_name[name]["status"] == "raised"
    for name in ("invalid_palette_kind", "invalid_texture", "invalid_palette_size", "invalid_n_distinct_colors",
                 "invalid_position_bias", "invalid_density", "unknown_axis"):
        assert by_name[name]["status"] == "returned" and by_name[name]["equal_to_baseline"]
    symmetric = next(row for row in report["degenerate_cases"] if row["texture"] == "already_symmetric")
    assert symmetric["self_check_errors"] == []
    assert verification[-1]["output_equals_input"]
    sources = {**report["sources"], "executed_rule_hash": applied["executed_rule_hash"],
               "applied_rule_text_sha256": applied["rule_text_sha256"],
               "public_apply_receipt_sha256": hashlib.sha256((OUT / "racket.json").read_bytes()).hexdigest()}
    result = {
        "task_id": TASK, "sources": sources,
        "reference_cases_checked": len(verification), "canonical_labels_checked": 5,
        "reference_errors": 0, "canonical_label_mismatches": 0,
        "verification": verification,
        "finding_checks": {"retained_domain_failure_reproduced": True,
                           "four_documented_legal_override_rejections_reproduced": True,
                           "seven_invalid_or_unknown_override_acceptances_reproduced": True,
                           "already_symmetric_degenerate_self_check_false_acceptance_reproduced": True},
        "limits": "Public Racket apply labels exactly 12 retained cases: four generated witnesses, five canonical pairs, and three degenerates. The 600-draw census counts are structural; only those generated witnesses received Racket labels. No exhaustive seed, override-product, or lesson-identifiability claim.",
    }
    counterexample = {"finding": "Generated transpose-color conflict remains accepted; original nonzero cells are overwritten.",
                      "task_id": TASK, "sources": sources, **report["prior_reproduction"],
                      "racket_output": applied["results"][0]["output"],
                      "nonzero_input_cells_overwritten": verification[0]["nonzero_input_cells_overwritten"],
                      "prior_return": "review-10afcda5143660c3:v0001"}
    for name, value in (("reference_verification.json", result), ("counterexample.json", counterexample)):
        path = OUT / name
        if path.exists():
            raise FileExistsError(path)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"reference_cases_checked": 12, "canonical_labels_checked": 5,
                      "reference_errors": 0, "canonical_label_mismatches": 0,
                      "finding_checks": result["finding_checks"],
                      "executed_rule_hash": sources["executed_rule_hash"],
                      "applied_rule_text_sha256": sources["applied_rule_text_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
