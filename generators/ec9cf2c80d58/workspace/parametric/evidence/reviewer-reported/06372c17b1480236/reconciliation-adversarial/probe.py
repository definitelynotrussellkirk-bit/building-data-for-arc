#!/usr/bin/env python3
"""Adversarial reconciliation checks for ec9cf2c80d58 parametric evidence."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any

REPO = Path.cwd().resolve()
if not (REPO / "shared" / "runtime" / "reviewer_support.py").is_file():
    raise SystemExit(f"run from packet repo root, got {REPO}")
sys.path.insert(0, str(REPO / "shared" / "runtime"))

from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402

TASK = REPO / "generators" / "ec9cf2c80d58"
CHECKS = REPO.parent / "checks"
OLD_EVIDENCE = TASK / "workspace" / "parametric" / "evidence" / "owner-current"
NEW_EVIDENCE = CHECKS / "parametric-reconciled"
EXPECTED_GENERATOR_SHA = "39cb6a9ff704cbc37689246fc0a7f2cd40a6b95de37ea6fb94fa20e8947413e9"
EXPECTED_RULE_HASH = "899eb4e6a25d"
CONTENT_NAME = re.compile(r"challenge-([0-9a-f]{64})\.json\Z")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def encoded(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def mutate_visible_label(episode: dict[str, Any]) -> dict[str, Any]:
    changed = deepcopy(episode)
    cell = changed["train"][0]["output"][0][0]
    changed["train"][0]["output"][0][0] = 1 if cell == 0 else 0
    return changed


def main() -> None:
    proto = load_module("reconcile_proto", TASK / "workspace" / "parametric" / "prototype.py")
    builder = load_module("reconcile_builder", TASK / "workspace" / "parametric" / "build_evidence.py")
    old = read_json(OLD_EVIDENCE / "episodes.json")
    new = read_json(NEW_EVIDENCE / "episodes.json")
    public = read_json(NEW_EVIDENCE / "public_challenges.json")
    summary = read_json(NEW_EVIDENCE / "summary.json")

    preserved: dict[str, Any] = {}
    privacy: dict[str, Any] = {}
    public_files: dict[str, Any] = {}

    for policy in ("column", "row"):
        old_pairs = [*old[policy]["train"], *old[policy]["test"]]
        new_pairs = [*new[policy]["train"], *new[policy]["test"]]
        assert new_pairs[:4] == old_pairs, f"{policy}: historical teaching prefix changed"
        assert len(new[policy]["train"]) == 3
        assert len(new[policy]["test"]) == 4
        input_keys = [encoded(pair["input"]) for pair in new_pairs]
        assert len(set(input_keys)) == 7, f"{policy}: duplicate episode input"
        assert all(
            encoded(pair["input"]) not in {encoded(p["input"]) for p in old_pairs}
            for pair in new[policy]["test"][1:]
        ), f"{policy}: appended query repeats historical input"
        preserved[policy] = {
            "historical_pair_count": len(old_pairs),
            "historical_prefix_unchanged": True,
            "new_query_count": len(new[policy]["test"]),
            "appended_distinct_queries": 3,
            "all_episode_inputs_distinct": True,
        }

        challenge = proto.public_challenge(new[policy])
        name = proto.public_filename(new[policy])
        expected_name = f"challenge-{public_challenge_id(challenge)}.json"
        assert name == expected_name

        private_only = deepcopy(new[policy])
        private_only["seed"] += 999
        private_only["parameter"] = {"tie_policy": "row" if policy == "column" else "column"}
        private_only["program"] = "private replacement"
        private_only["test"][0]["output"] = [[99]]
        assert proto.public_filename(private_only) == name

        visible_changed = mutate_visible_label(new[policy])
        assert proto.public_filename(visible_changed) != name
        privacy[policy] = {
            "content_id_matches_helper": True,
            "private_setting_metadata_program_and_query_labels_ignored": True,
            "visible_demonstration_label_changes_id": True,
            "public_name": name,
        }

    names = list(public)
    assert names == sorted(names), "aggregate public keys are not sorted"
    assert set(names) == {proto.public_filename(episode) for episode in new.values()}
    for name in names:
        match = CONTENT_NAME.fullmatch(name)
        assert match is not None, name
        challenge = public[name]
        payload = public_challenge_bytes(challenge)
        path = NEW_EVIDENCE / "public" / name
        assert path.read_bytes() == payload, f"{name}: file bytes are not canonical visible bytes"
        digest = hashlib.sha256(payload).hexdigest()
        assert digest == match.group(1), f"{name}: filename is not payload SHA-256"
        public_files[name] = {
            "bytes": len(payload),
            "sha256_matches_filename": True,
            "exact_canonical_visible_bytes": True,
        }

    duplicate_registry: dict[str, Any] = {}
    builder._register_public_challenge(duplicate_registry, proto, new["column"])
    try:
        builder._register_public_challenge(duplicate_registry, proto, deepcopy(new["column"]))
    except ValueError as exc:
        assert "duplicate public challenge" in str(exc)
    else:
        raise AssertionError("duplicate public challenge was accepted")

    execution = summary["execution"]
    assert summary["status"] == "pass"
    assert summary["source"]["canonical_generator_sha256"] == EXPECTED_GENERATOR_SHA
    assert summary["source"]["canonical_rule_hash"] == EXPECTED_RULE_HASH
    assert summary["source"]["canonical_authority_changed"] is False
    assert summary["source"]["column_program_is_exact_canonical_text"] is True
    assert sum(row["pair_count"] for row in execution.values()) == 14
    assert all(row["racket_outputs_match_stored"] for row in execution.values())
    assert all(row["python_outputs_match_racket"] for row in execution.values())
    assert sum(row["query_count"] for row in execution.values()) == 8
    assert all(row["all_queries_distinguish_opposite_setting"] for row in execution.values())
    assert all(all(row["query_distinctions"]) for row in execution.values())

    result = {
        "schema": "ec9cf2c80d58-reconciliation-adversarial-v1",
        "status": "pass",
        "historical_prefix": preserved,
        "public_identity_privacy": privacy,
        "public_files": public_files,
        "duplicate_public_payload_rejected": True,
        "live_racket": {
            "stored_labels_matched": 14,
            "queries_distinguishing_opposite_policy": 8,
            "generator_sha256_unchanged": EXPECTED_GENERATOR_SHA,
            "canonical_rule_hash_unchanged": EXPECTED_RULE_HASH,
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
