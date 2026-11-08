from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "0994294912bf"
REPO = Path(__file__).resolve().parents[4] / "repo"
GENERATOR = REPO / "generators" / TASK_ID / "generator.py"
spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def grid_sha(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()

def generate_case(name, seed, sample_index):
    row = {"name": name, "seed": seed, "sample_index": sample_index,
           "seed_type": type(seed).__name__, "sample_index_type": type(sample_index).__name__}
    try:
        grid = module.generate(seed, sample_index, difficulty="easy")
    except Exception as exc:
        row.update(status="rejected", exception=type(exc).__name__, message=str(exc))
        return row
    row.update(status="accepted", shape=[len(grid), len(grid[0])],
               self_check=module.self_check(grid, difficulty="easy"),
               grid_sha256=grid_sha(grid), grid=grid)
    return row

def profile_case(name, seed, sample_index):
    row = {"name": name, "seed": seed, "sample_index": sample_index,
           "seed_type": type(seed).__name__, "sample_index_type": type(sample_index).__name__}
    try:
        profile = module.schedule_profile(seed, sample_index, "easy")
    except Exception as exc:
        row.update(status="rejected", exception=type(exc).__name__, message=str(exc))
        return row
    row.update(status="accepted", profile=profile)
    return row

cases = [
    generate_case("generate_negative_sample_index", 0, -1),
    profile_case("profile_negative_sample_index", 0, -1),
    generate_case("generate_boolean_sample_index", 0, True),
    profile_case("profile_boolean_sample_index", 0, True),
    generate_case("generate_float_sample_index", 0, 1.5),
    profile_case("profile_float_sample_index", 0, 1.5),
    generate_case("generate_boolean_seed", True, 0),
]
report = {
    "schema": "arcpuzzles-audit-strict-scalar-v1",
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    "cases": cases,
    "scheduler_generator_float_mismatch": (
        cases[4]["status"] == "rejected" and cases[5]["status"] == "accepted"
    ),
}
out = Path(__file__).with_name("evidence.json")
out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": report["generator_sha256"],
    "negative_generate": cases[0]["status"],
    "negative_profile": cases[1].get("profile"),
    "float_generate": [cases[4]["status"], cases[4].get("exception"), cases[4].get("message")],
    "float_schedule_profile": [cases[5]["status"], cases[5].get("profile")],
    "scheduler_generator_float_mismatch": report["scheduler_generator_float_mismatch"],
    "evidence": str(out),
}, indent=2, sort_keys=True))
