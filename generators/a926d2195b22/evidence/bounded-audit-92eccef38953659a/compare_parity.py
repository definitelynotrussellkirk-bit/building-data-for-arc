#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
from pathlib import Path
base = Path(__file__).parent
expected = json.loads((base / "parity-expected.json").read_text())
racket = json.loads((base / "parity-racket.json").read_text())
failures = []
for case, actual in zip(expected["cases"], racket["results"]):
    if case["self_check"]:
        failures.append({"seed": case["seed"], "sample_index": case["sample_index"], "kind": "self_check", "errors": case["self_check"]})
    if case["python_expected"] != actual.get("output"):
        failures.append({"seed": case["seed"], "sample_index": case["sample_index"], "kind": "racket_mismatch"})
report = {
    "schema": "arcpuzzles-audit-racket-parity-v1",
    "task_id": expected["task_id"],
    "generator_sha256": expected["generator_sha256"],
    "canonical_rule_hash": racket.get("executed_rule_hash"),
    "catalog_rule_hash": racket.get("catalog_rule_hash"),
    "rule_hash_matches_catalog": racket.get("rule_hash_matches_catalog"),
    "case_count": len(expected["cases"]),
    "profile_counts": {name: sum(c["profile"] == name for c in expected["cases"]) for name in sorted({c["profile"] for c in expected["cases"]})},
    "failures": failures,
    "passed": not failures and len(expected["cases"]) == len(racket.get("results", [])),
    "source_files": {
        "expected_sha256": hashlib.sha256((base / "parity-expected.json").read_bytes()).hexdigest(),
        "racket_sha256": hashlib.sha256((base / "parity-racket.json").read_bytes()).hexdigest(),
    },
}
(base / "racket-parity.json").write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
print(json.dumps({"case_count": report["case_count"], "failures": len(failures), "passed": report["passed"]}, sort_keys=True))
raise SystemExit(0 if report["passed"] else 1)
