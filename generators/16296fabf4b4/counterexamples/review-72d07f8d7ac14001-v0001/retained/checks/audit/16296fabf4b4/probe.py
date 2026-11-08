from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKET_WORK = HERE.parents[2]
SOURCE = PACKET_WORK / "repo/generators/16296fabf4b4/generator.py"

def load_module():
    spec = importlib.util.spec_from_file_location("audit_16296fabf4b4", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

module = load_module()
grid = json.loads((HERE / "input.json").read_text())
racket = json.loads((HERE / "racket.json").read_text())
actual = racket["results"][0]["output"]
validator_errors = module.self_check(grid, difficulty="easy", meta=None)
record = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": "16296fabf4b4",
    "finding": (
        "validator admits a wide-only identity scene despite the documented "
        "ordinary-domain invariant requiring both a tall and a non-tall component"
    ),
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "rule_hash": racket["executed_rule_hash"],
    "input": grid,
    "validator_call": {"difficulty": "easy", "meta": None},
    "validator_errors": validator_errors,
    "passes_target_validator": validator_errors == [],
    "belongs_to_documented_nondegenerate_domain": False,
    "domain_reason": "one wide component, no tall component",
    "actual_racket_output": actual,
    "rival_name": "identity",
    "rival_output": grid,
    "rival_matches_actual": actual == grid,
    "supported_apply_evidence": "checks/audit/16296fabf4b4/racket.json",
}
(HERE / "counterexample.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({
    "validator_errors": validator_errors,
    "rival_matches_actual": actual == grid,
    "generator_sha256": record["generator_sha256"],
}, sort_keys=True))
assert validator_errors == []
assert actual == grid
