from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "4c33979d9cc2"
REPO = Path(__file__).resolve().parents[3] / "repo"
PATH = REPO / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location(f"audit_{TASK}", PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

record = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(PATH.read_bytes()).hexdigest(),
    "invalid_sample_index": -1,
    "cases": [],
}
for difficulty in (None, "easy", "medium", "hard"):
    case = {"difficulty": difficulty}
    try:
        case["schedule_profile"] = mod.schedule_profile(7, -1, difficulty)
    except Exception as exc:
        case["schedule_error"] = f"{type(exc).__name__}: {exc}"
    try:
        grid = mod.generate(7, -1, difficulty=difficulty)
        case["generate"] = {
            "accepted": True,
            "shape": [len(grid), len(grid[0])],
            "self_check": mod.self_check(grid),
            "observed": mod.observe_overrides(grid),
        }
    except Exception as exc:
        case["generate"] = {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}
    record["cases"].append(case)
print(json.dumps(record, indent=2, sort_keys=True))
