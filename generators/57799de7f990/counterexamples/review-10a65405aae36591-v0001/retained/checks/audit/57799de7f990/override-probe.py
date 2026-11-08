"""One exact override witness; labels are obtained separately via CLI apply."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
SOURCE = REPO / "generators/57799de7f990/generator.py"
spec = importlib.util.spec_from_file_location("audit_override_target", SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

overrides = {"grid_h": 12, "grid_w": 12}
grid = mod.generate(0, 0, difficulty="hard", **overrides)
record = {"task_id": "57799de7f990", "seed": 0, "sample_index": 0,
          "difficulty": "hard", "overrides": overrides,
          "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          "input": grid, "requested_dimensions": [12, 12],
          "actual_dimensions": [len(grid), len(grid[0])],
          "validator_errors": mod.self_check(grid, difficulty="hard"),
          "finding": "Explicit dimensions declared valid by AXES are ignored."}
(HERE / "override-input.json").write_text(json.dumps(grid) + "\n")
(HERE / "override-probe.json").write_text(json.dumps(record, indent=1) + "\n")
print(json.dumps({k: record[k] for k in ("requested_dimensions", "actual_dimensions", "validator_errors", "generator_sha256")}))
