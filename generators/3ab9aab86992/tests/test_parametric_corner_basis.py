"""Prototype-only tests for the proposed occupied-vs-missing corner basis."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[1]
SOURCE = TASK_ROOT / "workspace/parametric/prototype.py"


def _load_prototype():
    assert SOURCE.exists(), "corner-basis parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("corner_basis_prototype", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


@pytest.fixture(scope="module")
def executed(prototype):
    witness = [
        [2, 2, 8, 8, 8],
        [2, 8, 8, 8, 8],
        [8, 8, 8, 8, 8],
        [8, 8, 8, 8, 8],
        [8, 8, 8, 8, 8],
    ]
    sampled = [prototype.sample_input(23, index) for index in range(4)]
    inputs = [witness, *sampled]
    labels = {}
    receipts = {}
    for basis in prototype.CORNER_BASES:
        receipt = prototype.execute_program(
            prototype.rule_program(basis, root=REPO_ROOT),
            inputs,
        )
        assert receipt["status"] == "pass", receipt
        labels[basis] = receipt["outputs"]
        receipts[basis] = receipt
    return witness, sampled, labels, receipts


def test_default_setting_is_byte_exact_canonical_program(prototype):
    with (REPO_ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as stream:
        canonical = next(
            row
            for row in map(json.loads, stream)
            if row.get("task_id") == "3ab9aab86992"
        )
    assert prototype.DEFAULT_CORNER_BASIS == "occupied"
    assert prototype.rule_program(root=REPO_ROOT) == canonical["program_solution"]


def test_racket_executes_distinct_occupied_and_missing_corner_rules(prototype, executed):
    _, _, labels, _ = executed
    assert labels["occupied"][0] == [
        [2, 2, 8, 8, 8],
        [2, 8, 8, 8, 8],
        [8, 8, 8, 8, 8],
        [8, 8, 8, 8, 8],
        [8, 8, 8, 8, 8],
    ]
    assert labels["missing"][0] == [
        [8, 8, 8, 8, 8],
        [8, 8, 8, 8, 8],
        [8, 8, 8, 8, 8],
        [8, 8, 8, 8, 2],
        [8, 8, 8, 2, 2],
    ]
    assert labels["occupied"][0] != labels["missing"][0]


def test_hidden_rule_is_episode_level_and_input_stream_is_independent(prototype):
    assert {prototype.choose_corner_basis(seed) for seed in range(32)} == set(prototype.CORNER_BASES)
    for seed in range(8):
        inputs = [prototype.sample_input(seed, index) for index in range(4)]
        assert inputs == [prototype.sample_input(seed, index) for index in range(4)]
        for grid in inputs:
            assert prototype.validate_input(grid) == []
        assert prototype.episode_inputs(seed, corner_basis="occupied") == inputs
        assert prototype.episode_inputs(seed, corner_basis="missing") == inputs


def test_declared_parameter_rival_is_refuted_for_every_holdout(prototype, executed):
    _, _, labels, _ = executed
    per_setting = {
        basis: values[-4:]
        for basis, values in labels.items()
    }
    for selected in prototype.CORNER_BASES:
        result = prototype.parameter_teachability(per_setting, selected)
        assert result["production"]["identifiable"]
        assert all(rotation["identifiable"] for rotation in result["rotations"])
        assert result["rivals"][0]["refuting_pair_indices"] == [0, 1, 2, 3]


def test_public_projection_omits_hidden_parameter_program_and_query_answer(prototype, executed):
    _, sampled, labels, _ = executed
    for basis in prototype.CORNER_BASES:
        episode = prototype.assemble_episode(
            seed=23,
            corner_basis=basis,
            inputs=sampled,
            outputs=labels[basis][-4:],
            program=prototype.rule_program(basis, root=REPO_ROOT),
        )
        public = prototype.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 3 and len(public["test"]) == 1
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        serialized = json.dumps(public)
        assert "corner_basis" not in serialized
        assert "program" not in serialized
        assert "seed" not in serialized


def test_invalid_parameter_values_fail_loudly(prototype):
    for invalid in (None, "corner", "OCCUPIED", 0, 1, True, False, 1.0):
        with pytest.raises(ValueError):
            prototype.rule_program(invalid, root=REPO_ROOT)


def test_default_racket_program_accepts_and_matches_all_canonical_pairs(prototype):
    with (REPO_ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as stream:
        canonical = next(
            row
            for row in map(json.loads, stream)
            if row.get("task_id") == "3ab9aab86992"
        )
    pairs = canonical["train"] + canonical["test"]
    receipt = prototype.execute_program(
        prototype.rule_program(root=REPO_ROOT),
        [pair["input"] for pair in pairs],
    )
    assert receipt["status"] == "pass", receipt
    assert receipt["outputs"] == [pair["output"] for pair in pairs]
