#!/usr/bin/env python3
"""Reproduce the pinned identity/evidence chain for one retained tool request.

This is intentionally source-bound.  It authenticates the retained request and
asset that are present in the review packet; it does not promote the proposal
or infer that the original 3,941-generator sample can be replayed from a
300-generator packet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TICKET_ID = "ticket-01c915d5ead476c8"
REQUEST_ID = "review-597e2d03726aa4c9:v0001:F3"
TASK_ID = "cfadc43e5098"
EXPECTED = {
    "assets_manifest_sha256": "08d0feff979ab58355bfe522a23e5645b47dc4a490884dbbee84cb13755818d1",
    "generator_sha256": "e3465bcdcdcad8ad2bb616bc4301d69eb24a36b4bffbc7bce3dc771e5816cf04",
    "request_sha256": "5470d828159a27813c8cb5db8891507ecb8ef9c90ab35269a466c719aaa34f74",
    "request_source_sha256": "67fdad2e6b3cdd0fa6d8aeeff83afa2790f0fa67260178aab768276cae85e633",
    "asset_sha256": "679a6f2390bd3a83d4d2b26302da52c3284f8d6946fe4aef43a0cc07391b17b4",
}
EXPECTED_AUDIT_SEED = "570b9801db5d9db653dd3c41fb4aac3f14784d4a50e621133e388584f2bfe19b"
EXPECTED_SAMPLE = ["fcabbbbdfc11", "2786bc764238", "bf47583ab6e3"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compact_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_request(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: list[Any] = []
    if isinstance(payload, list):
        rows.extend(payload)
    elif isinstance(payload, dict):
        for value in payload.values():
            if isinstance(value, list):
                rows.extend(value)
            elif isinstance(value, dict):
                rows.append(value)
    matches = [row for row in rows if isinstance(row, dict) and row.get("request_id") == REQUEST_ID]
    if len(matches) != 1:
        raise RuntimeError(f"expected one {REQUEST_ID!r} row, found {len(matches)}")
    return matches[0]


def checked(name: str, expected: Any, actual: Any) -> dict[str, Any]:
    return {"name": name, "expected": expected, "actual": actual, "passed": actual == expected}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    work = Path(__file__).resolve().parents[3]
    manifest_path = work / "repo/shared/tools/proposals/4ad2bbcf06b661b3/manifest.json"
    request_source_path = work / "repo/REVIEW/suggestions.json"
    generator_path = work / f"repo/generators/{TASK_ID}/generator.py"
    packet_path = work / "PACKET-MANIFEST.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    request = load_request(request_source_path)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    if len(manifest.get("files", [])) != 1:
        raise RuntimeError("this bounded reproduction expects exactly one retained asset")
    asset_entry = manifest["files"][0]
    asset_path = work / "repo" / asset_entry["path"]
    audit = json.loads(asset_path.read_text(encoding="utf-8"))

    checks = [
        checked("manifest file sha256", EXPECTED["assets_manifest_sha256"], sha256_file(manifest_path)),
        checked("request source file sha256", EXPECTED["request_source_sha256"], sha256_file(request_source_path)),
        checked("canonical compact request row sha256", EXPECTED["request_sha256"], compact_sha256(request)),
        checked("current task generator sha256", EXPECTED["generator_sha256"], sha256_file(generator_path)),
        checked("manifest request id", REQUEST_ID, manifest.get("request_id")),
        checked("manifest generator id", TASK_ID, manifest.get("generator_id")),
        checked("manifest schema", "arcpuzzles-tool-proposal-assets-v1", manifest.get("schema")),
        checked("manifest runtime approval", False, manifest.get("runtime_approved")),
        checked("manifest asset sha256", EXPECTED["asset_sha256"], asset_entry.get("sha256")),
        checked("retained asset file sha256", EXPECTED["asset_sha256"], sha256_file(asset_path)),
        checked("audit schema", "arcpuzzles-randomized-allocation-audit-v1", audit.get("schema")),
        checked("audit seed", EXPECTED_AUDIT_SEED, audit.get("seed")),
        checked("audit population", 3941, audit.get("population_count")),
        checked("audit sampled ids", EXPECTED_SAMPLE, audit.get("sampled_ids")),
        checked(
            "audit sampling method",
            "random.Random(int(seed, 16)).sample(sorted(generator_ids), 3)",
            audit.get("sampling"),
        ),
    ]

    packet_generator_ids = set(packet.get("generators", {}))
    present = [task_id for task_id in EXPECTED_SAMPLE if task_id in packet_generator_ids]
    absent = [task_id for task_id in EXPECTED_SAMPLE if task_id not in packet_generator_ids]
    owner_population = packet.get("selection", {}).get("owner_generator_count")
    identity_verified = all(item["passed"] for item in checks)
    full_population_replay = len(packet_generator_ids) == audit.get("population_count")

    result = {
        "schema": "arcpuzzles-ticket-tool-reproduction-v1",
        "ticket_id": TICKET_ID,
        "request_id": REQUEST_ID,
        "task_id": TASK_ID,
        "status": "completed" if identity_verified else "blocked",
        "identity_verified": identity_verified,
        "checks": checks,
        "retained_asset": {
            "path": str(asset_path.relative_to(work)),
            "bytes": asset_path.stat().st_size,
            "schema": audit.get("schema"),
            "sampled_ids": audit.get("sampled_ids"),
            "coverage_limits": audit.get("coverage_limits", []),
        },
        "replay_scope": {
            "packet_generator_count": len(packet_generator_ids),
            "owner_population_count_reported_by_packet": owner_population,
            "retained_audit_population_count": audit.get("population_count"),
            "sampled_ids_present_in_packet": present,
            "sampled_ids_absent_from_packet": absent,
            "full_population_sample_replay_possible": full_population_replay,
            "reason": (
                "The exact request, manifest, current source, and retained asset are reproducible, "
                "but the packet contains only 300 of the reported 3,941 owner generators, so the "
                "original population sample cannot be independently recomputed here."
            ),
        },
        "proposed_disposition": {
            "decision": "retain_authenticated_source_bound_proposal_only",
            "runtime_approved": False,
            "shared_change": "none",
            "rationale": (
                "The pinned identity/evidence chain is intact and internally coherent.  The asset is "
                "evidence for a proposal, not proof that its allocation policy is optimal or safe to "
                "install.  Keep it available to the stated consumer and require a fresh bounded A/B "
                "test before any shared allocation change."
            ),
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ticket_id": TICKET_ID,
        "status": result["status"],
        "checks_passed": sum(item["passed"] for item in checks),
        "checks_total": len(checks),
        "full_population_replay_possible": full_population_replay,
        "output": str(args.out),
    }, sort_keys=True))
    return 0 if identity_verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
