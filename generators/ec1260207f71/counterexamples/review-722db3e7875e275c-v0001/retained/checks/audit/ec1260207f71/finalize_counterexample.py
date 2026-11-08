from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GEN_PATH = ROOT / "repo/generators/ec1260207f71/generator.py"
spec = importlib.util.spec_from_file_location("audit_ec1260207f71", GEN_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

here = Path(__file__).resolve().parent
grids = json.loads((here / "input.json").read_text())
apply_record = json.loads((here / "racket.json").read_text())
outputs = [item["output"] for item in apply_record["results"]]
observed = [mod.observe_overrides(grid) for grid in grids]

def upper_only(grid):
    if mod.observe_overrides(grid)["dot_band"] == "upper":
        return mod.rule_mirror(grid)
    return [row[:] for row in grid]

rivals = [upper_only(grid) for grid in grids]
assert rivals[:4] == outputs[:4]
assert rivals[4] != outputs[4]
assert mod.self_check(grids[4]) == []
record = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "classification": "suspected shortcut / reproducible lesson-identifiability failure",
    "task_id": mod.TASK_ID,
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "declared_rule_hash": mod.RULE_HASH,
    "executed_rule_hash": apply_record["executed_rule_hash"],
    "rule_text_sha256": apply_record["rule_text_sha256"],
    "seed": 2,
    "sample_index": 33,
    "difficulty": "easy",
    "lesson_assembly": "one seed, consecutive sample indexes 33..37, first four demos and fifth query",
    "generator_domain": {
        "all_inputs_pass_self_check": True,
        "validator_errors": [mod.self_check(grid) for grid in grids],
        "observed_axes": observed,
    },
    "rival": {
        "name": "upper_only",
        "definition": "Apply the selected offset-transfer rule when dot_band is upper; otherwise return the input unchanged.",
        "fits_all_four_demonstrations": True,
        "fails_query": True,
    },
    "demonstrations": [
        {"sample_index": 33 + i, "input": grids[i], "racket_output": outputs[i], "rival_output": rivals[i]}
        for i in range(4)
    ],
    "query": {
        "sample_index": 37,
        "input": grids[4],
        "racket_output": outputs[4],
        "rival_output": rivals[4],
    },
    "apply_command": [
        "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
        "ec1260207f71", "--input", "../checks/audit/ec1260207f71/input.json",
        "--out", "../checks/audit/ec1260207f71/racket.json"
    ],
    "apply_cwd": "packet_root",
}
(here / "counterexample.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({
    "fits_demos": record["rival"]["fits_all_four_demonstrations"],
    "fails_query": record["rival"]["fails_query"],
    "query_dot_band": observed[4]["dot_band"],
    "generator_sha256": record["generator_sha256"],
    "executed_rule_hash": record["executed_rule_hash"],
}, indent=2))
