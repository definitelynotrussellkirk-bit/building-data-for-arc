"""Portable focused tests for the PROPOSED parametric prototype only.

These do not test or import the selected production generator. The five labeled
canonical pairs are authoring data, used only after the separate blind solve.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import canonical_pairs, canonical_path, find_root

ROOT = find_root(__file__)
PROTOTYPE = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location("tile75_parametric_prototype", PROTOTYPE)
assert SPEC and SPEC.loader
proto = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(proto)


@pytest.fixture(scope="module")
def bridge():
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip("Optional Racket runtime unavailable: " + status["reason"])
    with RacketBridge(timeout=10.0, startup_timeout=30.0) as active:
        yield active


@pytest.fixture(scope="module")
def episodes(bridge):
    return [proto.build_episode(seed, bridge) for seed in range(6)]


def test_seed_schedule_inputs_and_parameter_bounds():
    assert proto.DEFAULT_PARAMETERS == ("mirror", 2)
    assert proto.choose_parameters(proto.DEFAULT_SEED) == proto.DEFAULT_PARAMETERS
    assert {proto.choose_parameters(seed) for seed in range(6)} == set(proto.SETTINGS)
    assert len({proto.program_for(*setting) for setting in proto.SETTINGS}) == 6
    for invalid in (-1, True, 2.0, "2"):
        with pytest.raises(ValueError):
            proto.choose_parameters(invalid)
    for first, pairs in (("vertical", 2), ("mirror", 0), ("input", 4), ("mirror", True)):
        with pytest.raises(ValueError):
            proto.program_for(first, pairs)
    for seed in (0, 1, 5, 6, 17):
        inputs = proto.episode_inputs(seed)
        assert inputs == proto.episode_inputs(seed)
        assert len(inputs) == 4
        assert len({json.dumps(grid) for grid in inputs}) == 4
        assert all(proto.validate_input(grid) == grid for grid in inputs)
    assert all(proto.episode_inputs(seed) == proto.episode_inputs(0) for seed in range(6))
    with pytest.raises(ValueError):
        proto.validate_input([[5, 7, 5], [7, 8, 7], [8, 5, 8]])


def test_every_setting_executes_one_complete_episode(episodes):
    for seed, episode in enumerate(episodes):
        setting = proto.choose_parameters(seed)
        assert episode["parameters"] == {"first_tile": setting[0], "tile_pairs": setting[1]}
        assert episode["program"] == proto.program_for(*setting)
        assert len(episode["train"]) == 3 and len(episode["test"]) == 1
        assert episode["seed"] == seed
        for pair in episode["train"] + episode["test"]:
            assert len(pair["output"]) == 3
            assert len(pair["output"][0]) == 6 * setting[1] <= 30
            assert {cell for row in pair["output"] for cell in row} == {5, 7, 8}


def test_each_demo_identifies_its_setting_among_all_six(episodes):
    # All six episode settings were run by the Racket fixture on shared inputs.
    for chosen in episodes:
        for rival in episodes:
            if chosen["parameters"] == rival["parameters"]:
                continue
            for index in range(3):
                assert chosen["train"][index]["input"] == rival["train"][index]["input"]
                assert chosen["train"][index]["output"] != rival["train"][index]["output"]
            assert chosen["test"][0]["output"] != rival["test"][0]["output"]


def test_original_program_and_execution_agree_with_all_canonical_pairs(bridge):
    program = proto.program_for(*proto.DEFAULT_PARAMETERS)
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        authority = [json.loads(line)["program_solution"] for line in stream
                     if line.strip() and json.loads(line).get("task_id") == proto.TASK_ID]
    assert authority == [program]
    pairs = canonical_pairs(proto.TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        assert proto.execute_program(bridge, program, pair["input"]) == pair["output"]


def test_public_challenges_omit_hidden_metadata_and_query_answers(episodes):
    for episode in episodes:
        public = proto.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert len(public["train"]) == 3 and len(public["test"]) == 1
        original_cell = episode["test"][0]["input"][0][0]
        public["test"][0]["input"][0][0] = 0
        assert episode["test"][0]["input"][0][0] == original_cell
