from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
pre = json.loads((HERE / "pre-evidence.json").read_text())
racket = json.loads((HERE / "racket.json").read_text())
cases = pre["lesson"]["cases"]

for case, result in zip(cases, racket["results"], strict=True):
    assert case["input"] == result["input"]
    assert result["valid_output"] is True
    assert result["generator_domain"]["status"] == "valid"
    assert case["python_rotation_matrix"] == result["output"]
    case.update({
        "racket_output": result["output"],
        "racket_valid_output": result["valid_output"],
        "racket_error": result["error"],
        "input_sha256": result["input_sha256"],
        "output_sha256": result["output_sha256"],
    })

assert all(case["identity_rival_output"] == case["racket_output"] for case in cases[:3])
assert cases[3]["identity_rival_output"] != cases[3]["racket_output"]

final = {
    "schema": "arcpuzzles-audit-c29d882947ce-v1",
    "task_id": pre["task_id"],
    "source_identity": {
        "generator_path": pre["generator_path"],
        "generator_sha256": pre["generator_sha256"],
        "executed_rule_hash": racket["executed_rule_hash"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "rule_hash_matches_catalog": racket["rule_hash_matches_catalog"],
    },
    "search": pre["search"],
    "finding_identity_shortcut_lesson": {
        "assembly": (
            f"consecutive default easy draws at seed {pre['lesson']['seed']}, "
            f"demos indices {pre['lesson']['start_index']}..{pre['lesson']['start_index'] + 2}, "
            f"query index {pre['lesson']['start_index'] + 3}"
        ),
        "rival": "always output the identity matrix with dimension equal to the component count",
        "demos_fit_rival": True,
        "query_refutes_rival": True,
        "cases": cases,
    },
    "command": {
        "cwd": racket["cwd"],
        "argv": racket["command"],
        "exit_code": 0,
        "evidence": "racket.json",
    },
    "conclusion": {
        "source_edited": False,
        "ordinary_consecutive_lesson_ambiguity_reproduced": True,
        "all_inputs_pass_selected_self_check": True,
        "all_reference_outputs_are_valid": True,
    },
}
(HERE / "evidence.json").write_text(json.dumps(final, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "seed": pre["lesson"]["seed"],
    "indices": [case["sample_index"] for case in cases],
    "identity_flags": [case["identity_rival_output"] == case["racket_output"] for case in cases],
    "query_output": cases[-1]["racket_output"],
}, indent=2))
