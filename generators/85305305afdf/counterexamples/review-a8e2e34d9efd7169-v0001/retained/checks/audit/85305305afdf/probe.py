from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "85305305afdf"
SEED = 20261007
SAMPLE_INDEX = 11
DIFFICULTY = "medium"
ROOT = Path.cwd()
GEN_PATH = ROOT / "generators" / TASK / "generator.py"
OUT_DIR = ROOT.parent / "checks" / "audit" / TASK

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GEN_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def digest(grid):
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()

def capture(**overrides):
    try:
        grid = mod.generate(SEED, SAMPLE_INDEX, difficulty=DIFFICULTY, **overrides)
        return {
            "status": "ok",
            "shape": [len(grid), len(grid[0]) if grid else 0],
            "grid_sha256": digest(grid),
            "self_check": mod.self_check(grid, difficulty=DIFFICULTY),
            "grid": grid,
        }
    except Exception as exc:  # audit records the public failure
        return {"status": "error", "error_type": type(exc).__name__, "error": str(exc)}

base = capture()
textures = {name: capture(texture=name) for name in ("default", "warm", "cool", "varied")}
unknown = capture(typo_axis=99)
valid_boundary_requests = {
    "grid_h_12": capture(grid_h=12),
    "grid_w_16": capture(grid_w=16),
    "cells_12": capture(cells=12),
}
degenerates = {name: capture(texture=name) for name in ("no_cells", "cell_at_right_edge", "cells_blocked")}

right_edge = degenerates["cell_at_right_edge"]
assert right_edge["status"] == "ok"
(OUT_DIR / "input.json").write_text(json.dumps(right_edge["grid"], indent=2) + "\n")

report = {
    "schema": "audit-generator-contract-probe-v1",
    "task_id": TASK,
    "generator_path": f"generators/{TASK}/generator.py",
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "seed": SEED,
    "sample_index": SAMPLE_INDEX,
    "difficulty": DIFFICULTY,
    "command": ["python3", "run_with_racket.py", "python3", f"../checks/audit/{TASK}/probe.py"],
    "effective_cwd": str(ROOT),
    "base": base,
    "helpful_texture_cases": textures,
    "all_helpful_textures_equal_base": all(v.get("grid_sha256") == base.get("grid_sha256") for v in textures.values()),
    "unknown_override_case": unknown,
    "unknown_override_equal_base": unknown.get("grid_sha256") == base.get("grid_sha256"),
    "declared_valid_boundary_requests": valid_boundary_requests,
    "degenerate_cases": degenerates,
    "right_edge_input_path": f"checks/audit/{TASK}/input.json",
    "observations": [
        "All four helpful texture values are byte-identical to the no-texture draw for this seed/sample.",
        "An unknown override is accepted silently and is byte-identical to the base draw.",
        "Declared valid high-bound exact overrides are rejected by narrower difficulty-local draw ranges.",
        "The advertised cell_at_right_edge texture passes self_check although it violates the ordinary right-room invariant.",
    ],
}
(OUT_DIR / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "probe": f"../checks/audit/{TASK}/probe.json",
    "input": f"../checks/audit/{TASK}/input.json",
    "all_helpful_textures_equal_base": report["all_helpful_textures_equal_base"],
    "unknown_override_equal_base": report["unknown_override_equal_base"],
    "boundary_statuses": {k: v["status"] for k, v in valid_boundary_requests.items()},
    "right_edge_self_check": right_edge["self_check"],
}, indent=2))
