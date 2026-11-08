from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

TASK = "2a10fa5d18dc"
path = Path("generators") / TASK / "generator.py"
spec = importlib.util.spec_from_file_location(f"audit_{TASK}", path)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def attempt(label, *args, **kwargs):
    try:
        grid = mod.generate(*args, **kwargs)
    except Exception as exc:
        return {"label": label, "accepted": False,
                "error": f"{type(exc).__name__}: {exc}"}
    return {
        "label": label,
        "accepted": True,
        "shape": [len(grid), len(grid[0])],
        "self_check": mod.self_check(grid),
        "colors": sorted({v for row in grid for v in row}),
        "sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest(),
    }

cases = [
    attempt("control", 991, 0),
    attempt("unknown override", 991, 0, unknown_axis=1),
    attempt("declared n_frames=1", 991, 0, n_frames=1),
    attempt("declared n_frames=3", 991, 0, n_frames=3),
    attempt("declared texture=no_frames", 991, 0, texture="no_frames"),
    attempt("declared texture=no_seeds", 991, 0, texture="no_seeds"),
    attempt("declared texture=multi_seeds", 991, 0, texture="multi_seeds"),
    attempt("invalid difficulty", 991, 0, difficulty="__invalid_difficulty__"),
    attempt("boolean seed", True, 0),
    attempt("negative sample_index", 991, -1),
]
report = {
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "finding": "declared/unknown controls are accepted while producing ignored or self-check-invalid samples",
    "cases": cases,
}
print(json.dumps(report, indent=2, sort_keys=True))
