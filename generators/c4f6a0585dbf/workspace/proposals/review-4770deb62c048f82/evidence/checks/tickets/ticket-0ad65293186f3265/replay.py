from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

TASK_ID = "241567a35764"
SOURCE_SHA = "69f86832961e4434279bde01ae305a6dc3113d31ad7e626e1bb0de961ed0d816"
AUDIT_INDEX_SHA = "1d68e28f291690d666dd1266aef4f83fa43cd7c3e74150c99466639e18964891"
ASSETS_SHA = "3d10e7ad12738af19d70194e0ff4581e3ac0f755d5e02275cef1a0960bbde782"
RETURN_ID = "review-faae0e7ca114d4aa:v0001"
HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
GEN_DIR = ROOT / "generators" / TASK_ID
AUDIT_ROOT = GEN_DIR / "counterexamples" / "review-faae0e7ca114d4aa-v0001"
RETAINED = AUDIT_ROOT / "retained" / "checks" / "audit" / TASK_ID


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_sha(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def evaluate(bridge, source, grid):
    body = strip_rule_wrapper(source)
    if body.lstrip().startswith("(lambda"):
        datum = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        value = bridge.eval_text(f"({body} '{datum})")
    else:
        bridge.define_grid("g", grid)
        value = bridge.eval_text(body)
    return normalize_grid(value)


started = time.monotonic()
source_path = GEN_DIR / "generator.py"
audit_index_path = GEN_DIR / "evidence" / "review_index.json"
assets_path = AUDIT_ROOT / "audit_assets.json"
assert sha(source_path) == SOURCE_SHA
assert sha(audit_index_path) == AUDIT_INDEX_SHA
assert sha(assets_path) == ASSETS_SHA

audit_index = json.loads(audit_index_path.read_text())
record = next(row for row in audit_index["audits"] if row["return_id"] == RETURN_ID)
record_sha = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
assert record_sha == "a68dc9c3c101fce2768ad67a8b9129733c87edba57a88971a80b49bc04738159"

generator, selected_source, selected_sha = load_selected_generator(TASK_ID, root=ROOT)
assert selected_source == source_path
assert selected_sha == SOURCE_SHA
actual_input = generator.generate(0, 1, difficulty="easy")
retained_input = json.loads((RETAINED / "input.json").read_text())
retained_receipt = json.loads((RETAINED / "racket.json").read_text())
assert actual_input == retained_input
assert generator.self_check(actual_input, difficulty="easy") == []

programs = []
with canonical_path(ROOT).open(encoding="utf-8") as handle:
    for line in handle:
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            programs.append(row["program_solution"])
assert len(set(programs)) == 1
program = programs[0]
with RacketBridge() as bridge:
    actual_output = evaluate(bridge, program, actual_input)
retained_output = retained_receipt["results"][0]["output"]
assert actual_output == retained_output
assert all(cell == 0 for row in actual_output for cell in row)

result = {
    "schema": "audit-replay-ticket-v1",
    "ticket_id": "ticket-0ad65293186f3265",
    "status": "reproduced",
    "task_id": TASK_ID,
    "audit_return_id": RETURN_ID,
    "pinned_identity": {
        "generator_sha256": selected_sha,
        "audit_index_sha256": sha(audit_index_path),
        "assets_manifest_sha256": sha(assets_path),
        "audit_record_sha256": record_sha,
        "rule_hash": retained_receipt["executed_rule_hash"],
        "rule_text_sha256": retained_receipt["rule_text_sha256"],
    },
    "witness": {
        "seed": 0,
        "sample_index": 1,
        "difficulty": "easy",
        "input_matches_retained": True,
        "input_sha256": grid_sha(actual_input),
        "self_check": [],
        "shape": [len(actual_input), len(actual_input[0])],
        "marker_7": [[r, c] for r, row in enumerate(actual_input) for c, value in enumerate(row) if value == 7],
        "marker_8": [[r, c] for r, row in enumerate(actual_input) for c, value in enumerate(row) if value == 8],
    },
    "authority": {
        "output_matches_retained": True,
        "output_sha256": grid_sha(actual_output),
        "nonzero_cells": sum(cell != 0 for row in actual_output for cell in row),
        "all_zero": True,
    },
    "claim": (
        "The unchanged pinned generator still emits the exact self-check-valid 12x14 witness, "
        "and the pinned canonical Racket authority still returns an all-zero output."
    ),
    "scope": "One pinned witness replay only; no scan and no audit disposition change.",
    "elapsed_seconds": round(time.monotonic() - started, 3),
}
(Path(__file__).with_name("result.json")).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
