#!/usr/bin/env python3
"""Bounded source-bound check for the assigned parameter_queries ticket."""
from __future__ import annotations

import collections
import hashlib
import json
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402

TICKET_ID = "ticket-0d477279b26ed8f2"
PINNED_GENERATOR_SHA = "33d8f354812b25e8e5afe7555c6296040b7d63e0b6315dea5a184c5515227b3f"
PINNED_INDEX_SHA = "10c09b18c9283679bcb5b805f87f3d2d186494a89aa8a5c149f47ba7c0def717"
GENERATOR = REPO / "generators/bee63e6e52bd/generator.py"
INDEX = REPO / "generators/bee63e6e52bd/workspace/parametric/evidence/manifest.json"
OUT = Path(__file__).with_name("report.json")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    generator_sha = sha256(GENERATOR)
    index_sha = sha256(INDEX)
    if generator_sha != PINNED_GENERATOR_SHA:
        raise SystemExit(f"generator identity mismatch: {generator_sha}")
    if index_sha != PINNED_INDEX_SHA:
        raise SystemExit(f"evidence index identity mismatch: {index_sha}")

    index = json.loads(INDEX.read_text(encoding="utf-8"))
    export = REPO / index["current_owner_export"]
    manifest_path = export / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    episodes_path = export / "private/episodes.jsonl"
    episodes = [json.loads(line) for line in episodes_path.read_text(encoding="utf-8").splitlines() if line]

    rows = []
    setting_counts: collections.Counter[str] = collections.Counter()
    privacy_ok = True
    exact_visible_byte_ids_ok = True
    for episode in episodes:
        setting = str(episode["parameters"]["spout_reach"])
        setting_counts[setting] += 1
        relative_public = episode["public_file"]
        public_path = export / relative_public
        raw = public_path.read_bytes()
        visible = json.loads(raw)
        expected_visible = {
            "train": episode["train"],
            "test": [{"input": pair["input"]} for pair in episode["test"]],
        }
        row_privacy_ok = (
            visible == expected_visible
            and set(visible) == {"train", "test"}
            and all(set(pair) == {"input", "output"} for pair in visible["train"])
            and all(set(pair) == {"input"} for pair in visible["test"])
        )
        filename_id = public_path.stem.removeprefix("challenge-")
        exact_id = public_challenge_id(episode)
        exact_bytes = public_challenge_bytes(episode)
        file_sha = hashlib.sha256(raw).hexdigest()
        legacy_compact_id = hashlib.sha256(
            json.dumps(visible, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        row_exact_ok = raw == exact_bytes and filename_id == exact_id == file_sha
        privacy_ok &= row_privacy_ok
        exact_visible_byte_ids_ok &= row_exact_ok
        rows.append({
            "seed": episode["seed"],
            "spout_reach": episode["parameters"]["spout_reach"],
            "train_count": len(episode["train"]),
            "query_count": len(episode["test"]),
            "public_path": relative_public,
            "public_projection_only": row_privacy_ok,
            "filename_id": filename_id,
            "file_sha256": file_sha,
            "reviewer_support_public_id": exact_id,
            "bytes_equal_reviewer_support_public_bytes": raw == exact_bytes,
            "filename_matches_reviewer_support_public_id": filename_id == exact_id,
            "filename_matches_legacy_compact_without_newline": filename_id == legacy_compact_id,
        })

    train_counts = sorted({row["train_count"] for row in rows})
    query_counts = sorted({row["query_count"] for row in rows})
    report = {
        "schema": "parameter-queries-ticket-probe-v1",
        "ticket_id": TICKET_ID,
        "status": "completed",
        "source_binding": {
            "generator_path": GENERATOR.relative_to(WORK).as_posix(),
            "generator_sha256": generator_sha,
            "evidence_index_path": INDEX.relative_to(WORK).as_posix(),
            "evidence_index_sha256": index_sha,
            "owner_export": export.relative_to(WORK).as_posix(),
            "owner_manifest_sha256": sha256(manifest_path),
        },
        "scope": manifest.get("scope"),
        "manifest_status": manifest.get("status"),
        "episode_count": len(rows),
        "setting_counts": dict(sorted(setting_counts.items())),
        "train_counts": train_counts,
        "query_counts": query_counts,
        "four_query_support_retained": all(count >= 4 for count in query_counts),
        "public_projection_privacy_ok": privacy_ok,
        "exact_visible_byte_ids_ok": exact_visible_byte_ids_ok,
        "assessment": (
            "The retained owner export keeps private settings, seeds, programs, and query answers out of public JSON, "
            "but it contains one query per episode rather than four. Its challenge filenames hash a legacy compact "
            "serialization without the reviewer_support newline, while the files themselves are pretty-printed; "
            "therefore filenames are not hashes of the exact visible bytes written. This is bounded prototype-support "
            "evidence only and does not approve the parameter variant."
        ),
        "episodes": rows,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "episode_count", "setting_counts", "train_counts", "query_counts",
        "four_query_support_retained", "public_projection_privacy_ok", "exact_visible_byte_ids_ok")
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
