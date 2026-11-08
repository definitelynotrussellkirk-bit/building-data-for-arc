from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "e22bef4f5826"
ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "repo" / "generators" / TASK_ID / "generator.py"

spec = importlib.util.spec_from_file_location("audit_e22_generator", GENERATOR)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

cases = [
    {"name": "declared_min_height_rejected_in_easy", "difficulty": "easy", "overrides": {"grid_h": 5}},
    {"name": "declared_max_width_rejected_in_easy", "difficulty": "easy", "overrides": {"grid_w": 12}},
    {"name": "declared_one_blob_rejected_in_medium", "difficulty": "medium", "overrides": {"n_blobs": 1}},
    {"name": "declared_four_blobs_rejected_in_easy", "difficulty": "easy", "overrides": {"n_blobs": 4}},
]
results = []
for index, case in enumerate(cases):
    try:
        grid = mod.generate(100 + index, 0, difficulty=case["difficulty"], **case["overrides"])
    except Exception as exc:
        results.append({**case, "status": "rejected", "exception_type": type(exc).__name__, "message": str(exc)})
    else:
        results.append({
            **case,
            "status": "accepted",
            "shape": [len(grid), len(grid[0])],
            "self_check": mod.self_check(grid, difficulty=case["difficulty"]),
        })

for texture in ("single_cell_blobs", "already_checker", "blob_overlap"):
    grid = mod.generate(200, 0, difficulty="medium", texture=texture)
    results.append({
        "name": f"advertised_texture_{texture}",
        "difficulty": "medium",
        "overrides": {"texture": texture},
        "status": "accepted",
        "shape": [len(grid), len(grid[0])],
        "self_check": mod.self_check(grid, difficulty="medium", meta={"texture": texture}),
    })

try:
    grid = mod.generate(300, 0, difficulty="medium", typo_axis="ignored")
except Exception as exc:
    unknown = {"status": "rejected", "exception_type": type(exc).__name__, "message": str(exc)}
else:
    unknown = {
        "status": "accepted",
        "shape": [len(grid), len(grid[0])],
        "self_check": mod.self_check(grid, difficulty="medium"),
    }

report = {
    "schema": "arcpuzzles-audit-override-contract-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "declared_rule_hash": getattr(mod, "RULE_HASH", None),
    "declared_axes": mod.AXES,
    "cases": results,
    "unknown_override_probe": {"overrides": {"typo_axis": "ignored"}, **unknown},
    "finding": (
        "The advertised override domain is not executable: declared legal values are rejected "
        "by difficulty-specific draw ranges, degenerate textures are advertised as valid but fail "
        "the generator's own self_check, and an unknown override is accepted."
    ),
    "commands": [
        {
            "cwd": "packet_root",
            "argv": ["python3", "review.py", "run", "python3", "../checks/audit/e22bef4f5826/probe.py"],
        }
    ],
}
(Path(__file__).resolve().parent / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "rejected_declared_cases": sum(row["status"] == "rejected" for row in results[:4]),
    "invalid_advertised_textures": sum(bool(row["self_check"]) for row in results[4:]),
    "unknown_override_status": unknown["status"],
}, sort_keys=True))
