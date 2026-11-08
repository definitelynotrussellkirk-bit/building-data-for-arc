"""Focused tests for the proposed match-relation episode prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
TASK_DIR = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_DIR / "workspace" / "parametric" / "prototype.py"
GENERATOR_PATH = TASK_DIR / "generator.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(PROTOTYPE_PATH, "bdd177308a5b_parametric_prototype")


def _generator():
    return _load(GENERATOR_PATH, "bdd177308a5b_parametric_test_generator")


def test_default_rule_is_exact_canonical_and_alternative_is_one_guarded_relation_change():
    prototype = _prototype()
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert prototype.materialize_rule(root=ROOT) == canonical
    alternative = prototype.materialize_rule("quarter_turn_cw", root=ROOT)
    assert alternative != canonical
    assert alternative.count(prototype.ALTERNATIVE_COMPARISON) == 1
    assert alternative.replace(
        prototype.ALTERNATIVE_COMPARISON,
        prototype.CANONICAL_COMPARISON,
        1,
    ) == canonical
    for bad in (True, 0, 1.0, "rotate", None):
        with pytest.raises((TypeError, ValueError)):
            prototype.materialize_rule(bad, root=ROOT)


def test_authored_inputs_are_canonical_lawful_and_distinguish_both_relations():
    prototype = _prototype()
    generator = _generator()
    fixtures = prototype.fixtures()
    assert len(fixtures) == 4
    with prototype.RacketBridge() as bridge:
        for fixture in fixtures:
            grid = fixture["input"]
            assert generator.self_check(grid) == []
            exact = prototype.execute_rule(
                prototype.materialize_rule("exact", root=ROOT), grid, bridge=bridge
            )
            rotated = prototype.execute_rule(
                prototype.materialize_rule("quarter_turn_cw", root=ROOT),
                grid,
                bridge=bridge,
            )
            assert exact != rotated, fixture["fixture_id"]
            assert grid == fixture["input"]


def test_complete_episodes_choose_one_parameter_and_refute_the_other_setting():
    prototype = _prototype()
    seen = set()
    with prototype.RacketBridge() as bridge:
        for seed in (0, 1):
            episode = prototype.make_episode(seed, root=ROOT, bridge=bridge)
            assert prototype.make_episode(seed, root=ROOT, bridge=bridge) == episode
            relation = episode["parameters"]["match_relation"]
            seen.add(relation)
            assert len(episode["train"]) == 3
            assert len(episode["test"]) == 1
            assert episode["status"] == "proposed_unapproved"
            assert episode["approved"] is False
            assert episode["ambiguities"] == []
            rival, = [
                row
                for row in episode["parameter_rivals"]
                if row["match_relation"] != relation
            ]
            assert rival["status"] == "refuted_by_demonstrations"
            assert rival["demonstration_mismatch_indices"] == [0, 1, 2]
            assert rival["query_mismatch_indices"] == [0]
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == prototype.execute_rule(
                    episode["racket_source"], pair["input"], bridge=bridge
                )
    assert seen == set(prototype.ALLOWED_MATCH_RELATIONS)


def test_public_challenge_omits_parameter_rule_seed_and_query_answer():
    prototype = _prototype()
    with prototype.RacketBridge() as bridge:
        episode = prototype.make_episode(0, root=ROOT, bridge=bridge)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    before = copy.deepcopy(episode)
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_evidence_retains_private_racket_data_and_hashes(tmp_path):
    prototype = _prototype()
    out = tmp_path / "evidence"
    report = prototype.write_evidence((0, 1), out=out, root=ROOT)
    assert report["status"] == "proposed_unapproved"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    assert report["counts"]["settings_covered"] == 2
    assert report["counts"]["canonical_pairs_checked"] == 8
    for row in report["episodes"]:
        public = json.loads((out / row["public_path"]).read_text())
        private = json.loads((out / row["private_path"]).read_text())
        source = (out / private["racket_path"]).read_text()
        assert hashlib.sha256(source.encode()).hexdigest() == private["racket_sha256"]
        assert public == prototype.public_challenge(private)
        assert "output" in private["test"][0]
        assert "output" not in public["test"][0]
    for row in report["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError):
        prototype.write_evidence((0, 1), out=out, root=ROOT)
