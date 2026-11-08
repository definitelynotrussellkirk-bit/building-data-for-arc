"""Contract tests for the proposed segment-owner rule parameter."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


TASK_ID = "964b23808a3c"
ROOT = find_root(__file__)


def _load_prototype():
    path = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
    assert path.is_file(), f"missing proposed parametric prototype: {path}"
    spec = importlib.util.spec_from_file_location(
        f"{TASK_ID}_segment_owner_prototype", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_source() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical source not found")


def test_default_setting_materializes_the_exact_canonical_racket_source():
    proto = _load_prototype()
    canonical = _canonical_source()
    assert proto.DEFAULT_SEGMENT_OWNER == "lower"
    assert proto.ALLOWED_SEGMENT_OWNERS == ("lower", "upper")
    assert proto.materialize_rule() == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == proto.CANONICAL_SOURCE_SHA256
    assert proto.CANONICAL_RULE_HASH == "c7e69da25375"


def test_two_settings_are_distinct_and_seed_selection_covers_both():
    proto = _load_prototype()
    selected = {
        proto.parameters_for_seed(seed)["segment_owner"] for seed in range(2)
    }
    assert selected == set(proto.ALLOWED_SEGMENT_OWNERS)
    sources = {
        proto.materialize_rule(owner) for owner in proto.ALLOWED_SEGMENT_OWNERS
    }
    assert len(sources) == 2


def test_segment_owner_changes_gap_cells_without_changing_marker_roles():
    proto = _load_prototype()
    grid = [
        [0, 0, 0],
        [0, 2, 0],
        [0, 0, 0],
        [0, 0, 0],
        [0, 5, 0],
        [0, 0, 0],
    ]
    lower = proto.apply_python(grid, "lower")
    upper = proto.apply_python(grid, "upper")
    assert lower != upper
    assert lower[2][1] == lower[3][1] == 5
    assert upper[2][1] == upper[3][1] == 2
    assert lower[1][1] == upper[1][1] == 2
    assert lower[4][1] == upper[4][1] == 5
    assert lower[5][1] == upper[5][1] == 0


@pytest.mark.parametrize("seed", range(2))
def test_each_episode_selects_once_refutes_the_other_setting_and_is_public_safe(seed):
    proto = _load_prototype()
    episode = proto.build_episode(seed, root=ROOT)
    assert proto.episode_errors(episode) == []
    owner = episode["parameters"]["segment_owner"]
    assert owner == proto.parameters_for_seed(seed)["segment_owner"]
    assert episode["parameter_selected_once"] is True
    assert episode["input_constraints_depend_on_parameter"] is False

    rival = next(value for value in proto.ALLOWED_SEGMENT_OWNERS if value != owner)
    for pair in episode["train"]:
        assert pair["output"] == proto.apply_python(pair["input"], owner)
        assert pair["output"] != proto.apply_python(pair["input"], rival)
    for pair in episode["test"]:
        assert pair["output"] == proto.apply_python(pair["input"], owner)
        assert pair["output"] != proto.apply_python(pair["input"], rival)

    public = proto.public_challenge(episode)
    assert "parameters" not in public
    assert "program" not in public
    assert "parameter_rivals" not in public
    assert all("output" not in pair for pair in public["test"])


@pytest.mark.parametrize("bad_owner", ["previous", "", 1, True, None])
def test_invalid_parameter_values_fail_closed(bad_owner):
    proto = _load_prototype()
    with pytest.raises((TypeError, ValueError), match="segment_owner"):
        proto.materialize_rule(bad_owner)
    with pytest.raises((TypeError, ValueError), match="segment_owner"):
        proto.apply_python([[0, 5]], bad_owner)


@pytest.mark.parametrize("bad_seed", [True, 1.0, "1", None, -1])
def test_invalid_episode_seed_fails_closed(bad_seed):
    proto = _load_prototype()
    with pytest.raises((TypeError, ValueError), match="seed"):
        proto.parameters_for_seed(bad_seed)
