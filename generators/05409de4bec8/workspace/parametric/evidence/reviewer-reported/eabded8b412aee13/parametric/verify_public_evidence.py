#!/usr/bin/env python3
"""Independently verify byte identity and privacy of parametric evidence.

This checker deliberately uses only the Python standard library.  It does not
import the prototype, verifier, or reviewer_support, so it can detect drift in
those components rather than reproducing their implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


FULL_SHA256 = re.compile(r"[0-9a-f]{64}")
EXPECTED_REPORT_SCHEMA = "05409de4bec8-parametric-rectangle-policy-v2"
EXPECTED_MANIFEST_SCHEMA = "parametric-evidence-manifest-v1"
EXPECTED_SETTINGS = {"longer", "both"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def grid_key(grid: Any) -> str:
    return json.dumps(grid, separators=(",", ":"), sort_keys=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def visible_projection(private_episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in private_episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in private_episode["test"]],
    }


def verify_manifest(evidence_dir: Path, manifest: dict[str, Any]) -> dict[str, str]:
    assert_true(
        manifest.get("schema") == EXPECTED_MANIFEST_SCHEMA,
        "unexpected manifest schema",
    )
    rows = manifest.get("files")
    assert_true(isinstance(rows, list) and rows, "manifest files must be nonempty")

    declared: dict[str, str] = {}
    for row in rows:
        assert_true(isinstance(row, dict), "manifest row must be an object")
        rel = row.get("path")
        digest = row.get("sha256")
        size = row.get("bytes")
        assert_true(isinstance(rel, str) and rel, "manifest path must be nonempty")
        assert_true(rel not in declared, f"duplicate manifest path: {rel}")
        path = evidence_dir / rel
        assert_true(path.is_file(), f"missing manifested file: {rel}")
        data = path.read_bytes()
        assert_true(size == len(data), f"manifest byte count mismatch: {rel}")
        assert_true(digest == sha256_bytes(data), f"manifest hash mismatch: {rel}")
        declared[rel] = digest

    actual = {
        str(path.relative_to(evidence_dir))
        for path in evidence_dir.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    assert_true(
        set(declared) == actual,
        f"manifest file set mismatch: declared={sorted(declared)} actual={sorted(actual)}",
    )
    report_digest = sha256_file(evidence_dir / "report.json")
    assert_true(
        manifest.get("report_sha256") == report_digest,
        "manifest report_sha256 mismatch",
    )
    return declared


def verify_evidence(evidence_dir: Path, verifier_path: Path) -> dict[str, Any]:
    evidence_dir = evidence_dir.resolve()
    verifier_path = verifier_path.resolve()
    assert_true(evidence_dir.is_dir(), f"missing evidence directory: {evidence_dir}")
    assert_true(verifier_path.is_file(), f"missing verifier: {verifier_path}")

    report_path = evidence_dir / "report.json"
    manifest_path = evidence_dir / "manifest.json"
    report = read_json(report_path)
    manifest = read_json(manifest_path)
    manifest_files = verify_manifest(evidence_dir, manifest)

    assert_true(
        report.get("schema") == EXPECTED_REPORT_SCHEMA,
        "unexpected report schema",
    )
    assert_true(
        report.get("status") == "passed_bounded_prototype_evidence",
        "report did not retain a passed bounded-evidence status",
    )
    current_verifier_hash = sha256_file(verifier_path)
    assert_true(
        report.get("verifier_sha256") == current_verifier_hash,
        "verifier hash does not match the retained report",
    )

    counts = report.get("counts")
    assert_true(
        counts == {"demonstrations": 5, "queries": 4},
        f"unexpected retained counts: {counts!r}",
    )
    query_count = counts["queries"]
    demo_count = counts["demonstrations"]

    public_order = report.get("public_write_order")
    assert_true(isinstance(public_order, list), "public_write_order must be a list")
    assert_true(public_order == sorted(public_order), "public write plan is not ID-sorted")
    assert_true(len(public_order) == len(set(public_order)), "duplicate public IDs")
    assert_true(
        all(isinstance(value, str) and FULL_SHA256.fullmatch(value) for value in public_order),
        "public IDs must be full lowercase SHA-256 values",
    )

    episodes = report.get("episodes")
    assert_true(isinstance(episodes, list) and len(episodes) == 2, "expected two episodes")
    settings = {episode.get("setting") for episode in episodes}
    assert_true(settings == EXPECTED_SETTINGS, f"unexpected settings: {settings!r}")
    assert_true(
        {episode.get("public_id") for episode in episodes} == set(public_order),
        "episode IDs do not match the public write plan",
    )

    public_rows: list[dict[str, Any]] = []
    all_visible_ids: list[str] = []
    for episode in episodes:
        setting = episode["setting"]
        public_id = episode.get("public_id")
        assert_true(
            isinstance(public_id, str) and FULL_SHA256.fullmatch(public_id) is not None,
            f"invalid public ID for {setting}",
        )
        expected_public_rel = f"public/episode-{public_id}.json"
        assert_true(
            episode.get("public_challenge") == expected_public_rel,
            f"public filename does not match ID for {setting}",
        )
        public_path = evidence_dir / expected_public_rel
        public_bytes = public_path.read_bytes()
        assert_true(
            sha256_bytes(public_bytes) == public_id,
            f"exact public bytes do not hash to ID for {setting}",
        )
        assert_true(
            manifest_files.get(expected_public_rel) == public_id,
            f"manifest public hash does not equal ID for {setting}",
        )

        public = json.loads(public_bytes)
        assert_true(set(public) == {"train", "test"}, f"private top-level key leaked for {setting}")
        assert_true(
            all(isinstance(pair, dict) and set(pair) == {"input", "output"} for pair in public["train"]),
            f"private or malformed training fields for {setting}",
        )
        assert_true(
            all(isinstance(pair, dict) and set(pair) == {"input"} for pair in public["test"]),
            f"query answer or private test field leaked for {setting}",
        )
        assert_true(len(public["train"]) == demo_count, f"demo count mismatch for {setting}")
        assert_true(len(public["test"]) == query_count, f"query count mismatch for {setting}")

        private_rel = episode.get("private_episode")
        assert_true(isinstance(private_rel, str), f"missing private episode for {setting}")
        private = read_json(evidence_dir / private_rel)
        assert_true(
            private.get("meta", {}).get("rectangle_policy") == setting,
            f"private setting mismatch for {setting}",
        )
        assert_true(
            private.get("meta", {}).get("seed") == episode.get("seed"),
            f"private seed mismatch for {setting}",
        )
        assert_true(
            len(private.get("train", [])) == demo_count
            and len(private.get("test", [])) == query_count,
            f"private counts mismatch for {setting}",
        )
        assert_true(
            sha256_bytes(private.get("program", "").encode("utf-8"))
            == episode.get("program_sha256"),
            f"program hash mismatch for {setting}",
        )
        assert_true(
            public == visible_projection(private),
            f"public projection does not match private episode for {setting}",
        )

        visible_inputs = [pair["input"] for pair in public["train"] + public["test"]]
        visible_keys = [grid_key(grid) for grid in visible_inputs]
        assert_true(
            len(visible_keys) == len(set(visible_keys)),
            f"duplicate visible input within {setting} episode",
        )
        assert_true(
            episode.get("all_labels_executed_by_racket") is True,
            f"Racket execution flag missing for {setting}",
        )
        assert_true(
            episode.get("query_rival_disagreement_indices") == list(range(query_count)),
            f"not every query rejects the rival for {setting}",
        )
        demo_disagreements = episode.get("demo_rival_disagreement_indices")
        assert_true(
            isinstance(demo_disagreements, list) and len(demo_disagreements) >= 2,
            f"insufficient demonstration disagreement for {setting}",
        )

        public_rows.append(
            {
                "setting": setting,
                "public_id": public_id,
                "path": expected_public_rel,
                "bytes": len(public_bytes),
            }
        )
        all_visible_ids.append(public_id)

    disagreement = read_json(evidence_dir / "private/same-input-disagreement.json")
    assert_true(disagreement.get("is_rectangle") is True, "disagreement witness is not a rectangle")
    outputs = disagreement.get("outputs")
    assert_true(
        isinstance(outputs, dict) and set(outputs) == EXPECTED_SETTINGS,
        "disagreement witness settings mismatch",
    )
    assert_true(
        outputs["longer"] != outputs["both"],
        "same-input witness does not distinguish settings",
    )

    public_rows.sort(key=lambda row: row["public_id"])
    return {
        "schema": "05409de4bec8-parametric-public-evidence-independent-v1",
        "status": "passed",
        "counts": dict(counts),
        "settings": sorted(settings),
        "public_ids": sorted(all_visible_ids),
        "public_files": public_rows,
        "source_hashes": {
            "verifier_sha256": current_verifier_hash,
            "report_sha256": sha256_file(report_path),
            "manifest_sha256": sha256_file(manifest_path),
            "production_generator_sha256": report.get("production_generator_sha256"),
            "prototype_sha256": report.get("prototype_sha256"),
        },
        "checks": {
            "current_verifier_hash_matches_report": True,
            "exact_public_bytes_hash_to_full_id": True,
            "public_projection_matches_private_episode": True,
            "visible_shape_excludes_settings_seeds_programs_and_query_answers": True,
            "public_write_plan_is_sorted_and_unique": True,
            "duplicate_visible_inputs_absent_within_each_episode": True,
            "all_four_queries_reject_declared_rival": True,
            "retained_racket_execution_flags_present": True,
            "same_input_parameter_disagreement_present": True,
            "manifest_complete_and_exact": True,
        },
        "limits": [
            "This static checker validates retained byte artifacts and Racket execution flags; it does not launch a second Racket process.",
            "The writer regression test, not filesystem metadata, verifies actual write-call ordering and overwrite preflight behavior.",
        ],
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--verifier", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(f"refusing to overwrite {args.out}")
    receipt = verify_evidence(args.evidence, args.verifier)
    write_json(args.out, receipt)
    print(json.dumps({"status": receipt["status"], "public_ids": receipt["public_ids"]}, sort_keys=True))


if __name__ == "__main__":
    main()
