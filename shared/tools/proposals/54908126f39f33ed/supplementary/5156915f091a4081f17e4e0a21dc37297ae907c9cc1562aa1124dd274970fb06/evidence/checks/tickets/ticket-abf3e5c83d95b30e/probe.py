#!/usr/bin/env python3
"""Reproduce a pinned mode-list tie-semantics tool request without shared edits."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TICKET_ID = "ticket-abf3e5c83d95b30e"
TASK_ID = "d3575d4206d7"
REQUEST_ID = "review-9bcf85b162267497:v0001:F1"
PROBE_SEED = "696797b551ae54c058a3f315b5ad21764e1310eb69681c12c2aab53c14095e6f"
EXPECTED = {
    "generator_sha256": "f2d7558b10285665b201f08482b40239d1a49e467337a91fd08005c435a72c15",
    "rule_hash": "abf875129734",
    "request_sha256": "a20498272f7b864ba43f3c896f23341a804267d283ac20cd162d45ae63661daa",
    "request_source_sha256": "a264898541b5dfff6ded18cd1a96798efe9576d7c70b3141864c8e86866c47b2",
    "assets_manifest_sha256": "047a14607f89592715fbd695cff1c516c4bee1d616b8555d1b931c5bc9e25789",
    "asset_sha256": "e7836edfd0ca9bbde791a421c74b414d6aeaa81e4e8eed2bbbd40866d2c65f5a",
    "historical_generator_sha256": "6fe181314ae12e34fa77ec47588b4586afd8aefdce4c1634c4ee0fbefba2b8af",
    "historical_racket_sha256": "7e6afa8252c263ce9a9636910759ed08f2c65b241fbfa5c2d5cf85256bc8c637",
}
CASES = [
    [1, 9],
    [9, 1],
    [1, 9, 9, 1],
    [2, 9],
    [9, 2],
    [3, 3, 0, 0, 3, 0, 3, 0],
]
# Literal labels retained in the repaired generator's tests from Racket 8.10.
EXPECTED_MODES = [9, 1, 9, 9, 9, 0]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def request_sha256(request: dict) -> str:
    # Matches src/arcpuzzles/review_tickets.py::_json (default ensure_ascii=True).
    body = json.dumps(request, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def load_ticket(assignment: dict) -> dict:
    matches = [
        row
        for row in assignment.get("supplementary_tickets", assignment.get("tickets", []))
        if row.get("ticket_id") == TICKET_ID
    ]
    if not matches:
        def walk(value):
            if isinstance(value, dict):
                if value.get("ticket_id") == TICKET_ID:
                    yield value
                for child in value.values():
                    yield from walk(child)
            elif isinstance(value, list):
                for child in value:
                    yield from walk(child)
        matches = list(walk(assignment))
    if len(matches) != 1:
        raise ValueError(f"expected one ticket binding, found {len(matches)}")
    return matches[0]


def run_racket_mode_probe(racket: Path, prelude: Path, ticket_dir: Path) -> dict:
    cases = " ".join("(" + " ".join(map(str, values)) + ")" for values in CASES)
    source = (
        "#lang racket\n"
        f"(require (file {json.dumps(str(prelude))}))\n"
        f"(define cases '({cases}))\n"
        "(for ([vals (in-list cases)]) (displayln (mode-list vals)))\n"
    )
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".rkt", prefix="mode-list-", dir=ticket_dir,
            encoding="utf-8", delete=False
        ) as handle:
            handle.write(source)
            temporary = Path(handle.name)
        completed = subprocess.run(
            [str(racket), str(temporary)],
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    if completed.returncode != 0:
        raise RuntimeError(
            f"Racket probe failed with {completed.returncode}: {completed.stderr.strip()}"
        )
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    actual = [int(line) for line in lines]
    return {
        "cases": CASES,
        "expected_modes": EXPECTED_MODES,
        "actual_modes": actual,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "exit_code": completed.returncode,
    }


def main() -> int:
    started = time.monotonic()
    here = Path(__file__).resolve()
    work = here.parents[3]
    repo = work / "repo"
    assignment_path = work / "AUDIT_ASSIGNMENT.json"
    suggestions_path = repo / "REVIEW/suggestions.json"
    manifest_path = repo / "shared/tools/proposals/54908126f39f33ed/manifest.json"
    generator_path = repo / f"generators/{TASK_ID}/generator.py"
    prelude_path = repo / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt"
    racket_path = work / ".review/racket-runtime/racket/bin/racket"

    assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
    ticket = load_ticket(assignment)
    assert ticket["request_id"] == REQUEST_ID
    assert ticket["request_sha256"] == EXPECTED["request_sha256"]
    assert ticket["generator_sha256"] == EXPECTED["generator_sha256"]
    assert ticket["rule_hash"] == EXPECTED["rule_hash"]
    assert ticket["seed"] == PROBE_SEED

    assert sha256(suggestions_path) == EXPECTED["request_source_sha256"]
    assert sha256(manifest_path) == EXPECTED["assets_manifest_sha256"]
    assert sha256(generator_path) == EXPECTED["generator_sha256"]

    suggestions = json.loads(suggestions_path.read_text(encoding="utf-8"))
    requests = [row for row in suggestions.get("items", []) if row.get("request_id") == REQUEST_ID]
    assert len(requests) == 1
    request = requests[0]
    assert request_sha256(request) == EXPECTED["request_sha256"]
    assert request["source_sha256"] == EXPECTED["historical_generator_sha256"]

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest.get("request_id") == REQUEST_ID
    assert manifest.get("runtime_approved") is False
    assert len(manifest.get("files", [])) == 1
    asset_row = manifest["files"][0]
    asset_path = repo / asset_row["path"]
    assert asset_path.is_file()
    assert asset_row["sha256"] == EXPECTED["asset_sha256"]
    assert sha256(asset_path) == EXPECTED["asset_sha256"]
    retained = json.loads(asset_path.read_text(encoding="utf-8"))
    assert retained["generator_sha256"] == EXPECTED["historical_generator_sha256"]
    assert retained["executed_rule_hash"] == EXPECTED["rule_hash"]
    assert retained["racket_sha256"] == EXPECTED["historical_racket_sha256"]
    assert len(retained["actual_vs_python_mirror_disagreement_cells"]) == 18

    sys.path.insert(0, str(repo / "shared/runtime"))
    from reviewer_support import load_selected_generator
    module, selected_source, selected_sha = load_selected_generator(TASK_ID, root=repo)
    assert selected_source == generator_path
    assert selected_sha == EXPECTED["generator_sha256"]
    assert module.RULE_HASH == EXPECTED["rule_hash"]

    assert racket_path.is_file()
    version_run = subprocess.run(
        [str(racket_path), "--version"], text=True, capture_output=True,
        timeout=10, check=False,
    )
    assert version_run.returncode == 0
    racket_probe = run_racket_mode_probe(racket_path, prelude_path, here.parent)
    assert racket_probe["actual_modes"] == EXPECTED_MODES
    python_modes = [module._mode_first(values) for values in CASES]
    assert python_modes == EXPECTED_MODES
    assert racket_probe["actual_modes"] == python_modes
    reverse_insertion_changes_winner = racket_probe["actual_modes"][0] != racket_probe["actual_modes"][1]
    assert reverse_insertion_changes_winner

    current_racket_sha = sha256(racket_path)
    exact_historical_runtime_available = current_racket_sha == EXPECTED["historical_racket_sha256"]
    checks = {
        "ticket_binding_matches": True,
        "request_source_hash_matches": True,
        "request_hash_matches": True,
        "assets_manifest_hash_matches": True,
        "listed_asset_hash_matches": True,
        "current_generator_hash_matches": True,
        "historical_asset_binding_matches": True,
        "historical_disagreement_has_18_cells": True,
        "current_racket_cases_match_literals": True,
        "current_python_mirror_matches_racket": True,
        "reverse_insertion_changes_winner_for_1_and_9": reverse_insertion_changes_winner,
        "exact_historical_racket_binary_available": exact_historical_runtime_available,
    }
    report = {
        "schema": "arcpuzzles-tool-reproduction-ticket-v1",
        "ticket_id": TICKET_ID,
        "status": "completed",
        "probe_seed": PROBE_SEED,
        "request_id": REQUEST_ID,
        "request_status": request.get("status"),
        "request_reason": request.get("reason"),
        "pinned_hashes": EXPECTED,
        "checks": checks,
        "retained_asset": {
            "path": asset_path.relative_to(work).as_posix(),
            "source_member": asset_row.get("source_member"),
            "historical_generator_sha256": retained["generator_sha256"],
            "executed_rule_hash": retained["executed_rule_hash"],
            "historical_racket_sha256": retained["racket_sha256"],
            "mirror_disagreement_cells": len(retained["actual_vs_python_mirror_disagreement_cells"]),
            "actual_matches_rivals": retained["actual_matches_rivals"],
        },
        "current_reproduction": {
            "generator_sha256": selected_sha,
            "rule_hash": module.RULE_HASH,
            "racket_path": str(racket_path),
            "racket_sha256": current_racket_sha,
            "racket_version": version_run.stdout.strip(),
            "prelude_sha256": sha256(prelude_path),
            "cases": CASES,
            "literal_expected_modes": EXPECTED_MODES,
            "racket_modes": racket_probe["actual_modes"],
            "python_mirror_modes": python_modes,
            "reverse_insertion_changes_winner": reverse_insertion_changes_winner,
        },
        "reproduced_state": "historical_receipt_valid_and_behavior_reproduced_on_current_packet_runtime",
        "limitations": [
            "The retained proposal asset is a failure summary, not a complete runnable arcpuzzles-apply receipt.",
            (
                "The exact historical Racket executable is not present in this packet; the current packet ships "
                f"{version_run.stdout.strip()} with SHA-256 {current_racket_sha}."
            ) if not exact_historical_runtime_available else "The exact historical Racket executable is present.",
            "This probe validates six bounded tie cases; it does not define universal hash-table tie semantics.",
        ],
        "proposed_disposition": {
            "status": "accepted",
            "action": "retain_as_confirmed_shared_contract_followup",
            "reason": (
                "All pinned request and asset hashes reproduce. The retained 18-cell mirror discrepancy is bound "
                "to the same canonical rule, and current Racket v8.10 directly reproduces the 1/9 reverse-insertion "
                "collision while the current task-local mirror matches it. Keep the request as a shared documentation/"
                "fixture or explicitly versioned-policy change; do not silently alter mode-list in this task return."
            ),
            "shared_change_implemented": False,
        },
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }
    result_path = here.with_name("probe.json")
    result_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    disposition = (
        "# Proposed request disposition\n\n"
        "**Accept as a confirmed shared-contract follow-up; do not implement it in this task return.**\n\n"
        "The pinned request, generator, manifest, and retained failure receipt hashes all match. The receipt records "
        "18 cells where the historical first-seen Python mirror disagreed with Racket under the same canonical rule. "
        "A fresh bounded probe on the packet's Racket v8.10 reproduces the key collision: `[1, 9]` selects `9`, while "
        "`[9, 1]` selects `1`; the repaired task-local mirror agrees on all six checked cases.\n\n"
        "The exact historical Racket executable bytes are not present and the retained asset is a summary rather than "
        "a complete apply receipt. Therefore this is evidence for documenting/testing the current helper or planning an "
        "explicitly versioned deterministic policy—not authority to silently change `mode-list` now.\n"
    )
    here.with_name("disposition.md").write_text(disposition, encoding="utf-8")
    print(json.dumps({
        "out": str(result_path),
        "reproduced_state": report["reproduced_state"],
        "proposed_status": report["proposed_disposition"]["status"],
        "exact_historical_runtime": exact_historical_runtime_available,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
