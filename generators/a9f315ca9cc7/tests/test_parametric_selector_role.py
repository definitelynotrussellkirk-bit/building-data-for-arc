"""Focused tests for the isolated self-tile selector-role prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

HERE = Path(__file__).resolve().parent
TASK_DIR = HERE.parent
PROTOTYPE_PATH = TASK_DIR / "workspace" / "parametric" / "prototype.py"
ROOT = find_root(__file__)


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "a9f315ca9cc7_parametric_selector_role", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


def _canonical_program() -> str:
    found = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("task_id") == "a9f315ca9cc7":
            found.append(record["program_solution"])
    assert len(found) == 1
    return found[0]


def test_parameter_contract_and_selection_are_strict_and_deterministic(prototype):
    assert prototype.PARAMETER_NAME == "selector_role"
    assert prototype.ALLOWED_SETTINGS == ("foreground", "background")
    assert prototype.DEFAULT_SETTING == "foreground"
    assert prototype.choose_setting(17) == prototype.choose_setting(17)
    with pytest.raises(TypeError):
        prototype.choose_setting(True)
    with pytest.raises(TypeError):
        prototype.program_for(0)
    with pytest.raises(ValueError):
        prototype.program_for("both")


def test_default_program_is_exact_canonical_authority(prototype):
    assert prototype.program_for("foreground") == _canonical_program()
    assert prototype.program_for("background") != _canonical_program()
    assert "self-tile" in prototype.program_for("background")
    assert "(= v 0)" in prototype.program_for("background")


def test_default_python_reference_matches_every_labelled_canonical_pair(prototype):
    for pair in canonical_pairs(
        prototype.TASK_ID, root=ROOT, labeled_only=True
    ):
        assert prototype.apply_python(pair["input"], "foreground") == pair["output"]


def test_each_episode_uses_one_setting_and_teaches_the_alternative(prototype):
    for setting in prototype.ALLOWED_SETTINGS:
        episode = prototype.build_episode(20261022, setting=setting)
        assert episode["meta"][prototype.PARAMETER_NAME] == setting
        selected = [
            pair["output"] for pair in episode["train"] + episode["test"]
        ]
        rival = next(value for value in prototype.ALLOWED_SETTINGS if value != setting)
        rival_outputs = [
            prototype.apply_python(pair["input"], rival)
            for pair in episode["train"] + episode["test"]
        ]
        assert all(left != right for left, right in zip(selected, rival_outputs))
        assert any(
            pair["output"] != prototype.apply_python(pair["input"], rival)
            for pair in episode["train"]
        )

        public = prototype.public_challenge(episode)
        assert all("output" in pair for pair in public["train"])
        assert all("output" not in pair for pair in public["test"])
        serialized = json.dumps(public, sort_keys=True)
        assert prototype.PARAMETER_NAME not in serialized
        assert "rule!" not in serialized
