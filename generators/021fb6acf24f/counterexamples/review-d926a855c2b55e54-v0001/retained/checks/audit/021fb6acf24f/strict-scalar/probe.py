from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "021fb6acf24f"
REPO = Path(__file__).resolve().parents[4] / "repo"
GENERATOR = REPO / "generators" / TASK_ID / "generator.py"
spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def grid_sha(grid):
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()

def run_case(name, seed, sample_index):
    row = {"name": name, "seed": seed, "sample_index": sample_index,
           "seed_type": type(seed).__name__, "sample_index_type": type(sample_index).__name__}
    try:
        grid = module.generate(seed, sample_index, difficulty="easy")
    except Exception as exc:
        row.update(status="rejected", exception=type(exc).__name__, message=str(exc))
        return row
    row.update(
        status="accepted",
        schedule_profile=module.schedule_profile(seed, sample_index, "easy"),
        shape=[len(grid), len(grid[0])],
        self_check=module.self_check(grid, difficulty="easy"),
        grid_sha256=grid_sha(grid),
        grid=grid,
    )
    return row

cases = [
    run_case("negative_sample_index", 0, -1),
    run_case("boolean_sample_index", 0, True),
    run_case("boolean_seed", True, 0),
    run_case("integer_seed_alias", 1, 0),
]
report = {
    "schema": "arcpuzzles-audit-strict-scalar-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "cases": cases,
    "boolean_seed_aliases_integer_one": (
        cases[2].get("status") == cases[3].get("status") == "accepted"
        and cases[2].get("grid_sha256") == cases[3].get("grid_sha256")
    ),
}
out = Path(__file__).with_name("evidence.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": report["generator_sha256"],
    "negative_sample_index": cases[0]["status"],
    "negative_profile": cases[0].get("schedule_profile"),
    "boolean_sample_index": cases[1]["status"],
    "boolean_seed": cases[2]["status"],
    "boolean_seed_aliases_integer_one": report["boolean_seed_aliases_integer_one"],
    "evidence": str(out),
}, indent=2, sort_keys=True))
