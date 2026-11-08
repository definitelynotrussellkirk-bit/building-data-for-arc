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
spec = importlib.util.spec_from_file_location(
    "parametric_196d5de2ea8c", MODULE_PATH
)
assert spec is not None and spec.loader is not None
proto = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = proto
spec.loader.exec_module(proto)


def _witness_grid() -> list[list[int]]:
    # Uniform divider row/column are index 3.  The canonical regional mode is 2;
    # including row/column zero changes the top-left mode to 8.
    return [
        [8, 8, 8, 5, 6, 7, 6],
        [8, 2, 2, 5, 3, 3, 4],
        [8, 2, 9, 5, 3, 4, 3],
        [5, 5, 5, 5, 5, 5, 5],
        [8, 1, 1, 5, 7, 7, 6],
        [8, 1, 0, 5, 7, 6, 7],
        [8, 0, 1, 5, 6, 7, 7],
    ]


def test_parameter_choice_is_deterministic_and_covers_both_settings() -> None:
    assert proto.choose_parameters(17) == proto.choose_parameters(17)
    observed = {
        proto.choose_parameters(seed)[proto.PARAMETER_NAME]
        for seed in range(64)
    }
    assert observed == set(proto.ALLOWED_BORDER_POLICIES)


def test_default_python_mirror_preserves_canonical_border_exclusion() -> None:
    grid = _witness_grid()
    canonical = proto.python_reference(
        grid, border_policy=proto.DEFAULT_BORDER_POLICY
    )
    alternative = proto.python_reference(grid, border_policy="include_outer")
    assert canonical == [[2, 5, 3], [5, 5, 5], [1, 5, 7]]
    assert alternative == [[8, 5, 3], [5, 5, 5], [1, 5, 7]]
    assert canonical != alternative


def test_materialized_rules_change_only_declared_region_starts() -> None:
    canonical = proto.CANONICAL_SOURCE_FIXTURE
    default = proto.materialize_rule(
        proto.DEFAULT_BORDER_POLICY, source=canonical
    )
    alternative = proto.materialize_rule("include_outer", source=canonical)
    assert default == canonical
    assert proto.CANONICAL_TL_CLAUSE in default
    assert proto.ALTERNATIVE_TL_CLAUSE in alternative
    assert proto.ALTERNATIVE_TR_CLAUSE in alternative
    assert proto.ALTERNATIVE_BL_CLAUSE in alternative
    assert proto.restore_canonical(alternative) == canonical


@pytest.mark.parametrize("bad", [True, 1.0, "1", -1])
def test_episode_seed_requires_nonnegative_literal_integer(bad) -> None:
    with pytest.raises((TypeError, ValueError)):
        proto.choose_parameters(bad)


def test_public_challenge_omits_hidden_parameter_source_and_query_answer() -> None:
    grid = _witness_grid()
    episode = {
        "demos": [{"input": grid, "output": grid}],
        "query": {"input": grid, "output": grid},
    }
    challenge = proto.public_challenge(episode)
    assert set(challenge) == {"schema", "task_id", "train", "test"}
    assert challenge["test"] == [{"input": grid}]
    serialized = repr(challenge)
    assert proto.PARAMETER_NAME not in serialized
    assert "racket" not in serialized.lower()
