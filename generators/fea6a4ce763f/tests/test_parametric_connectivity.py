"""Focused tests for the isolated connectivity-rule prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "workspace"
    / "parametric"
    / "prototype.py"
)


def _load():
    assert MODULE_PATH.is_file(), "parametric connectivity prototype is missing"
    spec = importlib.util.spec_from_file_location(
        "fea6a4ce763f_parametric_connectivity", MODULE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parameter_choice_is_episode_deterministic_and_covers_both_settings():
    proto = _load()
    assert proto.choose_parameters(17) == proto.choose_parameters(17)
    observed = {
        proto.choose_parameters(seed)[proto.PARAMETER_NAME]
        for seed in range(64)
    }
    assert observed == set(proto.ALLOWED_CONNECTIVITY)


def test_default_racket_text_is_exact_canonical_program():
    proto = _load()
    assert proto.racket_program({proto.PARAMETER_NAME: "four"}) == (
        "(rule! extract-largest)"
    )
    assert proto.racket_callable({proto.PARAMETER_NAME: "four"}) == (
        "extract-largest"
    )
    alternate = proto.racket_program({proto.PARAMETER_NAME: "eight"})
    assert "objects-8" in alternate
    assert "argmax obj-size" in alternate
    assert "crop-object" in alternate
    assert proto.racket_callable({proto.PARAMETER_NAME: "eight"}).startswith(
        "(lambda (g)"
    )


@pytest.mark.parametrize("seed", [0, 1, 2, 17, 99])
def test_every_constructed_pair_distinguishes_connectivity(seed):
    proto = _load()
    for index in range(4):
        grid = proto.make_input(seed, index)
        four = proto.python_reference(grid, connectivity="four")
        eight = proto.python_reference(grid, connectivity="eight")
        assert four != eight
        assert proto.domain_errors(grid, connectivity="four") == []
        assert proto.domain_errors(grid, connectivity="eight") == []


def test_public_challenge_omits_hidden_setting_program_seed_and_query_answer():
    proto = _load()
    grid = proto.make_input(7, 0)
    episode = {
        "seed": 7,
        "parameters": {proto.PARAMETER_NAME: "eight"},
        "racket_program": proto.racket_program({proto.PARAMETER_NAME: "eight"}),
        "demos": [{"input": grid, "output": grid}],
        "query": {"input": grid, "output": grid},
    }
    challenge = proto.public_challenge(episode)
    assert set(challenge) == {"schema", "task_id", "demos", "query"}
    assert challenge["query"] == {"input": grid}
    serialized = repr(challenge).lower()
    assert "connectivity" not in serialized
    assert "racket" not in serialized
    assert "seed" not in serialized


def test_materialized_racket_programs_execute_like_python_mirror():
    proto = _load()
    from arc_repl.racket_bridge import RacketBridge

    grid = proto.make_input(123, 2)
    with RacketBridge(timeout=20, max_calls_before_restart=16) as bridge:
        bridge.define_grid("g", grid)
        for setting in proto.ALLOWED_CONNECTIVITY:
            callable_source = proto.racket_callable(
                {proto.PARAMETER_NAME: setting}
            )
            actual = bridge.eval_text(f"({callable_source} g)")
            assert actual == proto.python_reference(grid, connectivity=setting)
