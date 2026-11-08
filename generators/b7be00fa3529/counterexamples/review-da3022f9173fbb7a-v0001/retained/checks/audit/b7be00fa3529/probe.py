from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

TASK = "b7be00fa3529"
source = Path(f"generators/{TASK}/generator.py")
spec = importlib.util.spec_from_file_location(f"audit_{TASK}", source)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
grid = module.generate(0, 0, texture="no_motifs")
report = {
    "task_id": TASK,
    "finding": "declared ordinary texture no_motifs produces a validator-accepted no-op grid",
    "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "seed": 0,
    "sample_index": 0,
    "difficulty": None,
    "overrides": {"texture": "no_motifs"},
    "grid": grid,
    "shape": [len(grid), len(grid[0])],
    "nonzero_count": sum(value != 0 for row in grid for value in row),
    "self_check": module.self_check(grid),
    "documented_visible_gravity_invariant": module.INVARIANTS[-1],
}
Path("../checks/audit/b7be00fa3529/probe.json").write_text(json.dumps(report, indent=2) + "\n")
Path("../checks/audit/b7be00fa3529/input.json").write_text(json.dumps(grid) + "\n")
print(json.dumps(report, indent=2))
