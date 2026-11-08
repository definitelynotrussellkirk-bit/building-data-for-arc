from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog

ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit-5cafd26ce560-counterexample.json"
TASK = "5cafd26ce560"
SEED = 123
SAMPLE_INDEX = 7
DIFFICULTY = "medium"
LOW = {"meta_density": 0.2}
HIGH = {"meta_density": 0.9}

catalog = Catalog(ROOT)
common = dict(
    count=1,
    seed=SEED,
    difficulty=DIFFICULTY,
    n_train=1,
    n_test=1,
    sample_index=SAMPLE_INDEX,
    allow_unapproved=True,
    timeout=240,
)
low_episode = catalog.generate(TASK, overrides=LOW, **common)[0]
high_episode = catalog.generate(TASK, overrides=HIGH, **common)[0]

# Validate the exact returned inputs against the target's own validator.
sys.path.insert(0, str(ROOT / "shared" / "runtime"))
gen_path = ROOT / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location(f"audit_{TASK}", gen_path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

def first_pair(episode: dict) -> dict:
    return episode["train"][0]

low_pair = first_pair(low_episode)
high_pair = first_pair(high_episode)
low_grid = low_pair["input"]
high_grid = high_pair["input"]
low_bytes = json.dumps(low_grid, separators=(",", ":"), sort_keys=False).encode()
high_bytes = json.dumps(high_grid, separators=(",", ":"), sort_keys=False).encode()

record = {
    "schema": "arc-review-audit-reproducer-v1",
    "finding": "declared meta_density override is accepted but not consumed",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(gen_path.read_bytes()).hexdigest(),
    "rule_hash": low_episode["provenance"]["rule_hash"],
    "seed": SEED,
    "sample_index": SAMPLE_INDEX,
    "difficulty": DIFFICULTY,
    "low_override": LOW,
    "high_override": HIGH,
    "low_input_sha256": hashlib.sha256(low_bytes).hexdigest(),
    "high_input_sha256": hashlib.sha256(high_bytes).hexdigest(),
    "inputs_byte_identical": low_grid == high_grid,
    "outputs_byte_identical": low_pair["output"] == high_pair["output"],
    "low_input": low_grid,
    "high_input": high_grid,
    "actual_racket_output_low": low_pair["output"],
    "actual_racket_output_high": high_pair["output"],
    "rival_output": None,
    "rival_output_reason": "Not a semantic rival: this reproduces the public override/API contract defect.",
    "validator_low": module.self_check(low_grid, difficulty=DIFFICULTY),
    "validator_high": module.self_check(high_grid, difficulty=DIFFICULTY),
    "belongs_to_documented_domain": True,
    "documented_axis": module.AXES["meta_density"],
    "command": [
        "python3", "run_with_racket.py", "python3", "../checks/make_audit_5cafd_reproducer.py"
    ],
    "cwd": "packet_root",
}
if not record["inputs_byte_identical"]:
    raise SystemExit("Expected ignored meta_density overrides to reproduce identical inputs")
if record["validator_low"] or record["validator_high"]:
    raise SystemExit("Exact reproducer did not pass target self_check")
OUT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(OUT)
print(json.dumps({k: record[k] for k in (
    "generator_sha256", "rule_hash", "inputs_byte_identical",
    "outputs_byte_identical", "validator_low", "validator_high"
)}, indent=2))
