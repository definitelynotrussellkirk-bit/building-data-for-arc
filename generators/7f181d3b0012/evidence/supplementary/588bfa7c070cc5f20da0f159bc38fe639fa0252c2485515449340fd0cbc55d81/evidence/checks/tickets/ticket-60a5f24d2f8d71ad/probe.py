from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog

ROOT = Path.cwd()
TASK = "7f181d3b0012"
TICKET_SEED = "73411de90bcb91f1cd0439dd7bc2a6d9d26cb62fbae1d9d66f6ebea4ec67e002"
EXPECTED_GENERATOR_SHA = "70eb2d7ac8dadba5519d165b4f9d81ecb42ca586a47c264b6dfa284a1f9e5073"
EXPECTED_RULE_HASH = "738584ea6289"
SOURCE = ROOT / f"generators/{TASK}/generator.py"
OUTPUT = ROOT.parent / "checks/tickets/ticket-60a5f24d2f8d71ad/result.json"

assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_GENERATOR_SHA
spec = importlib.util.spec_from_file_location("ticket_generator_7f181d3b0012", SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

seed = int(TICKET_SEED, 16)
grid = module.generate(seed, 0, difficulty="medium")
assert module.self_check(grid) == []
assert grid != list(reversed(grid)), "ticket seed unexpectedly produced a UD-symmetric grid"

application = Catalog(root=ROOT).apply(
    TASK,
    [grid],
    reference="canonical",
    timeout=110,
    check_generator_domain=True,
)
assert application["executed_rule_hash"] == EXPECTED_RULE_HASH
assert application["rule_hash_matches_catalog"] is True
canonical = application["results"][0]["output"]
expected = [*grid, *reversed(grid)]
plain_duplicate = [*grid, *grid]
assert canonical == expected
assert canonical != plain_duplicate
h = len(grid)
differences = [
    {"row": r, "column": c, "canonical": canonical[r][c], "plain_duplicate": plain_duplicate[r][c]}
    for r in range(h, 2 * h)
    for c in range(len(grid[0]))
    if canonical[r][c] != plain_duplicate[r][c]
]
assert differences

result = {
    "schema": "arc-review-ticket-adversarial-witness-v1",
    "ticket_id": "ticket-60a5f24d2f8d71ad",
    "task_id": TASK,
    "ticket_seed": TICKET_SEED,
    "sample_index": 0,
    "difficulty": "medium",
    "generator_sha256": EXPECTED_GENERATOR_SHA,
    "canonical_rule_hash": application["executed_rule_hash"],
    "rule_hash_matches_catalog": application["rule_hash_matches_catalog"],
    "generator_domain_check": application["results"][0].get("generator_domain"),
    "input": grid,
    "canonical_output": canonical,
    "shortcut": {
        "name": "plain_vertical_duplication",
        "output": plain_duplicate,
        "survives": False,
        "differing_cells": differences,
    },
    "lawfulness": {
        "self_check_errors": module.self_check(grid),
        "ud_asymmetric": grid != list(reversed(grid)),
        "input_height": len(grid),
        "input_width": len(grid[0]),
        "palette_size": len({value for row in grid for value in row}),
    },
    "reference_receipt": {
        key: application[key]
        for key in (
            "schema", "task_id", "rule_task_id", "reference", "rule_file",
            "executed_rule_hash", "catalog_rule_hash", "rule_hash_matches_catalog",
            "rule_text_sha256", "generator_sha256", "catalog_approved", "approved",
            "train_safety", "elapsed_seconds", "note",
        )
    },
    "conclusion": (
        "A lawful ticket-seed input is UD-asymmetric, and protected canonical Racket execution "
        "differs from the plausible 'stack the input twice' shortcut in the bottom half."
    ),
}
OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": "completed", "result": str(OUTPUT), "differing_cells": len(differences)}))
