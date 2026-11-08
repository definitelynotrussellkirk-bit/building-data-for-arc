"""Source-bound reproducer for 0c023af8384a's advertised exact-axis defects."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PACKET_ROOT = Path(__file__).resolve().parents[3]
REPO = PACKET_ROOT / "repo"
GENERATOR = REPO / "generators/0c023af8384a/generator.py"
sys.path.insert(0, str(REPO / "shared/runtime"))

spec = importlib.util.spec_from_file_location("audit_gen_0c023af8384a", GENERATOR)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

report = {
    "schema": "task-audit-override-reproducer-v1",
    "task_id": module.TASK_ID,
    "version": module.VERSION,
    "generator_path": "repo/generators/0c023af8384a/generator.py",
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "cases": [],
}

try:
    module.generate(0, 0, difficulty="easy", grid_h=16)
except Exception as exc:  # the rejection is the finding
    report["cases"].append({
        "name": "advertised_height_rejected_by_easy_band",
        "documented_axis_domain": module.AXES["grid_h"]["valid"],
        "call": {"seed": 0, "sample_index": 0, "difficulty": "easy", "grid_h": 16},
        "error_type": type(exc).__name__,
        "error": str(exc),
    })
else:
    raise AssertionError("expected advertised height 16 to expose the band-bound rejection")

for name, overrides in [
    ("on_axis_mutates_exact_height_pin", {"texture": "on_axis", "grid_h": 8, "grid_w": 7, "marks": 2}),
    ("dense_ignores_exact_marks_pin", {"texture": "dense", "grid_h": 8, "grid_w": 7, "marks": 2}),
]:
    grid = module.generate(0, 0, difficulty="easy", **overrides)
    report["cases"].append({
        "name": name,
        "call": {"seed": 0, "sample_index": 0, "difficulty": "easy", **overrides},
        "realized_height": len(grid),
        "realized_width": len(grid[0]),
        "realized_occupied": sum(value != 0 for row in grid for value in row),
        "self_check_errors": module.self_check(grid),
    })

out = Path(__file__).with_name("override_probe.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, indent=2, sort_keys=True))
