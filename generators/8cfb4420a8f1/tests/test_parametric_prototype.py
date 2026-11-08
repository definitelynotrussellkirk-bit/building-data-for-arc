from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "workspace"
    / "parametric"
    / "prototype.py"
)
spec = importlib.util.spec_from_file_location("parametric_8cfb4420a8f1", MODULE_PATH)
assert spec is not None and spec.loader is not None
proto = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = proto
spec.loader.exec_module(proto)


def _grid() -> list[list[int]]:
    return [
        [0, 4, 0, 0],
        [4, 0, 2, 2],
        [0, 4, 0, 0],
    ]


def test_parameter_choice_is_deterministic_and_covers_both_settings() -> None:
    assert proto.choose_parameters(17) == proto.choose_parameters(17)
    observed = {proto.choose_parameters(seed)["erase_scope"] for seed in range(64)}
    assert observed == set(proto.ALLOWED_ERASE_SCOPES)


def test_default_setting_is_canonical_and_alternative_changes_top_marker() -> None:
    grid = _grid()
    canonical = proto.python_reference(grid, erase_scope=proto.DEFAULT_ERASE_SCOPE)
    alternative = proto.python_reference(grid, erase_scope="all_occurrences")
    assert canonical == [
        [0, 4, 0, 0],
        [0, 0, 2, 2],
        [0, 0, 0, 0],
    ]
    assert alternative == [
        [0, 0, 0, 0],
        [0, 0, 2, 2],
        [0, 0, 0, 0],
    ]


def test_public_challenge_omits_hidden_rule_and_query_answer() -> None:
    episode = {
        "demos": [{"input": _grid(), "output": _grid()}],
        "query": {"input": _grid(), "output": _grid()},
    }
    challenge = proto.public_challenge(episode)
    assert set(challenge) == {"schema", "task_id", "demos", "query"}
    assert challenge["query"] == {"input": _grid()}
    serialized = repr(challenge)
    assert "erase_scope" not in serialized
    assert "racket" not in serialized.lower()


def test_each_racket_setting_is_materialized_as_a_callable_program() -> None:
    for scope in proto.ALLOWED_ERASE_SCOPES:
        source = proto.racket_program({"erase_scope": scope})
        assert source.lstrip().startswith("(lambda (g)")
        assert "grid-from-fn" in source
