"""Prototype-only tests for the proposed aura radius-delta parameter."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root


TASK_ID = "e706449ebf4c"
ROOT = find_root(__file__)
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    spec = importlib.util.spec_from_file_location("parametric_e706449ebf4c", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prototype = _load_prototype()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as runtime:
        yield runtime


def test_parameter_contract_and_canonical_default():
    assert prototype.ALLOWED_RADIUS_DELTAS == (0, 2)
    assert prototype.DEFAULT_RADIUS_DELTA == 0
    assert prototype.parameters_for_seed(0) == {"radius_delta": 0}
    assert prototype.parameters_for_seed(1) == {"radius_delta": 2}
    canonical = prototype.canonical_source(root=ROOT)
    assert prototype.materialize_rule(0, root=ROOT) == canonical
    expanded = prototype.materialize_rule(2, root=ROOT)
    assert expanded != canonical
    assert expanded.replace(prototype.EXPANDED_RADIUS_SITE, prototype.CANONICAL_RADIUS_SITE, 1) == canonical


@pytest.mark.parametrize("value", [True, -2, 1, 4, 1.5, "2", None])
def test_invalid_radius_delta_is_rejected(value):
    with pytest.raises(ValueError):
        prototype.materialize_rule(value, root=ROOT)


@pytest.mark.parametrize("seed", [False, -1, 1.5, "0", None])
def test_invalid_episode_seed_is_rejected(seed):
    with pytest.raises(ValueError):
        prototype.parameters_for_seed(seed)


def test_default_racket_reproduces_all_canonical_pairs(bridge):
    source = prototype.materialize_rule(0, root=ROOT)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert prototype.execute_rule(source, pair["input"], bridge=bridge) == pair["output"]


def test_two_settings_differ_and_both_match_python_mirror(bridge):
    inputs = prototype.episode_inputs(root=ROOT, seed=17)
    sources = {delta: prototype.materialize_rule(delta, root=ROOT) for delta in prototype.ALLOWED_RADIUS_DELTAS}
    differences = 0
    for row in inputs:
        grid = row["input"]
        outputs = {}
        for delta, source in sources.items():
            output = prototype.execute_rule(source, grid, bridge=bridge)
            assert output == prototype.python_transform(grid, delta)
            outputs[delta] = output
        differences += outputs[0] != outputs[2]
    assert differences == len(inputs)


def test_episode_selects_once_and_demonstrations_refute_other_setting(bridge):
    for seed, expected in ((0, 0), (1, 2)):
        episode = prototype.make_episode(seed, root=ROOT, bridge=bridge)
        assert episode["parameters"] == {"radius_delta": expected}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["ambiguities"] == []
        matching = [row for row in episode["parameter_rivals"] if row["status"] == "matches_episode"]
        refuted = [row for row in episode["parameter_rivals"] if row["status"] == "refuted_by_demonstrations"]
        assert [row["radius_delta"] for row in matching] == [expected]
        assert len(refuted) == 1
        assert refuted[0]["demonstration_mismatch_indices"]
        assert refuted[0]["query_mismatch_indices"] == [0]


def test_public_challenge_hides_parameter_rule_seed_and_query_answer(bridge):
    private = prototype.make_episode(1, root=ROOT, bridge=bridge)
    public = prototype.public_challenge(private)
    payload = json.dumps(public, sort_keys=True)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    for forbidden in ("radius_delta", "parameter", "racket", "seed"):
        assert forbidden not in payload


def test_evidence_writer_hashes_files_and_keeps_answers_private(tmp_path):
    out = tmp_path / "evidence"
    report = prototype.write_evidence((0, 1), out=out, root=ROOT)
    assert report["status"] == "proposed_unapproved"
    assert report["counts"]["episodes"] == 2
    assert report["counts"]["settings_exercised"] == 2
    assert report["counts"]["ambiguous_parameter_rivals"] == 0
    for row in report["episodes"]:
        public = json.loads((out / row["public_path"]).read_text())
        private = json.loads((out / row["private_path"]).read_text())
        assert public == prototype.public_challenge(private)
        assert "output" not in public["test"][0]
        assert "output" in private["test"][0]
    for row in report["files"]:
        assert hashlib.sha256((out / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    with pytest.raises(FileExistsError):
        prototype.write_evidence((0, 1), out=out, root=ROOT)
