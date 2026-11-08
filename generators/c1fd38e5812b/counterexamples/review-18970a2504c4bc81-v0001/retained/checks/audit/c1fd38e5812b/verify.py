#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve()
probe = json.loads((HERE.parent / "probe-preapply.json").read_text())
racket = json.loads((HERE.parent / "racket.json").read_text())
assert racket["generator_sha256"] == probe["generator_sha256"]
assert racket["rule_hash_matches_catalog"] is True
assert len(racket["results"]) == 1
row = racket["results"][0]
assert row["error"] is None
assert row["generator_domain"]["status"] == "valid"
assert row["generator_domain"]["errors"] == []
assert row["output"] == probe["python_authority_mirror"]
assert row["output"] != probe["rival_output"]
record = {
    "schema": "arcpuzzles-audit-finding-v1",
    "task_id": probe["task_id"],
    "severity": "moderate",
    "finding": "Generated support couples row-span and column-span uniformity, permitting a mixed-axis shortcut.",
    "generator_sha256": probe["generator_sha256"],
    "catalog_rule_hash": racket["catalog_rule_hash"],
    "executed_rule_hash": racket["executed_rule_hash"],
    "rule_hash_matches_catalog": racket["rule_hash_matches_catalog"],
    "rule_text_sha256": racket["rule_text_sha256"],
    "prior_audit_lead": probe["prior_audit_lead"],
    "input": row["input"],
    "generator_domain": row["generator_domain"],
    "actual_racket_output": row["output"],
    "rival_name": probe["rival_name"],
    "rival_output": probe["rival_output"],
    "construction": probe["construction"],
    "command": probe["apply_command"],
    "limitation": "One exact accepted witness revalidates the gap; this audit did not repeat the prior 48-draw census.",
}
(HERE.parent / "finding.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps({"task_id": probe["task_id"], "authority_verified": True, "rival_differs": True}, sort_keys=True))
