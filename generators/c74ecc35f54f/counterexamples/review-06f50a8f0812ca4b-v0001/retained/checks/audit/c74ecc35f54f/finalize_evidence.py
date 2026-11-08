from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
pre = json.loads((HERE / "pre-evidence.json").read_text())
valid = json.loads((HERE / "valid-racket.json").read_text())
mono = json.loads((HERE / "monocolor-racket.json").read_text())

for case, result in zip(pre["valid_cases"], valid["results"], strict=True):
    assert case["input"] == result["input"]
    case["racket_output"] = result["output"]
    case["racket_valid_output"] = result["valid_output"]
    case["racket_error"] = result["error"]
    case["input_sha256"] = result["input_sha256"]
    case["output_sha256"] = result["output_sha256"]

invalid = pre["invalid_output_case"]
mono_result = mono["results"][0]
assert invalid["input"] == mono_result["input"]
invalid.update({
    "racket_output": mono_result["output"],
    "racket_valid_output": mono_result["valid_output"],
    "racket_error": mono_result["error"],
    "input_sha256": mono_result["input_sha256"],
    "output_sha256": mono_result["output_sha256"],
})

lesson = pre["valid_cases"][1:]
assert all(row["component_count_rival_output"] == row["racket_output"] for row in lesson[:3])
assert lesson[3]["component_count_rival_output"] != lesson[3]["racket_output"]
assert pre["valid_cases"][0]["first_row_major_nonzero_color"] != 9
assert invalid["self_check"] == []
assert invalid["racket_valid_output"] is False

final = {
    "schema": "arcpuzzles-audit-c74ecc35f54f-v1",
    "task_id": pre["task_id"],
    "source_identity": {
        "generator_path": pre["generator_path"],
        "generator_sha256": pre["generator_sha256"],
        "executed_rule_hash": valid["executed_rule_hash"],
        "rule_text_sha256": valid["rule_text_sha256"],
        "rule_hash_matches_catalog": valid["rule_hash_matches_catalog"],
    },
    "finding_ignored_first_color_override": pre["valid_cases"][0],
    "finding_component_count_shortcut_lesson": {
        "assembly": "consecutive default easy draws at fixed seed 27, demos indices 0..2, query index 3",
        "rival": "count 4-connected nonzero components ignoring color; repeat first row-major nonzero color component_count times",
        "demos_fit_rival": True,
        "query_refutes_rival": True,
        "cases": lesson,
    },
    "finding_advertised_texture_invalid_output": invalid,
    "commands": [
        {
            "cwd": valid["cwd"],
            "argv": valid["command"],
            "exit_code": 0,
            "evidence": "valid-racket.json",
        },
        {
            "cwd": mono["cwd"],
            "argv": mono["command"],
            "exit_code": 1,
            "evidence": "monocolor-racket.json",
        },
    ],
    "conclusion": {
        "source_edited": False,
        "ordinary_lesson_ambiguity_reproduced": True,
        "advertised_override_violation_reproduced": True,
        "validator_accepted_invalid_reference_output_case": True,
    },
}
(HERE / "evidence.json").write_text(json.dumps(final, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "lesson_demo_widths": [len(row["racket_output"][0]) for row in lesson[:3]],
    "query_reference_width": len(lesson[3]["racket_output"][0]),
    "query_rival_width": len(lesson[3]["component_count_rival_output"][0]),
    "override_requested": 9,
    "override_observed": pre["valid_cases"][0]["first_row_major_nonzero_color"],
    "monocolor_valid_output": invalid["racket_valid_output"],
}, indent=2))
