#!/usr/bin/env python3
"""Reproduce and disposition the pinned lesson-admission tool request."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arcpuzzles.worker import lesson_check
from reviewer_support import find_root, load_selected_generator

TICKET_ID = "ticket-9d4aed9ddc0dc2a0"
REQUEST_ID = "review-2dfa006e85cfd4d0:v0001:F1"
REQUEST_SHA256 = "43db23063d06182514629e61a77d57b823811eaefa83601471d335d5cf22c158"
REQUEST_SOURCE_SHA256 = "67fdad2e6b3cdd0fa6d8aeeff83afa2790f0fa67260178aab768276cae85e633"
MANIFEST_SHA256 = "dd8211bfbf9ce60ab39ecc4a1f9c24b547429e4135e48210a6572bf8a95f3a56"
CURRENT_GENERATOR_SHA256 = "2f1d4a9496deb459cdf33397713daefd85e02ed53b5e1a979ee9439c3843f4dc"
TASK_ID = "31b8bedd699a"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_sha(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def main() -> int:
    root = find_root(__file__)
    suggestions_path = root / "REVIEW" / "suggestions.json"
    suggestions_bytes = suggestions_path.read_bytes()
    if sha256(suggestions_bytes) != REQUEST_SOURCE_SHA256:
        raise RuntimeError("suggestions source hash drift")
    suggestions = json.loads(suggestions_bytes)
    request = next(
        row for row in suggestions["items"] if row.get("request_id") == REQUEST_ID
    )
    if canonical_json_sha(request) != REQUEST_SHA256:
        raise RuntimeError("request row hash drift")

    manifest_path = root / request["assets_manifest"]["path"]
    manifest_bytes = manifest_path.read_bytes()
    if sha256(manifest_bytes) != MANIFEST_SHA256:
        raise RuntimeError("assets manifest hash drift")
    manifest = json.loads(manifest_bytes)
    if len(manifest["files"]) != 1:
        raise RuntimeError("expected one retained reproduction asset")
    asset_row = manifest["files"][0]
    asset_path = root / asset_row["path"]
    asset_bytes = asset_path.read_bytes()
    if sha256(asset_bytes) != asset_row["sha256"]:
        raise RuntimeError("retained asset hash drift")
    asset = json.loads(asset_bytes)

    query_position = asset["query_position"]
    pairs = asset["pairs"]
    demo_positions = asset["demonstration_positions"]
    demos_fit_retained_rival = all(
        pairs[index]["output"] == pairs[index]["rival_output"]
        for index in demo_positions
    )
    query_differs_from_retained_rival = (
        pairs[query_position]["output"]
        != pairs[query_position]["rival_output"]
    )
    if not demos_fit_retained_rival or not query_differs_from_retained_rival:
        raise RuntimeError("retained asset no longer reproduces the claimed ambiguity")

    generator, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    if source_sha != CURRENT_GENERATOR_SHA256:
        raise RuntimeError(f"current generator hash drift: {source_sha}")
    episode = {
        "train": [pairs[index] for index in demo_positions],
        "test": [pairs[query_position]],
    }
    diagnostic = lesson_check(
        generator,
        episode,
        {"demonstration_policy": {"automatic": False, "declared_minimum": 5}},
    )
    auto_blocked = False
    auto_error = None
    try:
        lesson_check(
            generator,
            episode,
            {"demonstration_policy": {"automatic": True, "declared_minimum": 5}},
        )
    except ValueError as exc:
        auto_blocked = True
        auto_error = str(exc)

    result = {
        "schema": "arc-supplementary-tool-reproduction-v1",
        "ticket_id": TICKET_ID,
        "request_id": REQUEST_ID,
        "request_sha256": REQUEST_SHA256,
        "request_source": {
            "path": suggestions_path.relative_to(root).as_posix(),
            "sha256": REQUEST_SOURCE_SHA256,
        },
        "assets_manifest": {
            "path": manifest_path.relative_to(root).as_posix(),
            "sha256": MANIFEST_SHA256,
        },
        "asset": {
            "path": asset_path.relative_to(root).as_posix(),
            "sha256": asset_row["sha256"],
            "historical_source_sha256": asset["source_sha256"],
            "demo_count": len(demo_positions),
            "query_position": query_position,
            "demos_fit_include_solids_rival": demos_fit_retained_rival,
            "query_differs_from_include_solids_rival": query_differs_from_retained_rival,
        },
        "current_source": {
            "path": source_path.relative_to(root).as_posix(),
            "sha256": source_sha,
        },
        "current_worker_replay": {
            "diagnostic_status": diagnostic["status"],
            "include_solids_rival_status": diagnostic["rivals"].get(
                "LESSON_COMPETITORS:include_solids_in_axis"
            ),
            "query_reasons": diagnostic["queries"],
            "automatic_policy_blocked": auto_blocked,
            "automatic_error": auto_error,
        },
        "proposed_disposition": {
            "status": "partially_satisfied_split_followup",
            "summary": (
                "The retained historical lesson reproduces the claimed five-demo "
                "ambiguity. The current shared worker now checks declared hooks and "
                "rivals on the exact materialized episode and blocks this asset when "
                "the demonstration policy is automatic, so the core per-episode "
                "admission request is implemented. Keep only a narrower follow-up "
                "for all-start finite-schedule preflight and an explicit policy for "
                "caller-forced demonstration counts; do not build a second census."
            ),
            "remaining_gap": (
                "Ordinary export checks episodes it materializes; it does not itself "
                "enumerate every start residue of a declared finite schedule before "
                "admission, and explicit n_train requests make lesson findings "
                "diagnostic rather than automatically blocking."
            ),
        },
    }
    out = Path(__file__).with_name("result.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": "completed",
        "asset_reproduced": True,
        "worker_detected": diagnostic["status"] == "diagnostic_unsupported",
        "automatic_policy_blocked": auto_blocked,
        "disposition": result["proposed_disposition"]["status"],
        "result": str(out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
