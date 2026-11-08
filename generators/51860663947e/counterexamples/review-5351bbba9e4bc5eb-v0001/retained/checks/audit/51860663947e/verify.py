"""Compare the retained supported-CLI receipt against the audit rival."""
import hashlib
import importlib.util
import json
from pathlib import Path

directory = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("audit_probe", directory / "probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
actual = json.loads((directory / "racket.json").read_text())
assert actual["generator_sha256"] == probe.identity["generator_sha256"]
assert actual["executed_rule_hash"] == probe.identity["rule_hash"]
assert actual["rule_hash_matches_catalog"] is True
comparisons = []
for case, grid, receipt, rival in zip(probe.cases, probe.inputs, actual["results"], probe.rivals, strict=True):
    assert grid == receipt["input"]
    assert receipt["input_sha256"] == case["input_sha256"]
    assert receipt["valid_output"] is True and receipt["error"] is None
    assert receipt["output"] == probe.rank_output(grid, len)
    changed_cells = [(r, c) for r in range(len(grid)) for c in range(len(grid[0])) if receipt["output"][r][c] != rival["output"][r][c]]
    comparisons.append({"case_id": case["case_id"], "input_index": case["input_index"], "self_check_errors": case["self_check_errors"], "documented_normal_region_invariants": case["satisfies_normal_documented_region_invariants"], "actual_matches_cell_count": True, "rival_matches_actual": not changed_cells, "rival_differing_cells": changed_cells, "actual_counts": {str(color): sum(row.count(color) for row in receipt["output"]) for color in (0, 1, 2, 8)}})
report = {**probe.identity, "executed_callable_text_sha256": actual["rule_text_sha256"], "receipt_sha256": hashlib.sha256((directory / "racket.json").read_bytes()).hexdigest(), "comparisons": comparisons}
(directory / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(comparisons, indent=2))
