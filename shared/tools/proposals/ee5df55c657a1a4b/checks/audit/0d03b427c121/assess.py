"""Verify retained Racket evidence and emit minimal source-bound audit findings."""
import hashlib
import json
from pathlib import Path


HOME = Path(__file__).resolve().parent
TASK = "0d03b427c121"


def hash_grid(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def main():
    probe = json.loads((HOME / "probe.json").read_text())
    racket = json.loads((HOME / "racket.json").read_text())
    lesson = json.loads((HOME / "lesson.jsonl").read_text().splitlines()[0])
    assert probe["generator_sha256"] == racket["generator_sha256"] == lesson["provenance"]["generator_sha256"]
    assert probe["catalog_rule_hash"] == racket["executed_rule_hash"] == lesson["executed_rule_hash"]
    assert len(probe["cases"]) == len(racket["results"]) == 10
    combined = {}
    for case, result in zip(probe["cases"], racket["results"], strict=True):
        assert case["input"] == result["input"]
        assert case["input_sha256"] == result["input_sha256"] == hash_grid(case["input"])
        combined[case["case_id"]] = {**case, "racket_result": result}
    binding = {
        "task_id": TASK, "generator_sha256": probe["generator_sha256"],
        "canonical_rule_hash": racket["executed_rule_hash"],
        "canonical_program_sha256": probe["rule_text_sha256"],
        "executed_rule_text_sha256": racket["rule_text_sha256"],
        "canonical_row_sha256": probe["canonical_row_sha256"],
    }
    ordinary = [row for key, row in combined.items() if key.startswith(("control_", "lesson_"))]
    assert len(ordinary) == 7
    assert all(row["racket_result"]["valid_output"] and not row["self_check"]
               and row["racket_result"]["output"] == row["python_mirror_output"] for row in ordinary)
    absent = combined["no_match"]
    assert absent["self_check"] == []
    assert absent["exact_match_count"] == 0
    assert absent["racket_result"]["generator_domain"]["status"] == "valid"
    assert absent["racket_result"]["valid_output"] is False
    duplicate = combined["multiple_matches"]
    assert duplicate["self_check"] == [] and duplicate["exact_match_count"] == 2
    validator = {
        **binding, "finding_id": "AUD-0d03-V1", "classification": "reproduced_validator_defect",
        "generate_call": {"seed": 0, "sample_index": 0, "difficulty": "medium", "overrides": {"texture": "no_match"}},
        "input": absent["input"], "self_check": absent["self_check"],
        "feature_match_count": absent["exact_match_count"],
        "actual_racket_output": absent["racket_result"]["output"],
        "actual_racket_error": absent["racket_result"]["error"],
        "generator_domain": absent["racket_result"]["generator_domain"],
        "rival_output": None, "rival_note": "No candidate object exists; no alternative output is asserted.",
        "domain_scope": "A declared adversarial texture; outside the intended ordinary unique-match domain, but accepted by self_check.",
        "secondary_witness": {"case_id": "multiple_matches", "feature_match_count": 2,
                              "self_check": [], "actual_racket_output": duplicate["racket_result"]["output"],
                              "qualification": "Both matches have the same crop; this proves the uniqueness-validator gap, not output ambiguity."},
        "racket_evidence": "checks/audit/0d03b427c121/racket.json", "racket_case_index": 1,
        "command": racket["command"], "cwd": racket["cwd"],
    }
    assert lesson["seed"] == 9 and lesson["sample_indices"] == [0, 1, 2, 3]
    assert not lesson["rejections"]
    assert len(lesson["train"]) == 3 and len(lesson["test"]) == 1
    pairs = lesson["train"] + lesson["test"]
    case_ids = ["lesson_train_0", "lesson_train_1", "lesson_train_2", "lesson_query_0"]
    agrees = []
    checks = []
    for pair, case_id in zip(pairs, case_ids, strict=True):
        case = combined[case_id]
        assert pair["input"] == case["input"]
        assert pair["output"] == case["racket_result"]["output"]
        agreement = case["area_only_rival_output"] == pair["output"]
        agrees.append(agreement)
        checks.append({"case_id": case_id, "input_sha256": hash_grid(pair["input"]),
                       "rival_matches_racket": agreement, "actual_racket_output": pair["output"],
                       "rival_output": case["area_only_rival_output"]})
    assert agrees == [True, True, True, False]
    assert all(row["rival_matches_label"] for row in probe["canonical_rival_checks"])
    rotations = [{"query_index": query, "demonstration_indices": [i for i in range(4) if i != query],
                  "rival_fits_demonstrations": all(agrees[i] for i in range(4) if i != query),
                  "rival_disagrees_query": not agrees[query],
                  "ambiguous": all(agrees[i] for i in range(4) if i != query) and not agrees[query]}
                 for query in range(4)]
    query = combined["lesson_query_0"]
    shortcut = {
        **binding, "finding_id": "AUD-0d03-L1", "classification": "reproduced_lesson_shortcut_ambiguity",
        "rival": "Read only the color-1 count; select the first body component with that area, ignoring all color-2 boundary markers; crop and paint 8.",
        "canonical_pairs_passed": 3, "canonical_pairs_total": 3,
        "generate_call": {"seed": 9, "sample_index": 0, "difficulty": "medium", "n_train": 3, "n_test": 1, "overrides": {}},
        "accepted_sample_indices": [0, 1, 2, 3], "rejections": [],
        "production_demonstrations_passed": 3, "production_demonstrations_total": 3,
        "production_query_passed": 0, "production_query_total": 1,
        "production_ambiguity_count": 1, "production_lessons_checked": 1,
        "rotations": rotations, "rotation_ambiguity_count": sum(r["ambiguous"] for r in rotations),
        "rotation_total": 4, "lesson_check": lesson["lesson_check"],
        "query_input": query["input"], "query_input_sha256": query["input_sha256"],
        "actual_racket_output": query["racket_result"]["output"],
        "rival_output": query["area_only_rival_output"], "query_self_check": query["self_check"],
        "query_marker_area": query["marker_area"], "query_marker_boundary": query["marker_boundary"],
        "query_area_match_count": query["area_match_count"], "query_exact_match_count": query["exact_match_count"],
        "pair_checks": checks, "racket_evidence": "checks/audit/0d03b427c121/racket.json",
        "materialized_lesson": "checks/audit/0d03b427c121/lesson.jsonl",
        "command": racket["command"], "cwd": racket["cwd"],
        "limits": "One materialized lesson and one canonical-fitting rival. The larger candidate search used a Python mirror and is not a Racket semantic census.",
    }
    summary = {
        **binding, "status": "findings_reproduced", "findings": [validator["finding_id"], shortcut["finding_id"]],
        "racket_inputs": 10, "racket_valid_outputs": 8, "racket_errors": 2,
        "expected_rejected_no_markers_controls": 1, "validator_accepted_no_match_errors": 1,
        "ordinary_generated_controls_and_lesson_pairs_verified": 7,
        "production_lessons_checked": 1, "production_ambiguities": 1,
        "rotation_count": 4, "rotation_ambiguities": 1,
        "canonical_rival_matches": "3/3", "source_changed": False,
        "exploratory_scan": probe["scan"],
    }
    for filename, value in (("counterexample-validator.json", validator), ("counterexample-lesson.json", shortcut),
                            ("assessment.json", summary)):
        with (HOME / filename).open("x") as handle:
            json.dump(value, handle, indent=2)
            handle.write("\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
