#!/usr/bin/env python3
"""Replay the retained unknown-override witness for ticket-e8b8b7cb6155e9e8."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root

ROOT = find_root(__file__)
TASK_ID = "2e9bbcd910a7"
PINNED_GENERATOR_SHA256 = "9301977697af1a47c63f609e71c4485d90002a7d15c32eb6f2470fc03ac1d8d6"
PINNED_ASSETS_SHA256 = "641123977f1bbb6e41aefd4799cefdf90ab2e1f9c24fda06526657cf5cd0afbe"
PINNED_INDEX_SHA256 = "7a74fac80585a935bbb41dc4e4f546cf3781c792b9ba5fe7a77bfd9799fbaf7e"
PINNED_AUDIT_RECORD_SHA256 = "b2fb2e04a5630f91b510ed92c7b4a850e6a74a146f70db07ae872adbc2735a99"
SOURCE = ROOT / f"generators/{TASK_ID}/generator.py"
ASSETS = ROOT / (
    "generators/2e9bbcd910a7/counterexamples/"
    "review-b4138a0a6f4e419e-v0001/audit_assets.json"
)
INDEX = ROOT / f"generators/{TASK_ID}/evidence/review_index.json"
RETAINED = ASSETS.parent / "retained/checks/audit/2e9bbcd910a7/unknown_override.json"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    identities = {
        "generator": digest(SOURCE.read_bytes()),
        "assets_manifest": digest(ASSETS.read_bytes()),
        "audit_index": digest(INDEX.read_bytes()),
    }
    expected = {
        "generator": PINNED_GENERATOR_SHA256,
        "assets_manifest": PINNED_ASSETS_SHA256,
        "audit_index": PINNED_INDEX_SHA256,
    }
    if identities != expected:
        raise ValueError(f"pinned identity mismatch: {identities!r}")

    assets = json.loads(ASSETS.read_text(encoding="utf-8"))
    retained_relative = RETAINED.relative_to(ROOT).as_posix()
    asset_row = next((row for row in assets["files"] if row["path"] == retained_relative), None)
    if asset_row is None:
        raise ValueError("assets manifest omits retained unknown-override witness")
    if RETAINED.stat().st_size != asset_row["bytes"] or digest(RETAINED.read_bytes()) != asset_row["sha256"]:
        raise ValueError("retained witness identity mismatch")
    retained = json.loads(RETAINED.read_text(encoding="utf-8"))

    index = json.loads(INDEX.read_text(encoding="utf-8"))
    audit = next(
        row for row in index.get("audits", [])
        if row.get("return_id") == "review-b4138a0a6f4e419e:v0001"
    )
    if audit.get("source_sha256") != PINNED_GENERATOR_SHA256:
        raise ValueError("audit index is not bound to the pinned source")
    if "unknown override is silently accepted" not in audit.get("text", ""):
        raise ValueError("audit index no longer contains the pinned claim")

    spec = importlib.util.spec_from_file_location("ticket_replay_2e9bbcd910a7", SOURCE)
    if spec is None or spec.loader is None:
        raise ImportError(SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    seed = 19
    sample_index = 23
    difficulty = "medium"
    unknown_override = {"typo_scene_family": "tie_se"}
    base = module.generate(seed, sample_index, difficulty=difficulty)
    accepted = True
    try:
        unknown = module.generate(
            seed,
            sample_index,
            difficulty=difficulty,
            **unknown_override,
        )
    except Exception as exc:
        accepted = False
        unknown = None
        rejection = {"type": type(exc).__name__, "message": str(exc)}
    else:
        rejection = None

    same_as_unoverridden = accepted and unknown == base
    self_check_errors = module.self_check(unknown) if accepted else None
    grid_sha256 = (
        digest(json.dumps(unknown, separators=(",", ":")).encode())
        if accepted else None
    )
    reproduced = (
        accepted
        and same_as_unoverridden
        and self_check_errors == []
        and grid_sha256 == retained["grid_sha256"]
        and retained["accepted"] is True
        and retained["same_as_unoverridden"] is True
    )

    result = {
        "schema": "arc-ticket-audit-replay-v1",
        "ticket_id": "ticket-e8b8b7cb6155e9e8",
        "type": "audit_replay",
        "status": "finding" if reproduced else "completed",
        "task_id": TASK_ID,
        "audit_return_id": "review-b4138a0a6f4e419e:v0001",
        "pinned_audit_record_sha256": PINNED_AUDIT_RECORD_SHA256,
        "identities": identities,
        "probe": {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "unknown_override": unknown_override,
            "accepted": accepted,
            "rejection": rejection,
            "same_as_unoverridden": same_as_unoverridden,
            "self_check_errors": self_check_errors,
            "grid_sha256": grid_sha256,
            "retained_grid_sha256": retained["grid_sha256"],
        },
        "reproduced": reproduced,
        "summary": (
            "Reproduced the pinned contract defect: typo_scene_family='tie_se' is accepted and returns the exact same valid grid as the unoverridden seed 19/sample 23 draw."
            if reproduced else
            "The pinned unknown-override witness did not reproduce exactly on the pinned source."
        ),
        "limits": [
            "Single retained witness only; no peer battery or search for additional override keys.",
            "Reproduction does not clear or broaden the existing audit assessment.",
        ],
    }
    out = Path(__file__).with_name("result.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if reproduced else 1


if __name__ == "__main__":
    raise SystemExit(main())
