#!/usr/bin/env python3
"""Reproduce the pinned color-role-gate request from its retained assets."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

TICKET_ID = "ticket-472e945e0edcab09"
REQUEST_ID = "review-e409b7532b6dbf2c:v0001:F1"
PROBE_SEED = "ac7e54594acc05c60a5f2920a02daf8189964fb906478b500659d66fec389bea"
EXPECTED = {
    "assets_manifest_sha256": "e99e4b360c2dc8f22a8cd662b6057b54a7a5fdd8ffb17761dd946ba2140bb6e2",
    "request_source_sha256": "a264898541b5dfff6ded18cd1a96798efe9576d7c70b3141864c8e86866c47b2",
    "request_sha256": "606fd7e0a57b390b6afdf07fa1fe9034ba4df7a8a09d1b9d62920dc8c74bc8fd",
    "generator_sha256": "132987cd4a2c9f6e2634c8edc5e54db1ff5a493c9a7b3ba6d8c3246150f4b6a0",
    "asset_sha256": "7da0633da52206aa70517465a0b73bbd27e6cfeeb2dcd9aa35cf5f9ccf617c1d",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_sha(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def nearest_corner_fill(grid: list[list[int]]) -> list[list[int]]:
    """Independent reconstruction of the retained canonical corner-fill witness."""
    height, width = len(grid), len(grid[0])
    top_rows = (height + 1) // 2
    left_cols = (width + 1) // 2
    tl, tr = grid[0][0], grid[0][-1]
    bl, br = grid[-1][0], grid[-1][-1]
    return [
        [
            (tl if col < left_cols else tr)
            if row < top_rows
            else (bl if col < left_cols else br)
            for col in range(width)
        ]
        for row in range(height)
    ]


def main() -> int:
    started = time.monotonic()
    work = Path(__file__).resolve().parents[3]
    repo = work / "repo"
    manifest_path = repo / "shared/tools/proposals/1b3197be73de9391/manifest.json"
    suggestions_path = repo / "REVIEW/suggestions.json"
    generator_path = repo / "generators/c5a69e7cd8c8/generator.py"

    suggestions = json.loads(suggestions_path.read_text(encoding="utf-8"))
    matches = [row for row in suggestions.get("items", []) if row.get("request_id") == REQUEST_ID]
    if len(matches) != 1:
        raise ValueError(f"expected one pinned request, found {len(matches)}")
    request = matches[0]

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    listed = []
    for row in manifest.get("files", []):
        path = repo / row["path"]
        listed.append(
            {
                "path": path.relative_to(work).as_posix(),
                "exists": path.is_file(),
                "expected_sha256": row["sha256"],
                "actual_sha256": digest(path) if path.is_file() else None,
                "hash_matches": path.is_file() and digest(path) == row["sha256"],
            }
        )
    if len(listed) != 1 or not listed[0]["hash_matches"]:
        raise AssertionError(f"retained asset mismatch: {listed}")

    asset_path = work / listed[0]["path"]
    asset = json.loads(asset_path.read_text(encoding="utf-8"))
    witness = asset["counterexample"]
    reconstructed = nearest_corner_fill(witness["input"])
    expected = witness["canonical_expected_output"]
    rival = witness["profile_palette_rival_output"]

    tool_sources = [
        path
        for path in (repo / "shared/tools").glob("*.py")
        if path.is_file()
    ]
    contract_hits = [
        path.relative_to(repo).as_posix()
        for path in tool_sources
        if "INTERCHANGEABLE_COLOR_ROLES" in path.read_text(encoding="utf-8", errors="replace")
    ]

    checks = {
        "assets_manifest_hash": digest(manifest_path) == EXPECTED["assets_manifest_sha256"],
        "request_source_hash": digest(suggestions_path) == EXPECTED["request_source_sha256"],
        "request_hash": canonical_json_sha(request) == EXPECTED["request_sha256"],
        "generator_hash": digest(generator_path) == EXPECTED["generator_sha256"],
        "listed_asset_hash": digest(asset_path) == EXPECTED["asset_sha256"],
        "ordinary_draw_count_consistent": asset.get("ordinary_draws_checked") == 480,
        "retained_rival_fit_count_consistent": asset.get("profile_palette_rival_fits") == 480,
        "counterexample_reconstructs_canonical_output": reconstructed == expected,
        "counterexample_refutes_profile_palette_rival": rival != expected,
        "shared_opt_in_contract_absent": not contract_hits,
        "runtime_not_selected": manifest.get("runtime_approved") is False,
    }
    if not all(checks.values()):
        raise AssertionError({name: value for name, value in checks.items() if not value})

    report = {
        "schema": "arcpuzzles-tool-reproduction-ticket-v1",
        "ticket_id": TICKET_ID,
        "probe_seed": PROBE_SEED,
        "request_id": REQUEST_ID,
        "request_status": request.get("status"),
        "request_text": request.get("text"),
        "pinned_hashes": EXPECTED,
        "observed": {
            "assets_manifest": manifest_path.relative_to(work).as_posix(),
            "request_source": suggestions_path.relative_to(work).as_posix(),
            "generator": generator_path.relative_to(work).as_posix(),
            "listed_assets": listed,
            "manifest_scope": manifest.get("scope"),
            "runtime_approved": manifest.get("runtime_approved"),
            "asset_generator_sha256": asset.get("generator_sha256"),
            "ordinary_draws_checked": asset.get("ordinary_draws_checked"),
            "profile_palette_rival_fits": asset.get("profile_palette_rival_fits"),
            "counterexample_profile": witness.get("profile"),
            "counterexample_input_shape": [len(witness["input"]), len(witness["input"][0])],
            "differing_cells": sum(
                expected[r][c] != rival[r][c]
                for r in range(len(expected))
                for c in range(len(expected[0]))
            ),
            "shared_contract_hits": contract_hits,
        },
        "checks": checks,
        "reproduced_state": "hash_bound_static_witness_reproduced",
        "limits": [
            "The retained packet contains the aggregate 480/480 receipt and one counterexample, not the historical generator source or all 480 grids; the census itself was not rerun.",
            "The counterexample output was independently reconstructed from its corner-fill semantics, but no historical Racket program for audit target 89704f9047c0 is retained in this packet.",
        ],
        "proposed_disposition": {
            "status": "accept_scoped_followup",
            "action": "retain as an opt-in shared-tool design request, not a selected implementation",
            "reason": (
                "All pinned hashes match, the retained 480/480 confounding receipt is internally consistent, "
                "and the legal corner-fill witness independently refutes the profile/palette rival. The proposed "
                "INTERCHANGEABLE_COLOR_ROLES contract is absent from current shared tool sources. Before "
                "implementation, require an executable source-bound fixture for the census plus false-positive "
                "tests for fixed-symbol tasks and declared schedule/profile conditioning."
            ),
        },
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    out = Path(__file__).with_name("probe.json")
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "reproduced_state": report["reproduced_state"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
