"""Focused tests for the separate proposed stamp-anchor prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
)


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "b985d561c63b_parametric_anchor", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_rule_is_byte_exact_canonical_and_alternative_is_reversible():
    prototype = _load_prototype()
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert prototype.materialize_rule(root=ROOT) == canonical
    assert prototype.materialize_rule("top_left", root=ROOT) == canonical

    alternative = prototype.materialize_rule("bottom_right", root=ROOT)
    assert alternative != canonical
    assert prototype.restore_canonical_rule(alternative) == canonical
    assert prototype.rule_callable(alternative) != prototype.rule_callable(canonical)

    for bad in (True, 0, 1, "center", "top-left", None):
        with pytest.raises((TypeError, ValueError)):
            prototype.materialize_rule(bad, root=ROOT)


def test_complete_episodes_choose_one_anchor_and_refute_the_other_setting():
    prototype = _load_prototype()
    seen = set()
    with prototype.RacketBridge() as bridge:
        for seed in (0, 1):
            episode = prototype.make_episode(seed, root=ROOT, bridge=bridge)
            assert prototype.make_episode(seed, root=ROOT, bridge=bridge) == episode
            anchor = episode["parameters"]["stamp_anchor"]
            seen.add(anchor)
            assert len(episode["train"]) == 3
            assert len(episode["test"]) == 1
            assert episode["status"] == "proposed_unapproved"
            assert episode["approved"] is False
            assert episode["input_constraints_depend_on_parameter"] is False
            assert not episode["ambiguities"]
            assert len({pair["input_sha256"] for pair in episode["train"] + episode["test"]}) == 4

            rival, = [
                row for row in episode["parameter_rivals"]
                if row["stamp_anchor"] != anchor
            ]
            assert rival["status"] == "refuted_by_demonstrations"
            assert rival["demonstration_mismatch_indices"] == [0, 1, 2]
            assert rival["query_mismatch_indices"] == [0]

            for pair in episode["train"] + episode["test"]:
                observation = pair["input_observation"]
                assert observation["template_style"] == "dense"
                assert observation["extra_rows"] == 1
                assert observation["extra_cols"] == 1
                assert pair["output"] == prototype.execute_rule(
                    episode["racket_source"], pair["input"], bridge=bridge
                )
                assert pair["output"] == prototype.python_mirror(
                    pair["input"], stamp_anchor=anchor
                )
    assert seen == set(prototype.ALLOWED_STAMP_ANCHORS)


def test_public_challenge_omits_parameter_rule_seed_rivals_and_query_answer():
    prototype = _load_prototype()
    with prototype.RacketBridge() as bridge:
        episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in (
        "stamp_anchor", "racket_source", "parameter_rivals", "ambiguities", '"seed"'
    ):
        assert forbidden not in serialized

    before = copy.deepcopy(episode)
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_evidence_retains_exact_private_racket_and_hashes_all_files(tmp_path):
    prototype = _load_prototype()
    out = tmp_path / "evidence"
    report = prototype.write_evidence((0, 1), out=out, root=ROOT)
    assert report["status"] == "proposed_unapproved"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    assert report["counts"]["settings_covered"] == 2
    assert report["counts"]["canonical_pairs_checked"] >= 3

    for row in report["episodes"]:
        public = json.loads((out / row["public_path"]).read_text())
        private = json.loads((out / row["private_path"]).read_text())
        source = (out / private["racket_path"]).read_text()
        assert hashlib.sha256(source.encode()).hexdigest() == private["racket_sha256"]
        assert public == prototype.public_challenge(private)
        assert "output" in private["test"][0]
        assert "output" not in public["test"][0]
        assert not private["ambiguities"]

    witness = json.loads((out / "private/distinguishing_witness.json").read_text())
    assert witness["different"] is True
    for row in report["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError):
        prototype.write_evidence((0, 1), out=out, root=ROOT)
