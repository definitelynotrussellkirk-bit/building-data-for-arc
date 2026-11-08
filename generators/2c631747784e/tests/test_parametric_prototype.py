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
spec = importlib.util.spec_from_file_location("parametric_2c631747784e", MODULE_PATH)
assert spec is not None and spec.loader is not None
proto = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = proto
spec.loader.exec_module(proto)


def _line_grid() -> list[list[int]]:
    return [
        [8, 8, 8, 8, 8, 8],
        [8, 1, 2, 3, 4, 8],
        [8, 8, 8, 8, 8, 8],
    ]


def test_parameter_choice_is_once_per_seed_and_covers_both_settings() -> None:
    assert proto.choose_parameters(17) == proto.choose_parameters(17)
    observed = {
        proto.choose_parameters(seed)[proto.PARAMETER_NAME]
        for seed in range(32)
    }
    assert observed == set(proto.ALLOWED_REVERSE_SHIFTS)
    with pytest.raises(TypeError):
        proto.choose_parameters(True)
    with pytest.raises(ValueError):
        proto.choose_parameters(-1)


def test_default_setting_is_exact_canonical_source() -> None:
    canonical = proto.canonical_rule_source()
    assert proto.instantiate_rule(0) == canonical
    assert proto.DEFAULT_REVERSE_SHIFT == 0


def test_alternative_changes_the_executed_transformation_not_the_input_grammar() -> None:
    grid = _line_grid()
    canonical = proto.python_reference(grid, reverse_shift=0)
    alternative = proto.python_reference(grid, reverse_shift=1)
    assert canonical == [
        [8, 8, 8, 8, 8, 8],
        [8, 4, 3, 2, 1, 8],
        [8, 8, 8, 8, 8, 8],
    ]
    assert alternative == [
        [8, 8, 8, 8, 8, 8],
        [8, 3, 2, 1, 4, 8],
        [8, 8, 8, 8, 8, 8],
    ]
    assert proto.instantiate_rule(1) != proto.instantiate_rule(0)


def test_invalid_parameter_values_fail_loudly() -> None:
    for value in (True, False, 0.0, 1.0, "0", -1, 2):
        with pytest.raises((TypeError, ValueError)):
            proto.instantiate_rule(value)


def test_public_challenge_omits_parameter_program_seed_and_query_answer() -> None:
    grid = _line_grid()
    episode = {
        "seed": 7,
        "parameters": {proto.PARAMETER_NAME: 1},
        "racket_program": "secret",
        "demos": [{"input": grid, "output": grid}],
        "query": {"input": grid, "output": grid},
    }
    challenge = proto.public_challenge(episode)
    assert challenge["query"] == {"input": grid}
    serialized = repr(challenge)
    assert proto.PARAMETER_NAME not in serialized
    assert "secret" not in serialized
    assert "seed" not in serialized
