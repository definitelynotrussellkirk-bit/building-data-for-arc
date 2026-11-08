from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

TASK = "e7c4af96e258"
ROOT = Path.cwd()
OUT = ROOT / "../checks/audit/e7c4af96e258/probe.json"
SOURCE = ROOT / f"generators/{TASK}/generator.py"

sys.path.insert(0, str(ROOT / "shared/runtime"))
spec = importlib.util.spec_from_file_location("audit_e7_generator", SOURCE)
assert spec and spec.loader
gen = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gen
spec.loader.exec_module(gen)


def dims(grid: list[list[int]]) -> list[int]:
    return [len(grid), len(grid[0])]


def attempt(**kwargs):
    try:
        grid = gen.generate(**kwargs)
    except Exception as exc:  # evidence records explicit rejection if present
        return {"accepted": False, "exception_type": type(exc).__name__, "message": str(exc)}
    return {
        "accepted": True,
        "dimensions": dims(grid),
        "self_check": gen.self_check(grid, difficulty=kwargs.get("difficulty")),
    }

cases = {
    "grid_w_exact": {
        "call": {"seed": 0, "sample_index": 3, "difficulty": "easy", "grid_w": 16},
    },
    "grid_h_exact": {
        "call": {"seed": 0, "sample_index": 3, "difficulty": "easy", "grid_h": 13},
    },
    "unknown_key": {
        "call": {"seed": 0, "sample_index": 3, "difficulty": "easy", "not_a_declared_axis": 1},
    },
}
for item in cases.values():
    item["result"] = attempt(**item["call"])

assert cases["grid_w_exact"]["result"]["accepted"]
assert cases["grid_w_exact"]["result"]["dimensions"][1] != 16
assert cases["grid_h_exact"]["result"]["accepted"]
assert cases["grid_h_exact"]["result"]["dimensions"][0] != 13
assert cases["unknown_key"]["result"]["accepted"]

test_dir = ROOT / f"generators/{TASK}/tests"
test_files = sorted(str(p.relative_to(ROOT)) for p in test_dir.rglob("test*.py")) if test_dir.exists() else []
contract_symbols = {
    name: hasattr(gen, name)
    for name in (
        "strict_canonical_like",
        "SEMANTIC_WITNESSES",
        "BRANCH_WITNESSES",
        "lesson_identifiable",
        "LESSON_COMPETITORS",
        "observe_overrides",
    )
}

record = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "generator_version": getattr(gen, "VERSION", None),
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "declared_rule_hash": getattr(gen, "RULE_HASH", None),
    "cases": cases,
    "declared_axes": sorted(getattr(gen, "AXES", {}).keys()),
    "semantic_contract_symbols": contract_symbols,
    "task_test_files": test_files,
    "conclusions": {
        "exact_grid_width_override_violated": True,
        "exact_grid_height_override_violated": True,
        "unknown_override_silently_accepted": True,
        "no_executable_semantic_contract": not any(
            contract_symbols[k]
            for k in ("strict_canonical_like", "SEMANTIC_WITNESSES", "lesson_identifiable")
        ),
        "no_task_local_tests": not test_files,
    },
    "full_override_report": "checks/audit/e7c4af96e258/override/checks/e7c4af96e258_audit_override_results.json",
}
OUT.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
