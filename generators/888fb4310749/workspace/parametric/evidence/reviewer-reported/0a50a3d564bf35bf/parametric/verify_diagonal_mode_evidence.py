#!/usr/bin/env python3
"""Verify retained diagonal-mode evidence without trusting its report hashes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_public_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify(
    root: Path,
    demo_count: int,
    query_count: int,
    repo: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    report = json.loads((root / "report.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))

    require(report.get("status") == "prototype", "report status is not prototype")
    require(report.get("default_program_exact_canonical") is True,
            "default program is not exact canonical text")
    require(report.get("all_labels_and_rivals_executed_in_racket") is True,
            "report does not bind labels/rivals to Racket")
    require(report.get("all_episode_demonstrations_distinguish_rivals") is True,
            "demonstrations do not distinguish every rival")
    require(report.get("all_episode_queries_checked_against_rivals") is True,
            "not every query was checked against every rival")
    require(report.get("canonical_labels_checked") == 4,
            "expected four canonical labels")
    require(report.get("canonical_labels_passed") == 4,
            "canonical replay did not pass 4/4")
    require(report.get("complete_episodes") == 3,
            "expected one complete episode per mode")
    policy = report.get("input_policy", {})
    require(policy.get("demo_count") == demo_count, "demo count differs")
    require(policy.get("query_count") == query_count, "query count differs")

    manifest_rows = manifest.get("files")
    require(isinstance(manifest_rows, list), "manifest files must be a list")
    declared = {row["path"]: row for row in manifest_rows}
    actual = {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    require(set(declared) == set(actual), "manifest inventory differs from disk")
    for relative, path in actual.items():
        raw = path.read_bytes()
        row = declared[relative]
        require(row.get("bytes") == len(raw), f"size mismatch: {relative}")
        require(row.get("sha256") == sha256(raw), f"hash mismatch: {relative}")

    source_files_checked = 0
    if repo is not None:
        repo = repo.resolve()
        for relative, expected in report.get("source_hashes", {}).items():
            if relative == "canonical_program":
                continue
            relative_path = Path(relative)
            require(not relative_path.is_absolute() and ".." not in relative_path.parts,
                    f"unsafe source path in report: {relative}")
            source = repo / relative_path
            require(source.is_file(), f"reported source is missing: {relative}")
            require(sha256(source.read_bytes()) == expected,
                    f"reported source hash differs: {relative}")
            source_files_checked += 1

    episodes = report.get("episodes")
    require(isinstance(episodes, list) and len(episodes) == 3,
            "report must contain three episode rows")
    public_ids = [row.get("public_id") for row in episodes]
    require(all(isinstance(value, str) and len(value) == 64 for value in public_ids),
            "invalid public ID")
    require(public_ids == sorted(public_ids), "public IDs are not sorted")
    require(len(set(public_ids)) == len(public_ids), "duplicate public IDs")

    for row in episodes:
        public_id = row["public_id"]
        expected_path = f"public/{public_id}.json"
        require(row.get("public_path") == expected_path,
                f"public path is not content-addressed: {public_id}")
        path = root / expected_path
        raw = path.read_bytes()
        require(sha256(raw) == public_id,
                f"filename does not hash exact bytes: {expected_path}")
        value = json.loads(raw)
        require(raw == canonical_public_bytes(value),
                f"public bytes are not canonical exact bytes: {expected_path}")
        require(set(value) == {"train", "test"}, "public top-level field leak")
        require(len(value["train"]) == demo_count, "public demo count differs")
        require(len(value["test"]) == query_count, "public query count differs")
        require(all(set(pair) == {"input", "output"} for pair in value["train"]),
                "demonstration shape differs")
        require(all(set(pair) == {"input"} for pair in value["test"]),
                "query output or private field leaked")
        for rival_name, rival in row.get("rivals", {}).items():
            require(bool(rival.get("refuting_demonstration_indices")),
                    f"{public_id}: {rival_name} lacks a refuting demo")
            require(rival.get("query_differing_indices") == list(range(query_count)),
                    f"{public_id}: {rival_name} does not differ on every query")
            require(rival.get("all_queries_differ") is True,
                    f"{public_id}: {rival_name} query summary differs")

    return {
        "status": "verified",
        "canonical_labels": "4/4",
        "episodes": len(episodes),
        "demo_count": demo_count,
        "query_count": query_count,
        "public_ids": public_ids,
        "manifest_files": len(declared),
        "source_files_checked": source_files_checked,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--demo-count", type=int, default=3)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument("--repo", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(
        args.evidence, args.demo_count, args.query_count, repo=args.repo
    ), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
