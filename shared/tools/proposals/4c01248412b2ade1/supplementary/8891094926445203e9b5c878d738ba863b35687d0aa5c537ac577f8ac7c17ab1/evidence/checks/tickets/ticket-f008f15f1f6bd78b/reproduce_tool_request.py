#!/usr/bin/env python3
"""Bounded reproduction for tool request review-3fba77dccbdea44a:v0001:F2."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

TICKET_ID = "ticket-f008f15f1f6bd78b"
REQUEST_ID = "review-3fba77dccbdea44a:v0001:F2"
EXPECTED = {
    "request_source": "a264898541b5dfff6ded18cd1a96798efe9576d7c70b3141864c8e86866c47b2",
    "manifest": "96c059a87df7a26ba61fd19d323dda15a6bc8a323288e96f5bf160ad0118817f",
    "generator": "3300eb415d4a3cc51834b82a8d35017b6a08042c77af77df1b0efd1c4d5423ed",
    "gate": "dba9b919f36b93dad9998caf01c750ed53feb4d0058e3367eefcdee2cc4279b3",
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
    work = Path(__file__).resolve().parents[3]
    repo = work / "repo"
    request_source = repo / "REVIEW/suggestions.json"
    manifest_path = repo / "shared/tools/proposals/4c01248412b2ade1/manifest.json"
    generator_path = repo / "generators/77181d1aa16c/generator.py"
    gate_path = repo / "shared/tools/generator_semantic_gate.py"

    actual = {
        "request_source": sha256(request_source),
        "manifest": sha256(manifest_path),
        "generator": sha256(generator_path),
        "gate": sha256(gate_path),
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
    files = manifest.get("files") or []
    if len(files) != 1:
        raise SystemExit(f"expected one retained proposal asset, got {len(files)}")
    report_path = repo / files[0]["path"]
    report_sha = sha256(report_path)
    if report_sha != files[0]["sha256"]:
        raise SystemExit("retained report does not match proposal manifest")
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
        "full_disagreement_artifact_already_exists": all(
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
        "seed/sample_index/band": all(
            all(field in row for field in ("seed", "sample_index", "band")) for row in examples
        ),
        "authoritative_output": all("authoritative_output" in row for row in examples),
        "rival_output": all("rival_output" in row for row in examples),
        "source_binding": all("source_binding" in row for row in examples),
        "agreeing_rival_names": all("agreeing_rivals" in row for row in examples),
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
            "current_gate": {"path": str(gate_path.relative_to(work)), "sha256": actual["gate"]},
            "retained_report": {"path": str(report_path.relative_to(work)), "sha256": report_sha},
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
                "Keep the request's automatic violation-artifact requirement, but do not add "
                "a parallel relation-type API: WITNESS_RIVALS already expresses exact "
                "separation and BRANCH_WITNESSES already expresses descriptive branch coverage."
            ),
            "recommended_change": (
                "For each witness-true/rival-equal violation, retain a complete source-bound "
                "artifact with the input, canonical output, every named rival output (or at "
                "least the agreeing rival names and outputs), recipe, validation, and source "
                "hashes. Reuse the existing semantic-witness artifact schema where practical."
            ),
            "recommended_tests": [
                "a violated WITNESS_RIVALS claim retains full input/authority/rival grids",
                "the retained artifact binds generator, rule source, and callable hashes",
                "BRANCH_WITNESSES remains descriptive and produces no separation failure",
            ],
            "reason": (
                "The retained report reproduces the observability gap (26/60 violations with "
                "preview-only examples), while both proposed relation semantics are already "
                "represented by current declarations."
            ),
        },
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
