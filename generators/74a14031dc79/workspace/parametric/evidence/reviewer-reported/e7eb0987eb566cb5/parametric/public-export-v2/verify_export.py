#!/usr/bin/env python3
"""Verify the retained v2 parametric export without regenerating it."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import public_challenge_bytes, public_challenge_id


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_grid_sha(grid: Any) -> str:
    raw = json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(raw)


def verify(evidence: Path) -> dict[str, Any]:
    evidence = evidence.resolve()
    repo = Path.cwd().resolve()
    report = json.loads((evidence / "report.json").read_text())
    manifest = json.loads((evidence / "manifest.json").read_text())

    manifest_files = manifest["files"]
    for row in manifest_files:
        path = evidence / row["path"]
        assert path.is_file(), row["path"]
        assert sha256_path(path) == row["sha256"], row["path"]

    source_hashes_checked = 0
    for row in report["sources"]:
        source = repo / row["path"]
        assert source.is_file(), row["path"]
        assert sha256_path(source) == row["sha256"], row["path"]
        if row.get("snapshot"):
            snapshot = evidence / row["snapshot"]
            assert snapshot.read_bytes() == source.read_bytes(), row["path"]
        source_hashes_checked += 1

    ids = [row["public_id"] for row in report["episodes"]]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))

    checked = []
    settings = set()
    train_pairs = query_pairs = rival_checks = ambiguities = 0
    for row in report["episodes"]:
        public_id = row["public_id"]
        public_path = evidence / row["public_path"]
        private_path = evidence / row["private_path"]
        episode = json.loads(private_path.read_text())
        public_raw = public_path.read_bytes()
        expected_raw = public_challenge_bytes(episode)

        assert public_raw == expected_raw
        assert public_id == public_challenge_id(episode) == sha256_bytes(public_raw)
        assert public_path.stem == public_id

        visible = json.loads(public_raw)
        assert set(visible) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in visible["train"])
        assert all(set(pair) == {"input"} for pair in visible["test"])
        for forbidden in ("seed", "parameters", "rule", "parameter_rivals", "ambiguities"):
            assert forbidden not in visible

        demo_count = episode["counts"]["demonstrations"]
        query_count = episode["counts"]["queries"]
        assert len(episode["train"]) == demo_count == 3
        assert len(episode["test"]) == query_count == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        input_hashes = [stable_grid_sha(grid) for grid in inputs]
        assert len(input_hashes) == len(set(input_hashes)) == 7
        assert input_hashes == episode["input_source"]["input_sha256"]
        assert len(episode["parameter_rivals"]) == 3
        assert not episode["ambiguities"]

        setting = episode["parameters"]["occupancy_rule"]
        settings.add(setting)
        train_pairs += demo_count
        query_pairs += query_count
        rival_checks += len(episode["parameter_rivals"])
        ambiguities += len(episode["ambiguities"])
        checked.append(
            {
                "public_id": public_id,
                "seed": episode["seed"],
                "setting": setting,
                "unique_inputs": len(set(input_hashes)),
            }
        )

    counts = report["counts"]
    assert counts["episodes"] == len(checked) == 3
    assert counts["train_pairs"] == train_pairs == 9
    assert counts["query_pairs"] == query_pairs == 12
    assert counts["parameter_rival_episode_checks"] == rival_checks == 9
    assert counts["ambiguous_parameter_rivals"] == ambiguities == 0
    assert counts["episode_settings_exercised"] == len(settings) == 3
    assert settings == {"or", "xor", "and"}

    return {
        "status": "passed",
        "counts": counts,
        "public_ids_sorted": ids == sorted(ids),
        "duplicate_public_ids": len(ids) - len(set(ids)),
        "manifest_files_checked": len(manifest_files),
        "source_hashes_checked": source_hashes_checked,
        "episodes_checked": checked,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.evidence)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
