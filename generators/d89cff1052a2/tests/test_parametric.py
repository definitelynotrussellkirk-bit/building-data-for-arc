"""Proposed parametric prototype tests; these do not approve canonical changes."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


PROTOTYPE = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"


def test_separate_runnable_prototype_entry_point_exists():
    assert PROTOTYPE.is_file(), "The separate runnable parametric prototype is missing"


@pytest.fixture(scope="module")
def prototype():
    assert PROTOTYPE.is_file(), "The separate runnable parametric prototype is missing"
    sys.path.insert(0, str(PROTOTYPE.parent))
    spec = importlib.util.spec_from_file_location("d89cff_parametric_prototype", PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def oracle(prototype):
    with prototype.RacketOracle() as value:
        yield value


def test_exact_default_program_matches_all_canonical_labels(prototype, oracle):
    canonical = prototype.canonical_context()
    assert prototype.DEFAULT == prototype.Setting("vertical", "reflected_first")
    assert prototype.program_for(prototype.DEFAULT) == canonical["program"]
    assert canonical["program_sha256"].startswith("370a7fcc45fc")
    assert len(canonical["pairs"]) == 5
    for pair in canonical["pairs"]:
        assert oracle.label(prototype.program_for(prototype.DEFAULT), pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "axis,order,expected",
    [
        ("vertical", "reflected_first", [[2, 2, 1], [1, 2, 1], [1, 1, 2], [1, 1, 2], [1, 2, 1], [2, 2, 1]]),
        ("vertical", "original_first", [[1, 1, 2], [1, 2, 1], [2, 2, 1], [2, 2, 1], [1, 2, 1], [1, 1, 2]]),
        ("horizontal", "reflected_first", [[2, 1, 1, 1, 1, 2], [1, 2, 1, 1, 2, 1], [1, 2, 2, 2, 2, 1]]),
        ("horizontal", "original_first", [[1, 1, 2, 2, 1, 1], [1, 2, 1, 1, 2, 1], [2, 2, 1, 1, 2, 2]]),
    ],
)
def test_each_setting_executes_its_distinct_expected_racket_transformation(prototype, oracle, axis, order, expected):
    grid = [[1, 1, 2], [1, 2, 1], [2, 2, 1]]
    before = copy.deepcopy(grid)
    result = oracle.label(prototype.program_for(prototype.Setting(axis, order)), grid)
    assert result == expected
    assert grid == before
    assert oracle.runtime_identity["backend"] == "racket"
    assert oracle.runtime_identity["protected"] is True


@pytest.mark.parametrize("axis", ["vertical", "horizontal"])
@pytest.mark.parametrize("order", ["reflected_first", "original_first"])
def test_complete_episodes_distinguish_every_parameter_rival_in_every_rotation(prototype, oracle, axis, order):
    setting = prototype.Setting(axis, order)
    episode = prototype.generate_episode(17, setting=setting, oracle=oracle)
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    assert episode["parameters"] == {"axis": axis, "order": order}
    assert episode["approval_status"] == "unapproved_prototype"
    for pair in episode["train"] + episode["test"]:
        prototype.validate_input(pair["input"], setting)
        assert len(pair["output"]) <= 30 and len(pair["output"][0]) <= 30
        assert pair["output"] == oracle.label(episode["program"], pair["input"])
    assert len(episode["test"][0]["input"]) > max(len(pair["input"]) for pair in episode["train"])
    report = prototype.score_episode(episode, prototype.programs(), setting.key, oracle=oracle)
    assert report["status"] == "no_ambiguity_found"
    assert report["parameters_identified"] is True
    assert report["production"]["parameters_identified"] is True
    assert len(report["rotations"]) == 4
    for score in [report["production"], *report["rotations"]]:
        assert score["status"] == "no_ambiguity_found"
        assert score["parameters_identified"] is True
        assert len(score["rivals"]) == 3
        assert all(row["status"] == "refuted_by_demonstrations" for row in score["rivals"].values())


def test_seed_replay_is_local_and_sampling_selects_one_episode_setting(prototype, oracle):
    first = prototype.generate_episode(19, oracle=oracle)
    prototype.generate_episode(99, setting=prototype.ALL_SETTINGS[-1], oracle=oracle)
    assert prototype.generate_episode(19, oracle=oracle) == first
    assert first["parameters"] == {"axis": "vertical", "order": "reflected_first"}
    chosen = [prototype.sample_setting(seed) for seed in range(64)]
    assert set(chosen) == set(prototype.ALL_SETTINGS)
    assert chosen == [prototype.sample_setting(seed) for seed in range(64)]
    setting = prototype.sample_setting(73)
    episode = prototype.generate_episode(73, setting=setting, oracle=oracle)
    assert episode["program"] == prototype.program_for(setting)
    assert all(pair["output"] == oracle.label(episode["program"], pair["input"]) for pair in episode["train"] + episode["test"])


def test_public_challenge_is_a_deep_copy_with_no_hidden_fields(prototype, oracle):
    episode = prototype.generate_episode(7, oracle=oracle)
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert public["train"] == episode["train"]
    assert public["test"][0]["input"] == episode["test"][0]["input"]
    public["train"][0]["input"][0][0] = -1
    assert episode["train"][0]["input"][0][0] >= 0


@pytest.mark.parametrize("axis", ["vertical", "horizontal"])
def test_symmetric_demos_with_an_asymmetric_query_are_rejected_as_ambiguous(prototype, oracle, axis):
    fixture = prototype.ambiguity_fixture(axis, oracle=oracle)
    episode, report = fixture["episode"], fixture["audit"]
    rival_key = prototype.Setting(axis, "original_first").key
    rival = report["production"]["rivals"][rival_key]
    assert report["status"] == "ambiguous"
    assert report["production"]["status"] == "ambiguous"
    assert report["parameters_identified"] is False
    assert rival["demo_fit"] is True
    assert rival["status"] == "ambiguous_query"
    assert rival["query_differences"][0]["expected"] == episode["test"][0]["output"]
    assert rival["query_differences"][0]["prediction"] != episode["test"][0]["output"]
    assert sum(row["status"] == "ambiguous" for row in report["rotations"]) == 1


def test_a_rival_agreeing_on_all_answers_is_reported_without_false_ambiguity(prototype, oracle):
    grid = [[1, 2, 1], [2, 1, 2], [1, 2, 1]]
    selected = prototype.DEFAULT
    pair = {"input": grid, "output": oracle.label(prototype.program_for(selected), grid)}
    episode = {"train": [copy.deepcopy(pair)], "test": [copy.deepcopy(pair)]}
    report = prototype.score_episode(episode, prototype.programs(), selected.key, oracle=oracle)
    assert report["status"] == "no_ambiguity_found"
    assert report["parameters_identified"] is False
    assert report["production"]["rivals"]["vertical__original_first"]["status"] == "survived_all"


def test_incorrect_supplied_labels_and_unexecutable_rivals_fail_closed(prototype, oracle):
    episode = prototype.generate_episode(5, oracle=oracle)
    corrupt = copy.deepcopy(episode)
    corrupt["test"][0]["output"][0][0] = (corrupt["test"][0]["output"][0][0] + 1) % 10
    report = prototype.score_episode(corrupt, prototype.programs(), prototype.DEFAULT.key, oracle=oracle)
    assert report["status"] == "error"
    assert report["reference_labels_match"] is False
    candidates = {**prototype.programs(), "broken": "(rule! (does-not-exist g))"}
    report = prototype.score_episode(episode, candidates, prototype.DEFAULT.key, oracle=oracle)
    assert report["status"] == "error"
    assert report["production"]["rivals"]["broken"]["status"] == "execution_error"


@pytest.mark.parametrize("axis", ["vertical", "horizontal"])
@pytest.mark.parametrize("order", ["reflected_first", "original_first"])
def test_setting_specific_maximum_input_boundary_keeps_output_within_thirty(prototype, oracle, axis, order):
    setting = prototype.Setting(axis, order)
    height, width = ((15, 30) if axis == "vertical" else (30, 15))
    grid = prototype.draw_input(101, 8, height, width, palette_size=4)
    prototype.validate_input(grid, setting)
    output = oracle.label(prototype.program_for(setting), grid)
    assert (len(output), len(output[0])) == (30, 30)
    invalid = [[1] * (width + (axis == "horizontal")) for _ in range(height + (axis == "vertical"))]
    with pytest.raises(ValueError, match="dimensions"):
        prototype.validate_input(invalid, setting)


@pytest.mark.parametrize("axis,order", [("diagonal", "reflected_first"), ("vertical", "middle"), (True, "original_first")])
def test_invalid_parameter_values_are_rejected(prototype, axis, order):
    with pytest.raises((ValueError, TypeError)):
        prototype.Setting(axis, order)


@pytest.mark.parametrize("seed", [True, 1.0, "17", None])
def test_noninteger_seeds_are_rejected(prototype, seed):
    with pytest.raises(TypeError):
        prototype.sample_setting(seed)


def test_evidence_bundle_replays_exact_programs_and_keeps_public_files_clean(prototype, tmp_path):
    destination = tmp_path / "evidence"
    report = prototype.materialize_evidence(destination, seeds=[23])
    assert report["status"] == "pass"
    assert "json_hash_algorithm" in report
    assert report["summary"]["episode_count"] == 4
    assert report["summary"]["rotation_count"] == 16
    assert report["summary"]["ambiguous_episodes"] == 0
    assert report["summary"]["diagnostic_ambiguity_fixtures_detected"] == 2
    for item in report["episodes"]:
        public_path = destination / item["public_path"]
        private_path = destination / item["private_path"]
        public = json.loads(public_path.read_text())
        private = json.loads(private_path.read_text())
        assert item["file_sha256"]["public"] == hashlib.sha256(public_path.read_bytes()).hexdigest()
        assert item["file_sha256"]["episode"] == hashlib.sha256(private_path.read_bytes()).hexdigest()
        assert item["file_sha256"]["audit"] == hashlib.sha256((destination / item["audit_path"]).read_bytes()).hexdigest()
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert hashlib.sha256(private["program"].encode()).hexdigest() == private["program_sha256"]
        assert public == prototype.public_challenge(private)
    for item in report["diagnostics"]:
        assert item["file_sha256"] == hashlib.sha256((destination / item["path"]).read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):
        prototype.materialize_evidence(destination, seeds=[23])
