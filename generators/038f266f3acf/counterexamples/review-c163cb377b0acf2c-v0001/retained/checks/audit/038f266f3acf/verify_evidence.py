"""Verify this audit's retained facts without importing a private runner."""
import hashlib
import json
from pathlib import Path

WORK = Path.cwd().parent
OUT = WORK / "checks/audit/038f266f3acf"
read = lambda name: json.loads((OUT / name).read_text())
identity, report, census, actual = [read(name) for name in (
    "source_identity.json", "comparison.json", "python_census.json", "racket.json")]
source = WORK / identity["generator_path"]
assert hashlib.sha256(source.read_bytes()).hexdigest() == identity["generator_sha256"]
assert hashlib.sha256((OUT / "probe.py").read_bytes()).hexdigest() == identity["probe_sha256"]
assert actual["generator_sha256"] == identity["generator_sha256"]
assert actual["executed_rule_hash"] == identity["declared_rule_hash"]
assert actual["rule_hash_matches_catalog"]
assert len(actual["results"]) == 7
inputs = read("input.json")
for grid, row in zip(inputs, actual["results"]):
    assert grid == row["input"]
    assert row["valid_output"] and row["error"] is None
    assert row["generator_domain"] == {"status": "valid", "errors": []}
assert len(census["population"]) == 96
assert all(row["rival_equals_mirror"] and not row["self_check"] for row in census["population"])
assert len(census["canonical"]) == 10
assert sum(not row["rival_equals_recorded_output"] for row in census["canonical"]) == 2
comparisons = report["comparisons"]
assert all(row["mirror_equals_racket"] for row in comparisons)
assert all(row["rival_equals_racket"] for row in comparisons[:5])
assert comparisons[5]["matches_recorded_canonical"]
assert len(comparisons[5]["rival_differing_cells"]) == 28
assert comparisons[6]["rival_differing_cells"] == [[0, 0, 3, 0], [0, 1, 3, 0]]
assert all(not row["lesson_identifiable"] and row["rival_fits_all_demos"] for row in report["lessons"])
assert [row["rival_changes_query"] for row in report["lessons"]] == [False, True, True]
assert (OUT / "AUDIT_SECTION.md").read_text().startswith("## 038f266f3acf\n")

verification = {
    "status": "verified",
    "generator_sha256": identity["generator_sha256"],
    "executed_rule_source_sha256": actual["rule_text_sha256"],
    "live_racket_cases": 7,
    "canonical_counterexample_differing_cells": 28,
    "small_counterexample_differing_cells": 2,
    "python_only_census_draws": 96,
    "artifact_sha256": {str(path.relative_to(WORK)): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in sorted(OUT.iterdir()) if path.is_file()
                        and path.name not in ("commands.json", "verification.json")},
}
(OUT / "verification.json").write_text(json.dumps(verification, indent=2) + "\n")
print(json.dumps({k:v for k,v in verification.items() if k != "artifact_sha256"}, indent=2))
