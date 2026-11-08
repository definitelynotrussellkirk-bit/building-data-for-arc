#!/usr/bin/env python3
"""One bounded setting/count/privacy probe for ticket-89015c8f7684dd55."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "78ab57735469"
TICKET_ID = "ticket-89015c8f7684dd55"
PINNED_SOURCE_SHA256 = "7e22ad5afd49ca58f2c02cef3e531b55970da1444302467c8f07da99fa485342"
PINNED_MANIFEST_SHA256 = "2e3f43ba47b090694ca5cdf49cef4553d4c19b28e029c6141077b531f0dd8885"
MANIFEST_REL = Path("generators/78ab57735469/workspace/parametric/evidence/manifest.json")
OUTPUT = Path(__file__).with_name("boundary-result.json")
FORBIDDEN_PUBLIC_KEYS = {
    "answer",
    "answers",
    "meta",
    "parameters",
    "program",
    "seed",
    "setting",
    "output_sha256",
    "output_sha256_by_setting",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_projection(episode: dict) -> dict:
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def recursive_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from recursive_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from recursive_keys(child)


def main() -> int:
    root = find_root(__file__)
    manifest_path = root / MANIFEST_REL
    manifest_sha = sha256(manifest_path)
    if manifest_sha != PINNED_MANIFEST_SHA256:
        raise RuntimeError(f"manifest drift: {manifest_sha} != {PINNED_MANIFEST_SHA256}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["task_id"] != TASK_ID:
        raise RuntimeError("manifest task mismatch")
    if manifest["generator_sha256"] != PINNED_SOURCE_SHA256:
        raise RuntimeError("manifest source mismatch")

    records = {entry["path"]: entry for entry in manifest["files"]}
    for rel, entry in records.items():
        path = root / rel
        if not path.is_file():
            raise RuntimeError(f"manifest file missing: {rel}")
        actual = sha256(path)
        if actual != entry["sha256"]:
            raise RuntimeError(f"manifest file drift: {rel}: {actual} != {entry['sha256']}")
        if path.stat().st_size != entry["bytes"]:
            raise RuntimeError(f"manifest byte-size drift: {rel}")

    public_entries = sorted(rel for rel in records if "/public/challenge-" in rel)
    private_entries = sorted(rel for rel in records if "/private/episodes/" in rel)
    if len(public_entries) != 4 or len(private_entries) != 4:
        raise RuntimeError("expected exactly four public and four private episodes")

    public_by_id = {}
    public_checks = []
    for rel in public_entries:
        path = root / rel
        challenge = json.loads(path.read_text(encoding="utf-8"))
        challenge_id = path.stem.removeprefix("challenge-")
        canonical_bytes = public_challenge_bytes(challenge)
        computed_id = public_challenge_id(challenge)
        if computed_id != challenge_id:
            raise RuntimeError(f"visible-content ID mismatch: {rel}")
        if canonical_bytes != path.read_bytes():
            raise RuntimeError(f"public file is not canonical visible-content bytes: {rel}")
        if set(challenge) != {"train", "test"}:
            raise RuntimeError(f"unexpected public top-level keys: {rel}")
        if len(challenge["test"]) != 4:
            raise RuntimeError(f"public challenge does not contain four queries: {rel}")
        if any(set(pair) != {"input"} for pair in challenge["test"]):
            raise RuntimeError(f"public query leaks fields beyond input: {rel}")
        leaked = sorted(set(recursive_keys(challenge)) & FORBIDDEN_PUBLIC_KEYS)
        if leaked:
            raise RuntimeError(f"public challenge leaks private keys {leaked}: {rel}")
        query_hashes = [
            hashlib.sha256(
                json.dumps(pair["input"], separators=(",", ":")).encode()
            ).hexdigest()
            for pair in challenge["test"]
        ]
        if len(set(query_hashes)) != 4:
            raise RuntimeError(f"public challenge queries are not distinct: {rel}")
        public_by_id[challenge_id] = challenge
        public_checks.append(
            {
                "path": rel,
                "public_id": challenge_id,
                "train_count": len(challenge["train"]),
                "query_count": len(challenge["test"]),
                "distinct_query_count": len(set(query_hashes)),
                "forbidden_keys_found": leaked,
            }
        )

    private_checks = []
    matched_ids = set()
    settings = set()
    for rel in private_entries:
        episode = json.loads((root / rel).read_text(encoding="utf-8"))
        if len(episode["test"]) != 4 or episode["meta"]["n_test"] != 4:
            raise RuntimeError(f"private query count mismatch: {rel}")
        parameters = episode["parameters"]
        setting = (
            parameters["row_flip_phase"],
            parameters["column_flip_phase"],
        )
        settings.add(setting)
        for pair in episode["train"] + episode["test"]:
            pair_setting = tuple(pair["meta"]["setting"])
            if pair_setting != setting:
                raise RuntimeError(f"setting changed inside episode: {rel}")
        projection = public_projection(episode)
        challenge_id = public_challenge_id(projection)
        if challenge_id not in public_by_id:
            raise RuntimeError(f"private episode has no public projection: {rel}")
        if projection != public_by_id[challenge_id]:
            raise RuntimeError(f"public/private projection mismatch: {rel}")
        matched_ids.add(challenge_id)
        private_checks.append(
            {
                "path": rel,
                "setting": {
                    "row_flip_phase": setting[0],
                    "column_flip_phase": setting[1],
                },
                "selection_scope": episode["meta"]["selection_scope"],
                "query_count": len(episode["test"]),
                "public_id": challenge_id,
            }
        )
    if matched_ids != set(public_by_id):
        raise RuntimeError("public/private episode set mismatch")
    expected_settings = {
        ("even", "even"),
        ("even", "odd"),
        ("odd", "even"),
        ("odd", "odd"),
    }
    if settings != expected_settings:
        raise RuntimeError(f"setting coverage mismatch: {settings}")

    result = {
        "schema": "arcpuzzles-ticket-parameter-queries-v1",
        "ticket_id": TICKET_ID,
        "status": "completed",
        "task_id": TASK_ID,
        "manifest_path": str(MANIFEST_REL),
        "manifest_sha256": manifest_sha,
        "generator_sha256": manifest["generator_sha256"],
        "canonical_rule_hash": manifest["canonical_rule_hash"],
        "boundary": (
            "For every retained setting, the hidden setting is fixed for the "
            "whole episode, exactly four distinct queries are emitted, the "
            "public challenge is the exact answer-free projection, and its ID "
            "is derived from canonical visible bytes only."
        ),
        "public_checks": public_checks,
        "private_checks": private_checks,
        "variant_approval": False,
        "approval_note": (
            "This is bounded support for the retained prototype evidence, not "
            "approval of a production variant or training admission."
        ),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "completed",
                "settings": len(settings),
                "public_challenges": len(public_entries),
                "queries_per_challenge": 4,
                "result": str(OUTPUT),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
