#!/usr/bin/env python3
"""Bounded reproduction for tool request review-3fba77dccbdea44a:v0001:F2."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root

TICKET_ID = "ticket-90f382c8f36dd5cf"
REQUEST_ID = "review-3fba77dccbdea44a:v0001:F2"
EXPECTED = {
    "request_source": "2cf732622eeeca12a0b3d2618fd72be588896badeb17ad67a61226d101f1b646",
    "manifest": "160ff7ed4f027f8dc6dbfc067277e87615e4b460fa727140bdae1e68482ebe6d",
    "generator": "3300eb415d4a3cc51834b82a8d35017b6a08042c77af77df1b0efd1c4d5423ed",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_request(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        if value.get("request_id") == REQUEST_ID:
            return value
        for child in value.values():
            found = find_request(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_request(child)
            if found is not None:
                return found
    return None


def find_witness_stats(value: Any, name: str) -> dict[str, Any] | None:
    if isinstance(value, dict):
        candidate = value.get(name)
        if isinstance(candidate, dict) and isinstance(candidate.get("rival_claim"), dict):
            return candidate
        for child in value.values():
            found = find_witness_stats(child, name)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_witness_stats(child, name)
            if found is not None:
                return found
    return None


def main() -> None:
    repo = find_root(__file__)
    work = repo.parent
    request_source = repo / "REVIEW/suggestions.json"
    manifest_path = repo / "shared/tools/proposals/4c01248412b2ade1/manifest.json"
    generator_path = repo / "generators/77181d1aa16c/generator.py"
    gate_path = repo / "shared/tools/generator_semantic_gate.py"

    actual = {
        "request_source": sha256(request_source),
        "manifest": sha256(manifest_path),
        "generator": sha256(generator_path),
    }
    mismatches = {
        name: {"expected": EXPECTED[name], "actual": digest}
        for name, digest in actual.items()
        if digest != EXPECTED[name]
    }
    if mismatches:
        raise SystemExit("pinned source mismatch: " + json.dumps(mismatches, sort_keys=True))

    suggestions = json.loads(request_source.read_text(encoding="utf-8"))
    request = find_request(suggestions)
    if request is None:
        raise SystemExit(f"request {REQUEST_ID} not found")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report_rows = [
        row for row in manifest.get("files", [])
        if str(row.get("path", "")).endswith("77181d1aa16c_after_semantic_gate.json")
    ]
    if len(report_rows) != 1:
        raise SystemExit(f"expected one retained semantic-gate report, got {len(report_rows)}")
    report_row = report_rows[0]
    report_path = repo / report_row["path"]
    report_sha = sha256(report_path)
    if report_sha != report_row["sha256"]:
        raise SystemExit("retained semantic-gate report does not match proposal manifest")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    witness = find_witness_stats(report, "noncanonical_source_frame")
    if witness is None:
        raise SystemExit("noncanonical_source_frame stats not found")
    claim = witness["rival_claim"]
    examples = claim.get("violation_examples") or []
    example_fields = sorted({key for row in examples for key in row})

    gate_source = gate_path.read_text(encoding="utf-8")
    generator_source = generator_path.read_text(encoding="utf-8")
    capabilities = {
        "exact_separation_contract_already_exists": all(
            text in gate_source
            for text in (
                "WITNESS_RIVALS",
                "on every grid where this witness fires",
                "at least ONE of the named rivals",
            )
        ),
        "descriptive_branch_contract_already_exists": all(
            text in gate_source for text in ("BRANCH_WITNESSES", "positive branch coverage")
        ),
        "complete_disagreement_artifact_schema_exists": all(
            text in gate_source
            for text in (
                '"authoritative_output"',
                '"rival_output"',
                '"source_binding"',
                '"arcpuzzles-semantic-witness-v1"',
            )
        ),
        "violation_path_is_still_preview_only": all(
            text in gate_source for text in ('"violation_examples"', '"grid_preview": preview')
        ),
        "current_generator_witness_checks_real_separation": (
            "return _rival_fixed_canonical_source(grid) != _render_model(grid)"
            in generator_source
        ),
    }
    if not all(capabilities.values()):
        raise SystemExit("current source no longer supports the narrowed disposition")

    requested_fields = [
        "seed/sample_index/band",
        "authoritative_output",
        "rival_output",
        "source_binding",
        "agreeing_rival_names",
    ]
    retained = {
        "seed/sample_index/band": bool(examples) and all(
            all(field in row for field in ("seed", "sample_index", "band")) for row in examples
        ),
        "authoritative_output": bool(examples) and all("authoritative_output" in row for row in examples),
        "rival_output": bool(examples) and all("rival_output" in row for row in examples),
        "source_binding": bool(examples) and all("source_binding" in row for row in examples),
        "agreeing_rival_names": bool(examples) and all("agreeing_rivals" in row for row in examples),
    }

    output = {
        "schema": "arcpuzzles-tool-request-reproduction-v1",
        "ticket_id": TICKET_ID,
        "request_id": REQUEST_ID,
        "status": "completed",
        "pinned_sources": {
            "request_source": {"path": str(request_source.relative_to(work)), "sha256": actual["request_source"]},
            "proposal_manifest": {"path": str(manifest_path.relative_to(work)), "sha256": actual["manifest"]},
            "generator": {"path": str(generator_path.relative_to(work)), "sha256": actual["generator"]},
            "current_gate": {"path": str(gate_path.relative_to(work)), "sha256": sha256(gate_path)},
            "retained_report": {"path": str(report_path.relative_to(work)), "sha256": report_sha},
        },
        "request": {
            "status": request.get("status"),
            "source_sha256": request.get("source_sha256"),
            "generator_id": request.get("generator_id"),
        },
        "reproduction": {
            "witness": "noncanonical_source_frame",
            "named_rivals": claim.get("rivals"),
            "witness_hits": witness.get("hits"),
            "checked": claim.get("checked"),
            "claim_holds": claim.get("claim_holds"),
            "claim_violated": claim.get("claim_violated"),
            "violation_examples_retained": len(examples),
            "violation_example_fields": example_fields,
            "requested_field_retention": retained,
            "missing_requested_fields": [field for field in requested_fields if not retained[field]],
        },
        "current_source_capabilities": capabilities,
        "disposition": {
            "decision": "accept_narrowed",
            "summary": (
                "Keep the automatic violation-artifact requirement, but do not add a parallel "
                "relation-type API: WITNESS_RIVALS already expresses exact separation and "
                "BRANCH_WITNESSES already expresses descriptive branch coverage."
            ),
            "recommended_change": (
                "When a witness fires and every named rival agrees with authority, retain a "
                "complete source-bound artifact with the input, canonical output, agreeing rival "
                "names and outputs, recipe, validation, and source hashes. Reuse the existing "
                "semantic-witness artifact schema where practical."
            ),
            "recommended_tests": [
                "a violated WITNESS_RIVALS claim retains full input/authority/rival grids",
                "the retained artifact binds generator, rule source, and callable hashes",
                "BRANCH_WITNESSES remains descriptive and produces no separation failure",
            ],
            "reason": (
                "The pinned report reproduces 26 violations among 60 checked firings while its "
                "three retained violation rows contain replay metadata and grid previews only."
            ),
        },
        "limits": [
            "Retained source-bound evidence was inspected once; no new broad semantic census was run.",
            "This disposition does not approve the proposal for runtime selection or training admission.",
        ],
    }
    out_path = Path(__file__).with_name("reproduction.json")
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ticket_id": TICKET_ID,
        "status": "completed",
        "decision": output["disposition"]["decision"],
        "checked": claim.get("checked"),
        "claim_violated": claim.get("claim_violated"),
        "missing_requested_fields": output["reproduction"]["missing_requested_fields"],
        "output": str(out_path),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
