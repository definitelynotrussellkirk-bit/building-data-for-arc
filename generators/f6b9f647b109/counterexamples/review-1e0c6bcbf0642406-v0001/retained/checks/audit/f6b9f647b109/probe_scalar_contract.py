from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / "generators" / "f6b9f647b109" / "generator.py"
spec = importlib.util.spec_from_file_location("audit_f6b9f647b109", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

cases = [
    ("bool_seed", (True, 0), {"difficulty": "easy"}),
    ("float_seed", (1.0, 0), {"difficulty": "easy"}),
    ("bool_index", (1, True), {"difficulty": "easy"}),
    ("float_index", (1, 0.0), {"difficulty": "easy"}),
    ("string_index", (1, "0"), {"difficulty": "easy"}),
    ("negative_index", (1, -1), {"difficulty": "easy"}),
    ("unknown_difficulty", (1, 0), {"difficulty": "weird"}),
]
results = []
for name, args, kwargs in cases:
    try:
        grid = module.generate(*args, **kwargs)
        results.append({
            "case": name,
            "accepted": True,
            "shape": [len(grid), len(grid[0])],
            "self_check": module.self_check(grid),
            "schedule_profile": module.schedule_profile(args[0], args[1], kwargs["difficulty"]),
        })
    except Exception as exc:
        results.append({"case": name, "accepted": False, "error": f"{type(exc).__name__}: {exc}"})

report = {
    "task_id": module.TASK_ID,
    "version": module.VERSION,
    "rule_hash": module.RULE_HASH,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "working_directory": str(ROOT),
    "command": "PYTHONPATH=shared/runtime python3 ../checks/audit/f6b9f647b109/probe_scalar_contract.py",
    "results": results,
}
print(json.dumps(report, indent=2, sort_keys=True))
