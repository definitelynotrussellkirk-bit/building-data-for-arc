"""Focused tests of the unselected parametric prototype, not canonical repair."""
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


TASK_ID = "72f0b65569a4"
ROOT = find_root(__file__)
CANDIDATES = (
    Path(__file__).resolve().parent.parent / "workspace/parametric/prototype.py",
    ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py",
    ROOT / f"puzzle_generators/per_puzzle/{TASK_ID}/workspace/parametric/prototype.py",
)
SOURCE = next((path for path in CANDIDATES if path.is_file()), None)
if SOURCE is None:
    raise FileNotFoundError("The task-local parametric workspace must accompany these prototype tests")
SPEC = importlib.util.spec_from_file_location("test_parametric_mirror_prototype", SOURCE)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


@pytest.fixture(scope="module")
def oracle():
    value = MODULE.RacketOracle()
    try:
        yield value
    finally:
        value.close()


def test_default_is_exact_canonical_bytes_and_executes_all_canonical_labels(oracle):
    source = MODULE.materialize_program()
    assert source == MODULE.canonical_program()
    assert hashlib.sha256(source.encode()).hexdigest() == MODULE.CANONICAL_SHA256
    result = MODULE.check_canonical(oracle)
    assert result["canonical_program_byte_identical"] is True
    assert result["checked_pairs"] == 3
    assert all(pair["passed"] for pair in result["pairs"])


@pytest.mark.parametrize("axis,color", [
    ("diagonal", 7), ("", 7), (None, 7), ("vertical", True),
    ("vertical", 7.0), ("vertical", "7"), ("horizontal", 0),
    ("horizontal", 1), ("horizontal", 4), ("horizontal", 9),
])
def test_rule_parameter_domain_is_strict_and_bounded(axis, color):
    with pytest.raises(ValueError):
        MODULE.Parameters(axis, color)


def test_inputs_and_once_per_episode_parameter_sampling_are_deterministic():
    before = random.getstate()
    settings = MODULE.sample_parameters(20261019)
    assert MODULE.sample_parameters(20261019) == settings
    assert settings in MODULE.all_parameters()
    grids = [MODULE.sample_input(731, index) for index in range(9)]
    assert random.getstate() == before
    assert grids == [MODULE.sample_input(731, index) for index in range(9)]
    assert len({MODULE.value_hash(grid) for grid in grids}) == len(grids)
    assert all({c for row in grid for c in row} == {0, 1, 4} for grid in grids)
    pristine = copy.deepcopy(grids[0])
    grids[0][0][0] = 9
    assert MODULE.sample_input(731, 0) == pristine
    with pytest.raises(ValueError):
        MODULE.sample_parameters(True)
    with pytest.raises(ValueError):
        MODULE.sample_input(1, -1)


@pytest.mark.parametrize("axis,location", [("vertical", (2, 6)), ("horizontal", (4, 2))])
@pytest.mark.parametrize("color", [7, 2])
def test_all_settings_execute_the_hand_located_separating_witness(oracle, axis, location, color):
    grid = MODULE.witness_input()
    before = copy.deepcopy(grid)
    output = oracle.evaluate(MODULE.Parameters(axis, color), grid)
    r, c = location
    assert output[r][c] == color
    assert sum(a != b for row_a, row_b in zip(grid, output) for a, b in zip(row_a, row_b)) == 1
    assert output[2][2] == 4
    assert grid == before
    # Returned values are independent even when an exact bridge result is cached.
    output[0][0] = 9
    assert oracle.evaluate(MODULE.Parameters(axis, color), grid)[0][0] == 0


@pytest.mark.parametrize("axis,occupied", [("vertical", (2, 6)), ("horizontal", (4, 2))])
@pytest.mark.parametrize("color", [7, 2])
def test_racket_preserves_occupied_targets_axis_marks_and_blue_frame(oracle, axis, occupied, color):
    grid = MODULE.witness_input()
    grid[occupied[0]][occupied[1]] = 4
    grid[3][4] = 4  # The center lies on both frame axes.
    assert oracle.evaluate(MODULE.Parameters(axis, color), grid) == grid


def test_complete_episodes_refute_each_parameter_rival_and_labels_bind_to_execution(oracle):
    episodes = [MODULE.build_episode(731, p, oracle=oracle, n_train=3, n_test=2) for p in MODULE.all_parameters()]
    reference_inputs = [pair["input"] for pair in episodes[0]["train"] + episodes[0]["test"]]
    for episode in episodes:
        assert [pair["input"] for pair in episode["train"] + episode["test"]] == reference_inputs
        assert episode["parameters_fixed_for_all_pairs"] is True
        assert episode["all_parameter_rivals_refuted"] is True
        assert all(rival["status"] == "refuted_by_demonstrations" for rival in episode["rival_results"])
        assert all(rival["differing_train_indices"] for rival in episode["rival_results"])
        for pair in episode["train"] + episode["test"]:
            matches = [
                row for row in oracle.executions
                if row["program_sha256"] == episode["program_sha256"]
                and row["input_sha256"] == MODULE.value_hash(pair["input"])
            ]
            assert len(matches) == 1
            assert matches[0]["output"] == pair["output"]
        public = episode["public"]
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert public["train"] == episode["train"]
        assert MODULE.value_hash(public) == episode["public_sha256"]


def test_rival_scoring_distinguishes_ambiguity_from_answer_equivalence():
    assert MODULE.rival_status([0], [0]) == "refuted_by_demonstrations"
    assert MODULE.rival_status([], [0]) == "ambiguous"
    assert MODULE.rival_status([], []) == "survived_all"


def test_application_adapter_accepts_only_the_four_pinned_templates():
    with pytest.raises(ValueError, match="four pinned"):
        MODULE.rule_application("(rule! g)", MODULE.witness_input())


@pytest.mark.parametrize("train,test", [(0, 1), (True, 1), (1, 0), (9, 1), (1, 5)])
def test_episode_size_constraints_fail_before_any_label_execution(oracle, train, test):
    count = len(oracle.executions)
    with pytest.raises(ValueError):
        MODULE.build_episode(1, oracle=oracle, n_train=train, n_test=test)
    assert len(oracle.executions) == count


def test_retained_manifest_binds_artifacts_and_public_file_has_no_query_answer(oracle, tmp_path):
    episode = MODULE.build_episode(90210, MODULE.sample_parameters(90210), oracle=oracle, parameter_selection="seeded once")
    result = MODULE.save_evidence(tmp_path, [episode], oracle, MODULE.check_canonical(oracle), MODULE.check_witness(oracle))
    assert result["status"] == "passed"
    assert result["scope"] == "prototype"
    assert result["main_generator_dependency"] is False
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    for path, digest in manifest["files"].items():
        assert hashlib.sha256((tmp_path / path).read_bytes()).hexdigest() == digest
    public = json.loads((tmp_path / "public/episode-000.json").read_text())
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input"} for pair in public["test"])
    private = json.loads((tmp_path / "private/episodes.json").read_text())
    assert private[0]["parameters"] == episode["parameters"]
    assert all("output" in pair for pair in private[0]["test"])
