from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
TASK_ID = "ba32e05911b0"
SOURCE_SHA256 = "e71e4c26811b60906e4725b9f885f81a27857baeedb267234b8de7be59621345"
ASSETS_SHA256 = "69903b025a7026547a1509474cc0458ad75f3f75d227616a2f67c40ff99f4b6a"
INDEX_SHA256 = "ce431ffecc71ed23f972eb06b8d24aaf3d506c02c32244a370b56c2e564f9984"
AUDIT_RECORD_SHA256 = "8ad47d34e4d18d6ec5debbe63b4769e40de44a0ad3ec5eb5487c804e4afb4e14"
RETURN_ID = "review-4ea175c0c4711abd:v0001"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=ROOT)
assert generator_sha == SOURCE_SHA256
assets_path = ROOT / "generators" / TASK_ID / "counterexamples" / "review-4ea175c0c4711abd-v0001" / "audit_assets.json"
index_path = ROOT / "generators" / TASK_ID / "evidence" / "review_index.json"
assert sha256(assets_path) == ASSETS_SHA256
assert sha256(index_path) == INDEX_SHA256
assets = json.loads(assets_path.read_text())
for record in assets["files"]:
    path = ROOT / record["path"]
    assert path.is_file(), path
    assert path.stat().st_size == record["bytes"], path
    assert sha256(path) == record["sha256"], path

index = json.loads(index_path.read_text())
records = [row for row in index["audits"] if row.get("return_id") == RETURN_ID]
assert len(records) == 1
record = records[0]
record_sha = hashlib.sha256(
    json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
assert record_sha == AUDIT_RECORD_SHA256

programs: set[str] = set()
with canonical_path(ROOT).open(encoding="utf-8") as handle:
    for line in handle:
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            programs.add(row["program_solution"])
assert len(programs) == 1
program = programs.pop()


def straight_up(grid):
    output = normalize_grid(grid)
    for row_index, row in enumerate(grid):
        for column, value in enumerate(row):
            if value == 6:
                for above in range(row_index):
                    output[above][column] = 2
                output[0][column] = 6
    return output

inputs = [generator.generate(10, index, difficulty="medium") for index in range(4)]
validators = [generator.self_check(grid) for grid in inputs]
assert validators == [[], [], [], []]
profiles = [generator.observe_overrides(grid)["scene_profile"] for grid in inputs]
assert profiles[:3] == ["clear_climb", "clear_climb", "clear_climb"]
assert profiles[3] == "long_roll"
rivals = [straight_up(grid) for grid in inputs]

with RacketBridge() as bridge:
    runtime = dict(bridge.runtime_identity)
    callable_rule = wrap_rule(program)
    outputs = []
    for index, grid in enumerate(inputs):
        name = f"audit_replay_grid_{index}"
        bridge.define_grid(name, grid)
        outputs.append(normalize_grid(bridge.eval_text(f"({callable_rule} {name})")))

matches = [rival == actual for rival, actual in zip(rivals, outputs)]
assert matches[:3] == [True, True, True]
assert matches[3] is False
changed = [
    [row, column]
    for row, (rival_row, actual_row) in enumerate(zip(rivals[3], outputs[3]))
    for column, (rival_value, actual_value) in enumerate(zip(rival_row, actual_row))
    if rival_value != actual_value
]
mirror_matches = [generator.rule_mirror(grid) == actual for grid, actual in zip(inputs, outputs)]
assert all(mirror_matches)

retained_evidence_path = assets_path.parent / "retained" / "checks" / "audit" / TASK_ID / "evidence.json"
retained = json.loads(retained_evidence_path.read_text())
expected_changed = retained["conclusion"]["query_changed_cells"]
assert len(changed) == expected_changed

result = {
    "schema": "arcpuzzles-ticket-audit-replay-v1",
    "ticket_id": "ticket-b8db1a99de39339d",
    "type": "audit_replay",
    "task_id": TASK_ID,
    "source_sha256": generator_sha,
    "assets_manifest_sha256": sha256(assets_path),
    "audit_index_sha256": sha256(index_path),
    "audit_record_sha256": record_sha,
    "audit_return_id": RETURN_ID,
    "seed": 10,
    "difficulty": "medium",
    "sample_indices": [0, 1, 2, 3],
    "profiles": profiles,
    "validators": validators,
    "rival_matches": matches,
    "query_changed_cells": len(changed),
    "retained_query_changed_cells": expected_changed,
    "rule_mirror_matches_racket_all_four": all(mirror_matches),
    "racket": runtime,
    "conclusion": "The pinned existing audit witness reproduced exactly on the pinned current source: the no-roll rival fits all three demonstrations and differs on the long-roll query.",
    "proposed_disposition": "retain the existing audit as unresolved/repair-candidate; this replay is duplicate confirmation, not a new distinct finding and does not clear the audit",
    "limitations": [
        "Bounded to seed 10, medium difficulty, indices 0..3, and one declared rival.",
        "No peer source or shared source was modified.",
    ],
}
(HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, sort_keys=True))
