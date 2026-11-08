"""Focused tests for the proposed missing-extension rule parameter."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import find_root

TASK = "b88894a36787"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK
PROTOTYPE = HOME / "workspace" / "parametric" / "missing_extension.py"


def _load_prototype():
    assert PROTOTYPE.exists(), "missing_extension.py prototype has not been built"
    spec = importlib.util.spec_from_file_location("parametric_missing_extension", PROTOTYPE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    with (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row["program_solution"]
    raise AssertionError("canonical program not found")


def test_setting_and_seed_validation_are_strict_and_episode_scoped():
    prototype = _load_prototype()
    for bad in (True, False, 2.5, "2", None):
        with pytest.raises(TypeError):
            prototype.choose_missing_extension(bad)
    with pytest.raises(ValueError):
        prototype.program_for("past_bottom")
    for seed in range(32):
        selected = prototype.choose_missing_extension(seed)
        assert selected in prototype.ALLOWED_MISSING_EXTENSIONS
        assert prototype.choose_missing_extension(seed) == selected


def test_default_program_is_exact_canonical_and_alternative_is_one_bounded_change():
    prototype = _load_prototype()
    canonical = _canonical_program()
    bottom = prototype.program_for("bottom")
    penultimate = prototype.program_for("penultimate")
    assert prototype.DEFAULT_MISSING_EXTENSION == "bottom"
    assert bottom == canonical
    assert penultimate == canonical.replace(
        "(if dot (first dot) (- h 1))",
        "(if dot (first dot) (- h 2))",
        1,
    )
    assert bottom != penultimate
    assert prototype.program_sha256("bottom") != prototype.program_sha256("penultimate")


def test_complete_episodes_fix_one_setting_and_refute_the_other_setting():
    prototype = _load_prototype()
    generator = prototype._load_generator()
    for setting in prototype.ALLOWED_MISSING_EXTENSIONS:
        episode = prototype.build_episode(47, missing_extension=setting)
        assert episode["meta"]["missing_extension"] == setting
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert prototype.parameter_rival_findings(episode) == []
        for pair in episode["train"] + episode["test"]:
            grid = pair["input"]
            assert generator.self_check(grid) == []
            assert sum(entry[3] is None for entry in generator._entries(grid)) == 1
            assert pair["output"] == prototype.apply_python(grid, setting)
            rival = next(value for value in prototype.ALLOWED_MISSING_EXTENSIONS
                         if value != setting)
            assert prototype.apply_python(grid, rival) != pair["output"]


def test_default_python_mirror_preserves_canonical_behavior():
    prototype = _load_prototype()
    generator = prototype._load_generator()
    for grid in prototype._episode_inputs(91):
        assert prototype.apply_python(grid, "bottom") == generator._prediction(grid)


def test_public_challenge_hides_parameter_program_and_query_answer():
    prototype = _load_prototype()
    episode = prototype.build_episode(19, missing_extension="penultimate")
    public = prototype.public_challenge(episode)
    assert "meta" not in public
    assert "program" not in public
    assert all("output" in pair for pair in public["train"])
    assert public["test"] == [{"input": episode["test"][0]["input"]}]
