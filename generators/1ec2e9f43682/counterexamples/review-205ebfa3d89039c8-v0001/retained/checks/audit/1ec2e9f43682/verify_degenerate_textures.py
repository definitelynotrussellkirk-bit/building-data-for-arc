from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "1ec2e9f43682"
HERE = Path(__file__).resolve()
WORK = HERE.parents[3]
REPO = WORK / "repo"
SOURCE = REPO / "generators" / TASK / "generator.py"

spec = importlib.util.spec_from_file_location(f"audit_{TASK}", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
declared = module.AXES["texture"]["valid"].split("|")
rows = []
for index, texture in enumerate(module.DEGENERATE_TEXTURES):
    assert texture not in declared
    grid = module.generate(700 + index, 1, texture=texture)
    errors = module.self_check(grid)
    rows.append(
        {
            "texture": texture,
            "accepted_by_generate": True,
            "declared_in_axis_domain": False,
            "self_check_errors": errors,
            "grid": grid,
        }
    )
    assert errors, texture

result = {
    "schema": "audit-reproduction-v1",
    "task_id": TASK,
    "generator_sha256": source_sha,
    "finding": "generate accepts undeclared degenerate texture values and returns grids rejected by self_check",
    "declared_texture_values": declared,
    "degenerate_texture_values": list(module.DEGENERATE_TEXTURES),
    "cases": rows,
    "all_undeclared_values_accepted": all(row["accepted_by_generate"] for row in rows),
    "all_returned_grids_invalid": all(row["self_check_errors"] for row in rows),
}
assert result["all_undeclared_values_accepted"]
assert result["all_returned_grids_invalid"]
(HERE.parent / "reproduction.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n"
)
print(json.dumps({k: result[k] for k in ("task_id", "all_undeclared_values_accepted", "all_returned_grids_invalid")}, sort_keys=True))
