#!/usr/bin/env python3
"""Replay the pinned old-source easy-curriculum audit for ticket-520a041b56577462."""
from __future__ import annotations

from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import sys
import time

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared/runtime")]
TASK = "779c7c31edc3"
TICKET = "ticket-520a041b56577462"
RETURN_ID = "review-3f97e96eb4741d55:v0002"
PINNED_SEED = "79dfcbb99b07b4993d3963da2ee8a99f1faa87c04110c7fd324270cded20d816"
CURRENT_SOURCE = REPO / f"generators/{TASK}/generator.py"
CURRENT_SHA = "edf24cd3f96c55d55eff868bba6b39fdcf5331a7af423681f658bcd858293041"
INDEX = REPO / f"generators/{TASK}/evidence/review_index.json"
INDEX_SHA = "cc8efbaa76acad7ae9720f8e6ca06228c8c8b0cf9c5b64ad5a9ce79c68763368"
ASSETS = REPO / f"generators/{TASK}/counterexamples/review-3f97e96eb4741d55-v0002/audit_assets.json"
ASSETS_SHA = "5637a7209324179a3da6f09919ee6ca55754856adaa48e5ab2c89a4c30aaffdb"
OLD_SOURCE = ASSETS.parent / "audited_source.py"
OLD_SHA = "fba5f06351d8e949821abe54d553058bd39daf1a369661c09a55b44deb59e0e7"
OLD_RULE = ASSETS.parent / "audited_rule.jsonl"
AUDIT_RECORD_SHA = "8e35ecbcfa00548bc87b1cb1ac55e5e625da5206f48601b17208e2cf28c24cad"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_hash(value) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def grid_hash(grid) -> str:
    return sha(json.dumps(grid, separators=(",", ":")).encode())


def load(path: Path):
    spec = importlib.util.spec_from_file_location("ticket_old_779c7c31edc3", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        stack = [start]
        unseen.remove(start)
        cells = []
        while stack:
            r, c = stack.pop(); cells.append((r, c))
            for nr, nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if (nr, nc) in unseen and grid[nr][nc] == color:
                    unseen.remove((nr, nc)); stack.append((nr, nc))
        result.append((color, sorted(cells)))
    return result


def first_rectangle_only(grid):
    out = copy.deepcopy(grid)
    objects = components(grid)
    if not objects:
        return out
    _, cells = objects[0]
    rows = [r for r, _ in cells]; cols = [c for _, c in cells]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            out[r][c] = 0
    return out


started = time.monotonic()
identities = {
    "current_generator": sha(CURRENT_SOURCE.read_bytes()),
    "audit_index": sha(INDEX.read_bytes()),
    "assets_manifest": sha(ASSETS.read_bytes()),
    "audited_generator": sha(OLD_SOURCE.read_bytes()),
}
assert identities == {
    "current_generator": CURRENT_SHA,
    "audit_index": INDEX_SHA,
    "assets_manifest": ASSETS_SHA,
    "audited_generator": OLD_SHA,
}
assets = json.loads(ASSETS.read_text())
for item in assets["files"]:
    path = REPO / item["path"]
    assert path.is_file() and path.stat().st_size == item["bytes"] and sha(path.read_bytes()) == item["sha256"]
index = json.loads(INDEX.read_text())
audit = next(row for row in index["audits"] if row["return_id"] == RETURN_ID)
assert canonical_hash(audit) == AUDIT_RECORD_SHA
assert audit["source_sha256"] == OLD_SHA
assert audit["assets_manifest_sha256"] == ASSETS_SHA

old = load(OLD_SOURCE)
rule_row = json.loads(OLD_RULE.read_text().splitlines()[0])
program = rule_row["program_solution"]
canonical_pairs = rule_row["train"] + rule_row["test"]
canonical_component_counts = [len(components(pair["input"])) for pair in canonical_pairs]
canonical_dimensions = []
for pair in canonical_pairs:
    for _, cells in components(pair["input"]):
        rows = [r for r, _ in cells]; cols = [c for _, c in cells]
        canonical_dimensions.append([max(rows)-min(rows)+1, max(cols)-min(cols)+1])

generation_seed = int(PINNED_SEED[:16], 16)
easy_inputs = [old.generate(generation_seed, index, difficulty="easy") for index in range(3)]
easy_component_counts = [len(components(grid)) for grid in easy_inputs]
easy_dimensions = [
    [[max(r for r, _ in cells)-min(r for r, _ in cells)+1,
      max(c for _, c in cells)-min(c for _, c in cells)+1] for _, cells in components(grid)]
    for grid in easy_inputs
]

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
wrapped = wrap_rule(program)
with RacketBridge(timeout=30.0) as bridge:
    easy_cases = []
    for index, grid in enumerate(easy_inputs):
        bridge.define_grid(f"easy-{index}", grid)
        expected = bridge.eval_text(f"({wrapped} easy-{index})")
        rival = first_rectangle_only(grid)
        easy_cases.append({
            "sample_index": index,
            "input_sha256": grid_hash(grid),
            "component_count": easy_component_counts[index],
            "dimensions": easy_dimensions[index],
            "self_check_errors": old.self_check(grid),
            "rival_matches_racket": rival == expected,
            "racket_output_sha256": grid_hash(expected),
        })
    canonical = canonical_pairs[0]
    bridge.define_grid("canonical-witness", canonical["input"])
    canonical_racket = bridge.eval_text(f"({wrapped} canonical-witness)")
    canonical_rival = first_rectangle_only(canonical["input"])
    runtime = bridge.runtime_identity

reproduced = (
    canonical_component_counts == [3, 2, 3, 2, 3]
    and [5, 3] in canonical_dimensions
    and easy_component_counts == [1, 1, 1]
    and all(case["self_check_errors"] == [] and case["rival_matches_racket"] for case in easy_cases)
    and canonical_racket == canonical["output"]
    and canonical_rival != canonical_racket
)
result = {
    "schema": "arc-ticket-audit-replay-v1",
    "ticket_id": TICKET,
    "type": "audit_replay",
    "status": "finding" if reproduced else "completed",
    "task_id": TASK,
    "audit_return_id": RETURN_ID,
    "pinned_audit_record_sha256": AUDIT_RECORD_SHA,
    "identities": identities,
    "assigned_seed": PINNED_SEED,
    "generation_seed": generation_seed,
    "audited_source_version": old.VERSION,
    "current_source_differs_from_audited_source": CURRENT_SHA != OLD_SHA,
    "canonical_component_counts": canonical_component_counts,
    "canonical_rectangle_dimensions": canonical_dimensions,
    "canonical_contains_5x3": [5, 3] in canonical_dimensions,
    "easy_cases": easy_cases,
    "rival": "hollow only the first row-major rectangle; leave additional rectangles filled",
    "canonical_witness": {
        "input_sha256": grid_hash(canonical["input"]),
        "racket_matches_retained_label": canonical_racket == canonical["output"],
        "rival_differs": canonical_rival != canonical_racket,
        "different_cell_count": sum(
            canonical_rival[r][c] != canonical_racket[r][c]
            for r in range(len(canonical_racket)) for c in range(len(canonical_racket[0]))
        ),
    },
    "racket": runtime,
    "reproduced": reproduced,
    "summary": (
        "Reproduced the pinned old-source audit: three easy draws each contain one rectangle, so a first-rectangle-only rival matches all Racket labels, while the same rival fails a three-rectangle canonical example; canonical data also includes a 5x3 rectangle absent from the old 3..4 height sampler."
        if reproduced else
        "The pinned old-source easy-curriculum claim did not reproduce exactly in the single bounded replay."
    ),
    "limits": [
        "Exactly three easy draws from one pinned seed and one canonical discriminator; no seed search or battery.",
        "This replay is bound to the retained audited source, not the independently checked current generator.",
        "Reproduction does not automatically resolve or broaden the existing audit record.",
    ],
    "elapsed_seconds": time.monotonic() - started,
}
(HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: result[k] for k in ("status", "reproduced", "summary", "canonical_component_counts", "easy_cases", "elapsed_seconds")}, sort_keys=True))
