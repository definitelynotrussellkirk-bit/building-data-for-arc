#!/usr/bin/env python3
"""Replay the 55c08ab3ce73 support/override audit and bind its Racket result."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "repo/shared/runtime"
sys.path.insert(0, str(RUNTIME))
GEN_PATH = ROOT / "repo/generators/55c08ab3ce73/generator.py"
INPUT_PATH = Path(__file__).with_name("input.json")
RACKET_PATH = Path(__file__).with_name("racket.json")

spec = importlib.util.spec_from_file_location("audit_gen_55", GEN_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot import {GEN_PATH}")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

sha = hashlib.sha256(GEN_PATH.read_bytes()).hexdigest()
edge = 0
valid = 0
unique: set[tuple[tuple[int, ...], ...]] = set()
failures = []
for index in range(300):
    grid = gen.generate(52000 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
    errors = gen.self_check(grid)
    if errors:
        failures.append({"index": index, "errors": errors})
    else:
        valid += 1
    if any(row[0] not in (0, 5) for row in grid):
        edge += 1
    unique.add(tuple(tuple(row) for row in grid))

try:
    gen.generate(0, 3, difficulty="easy", grid_h=16)
except Exception as exc:  # evidence records the public rejection verbatim
    override_result = {"type": type(exc).__name__, "message": str(exc)}
else:
    override_result = {"type": None, "message": "accepted"}

input_grid = json.loads(INPUT_PATH.read_text())
probe = {
    "schema": "arcpuzzles-adversarial-audit-v1",
    "task_id": "55c08ab3ce73",
    "generator_sha256": sha,
    "generator_version": gen.VERSION,
    "sample": {
        "seed_start": 52000,
        "sample_index_range": [0, 299],
        "difficulty_cycle": ["easy", "medium", "hard"],
        "denominator": 300,
        "valid": valid,
        "unique_inputs": len(unique),
        "edge_touching_source_count": edge,
        "failures": failures[:5],
    },
    "advertised_override_probe": {
        "argv": ["generate", 0, 3, "difficulty=easy", "grid_h=16"],
        "declared_axis": "grid_h valid 4..16",
        "result": override_result,
    },
    "counterexample": {
        "input": input_grid,
        "self_check_errors": gen.self_check(input_grid),
        "belongs_to_canonical_rule_domain": not gen.self_check(input_grid),
        "generator_support_observation": "source motif touches column 0; 0/300 sampled generated inputs did so",
    },
}
Path(__file__).with_name("generator_probe.json").write_text(json.dumps(probe, indent=2, sort_keys=True) + "\n")

if not RACKET_PATH.is_file():
    raise SystemExit("run public arcpuzzles apply first; racket.json is missing")
racket = json.loads(RACKET_PATH.read_text())
entry = racket["results"][0]
rival = [row[:] for row in entry["input"]]
counterexample = {
    "schema": "arcpuzzles-adversarial-counterexample-v1",
    "task_id": "55c08ab3ce73",
    "generator_sha256": sha,
    "generator_version": gen.VERSION,
    "rule_hash": racket["executed_rule_hash"],
    "rule_text_sha256": racket["rule_text_sha256"],
    "seed": None,
    "sample_index": None,
    "overrides": {},
    "generated_by_target": False,
    "passes_target_validator": not probe["counterexample"]["self_check_errors"],
    "validator_errors": probe["counterexample"]["self_check_errors"],
    "belongs_to_documented_rule_domain": not probe["counterexample"]["self_check_errors"],
    "input": entry["input"],
    "input_sha256": entry["input_sha256"],
    "actual_racket_output": entry["output"],
    "actual_output_sha256": entry["output_sha256"],
    "rival_name": "ignore_column_zero_sources",
    "rival_description": "Mirror only motif cells in columns 1 through divider-1; leave column-0 source cells unmirrored. This fits the generator support because it never emits column-0 source cells.",
    "rival_output": rival,
    "disagrees": rival != entry["output"],
    "support_probe": probe["sample"],
    "advertised_override_probe": probe["advertised_override_probe"],
    "apply_command": racket["command"],
    "apply_cwd": racket["cwd"],
    "evidence_paths": [
        "checks/audit/55c08ab3ce73/generator_probe.json",
        "checks/audit/55c08ab3ce73/racket.json",
    ],
}
Path(__file__).with_name("counterexample.json").write_text(json.dumps(counterexample, indent=2, sort_keys=True) + "\n")
print(json.dumps({"sample": probe["sample"], "override": override_result, "disagrees": counterexample["disagrees"]}, indent=2))
