#!/usr/bin/env python3
"""Offline verifier for retained deflection-distance prototype evidence.

The verifier intentionally does not execute the generator or Racket.  It checks
that the retained evidence is self-consistent, source-bound, privacy-safe, and
cryptographically intact.  Use the focused tests/evidence build to regenerate
labels; use this script to validate a transported return without trusting its
manifest blindly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


TASK_ID = "8eb9146172f8"
EXPECTED_SETTINGS = (1, 2)
FORBIDDEN_PUBLIC_TOKENS = (
    "deflection_distance",
    '"seed"',
    '"program"',
    '"rivals"',
    '"output_sha256"',
)


class VerificationError(RuntimeError):
    """Raised when retained evidence violates its public/private contract."""


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"cannot read JSON {path}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def verify(evidence_dir: Path, repo_root: Path) -> dict[str, Any]:
    evidence_dir = evidence_dir.resolve()
    repo_root = repo_root.resolve()
    manifest_path = evidence_dir / "manifest.json"
    manifest_raw = manifest_path.read_bytes()
    manifest = load_json(manifest_path)

    require(manifest.get("schema") == "arc-ray-deflection-distance-evidence-v1",
            "unexpected evidence schema")
    require(manifest.get("task_id") == TASK_ID, "manifest task ID mismatch")
    require(manifest.get("status") == "proposed", "manifest status must remain proposed")

    tracked_file_checks: list[dict[str, Any]] = []
    files = manifest.get("files")
    require(isinstance(files, dict) and files, "manifest files map is missing")
    for relative, expected in sorted(files.items()):
        require(isinstance(relative, str) and isinstance(expected, str),
                "manifest files entries must be string hashes")
        path = evidence_dir / relative
        require(path.is_file(), f"retained evidence member is missing: {relative}")
        actual = sha256(path.read_bytes())
        tracked_file_checks.append({
            "path": relative,
            "expected_sha256": expected,
            "actual_sha256": actual,
            "matches": actual == expected,
        })
        require(actual == expected, f"retained evidence hash mismatch: {relative}")

    for relative, expected in sorted(manifest.get("source_sha256", {}).items()):
        path = repo_root / relative
        require(path.is_file(), f"tracked source is missing: {relative}")
        actual = sha256(path.read_bytes())
        require(actual == expected, f"tracked source hash mismatch: {relative}")

    parity_path = evidence_dir / "private/canonical-parity.json"
    parity = load_json(parity_path)
    require(isinstance(parity, list) and parity, "canonical parity rows are missing")
    require(all(row.get("matches") is True for row in parity),
            "at least one canonical parity row does not match")

    witness_path = evidence_dir / manifest["same_input_witness"]["path"]
    witness = load_json(witness_path)
    require(witness.get("settings_disagree") is True,
            "same-input witness does not distinguish the settings")
    require(witness.get("differing_cells") == manifest["same_input_witness"]["differing_cells"],
            "same-input witness count differs from manifest")
    require(witness.get("differing_cells", 0) > 0,
            "same-input witness has no differing cells")

    rows = manifest.get("episodes")
    require(isinstance(rows, list) and len(rows) == len(EXPECTED_SETTINGS),
            "expected one retained episode per declared setting")
    public_ids = [row.get("public_id") for row in rows]
    require(public_ids == sorted(public_ids), "manifest episodes are not sorted by public ID")
    require(len(set(public_ids)) == len(public_ids), "duplicate public challenge ID")

    episode_settings: list[int] = []
    public_checks: list[dict[str, Any]] = []
    all_identified = True
    all_queries_refute = True
    for row in rows:
        private_path = evidence_dir / row["private_path"]
        public_path = evidence_dir / row["public_path"]
        rule_path = evidence_dir / row["rule_path"]
        episode = load_json(private_path)
        public_raw = public_path.read_bytes()
        public = load_json(public_path)

        setting = episode.get("parameters", {}).get("deflection_distance")
        episode_settings.append(setting)
        require(setting in EXPECTED_SETTINGS, f"unexpected episode setting: {setting!r}")
        require(row.get("parameters") == {"deflection_distance": setting},
                "manifest/private setting mismatch")
        require(episode.get("parameter_domain") == {"deflection_distance": list(EXPECTED_SETTINGS)},
                "private episode parameter domain mismatch")
        require(episode.get("canonical_default") == {"deflection_distance": 1},
                "canonical default changed")

        program = episode.get("program")
        require(isinstance(program, str) and program, "private episode lacks exact program")
        require(rule_path.read_text(encoding="utf-8") == program,
                "retained Racket rule differs from private episode program")
        require(sha256(program.encode("utf-8")) == episode.get("program_sha256"),
                "private episode program hash mismatch")
        require(episode.get("program_sha256") == row.get("program_sha256"),
                "manifest/private program hash mismatch")

        train = episode.get("train")
        test = episode.get("test")
        require(isinstance(train, list) and len(train) == manifest["demo_count"],
                "private demonstration count mismatch")
        require(isinstance(test, list) and len(test) == manifest["query_count"],
                "private query count mismatch")
        require(all(set(pair) == {"input", "output"} for pair in train + test),
                "private pairs must contain exactly input/output")

        consistent = episode.get("rivals", {}).get("consistent_settings")
        query_mismatches = episode.get("rivals", {}).get("rival_query_mismatches")
        demo_mismatches = episode.get("rivals", {}).get("rival_demo_mismatches")
        identified = consistent == [setting]
        queries_refute = query_mismatches == list(range(len(test)))
        demos_refute = demo_mismatches == list(range(len(train)))
        all_identified = all_identified and identified and demos_refute
        all_queries_refute = all_queries_refute and queries_refute
        require(identified and demos_refute,
                f"demonstrations do not uniquely identify setting {setting}")
        require(queries_refute, f"not every query refutes the rival for setting {setting}")

        visible = {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in train
            ],
            "test": [{"input": pair["input"]} for pair in test],
        }
        expected_public_raw = canonical_bytes(visible)
        require(public_raw == expected_public_raw,
                "public challenge bytes do not equal the private visible projection")
        visible_sha = sha256(public_raw)
        require(visible_sha == row.get("public_id"),
                "public challenge ID is not its exact visible-byte SHA-256")
        require(public_path.name == f"challenge-{visible_sha}.json",
                "public filename is not derived solely from visible bytes")
        require(public == visible, "public JSON differs from visible projection")
        text = public_raw.decode("utf-8")
        forbidden_absent = all(token not in text for token in FORBIDDEN_PUBLIC_TOKENS)
        require(forbidden_absent, "public challenge leaks private metadata")
        require(all(set(pair) == {"input", "output"} for pair in public["train"]),
                "public demonstrations must remain labeled")
        require(all(set(pair) == {"input"} for pair in public["test"]),
                "public queries must omit answers")

        public_checks.append({
            "path": str(public_path.relative_to(evidence_dir.parent.parent)),
            "sha256": visible_sha,
            "filename_id": public_path.stem.removeprefix("challenge-"),
            "filename_matches_visible_sha256": True,
            "forbidden_strings_absent": forbidden_absent,
            "train_count": len(public["train"]),
            "query_count": len(public["test"]),
            "train_shape_ok": True,
            "test_shape_ok": True,
        })

    require(sorted(episode_settings) == list(EXPECTED_SETTINGS),
            "retained settings are incomplete or duplicated")

    return {
        "schema": "arc-ray-deflection-distance-offline-verification-v1",
        "status": "pass",
        "manifest_path": str(manifest_path.relative_to(evidence_dir.parents[2])),
        "manifest_sha256": sha256(manifest_raw),
        "canonical_pair_count": len(parity),
        "canonical_all_match": True,
        "episode_count": len(rows),
        "episode_settings": sorted(episode_settings),
        "manifest_public_ids_sorted": True,
        "all_episode_settings_identified": all_identified,
        "all_four_queries_refute_rival": all_queries_refute,
        "public_challenges": public_checks,
        "tracked_file_checks": tracked_file_checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    evidence_dir = args.evidence_dir.resolve()
    work_root = evidence_dir.parents[2]
    repo_root = (args.repo or work_root / "repo").resolve()
    result = verify(evidence_dir, repo_root)
    raw = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(raw, encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "canonical_pairs": result["canonical_pair_count"],
        "episodes": result["episode_count"],
        "settings": result["episode_settings"],
        "public_challenges": len(result["public_challenges"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VerificationError as exc:
        raise SystemExit(f"verification failed: {exc}") from exc
