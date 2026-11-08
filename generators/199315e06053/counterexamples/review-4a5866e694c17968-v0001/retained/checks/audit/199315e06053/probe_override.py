from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3] / "repo"
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

source = REPO / "generators" / "199315e06053" / "generator.py"
spec = importlib.util.spec_from_file_location("audit_199315e06053", source)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

call = {
    "seed": 0,
    "sample_index": 0,
    "difficulty": None,
    "overrides": {"dot_count": 3, "dot_color": 2},
}
grid = module.generate(
    call["seed"],
    call["sample_index"],
    difficulty=call["difficulty"],
    **call["overrides"],
)
observed_colors = sorted({value for row in grid for value in row if value != 0})
record = {
    "schema": "arcpuzzles-audit-override-witness-v1",
    "task_id": "199315e06053",
    "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "call": call,
    "advertised_dot_color_axis": module.AXES["dot_color"],
    "observed_grid": grid,
    "observed_dot_count": sum(value != 0 for row in grid for value in row),
    "observed_nonzero_colors": observed_colors,
    "override_honored": observed_colors == [2],
    "self_check": module.self_check(grid),
    "conclusion": "dot_count=3 is honored, but the advertised exact dot_color=2 override is silently ignored",
    "command": ["python3", "../checks/audit/199315e06053/probe_override.py"],
    "cwd": "repo",
}
out = Path(__file__).with_name("witness.json")
out.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
