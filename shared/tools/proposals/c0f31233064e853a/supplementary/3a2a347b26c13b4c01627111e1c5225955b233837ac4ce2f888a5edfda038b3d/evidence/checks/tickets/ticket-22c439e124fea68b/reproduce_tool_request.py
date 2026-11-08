#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

TICKET_ID = "ticket-22c439e124fea68b"
REQUEST_ID = "review-84d80652cf29f872:v0001:F1"
TICKET_SEED = "dfa178f9b97f2832d1e0ab96c44aa524cc150936be0292150e45e1ed830180d7"
WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
OUT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


manifest_path = REPO / "shared/tools/proposals/c0f31233064e853a/manifest.json"
suggestions_path = REPO / "REVIEW/suggestions.json"
generator_path = REPO / "generators/537b409b6744/generator.py"
expected = {
    "assets_manifest": "140f6f49e1b7d0747a87ec940386ee69d44975ef6b9a1a00a59f9adf70005ac8",
    "request_source": "67fdad2e6b3cdd0fa6d8aeeff83afa2790f0fa67260178aab768276cae85e633",
    "generator": "61fe1c7026345bbfe8521c5b41576a8bda5a4695d037b84b255eb75461baa3ab",
    "request": "b3326bdc92e0c4a827a90cac06949461e081c7726f8f7a607815078df53e2155",
}
actual = {
    "assets_manifest": sha(manifest_path),
    "request_source": sha(suggestions_path),
    "generator": sha(generator_path),
}
manifest = json.loads(manifest_path.read_text())
request = next(row for row in json.loads(suggestions_path.read_text())["items"] if row["request_id"] == REQUEST_ID)
actual["request"] = canonical_sha(request)

asset_checks = []
for row in manifest["files"]:
    path = REPO / row["path"]
    asset_checks.append({
        "path": row["path"],
        "expected_sha256": row["sha256"],
        "actual_sha256": sha(path),
        "verified": sha(path) == row["sha256"],
    })

census_path = REPO / "shared/tools/proposals/c0f31233064e853a/checks/lesson-census.json"
census = json.loads(census_path.read_text())
summary = census["summary"]
retained_evidence_reproduces_expected_shape = (
    census["contract"] == "rivals"
    and census["status"] == "no_ambiguity_found"
    and census["rotation_status"] == "no_ambiguity_found"
    and census["production_status"] == "no_ambiguity_found"
    and summary["requested"] == summary["materialized"] == 300
    and summary["ambiguous"] == summary["ambiguous_rotations"] == 0
    and summary["materialization_errors"] == summary["scoring_errors"] == 0
    and summary["rotations"] == 1200
    and len(census["rivals"]) == 4
)

# Exercise the current exact semantic-gate source on a synthetic legacy generator
# with no semantic declarations.  Dependency modules are stubbed only because the
# NO_CONTRACT branch returns before canonical data or Racket execution is needed.
scripts = ModuleType("scripts")
scripts.__path__ = []
profile = ModuleType("scripts.canonical_profile_gate")
profile.BANDS = ("easy", "medium", "hard")
profile._pinned_seed = lambda *args: 1
profile.canonical_inputs = lambda *args: []
profile.canonical_pairs = lambda *args: []
verifier = ModuleType("scripts.coder_synth_verify")
verifier._grids_equal = lambda left, right: left == right
pkg = ModuleType("puzzle_generators")
pkg.__path__ = []
per_puzzle = ModuleType("puzzle_generators.per_puzzle")
per_puzzle.__path__ = []
fixture_pkg = ModuleType("puzzle_generators.per_puzzle.fixture")
fixture_pkg.__path__ = []
fixture = ModuleType("puzzle_generators.per_puzzle.fixture.generator")
for name, module in {
    "scripts": scripts,
    "scripts.canonical_profile_gate": profile,
    "scripts.coder_synth_verify": verifier,
    "puzzle_generators": pkg,
    "puzzle_generators.per_puzzle": per_puzzle,
    "puzzle_generators.per_puzzle.fixture": fixture_pkg,
    "puzzle_generators.per_puzzle.fixture.generator": fixture,
}.items():
    sys.modules[name] = module

semantic_path = REPO / "shared/tools/generator_semantic_gate.py"
spec = importlib.util.spec_from_file_location("ticket_semantic_gate", semantic_path)
assert spec and spec.loader
semantic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(semantic)
baseline = semantic.audit_task("fixture", strict=True, require_contract=False)
after = semantic.audit_task("fixture", strict=True, require_contract=True)

battery_path = REPO / "shared/tools/run_generator_battery.sh"
battery_text = battery_path.read_text()
policy_markers = {
    "after_adds_require_contract": 'strict=" --strict --require-contract --require-rival-witness --require-shortcut-counterexample --rotate-query"' in battery_text,
    "before_branch_remains_advisory": 'case "$PHASE" in before*) ;; *) strict=' in battery_text,
    "after_comment_states_fail_closed": "The AFTER phase is the opposite" in battery_text,
}
current_policy_reproduced = (
    baseline["status"] == "NO_CONTRACT"
    and not baseline["errors"]
    and after["status"] == "FAIL"
    and any("required under --require-contract" in message for message in after["errors"])
    and all(policy_markers.values())
)

report = {
    "schema": "arcpuzzles-tool-request-reproduction-v1",
    "ticket_id": TICKET_ID,
    "type": "tool_reproduction",
    "ticket_seed": TICKET_SEED,
    "request_id": REQUEST_ID,
    "identity": {
        "expected_sha256": expected,
        "actual_sha256": actual,
        "verified": actual == expected,
        "asset_files": asset_checks,
        "asset_files_verified": all(row["verified"] for row in asset_checks),
    },
    "retained_lesson_census": {
        "path": census_path.relative_to(REPO).as_posix(),
        "sha256": sha(census_path),
        "contract": census["contract"],
        "rivals": census["rivals"],
        "summary": summary,
        "status": census["status"],
        "expected_passing_shape_reproduced": retained_evidence_reproduces_expected_shape,
        "scope": census["limits"],
    },
    "current_policy_probe": {
        "semantic_gate_path": semantic_path.relative_to(REPO).as_posix(),
        "semantic_gate_sha256": sha(semantic_path),
        "battery_path": battery_path.relative_to(REPO).as_posix(),
        "battery_sha256": sha(battery_path),
        "baseline_without_require_contract": {
            "status": baseline["status"],
            "errors": baseline["errors"],
            "advisories": baseline["advisories"],
        },
        "after_with_require_contract": {
            "status": after["status"],
            "errors": after["errors"],
            "advisories": after["advisories"],
        },
        "battery_policy_markers": policy_markers,
        "reproduced": current_policy_reproduced,
    },
    "proposed_disposition": {
        "status": "implemented",
        "reason": "The current after-phase battery passes --require-contract and the exact current semantic gate converts an otherwise advisory NO_CONTRACT result into FAIL. The retained 537b409b6744 census also has the requested real lesson, four declared rivals, 300/300 materialization, and 1,200/1,200 unambiguous rotations. Close the deferred request as implemented; do not add another shared-tool change from this ticket.",
        "caveat": "The probe is a bounded synthetic no-contract branch exercise plus retained source-bound evidence, not a full battery run or a universal proof of every opt-out path.",
    },
}
report_path = OUT / "reproduction.json"
report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({
    "identity_verified": report["identity"]["verified"] and report["identity"]["asset_files_verified"],
    "retained_evidence_reproduced": retained_evidence_reproduces_expected_shape,
    "current_policy_reproduced": current_policy_reproduced,
    "proposed_disposition": report["proposed_disposition"]["status"],
    "out": str(report_path),
}, indent=2))
assert report["identity"]["verified"]
assert report["identity"]["asset_files_verified"]
assert retained_evidence_reproduces_expected_shape
assert current_policy_reproduced
