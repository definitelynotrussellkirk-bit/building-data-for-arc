"""Focused tests for the isolated ef02aedbac38 selector-role prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root

HERE = Path(__file__).resolve().parent
TASK_DIR = HERE.parent
PROTOTYPE_PATH = TASK_DIR / "workspace" / "parametric" / "prototype.py"
ROOT = find_root(__file__)


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "ef02aedbac38_parametric_selector_role", PROTOTYPE_PATH
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
        if record.get("task_id") == "ef02aedbac38":
            found.append(record["program_solution"])
    assert len(found) == 1
    return found[0]


def test_parameter_contract_is_strict_and_seeded_once(prototype):
    assert prototype.PARAMETER_NAME == "selector_role"
    assert prototype.ALLOWED_SETTINGS == ("five", "companion")
    assert prototype.DEFAULT_SETTING == "five"
    assert prototype.choose_setting(0) == "five"
    assert prototype.choose_setting(1) == "companion"
    assert prototype.choose_setting(17) == prototype.choose_setting(17)
    with pytest.raises(TypeError):
        prototype.choose_setting(True)
    with pytest.raises(TypeError):
        prototype.program_for(0)
    with pytest.raises(ValueError):
        prototype.program_for("both")


def test_default_program_is_exact_canonical_authority(prototype):
    canonical = _canonical_program()
    assert prototype.program_for("five") == canonical
    alternative = prototype.program_for("companion")
    assert alternative != canonical
    assert "(!= v 5)" in alternative
    assert "(if (!= v 5) 5 0)" in alternative


def test_default_python_reference_matches_every_labelled_canonical_pair(prototype):
    for pair in canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True):
        assert prototype.apply_python(pair["input"], "five") == pair["output"]


def test_default_complete_program_executes_to_canonical_label(prototype):
    pair = canonical_pairs(prototype.TASK_ID, root=ROOT, labeled_only=True)[0]
    with RacketBridge() as bridge:
        actual = prototype.execute_racket(
            bridge, prototype.program_for("five"), pair["input"]
        )
    assert actual == pair["output"]


def test_companion_setting_selects_the_opposite_role(prototype):
    grid = [[5, 2, 5], [2, 5, 2], [5, 2, 5]]
    assert prototype.apply_python(grid, "five") == [
        [2, 0, 2],
        [0, 2, 0],
        [2, 0, 2],
    ]
    assert prototype.apply_python(grid, "companion") == [
        [0, 5, 0],
        [5, 0, 5],
        [0, 5, 0],
    ]


def test_each_episode_uses_one_setting_and_teaches_the_declared_rival(prototype):
    for setting in prototype.ALLOWED_SETTINGS:
        episode = prototype.build_episode(20261022, setting=setting)
        assert episode["meta"][prototype.PARAMETER_NAME] == setting
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        inputs = [
            json.dumps(pair["input"], sort_keys=True)
            for pair in episode["train"] + episode["test"]
        ]
        assert len(set(inputs)) == 7
        rival = next(value for value in prototype.ALLOWED_SETTINGS if value != setting)
        pairs = episode["train"] + episode["test"]
        assert all(
            pair["output"] != prototype.apply_python(pair["input"], rival)
            for pair in pairs
        )
        public = prototype.public_challenge(episode)
        assert all("output" in pair for pair in public["train"])
        assert all("output" not in pair for pair in public["test"])
        serialized = json.dumps(public, sort_keys=True)
        assert prototype.PARAMETER_NAME not in serialized
        assert "rule!" not in serialized
        assert "program" not in serialized
