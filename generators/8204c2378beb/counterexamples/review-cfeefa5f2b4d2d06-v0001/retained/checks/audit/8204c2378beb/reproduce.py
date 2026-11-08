from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "8204c2378beb"
REPO = Path(__file__).resolve().parents[3] / "repo"
PATH = REPO / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location(f"audit_{TASK}", PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

record = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(PATH.read_bytes()).hexdigest(),
    "declared_stamp_size_valid": mod.AXES["stamp_size"]["valid"],
    "stamp_size_2_probes": [],
}
for difficulty in (None, "easy", "medium", "hard"):
    case = {"difficulty": difficulty}
    try:
        grid = mod.generate(0, 0, difficulty=difficulty, stamp_size=2)
        case.update({
            "accepted": True,
            "shape": [len(grid), len(grid[0])],
            "self_check": mod.self_check(grid),
        })
    except Exception as exc:
        case.update({"accepted": False, "error": f"{type(exc).__name__}: {exc}"})
    record["stamp_size_2_probes"].append(case)

print(json.dumps(record, indent=2, sort_keys=True))
