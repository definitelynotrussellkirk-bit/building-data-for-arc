"""Focused tests for the task-local waypoint-choice prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators/40ad7195c775/workspace/parametric/prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.exists(), "waypoint-choice prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("waypoint_choice_prototype", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program(task_id):
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row["program_solution"]
    raise AssertionError("canonical task missing")


def test_parameter_is_bounded_and_default_program_is_exact_canonical_authority():
    prototype = _load_prototype()
    assert prototype.ALLOWED_WAYPOINT_CHOICES == ("left", "middle", "right")
    assert prototype.DEFAULT_WAYPOINT_CHOICE == "middle"
    assert prototype.program_for("middle") == _canonical_program(prototype.TASK_ID)
    assert prototype.program_for("left") != prototype.program_for("middle")
    assert prototype.program_for("right") != prototype.program_for("middle")
    with pytest.raises(ValueError):
        prototype.program_for("nearest")
    with pytest.raises(ValueError):
        prototype.program_for(True)


def test_waypoint_choice_changes_the_executed_route_not_the_input():
    prototype = _load_prototype()
    grid = prototype.build_inputs(seed=20261021, count=1)[0]
    frozen = [row[:] for row in grid]
    outputs = {
        choice: prototype.apply_python(grid, choice)
        for choice in prototype.ALLOWED_WAYPOINT_CHOICES
    }
    assert len({json.dumps(output) for output in outputs.values()}) == 3
    assert grid == frozen


def test_episode_parameter_is_chosen_once_and_every_demo_distinguishes_settings():
    prototype = _load_prototype()
    observed = set()
    for seed in (0, 1, 2):
        episode = prototype.build_episode(seed, n_train=3, n_test=1)
        selected = episode["private"]["waypoint_choice"]
        observed.add(selected)
        assert selected in prototype.ALLOWED_WAYPOINT_CHOICES
        for pair in episode["train"] + episode["test"]:
            candidates = {
                choice: prototype.apply_python(pair["input"], choice)
                for choice in prototype.ALLOWED_WAYPOINT_CHOICES
            }
            assert pair["output"] == candidates[selected]
            assert len({json.dumps(output) for output in candidates.values()}) == 3
    assert observed == set(prototype.ALLOWED_WAYPOINT_CHOICES)


def test_public_challenge_omits_parameter_program_and_query_answer():
    prototype = _load_prototype()
    public = prototype.public_challenge(prototype.build_episode(1, n_train=3, n_test=1))
    blob = json.dumps(public, sort_keys=True)
    assert "waypoint_choice" not in blob
    assert "program" not in blob
    assert all("output" in pair for pair in public["train"])
    assert all("output" not in pair for pair in public["test"])


def test_commented_canonical_rule_wrapper_is_callable():
    prototype = _load_prototype()
    source = prototype.program_for("middle")
    assert source.lstrip().startswith("(rule!")
    assert ";;" in source.split("(lambda", 1)[0]
    body = prototype._racket_callable(source)
    assert "(lambda" in body
    assert prototype._application(source, prototype.build_inputs(seed=0, count=1)[0])
