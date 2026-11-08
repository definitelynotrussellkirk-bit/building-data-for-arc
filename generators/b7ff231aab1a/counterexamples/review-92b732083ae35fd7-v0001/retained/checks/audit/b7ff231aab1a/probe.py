from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

TASK = "b7ff231aab1a"
path = Path("generators") / TASK / "generator.py"
spec = importlib.util.spec_from_file_location(f"audit_{TASK}", path)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()

def attempt(axis, value):
    args = [991, 0]
    kwargs = {}
    if axis == "seed": args[0] = value
    elif axis == "sample_index": args[1] = value
    elif axis == "difficulty": kwargs["difficulty"] = value
    try:
        grid = mod.generate(*args, **kwargs)
    except Exception as exc:
        return {"axis": axis, "value": repr(value), "accepted": False,
                "error": f"{type(exc).__name__}: {exc}"}
    return {"axis": axis, "value": repr(value), "accepted": True,
            "shape": [len(grid), len(grid[0])], "sha256": digest(grid),
            "self_check": mod.self_check(grid)}

probes = []
for value in (True, False, 1.0, 1.75, "1"):
    probes.append(attempt("seed", value))
for value in (True, False, 1.0, 1.75, "1", -1):
    probes.append(attempt("sample_index", value))
for value in (True, False, 0, 1.0, "__invalid_difficulty__"):
    probes.append(attempt("difficulty", value))
report = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "finding": "non-integer seed/sample_index values are silently coerced/accepted",
    "probes": probes,
}
print(json.dumps(report, indent=2, sort_keys=True))
