"""Verify the retained live-Racket witness against the audit's independent rival."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


probe = read("probe.json")
execution = read("racket.json")
grid = read("input.json")
expected = read("expected_row_profile.json")
rival = read("rectangle_rival.json")
assert execution["task_id"] == "a286d31d63fb"
assert execution["generator_sha256"] == probe["source_sha256"]
assert execution["rule_hash_matches_catalog"] is True
assert execution["executed_rule_hash"] == probe["canonical_rule_sha256"][:12]
assert len(execution["results"]) == 1
result = execution["results"][0]
assert result["error"] is None and result["valid_output"] is True
assert result["input"] == grid
assert result["output"] == expected
assert result["output"] != rival
changed = [[r, c] for r in range(len(grid)) for c in range(len(grid[0]))
           if grid[r][c] != result["output"][r][c]]
assert changed == [[1, 1], [1, 2], [2, 2], [2, 3]]
assert hashlib.sha256(Path(probe["source_path"]).read_bytes()).hexdigest() == probe["source_sha256"]
report = {
    "verified": True, "task_id": "a286d31d63fb", "actual_racket_cases": 1,
    "generator_sha256": probe["source_sha256"],
    "canonical_raw_rule_sha256": probe["canonical_rule_sha256"],
    "executed_normalized_rule_text_sha256": execution["rule_text_sha256"],
    "executed_rule_hash": execution["executed_rule_hash"],
    "self_check_accepted": probe["witness"]["self_check"] == [],
    "racket_matches_independent_row_profile_model": result["output"] == expected,
    "rectangle_rival_differs_from_racket": result["output"] != rival,
    "racket_changed_cells": changed, "source_unchanged": True,
}
(HERE / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
