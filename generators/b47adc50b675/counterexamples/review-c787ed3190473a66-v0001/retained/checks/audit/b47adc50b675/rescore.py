"""Verify the retained counterexample against source-bound public Racket labels."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    probe = json.loads((HERE / "probe.json").read_text())
    applied = json.loads((HERE / "racket.json").read_text())
    expected = json.loads((HERE / "expected.json").read_text())
    rivals = json.loads((HERE / "rival.json").read_text())
    assert applied["generator_sha256"] == probe["generator_sha256"]
    assert applied["executed_rule_hash"] == probe["declared_rule_hash"]
    assert applied["rule_hash_matches_catalog"] is True
    assert applied["reference"] == "canonical"
    assert len(applied["results"]) == 5
    for index, row in enumerate(applied["results"]):
        assert row["valid_output"] is True and row["error"] is None
        assert row["generator_domain"] == {"status": "valid", "errors": []}
        assert row["output"] == expected[index]
    agree = [rivals[i] == row["output"] for i, row in enumerate(applied["results"])]
    assert agree == [True, True, True, False, False]
    # Rotate the first original demonstration to the query; the old query now
    # refutes this rival. This is one specific rotation, not a complete census.
    rotated_query = 0
    rotated_demo_agreement = [agree[i] for i in range(4) if i != rotated_query]
    assert rotated_demo_agreement == [True, True, False]
    result = {**probe, "conclusion": "Issue found: a canonical-fitting first-cell anchor rival fits all three default demonstrations and changes the lawful query answer.",
              "severity": "teaching_ambiguity", "racket_inputs_checked": 5,
              "racket_rule_hash": applied["executed_rule_hash"],
              "racket_rule_text_sha256": applied["rule_text_sha256"],
              "racket_inputs_valid": 5, "racket_outputs_valid": 5,
              "independent_oracle_matches_racket": 5,
              "rival_agrees_with_racket": agree,
              "normal_query": {"pair_index": 3, "demo_fit": True,
                               "query_differs": True, "status": "ambiguous"},
              "single_query_rotation": {"pair_index": rotated_query,
                                         "demo_agreement": rotated_demo_agreement,
                                         "status": "rival_refuted"},
              "minimal_witness": {"apply_index": 4, "dimensions": [5, 6],
                                  "input_green_cells": [[1, 2], [2, 2], [3, 1], [3, 2]],
                                  "racket_output_green_cells": [[0, 1], [1, 1], [2, 0], [2, 1]],
                                  "rival_output_green_cells": [[0, 0], [1, 0], [2, 0]]},
              "recommended_action": "Teach bbox minima independently: add first-row-major-anchor as a canonical shortcut/lesson rival and ensure default lessons include an empty bbox-top-left shape. Preserve a second refuting example per four-pair window if query rotations must also be guaranteed.",
              "audit_source_edited": False, "full_battery_run": False,
              "authority_note": "The rule labels are correct and all five inputs satisfy the generator validator. The finding concerns demonstration insufficiency, not a label or structural-control failure.",
              "evidence_sha256": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                                  for name in ("probe.py", "probe.json", "input.json", "racket.json",
                                               "expected.json", "rival.json")}}
    (HERE / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"conclusion": result["conclusion"],
                      "racket_rule_hash": result["racket_rule_hash"],
                      "rival_agreement": agree, "racket_inputs": 5}, sort_keys=True))


if __name__ == "__main__":
    main()
