"""Focused tests for the separate bar-length rule prototype."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import find_root


TASK_ID = "474634a9f7b7"
ROOT = find_root(__file__)
SOURCE = Path(__file__).resolve().parent.parent / "workspace/parametric/prototype.py"


def _load_module():
    assert SOURCE.is_file(), "the task-local parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("test_parametric_bar_length_prototype", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def module():
    return _load_module()


@pytest.fixture(scope="module")
def oracle(module):
    value = module.RacketOracle()
    try:
        yield value
    finally:
        value.close()


def test_default_program_is_exact_canonical_bytes_and_labels(oracle, module):
    source = module.materialize_program()
    assert source == module.canonical_program()
    assert hashlib.sha256(source.encode()).hexdigest() == module.CANONICAL_SHA256
    result = module.check_canonical(oracle)
    assert result["canonical_program_byte_identical"] is True
    assert result["checked_pairs"] == 8
    assert all(pair["passed"] for pair in result["pairs"])


@pytest.mark.parametrize("value", [True, 0, 2, 4, 3.0, "3", None])
def test_rule_parameter_domain_is_strict_and_bounded(module, value):
    with pytest.raises(ValueError):
        module.Parameters(value)


def test_once_per_episode_parameter_sampling_and_inputs_are_deterministic(module):
    before = random.getstate()
    settings = module.sample_parameters(20261019)
    assert module.sample_parameters(20261019) == settings
    assert settings in module.all_parameters()
    grids = [module.sample_input(731, index) for index in range(7)]
    assert random.getstate() == before
    assert grids == [module.sample_input(731, index) for index in range(7)]
    assert len({module.value_hash(grid) for grid in grids}) == len(grids)
    assert all(module.MAIN.self_check(grid) == [] for grid in grids)
    pristine = copy.deepcopy(grids[0])
    grids[0][0][0] = 9
    assert module.sample_input(731, 0) == pristine
    with pytest.raises(ValueError):
        module.sample_parameters(True)
    with pytest.raises(ValueError):
        module.sample_input(1, -1)


def test_both_settings_execute_and_change_only_the_two_outer_bar_cells(oracle, module):
    for index, target_side in enumerate(module.MAIN.SIDES):
        grid = module.MAIN.generate(911, index, target_side=target_side)
        short = oracle.evaluate(module.Parameters(1), grid)
        canonical = oracle.evaluate(module.Parameters(3), grid)
        assert canonical == module.MAIN.rule_mirror(grid)
        differences = {
            (row, col)
            for row in range(len(grid))
            for col in range(len(grid[0]))
            if short[row][col] != canonical[row][col]
        }
        assert len(differences) == 2
        assert differences < set(module.MAIN._analyze(grid)["bar"])


def test_complete_episodes_refute_the_other_setting_and_bind_labels_to_racket(oracle, module):
    episodes = [
        module.build_episode(731, parameters, oracle=oracle, n_train=4, n_test=1)
        for parameters in module.all_parameters()
    ]
    reference_inputs = [pair["input"] for pair in episodes[0]["train"] + episodes[0]["test"]]
    for episode in episodes:
        assert [pair["input"] for pair in episode["train"] + episode["test"]] == reference_inputs
        assert episode["parameters_fixed_for_all_pairs"] is True
        assert episode["all_parameter_rivals_refuted"] is True
        assert len(episode["rival_results"]) == 1
        rival = episode["rival_results"][0]
        assert rival["status"] == "refuted_by_demonstrations"
        assert rival["differing_train_indices"] == [0, 1, 2, 3]
        for pair in episode["train"] + episode["test"]:
            matches = [
                row
                for row in oracle.executions
                if row["program_sha256"] == episode["program_sha256"]
                and row["input_sha256"] == module.value_hash(pair["input"])
            ]
            assert len(matches) == 1
            assert matches[0]["output"] == pair["output"]
        public = episode["public"]
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert "parameters" not in public
        assert public["train"] == episode["train"]
        assert module.value_hash(public) == episode["public_sha256"]


def test_retained_manifest_binds_private_evidence_and_public_hides_query_answer(
    oracle, module, tmp_path
):
    episode = module.build_episode(
        90210,
        module.sample_parameters(90210),
        oracle=oracle,
        parameter_selection="seeded once",
    )
    result = module.save_evidence(
        tmp_path,
        [episode],
        oracle,
        module.check_canonical(oracle),
        module.check_witness(oracle),
    )
    assert result["status"] == "passed"
    assert result["scope"] == "prototype"
    assert result["main_generator_dependency"] is True
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    for path, digest in manifest["files"].items():
        assert hashlib.sha256((tmp_path / path).read_bytes()).hexdigest() == digest
    public = json.loads((tmp_path / "public/episode-000.json").read_text())
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "parameters" not in public
    private = json.loads((tmp_path / "private/episodes.json").read_text())
    assert private[0]["parameters"] == episode["parameters"]
    assert all("output" in pair for pair in private[0]["test"])
