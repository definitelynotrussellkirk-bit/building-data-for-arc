"""Artifact and exact-Racket tests for the projection-reach prototype verifier."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve()
ROOT = next(parent for parent in HERE.parents if (parent / "shared" / "runtime").is_dir())
for path in (ROOT / "shared" / "runtime", ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from reviewer_support import public_challenge_bytes

VERIFY_PATH = HERE.parents[1] / "workspace" / "parametric" / "verify.py"


def _load_verify():
    assert VERIFY_PATH.is_file(), f"verifier missing: {VERIFY_PATH}"
    spec = importlib.util.spec_from_file_location(
        "test_projection_reach_verifier_subject", VERIFY_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_public_batch_rejects_duplicate_visible_payload_before_write(tmp_path):
    verify = _load_verify()
    proto = verify._load_prototype()
    episode = proto.generate_episode(
        20, projection_reach="one_step", n_train=2, n_test=4
    )
    out_dir = tmp_path / "public"
    with pytest.raises(ValueError, match="duplicate public challenge"):
        verify.write_public_batch([episode, episode], out_dir, proto=proto)
    assert not out_dir.exists() or list(out_dir.iterdir()) == []


def test_verifier_replays_both_settings_and_builds_visible_only_artifacts(tmp_path):
    verify = _load_verify()
    report = verify.build_report(artifact_root=tmp_path)

    assert report["schema"] == "48bda9528e71-parametric-projection-reach-v1"
    assert report["status"] == "proposed_prototype_not_selected"
    assert report["all_racket_exact"] is True
    assert report["all_rival_racket_python_exact"] is True
    assert report["all_rivals_refuted_by_every_demo"] is True
    assert report["all_queries_setting_sensitive"] is True
    assert report["all_public_challenges_masked"] is True
    assert report["all_public_ids_unique"] is True
    assert report["canonical_default_racket_exact"] is True
    assert report["unique_input_count"] == 16

    assert [row["setting"] for row in report["settings"]] == [
        "one_step",
        "to_boundary",
    ]
    public_ids = []
    for row in report["settings"]:
        assert row["demo_count"] == 4
        assert row["query_count"] == 4
        assert len(row["pairs"]) == 8
        assert row["rival_refuted_by_every_demo"] is True
        assert row["rival_changes_every_query"] is True
        assert row["all_racket_exact"] is True
        assert row["rival_racket_python_exact"] is True
        public_path = ROOT / row["public_episode_path"]
        private_path = ROOT / row["private_episode_path"]
        program_path = ROOT / row["program_path"]
        # Test roots may be outside the repository, in which case paths are absolute.
        public_path = Path(row["public_episode_path"])
        private_path = Path(row["private_episode_path"])
        program_path = Path(row["program_path"])
        assert public_path.name == f"challenge-{row['public_id']}.json"
        assert row["setting"] not in public_path.name
        assert str(row["seed"]) not in public_path.name
        public = json.loads(public_path.read_text())
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert public_path.read_bytes() == public_challenge_bytes(public)
        assert private_path.is_file()
        assert program_path.is_file()
        public_ids.append(row["public_id"])
    assert len(public_ids) == len(set(public_ids)) == 2

    manifest = tmp_path / "evidence" / "manifest.json"
    assert json.loads(manifest.read_text()) == report


def test_verifier_source_manifest_covers_the_executed_prototype_and_verifier(tmp_path):
    verify = _load_verify()
    report = verify.build_report(artifact_root=tmp_path)
    source_hashes = report["source_hashes"]
    assert any(path.endswith("generator.py") for path in source_hashes)
    assert any(path.endswith("workspace/parametric/prototype.py") for path in source_hashes)
    assert any(path.endswith("workspace/parametric/verify.py") for path in source_hashes)
    assert all(len(digest) == 64 for digest in source_hashes.values())
