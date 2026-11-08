"""Focused tests for the proposed Boolean-operator episode prototype."""
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
    return _load(PROTOTYPE_PATH, "task_55993f4c12af_parametric_prototype")


def _generator():
    return _load(GENERATOR_PATH, "task_55993f4c12af_parametric_generator")


def test_default_rule_is_exact_canonical_and_alternatives_are_guarded_changes():
    prototype = _prototype()
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert prototype.materialize_rule(root=ROOT) == canonical

    for operator in ("xor", "and"):
        source = prototype.materialize_rule(operator, root=ROOT)
        condition = prototype.OPERATOR_CONDITIONS[operator]
        assert source != canonical
        assert source.count(condition) == 1
        assert source.replace(
            condition,
            prototype.OPERATOR_CONDITIONS[prototype.DEFAULT_OPERATOR],
            1,
        ) == canonical

    for bad in (True, 0, 1.0, "union", None):
        with pytest.raises(ValueError, match="operator"):
            prototype.materialize_rule(bad, root=ROOT)


def test_prototype_inputs_are_lawful_and_all_operators_disagree():
    prototype = _prototype()
    generator = _generator()
    inputs = prototype.episode_inputs(37, root=ROOT)
    assert len(inputs) == 4

    with prototype.RacketBridge() as bridge:
        for grid in inputs:
            before = copy.deepcopy(grid)
            assert generator.self_check(grid) == []
            outputs = {
                operator: prototype.execute_rule(
                    prototype.materialize_rule(operator, root=ROOT),
                    grid,
                    bridge=bridge,
                )
                for operator in prototype.ALLOWED_OPERATORS
            }
            assert len({json.dumps(value) for value in outputs.values()}) == 3
            assert grid == before


def test_complete_episodes_choose_one_parameter_and_refute_all_other_settings():
    prototype = _prototype()
    seen = set()
    with prototype.RacketBridge() as bridge:
        for seed in prototype.COVERAGE_SEEDS:
            episode = prototype.make_episode(seed, root=ROOT, bridge=bridge)
            assert prototype.make_episode(seed, root=ROOT, bridge=bridge) == episode
            operator = episode["parameters"]["operator"]
            seen.add(operator)
            assert len(episode["train"]) == 3
            assert len(episode["test"]) == 1
            assert episode["status"] == "proposed_unapproved"
            assert episode["approved"] is False
            assert episode["ambiguities"] == []
            assert {row["operator"] for row in episode["parameter_rivals"]} == (
                set(prototype.ALLOWED_OPERATORS) - {operator}
            )
            for rival in episode["parameter_rivals"]:
                assert rival["status"] == "refuted_by_demonstrations"
                assert rival["demonstration_mismatch_indices"] == [0, 1, 2]
                assert rival["query_mismatch_indices"] == [0]
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == prototype.execute_rule(
                    episode["racket_source"], pair["input"], bridge=bridge
                )
    assert seen == set(prototype.ALLOWED_OPERATORS)


def test_public_challenge_omits_hidden_parameter_rule_seed_and_query_answer():
    prototype = _prototype()
    with prototype.RacketBridge() as bridge:
        episode = prototype.make_episode(prototype.COVERAGE_SEEDS[0], root=ROOT, bridge=bridge)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    before = copy.deepcopy(episode)
    public["train"][0]["input"][0][0] = 9
    assert episode == before


def test_evidence_retains_private_racket_data_hashes_and_canonical_replay(tmp_path):
    prototype = _prototype()
    out = tmp_path / "evidence"
    report = prototype.write_evidence(prototype.COVERAGE_SEEDS, out=out, root=ROOT)
    assert report["status"] == "proposed_unapproved"
    assert report["counts"] == {
        "episodes": 3,
        "settings_covered": 3,
        "ambiguous_parameter_rivals": 0,
        "canonical_pairs_checked": 5,
    }
    assert report["canonical_replay"]["status"] == "pass"

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
        prototype.write_evidence(prototype.COVERAGE_SEEDS, out=out, root=ROOT)
