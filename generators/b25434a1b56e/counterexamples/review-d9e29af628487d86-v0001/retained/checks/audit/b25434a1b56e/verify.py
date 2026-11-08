from __future__ import annotations

import json
from pathlib import Path

TASK_ID = "b25434a1b56e"
BASE = Path("../checks/audit") / TASK_ID
probe = json.loads((BASE / "probe-preapply.json").read_text())
racket = json.loads((BASE / "right-empty-racket.json").read_text())
result = racket["results"][0]
case = probe["lawful_counterexample"]

assert racket["task_id"] == TASK_ID
assert racket["generator_sha256"] == probe["generator_sha256"]
assert result["input"] == json.loads((BASE / "right-empty-input.json").read_text())
assert result["output"] == case["python_official"]

report = {
    **probe,
    "schema": "arcpuzzles-audit-probe-v1",
    "lawful_counterexample": {
        **case,
        "canonical_rule_hash": racket["executed_rule_hash"],
        "canonical_racket": result["output"],
        "racket_valid_output": result["valid_output"],
        "supported_apply_generator_domain": result["generator_domain"],
        "racket_matches_official": result["output"] == case["python_official"],
        "rival_differs": case["rival"] != case["python_official"],
    },
    "conclusions": {
        "production_never_places_empty_on_right": probe["generated_census"]["right_empty_count"] == 0,
        "rival_survives_all_generated": (
            probe["generated_census"]["rival_matches_official"]
            == probe["generated_census"]["total"]
        ),
        "rival_survives_all_canonical": (
            probe["canonical_census"]["rival_matches_labels"]
            == probe["canonical_census"]["total"]
        ),
        "right_empty_counterexample_is_accepted": (
            result["generator_domain"]["status"] == "valid"
            and not case["self_check"]
            and not case["strict_canonical_like"]
        ),
        "canonical_rule_refutes_rival_on_counterexample": (
            result["output"] == case["python_official"]
            and case["rival"] != case["python_official"]
        ),
    },
}
(BASE / "right-empty-reproduction.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n"
)
print(json.dumps(report["conclusions"], sort_keys=True))
