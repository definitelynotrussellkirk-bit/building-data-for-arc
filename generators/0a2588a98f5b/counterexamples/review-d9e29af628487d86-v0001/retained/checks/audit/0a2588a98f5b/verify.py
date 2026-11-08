from __future__ import annotations

import json
from pathlib import Path

TASK_ID = "0a2588a98f5b"
BASE = Path("../checks/audit") / TASK_ID
probe = json.loads((BASE / "probe-preapply.json").read_text())
racket = json.loads((BASE / "code4-racket.json").read_text())
result = racket["results"][0]

assert racket["task_id"] == TASK_ID
assert racket["generator_sha256"] == probe["generator_sha256"]
assert result["input"] == json.loads((BASE / "code4-input.json").read_text())
assert result["output"] == probe["canonical_code4_boundary"]["python_mirror_output"]

integer_zero = probe["override_probes"]["declared_integer_zero"]
string_zero = probe["override_probes"]["string_zero_coercion"]
unknown = probe["override_probes"]["unknown_axis"]

report = {
    **probe,
    "schema": "arcpuzzles-audit-probe-v1",
    "canonical_code4_boundary": {
        **probe["canonical_code4_boundary"],
        "canonical_rule_hash": racket["executed_rule_hash"],
        "canonical_racket_output": result["output"],
        "racket_valid_output": result["valid_output"],
        "supported_apply_generator_domain": result["generator_domain"],
        "mirror_matches_racket": (
            result["output"]
            == probe["canonical_code4_boundary"]["python_mirror_output"]
        ),
    },
    "conclusions": {
        "canonical_code4_is_executable": result["valid_output"] and result["error"] is None,
        "self_check_rejects_canonical_code4": result["generator_domain"]["status"] == "invalid",
        "integer_zero_override_is_unusable": integer_zero["status"] == "raised",
        "string_zero_bypasses_integer_validation": string_zero.get("header_count") == 0,
        "unknown_overrides_are_ignored": unknown["status"] == "returned",
    },
}
(BASE / "probe-results.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report["conclusions"], sort_keys=True))
