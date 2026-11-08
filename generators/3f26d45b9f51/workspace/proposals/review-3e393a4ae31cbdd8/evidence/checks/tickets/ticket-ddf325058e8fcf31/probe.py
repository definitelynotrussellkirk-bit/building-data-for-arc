#!/usr/bin/env python3
"""Bounded privacy/count probe for ticket-ddf325058e8fcf31."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

ROOT = find_root(__file__)
TASK_ID = "8291f3ee7e54"
PINNED_MANIFEST_SHA256 = "55aa8fdf7851534571920dbb3b76724c4243e61faa46eac1032459662b3f1610"
PINNED_GENERATOR_SHA256 = "5e1e28490be83e36d8e8243e23082015d5110e9ed98a3a189941476443fcb2af"
OWNER_MANIFEST = ROOT / f"generators/{TASK_ID}/workspace/parametric/evidence/manifest.json"
EVIDENCE = ROOT / (
    "generators/8291f3ee7e54/workspace/parametric/evidence/"
    "reviewer-reported/e1b6d098e7e50811/parametric/8291f3ee7e54-ring-order-v4"
)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def grid_digest(grid) -> str:
    return digest(json.dumps(grid, sort_keys=True, separators=(",", ":")).encode())


def main() -> int:
    generator = ROOT / f"generators/{TASK_ID}/generator.py"
    if digest(OWNER_MANIFEST.read_bytes()) != PINNED_MANIFEST_SHA256:
        raise ValueError("pinned evidence manifest identity mismatch")
    if digest(generator.read_bytes()) != PINNED_GENERATOR_SHA256:
        raise ValueError("pinned generator identity mismatch")

    owner = json.loads(OWNER_MANIFEST.read_text(encoding="utf-8"))
    listed = {row["path"]: row for row in owner["files"]}
    relevant_paths = [
        EVIDENCE / "manifest.json",
        EVIDENCE / "report.json",
        EVIDENCE / "verification.json",
    ]
    for path in relevant_paths:
        relative = path.relative_to(ROOT).as_posix()
        row = listed.get(relative)
        if row is None:
            raise ValueError(f"owner manifest omits {relative}")
        if path.stat().st_size != row["bytes"] or digest(path.read_bytes()) != row["sha256"]:
            raise ValueError(f"owner manifest mismatch for {relative}")

    report = json.loads((EVIDENCE / "report.json").read_text(encoding="utf-8"))
    verification = json.loads((EVIDENCE / "verification.json").read_text(encoding="utf-8"))
    if verification.get("status") != "pass":
        raise ValueError("retained verifier did not pass")
    episode_rows = report.get("episodes", [])
    if len(episode_rows) != 2:
        raise ValueError("expected exactly two retained settings")
    ids = [row["public_id"] for row in episode_rows]
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise ValueError("report public IDs are not unique and sorted")

    settings = set()
    counts = {"demonstrations": 0, "queries": 0, "distinct_inputs": 0}
    privacy_checks = 0
    for row in episode_rows:
        private_path = EVIDENCE / row["private_path"]
        public_path = EVIDENCE / row["public_path"]
        private = json.loads(private_path.read_text(encoding="utf-8"))
        public = json.loads(public_path.read_text(encoding="utf-8"))
        setting = private["parameters"]["ring_order"]
        settings.add(setting)
        if len(private["train"]) != 2 or len(private["test"]) != 4:
            raise ValueError(f"unexpected private counts for {setting}")
        if len(public["train"]) != 2 or len(public["test"]) != 4:
            raise ValueError(f"unexpected public counts for {setting}")
        if any(set(pair) != {"input", "output"} for pair in public["train"]):
            raise ValueError("public demonstration shape is not exact")
        if any(set(pair) != {"input"} for pair in public["test"]):
            raise ValueError("public query leaks a hidden field")
        inputs = [pair["input"] for pair in private["train"] + private["test"]]
        hashes = [grid_digest(grid) for grid in inputs]
        if len(hashes) != 6 or len(set(hashes)) != 6:
            raise ValueError(f"episode {setting} does not have six distinct inputs")
        raw = public_challenge_bytes(public)
        if public_path.read_bytes() != raw:
            raise ValueError("public file differs from canonical visible bytes")
        public_id = public_challenge_id(public)
        if row["public_id"] != public_id or public_path.name != f"challenge-{public_id}.json":
            raise ValueError("public content ID/filename mismatch")

        tampered = copy.deepcopy(private)
        tampered["seed"] += 999
        tampered["parameters"]["ring_order"] = "private-only-change"
        tampered["program"] = "private-only-change"
        tampered["test"][0]["output"][0][0] = (tampered["test"][0]["output"][0][0] + 1) % 10
        projected = {
            "train": tampered["train"],
            "test": [{"input": pair["input"]} for pair in tampered["test"]],
        }
        if public_challenge_bytes(projected) != raw or public_challenge_id(projected) != public_id:
            raise ValueError("hidden-only changes affected public bytes or ID")
        privacy_checks += 1
        counts["demonstrations"] += 2
        counts["queries"] += 4
        counts["distinct_inputs"] += 6

    expected_settings = {"largest_outside", "smallest_outside"}
    if settings != expected_settings:
        raise ValueError(f"retained settings mismatch: {settings}")

    result = {
        "schema": "arc-ticket-parameter-queries-v1",
        "ticket_id": "ticket-ddf325058e8fcf31",
        "type": "parameter_queries",
        "status": "completed",
        "task_id": TASK_ID,
        "pinned_manifest_sha256": PINNED_MANIFEST_SHA256,
        "pinned_generator_sha256": PINNED_GENERATOR_SHA256,
        "boundary": "two settings; 2 demonstrations and 4 distinct queries per setting; public/private projection",
        "counts": counts,
        "settings": sorted(settings),
        "privacy_checks": privacy_checks,
        "public_ids_sorted_unique": True,
        "retained_verification_status": verification["status"],
        "summary": (
            "Pinned evidence retains both fixed ring_order settings, each with 2 demos and 4 distinct queries. "
            "Public files are exact visible-byte hashes; query answers and private seed/setting/program fields do not affect IDs."
        ),
        "limits": [
            "Evidence-only boundary probe; Racket labels were not re-executed.",
            "This does not approve the variant or resolve the owner-reported physical file creation-order gap.",
        ],
    }
    out = Path(__file__).with_name("result.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
