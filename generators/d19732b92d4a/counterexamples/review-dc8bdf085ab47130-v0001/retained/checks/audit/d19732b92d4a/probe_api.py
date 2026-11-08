from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "d19732b92d4a"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks/audit/d19732b92d4a/probe_result.json"


def attempt(fn, *args, **kwargs):
    try:
        value = fn(*args, **kwargs)
    except Exception as exc:  # evidence records the public failure mode
        return {"accepted": False, "error_type": type(exc).__name__, "error": str(exc)}
    result = {"accepted": True, "type": type(value).__name__}
    if isinstance(value, list) and value and isinstance(value[0], list):
        result["dims"] = [len(value), len(value[0])]
    else:
        result["value"] = value
    return result


gen, source, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
result = {
    "schema": "arcpuzzles-peer-api-probe-v1",
    "task_id": TASK_ID,
    "generator_path": str(source.relative_to(ROOT)),
    "generator_sha256": source_sha256,
    "declared_rule_hash": getattr(gen, "RULE_HASH", None),
    "cwd": str(ROOT),
    "command": ["python3", "../checks/audit/d19732b92d4a/probe_api.py"],
    "cases": {
        "bool_seed": attempt(gen.generate, True, 0),
        "float_seed": attempt(gen.generate, 1.5, 0),
        "bool_sample_index": attempt(gen.generate, 1, False),
        "fractional_sample_index": attempt(gen.generate, 1, 0.5),
        "string_sample_index": attempt(gen.generate, 1, "0"),
        "negative_sample_index": attempt(gen.generate, 1, -1),
        "fractional_schedule_index": attempt(gen.schedule_profile, 1, 0.5),
    },
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
