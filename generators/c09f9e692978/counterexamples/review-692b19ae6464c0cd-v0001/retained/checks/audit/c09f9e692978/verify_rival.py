from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

TASK = "c09f9e692978"
ROOT = Path.cwd()
REPORT = ROOT / "../checks/audit/c09f9e692978/required-rotations/checks/c09f9e692978_audit_semantic_gate.json"
RACKET = ROOT / "../checks/audit/c09f9e692978/rotation-racket.json"
OUT = ROOT / "../checks/audit/c09f9e692978/rotation-counterexample.json"

report = json.loads(REPORT.read_text())
audit = report["audits"][0]
example = audit["lessons"]["rotations"]["examples"][0]
instance = example["instance"]
all_pairs = instance["train"] + instance["test"]
train_pairs = [all_pairs[i] for i in example["train_indices"]]
query = all_pairs[example["query_index"]]

sys.path.insert(0, str(ROOT / "shared/runtime"))
source = ROOT / f"generators/{TASK}/generator.py"
spec = importlib.util.spec_from_file_location("audit_c09_generator", source)
assert spec and spec.loader
gen = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gen
spec.loader.exec_module(gen)

rival = gen.LESSON_COMPETITORS["border_colour_parity"]
for source_index, demo in zip(example["train_indices"], train_pairs, strict=True):
    assert rival(demo["input"]) == demo["output"], f"rival misses rotated demo source index {source_index}"

canonical = gen.rule_mirror(query["input"])
assert canonical == query["output"]
rival_output = rival(query["input"])
assert rival_output != canonical

racket = json.loads(RACKET.read_text())
racket_output = None
if isinstance(racket.get("results"), list) and racket["results"]:
    racket_output = racket["results"][0].get("output")
if racket_output is None:
    racket_output = racket.get("output") or racket.get("result") or racket.get("grid")
if isinstance(racket_output, dict):
    racket_output = racket_output.get("output") or racket_output.get("grid") or racket_output.get("result")
assert racket_output == canonical, "source-bound Racket result does not match canonical query output"

changes = [
    [r, c, canonical[r][c], rival_output[r][c]]
    for r in range(len(canonical))
    for c in range(len(canonical[0]))
    if canonical[r][c] != rival_output[r][c]
]

record = {
    "schema": "arcpuzzles-audit-rotation-counterexample-v1",
    "task_id": TASK,
    "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "declared_rule_hash": gen.RULE_HASH,
    "source_report": "checks/audit/c09f9e692978/required-rotations/checks/c09f9e692978_audit_semantic_gate.json",
    "source_bound_racket_receipt": "checks/audit/c09f9e692978/rotation-racket.json",
    "band": example["band"],
    "seed": example["seed"],
    "sample_index": example["sample_index"],
    "query_index": example["query_index"],
    "train_indices": example["train_indices"],
    "rival": "border_colour_parity",
    "warnings": example["warnings"],
    "demonstrations": [
        {"source_pair_index": i, **pair}
        for i, pair in zip(example["train_indices"], train_pairs, strict=True)
    ],
    "query": {"source_pair_index": example["query_index"], **query},
    "rival_query_output": rival_output,
    "rival_fits_all_demonstrations": True,
    "canonical_matches_source_bound_racket": True,
    "differing_cells": changes,
    "differing_cell_count": len(changes),
    "all_declared_rival_statuses": example["rivals"],
    "instance_hash": example["instance_hash"],
    "rotation_reconstruction_note": (
        "The report stores the original 3-train/1-test lesson. The rotated lesson is reconstructed "
        "from train_indices=[0,1,3] and query_index=2."
    ),
}
OUT.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({
    "generator_sha256": record["generator_sha256"],
    "band": record["band"],
    "seed": record["seed"],
    "sample_index": record["sample_index"],
    "query_index": record["query_index"],
    "train_indices": record["train_indices"],
    "rival": record["rival"],
    "rival_fits_all_demonstrations": record["rival_fits_all_demonstrations"],
    "canonical_matches_source_bound_racket": record["canonical_matches_source_bound_racket"],
    "differing_cell_count": record["differing_cell_count"],
    "differing_cells": record["differing_cells"],
}, indent=2))
