from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

REPO = Path.cwd().resolve()
OUT = (REPO / "../checks/audit/38300735cc4d").resolve()
TASK_ID = "38300735cc4d"
SOURCE = REPO / "generators" / TASK_ID / "generator.py"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid: Any) -> str:
    return sha256_bytes(json.dumps(grid, separators=(",", ":")).encode())


def load_module():
    spec = importlib.util.spec_from_file_location("audit_383_generator", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


module = load_module()
input_payload = json.loads((OUT / "input.json").read_text())
grid = input_payload["input"]
racket = json.loads((OUT / "racket.json").read_text())
racket_output = racket["results"][0]["output"]
copy_output = module.SEMANTIC_RIVALS["copy_input"](grid)
mirror_output = module.rule_mirror(grid)
facts = module.semantic_observables(grid)
witness_value = module.SEMANTIC_WITNESSES["clear_bridge_changes_grid"](grid)

rival_doc = {
    "schema": "arcpuzzles-audit-rival-v1",
    "task_id": TASK_ID,
    "rival_name": "copy_input",
    "description": "Return the input unchanged.",
    "output": copy_output,
    "output_sha256": grid_hash(copy_output),
}
(OUT / "rival.json").write_text(json.dumps(rival_doc, indent=2) + "\n")

generated_rows = []
for band_index, difficulty in enumerate(("easy", "medium", "hard")):
    seed = 94000 + band_index
    for sample_index in range(30):
        sample = module.generate(seed, sample_index, difficulty=difficulty)
        generated_rows.append({
            "difficulty": difficulty,
            "seed": seed,
            "sample_index": sample_index,
            "input_sha256": grid_hash(sample),
            "validator_ok": not module.self_check(sample),
            "nonidentity": module.rule_mirror(sample) != sample,
        })

probe = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK_ID,
    "generator_sha256": sha256_bytes(SOURCE.read_bytes()),
    "declared_rule_hash": module.RULE_HASH,
    "counterexample": {
        "input_sha256": racket["results"][0]["input_sha256"],
        "selected_racket_output_sha256": racket["results"][0]["output_sha256"],
        "validator_errors": module.self_check(grid),
        "validator_status": racket["results"][0]["generator_domain"],
        "pair_spans": [pair["span"] for pair in facts["pairs"]],
        "pair_interior_lengths": [len(pair["interior"]) for pair in facts["pairs"]],
        "scene_profile": facts["scene_profile"],
        "mirror_matches_selected_racket": mirror_output == racket_output,
        "copy_rival_matches_selected_racket": copy_output == racket_output,
        "clear_bridge_changes_grid_witness": witness_value,
        "selected_output_equals_input": racket_output == grid,
        "interpretation": "self_check accepts a lawful adjacent-only no-op scene even though its docstring says rule-hiding scenes are rejected; generated lessons separately exclude identity outputs.",
    },
    "generated_policy": {
        "difficulties": ["easy", "medium", "hard"],
        "seeds": {"easy": 94000, "medium": 94001, "hard": 94002},
        "sample_indices": [0, 29],
        "samples_per_band": 30,
        "total_samples": len(generated_rows),
    },
    "generated_unique_inputs": len({row["input_sha256"] for row in generated_rows}),
    "generated_validator_passes": sum(row["validator_ok"] for row in generated_rows),
    "generated_nonidentity": sum(row["nonidentity"] for row in generated_rows),
}
(OUT / "probe.json").write_text(json.dumps(probe, indent=2) + "\n")

counterexample = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": TASK_ID,
    "finding_id": "A-383-1",
    "generator_sha256": probe["generator_sha256"],
    "rule_hash": module.RULE_HASH,
    "generated": False,
    "seed": None,
    "sample_index": None,
    "overrides": {},
    "input": grid,
    "input_sha256": racket["results"][0]["input_sha256"],
    "actual_racket_output": racket_output,
    "actual_racket_output_sha256": racket["results"][0]["output_sha256"],
    "rival_name": "copy_input",
    "rival_output": copy_output,
    "rival_output_sha256": rival_doc["output_sha256"],
    "differing_cell_count": 0,
    "validator_status": racket["results"][0]["generator_domain"],
    "generator_domain_membership": "validator-valid but outside generate() support",
    "witness_clear_bridge_changes_grid": witness_value,
    "command": racket["command"],
    "cwd": racket["cwd"],
    "evidence": [
        "checks/audit/38300735cc4d/input.json",
        "checks/audit/38300735cc4d/racket.json",
        "checks/audit/38300735cc4d/rival.json",
        "checks/audit/38300735cc4d/probe.json"
    ],
}
(OUT / "counterexample.json").write_text(json.dumps(counterexample, indent=2) + "\n")
print(json.dumps({
    "validator_errors": probe["counterexample"]["validator_errors"],
    "copy_matches": probe["counterexample"]["copy_rival_matches_selected_racket"],
    "witness": witness_value,
    "generated_nonidentity": [probe["generated_nonidentity"], probe["generated_policy"]["total_samples"]],
}, indent=2))
