from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "shared" / "runtime"))
TASK = "f869ac2ae3e4"
GEN = ROOT / "generators" / TASK / "generator.py"
OUT = ROOT.parent / "checks" / "audit" / TASK

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GEN)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

seed, sample_index, difficulty = 73, 4, "medium"
overrides_a = {"grid_h": 5, "grid_w": 5, "shape_size": 2, "direction": "right"}
overrides_b = {"grid_h": 24, "grid_w": 24, "shape_size": 8, "direction": "right"}
grid_a = mod.generate(seed, sample_index, difficulty=difficulty, **overrides_a)
grid_b = mod.generate(seed, sample_index, difficulty=difficulty, **overrides_b)
errors = mod.self_check(grid_a, difficulty=difficulty, meta={})
components = mod._sc_color_components(grid_a)
shape_sizes = sorted(len(cells) for _color, cells in components if len(cells) > 1)
actual = {
    "grid_h": len(grid_a),
    "grid_w": len(grid_a[0]),
    "shape_size": shape_sizes[0] if len(shape_sizes) == 1 else shape_sizes,
}
sha = hashlib.sha256(GEN.read_bytes()).hexdigest()
report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "generator_sha256": sha,
    "generator_version": mod.VERSION,
    "seed": seed,
    "sample_index": sample_index,
    "difficulty": difficulty,
    "finding": "declared exact grid_h, grid_w, and shape_size overrides are ignored",
    "overrides_a": overrides_a,
    "overrides_b": overrides_b,
    "actual_from_a": actual,
    "same_grid_under_conflicting_exact_overrides": grid_a == grid_b,
    "self_check_errors": errors,
    "validator_accepted": errors == [],
    "belongs_to_documented_ordinary_domain": errors == [],
    "reproduced": (
        grid_a == grid_b
        and actual["grid_h"] != overrides_a["grid_h"]
        and actual["grid_w"] != overrides_a["grid_w"]
        and actual["shape_size"] != overrides_a["shape_size"]
        and errors == []
    ),
    "source_observation": "generate uses rng.randint for dimensions/shape size instead of GenCtx typed draws; only direction reads overrides directly",
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "input.json").write_text(json.dumps(grid_a, indent=2) + "\n")
(OUT / "probe-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
(OUT / "overrides.json").write_text(json.dumps({"a": overrides_a, "b": overrides_b}, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if report["reproduced"] else 1)
