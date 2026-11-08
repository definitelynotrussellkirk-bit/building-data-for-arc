from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


TASK_ID = "e1516c24afbd"


def _load_prototype():
    root = find_root(__file__)
    path = root / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
    assert path.is_file(), f"missing proposed parametric prototype: {path}"
    spec = importlib.util.spec_from_file_location(f"{TASK_ID}_parametric_prototype", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_source() -> str:
    for line in canonical_path(find_root(__file__)).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical source not found")


def test_default_setting_materializes_the_exact_canonical_racket_source():
    proto = _load_prototype()
    canonical = _canonical_source()
    assert proto.DEFAULT_TARGET_STATE == "00"
    assert proto.DEFAULT_OUTPUT_COLOR == 2
    assert proto.materialize_rule() == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == proto.CANONICAL_SHA256


def test_four_settings_are_distinct_and_seed_selection_covers_each_once():
    proto = _load_prototype()
    expected = {
        (state, color)
        for state in proto.ALLOWED_TARGET_STATES
        for color in proto.ALLOWED_OUTPUT_COLORS
    }
    selected = {
        (params["target_state"], params["output_color"])
        for params in (proto.parameters_for_seed(seed) for seed in range(4))
    }
    assert selected == expected
    sources = {
        proto.materialize_rule(state, color)
        for state, color in expected
    }
    assert len(sources) == len(expected)


@pytest.mark.parametrize("seed", range(4))
def test_each_episode_is_constant_public_safe_and_refutes_all_declared_parameter_rivals(seed):
    proto = _load_prototype()
    episode = proto.build_episode(seed)
    assert proto.episode_errors(episode) == []
    assert episode["parameter"] == proto.parameters_for_seed(seed)

    selected = (
        episode["parameter"]["target_state"],
        episode["parameter"]["output_color"],
    )
    alternatives = [setting for setting in proto.SETTINGS if setting != selected]
    for pair in episode["train"]:
        assert pair["output"] == proto.apply_python(pair["input"], *selected)
        assert all(
            proto.apply_python(pair["input"], *alternative) != pair["output"]
            for alternative in alternatives
        )

    public = proto.public_challenge(episode)
    assert "parameter" not in public
    assert "program" not in public
    assert all("output" not in pair for pair in public["test"])


@pytest.mark.parametrize(
    ("target_state", "output_color"),
    [("01", 2), ("00", 1), (None, 2), ("00", True)],
)
def test_invalid_parameter_values_fail_closed(target_state, output_color):
    proto = _load_prototype()
    with pytest.raises((TypeError, ValueError)):
        proto.materialize_rule(target_state, output_color)
