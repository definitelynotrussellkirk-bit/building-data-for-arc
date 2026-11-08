"""Prototype-only tests for the proposed nearby rule family.

These tests exercise files under ``workspace/parametric`` only.  They do not
change or approve the selected canonical Racket rule.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import shutil
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"
GENERATOR_PATH = HOME / "generator.py"


def _load_module(path: Path, name: str):
    assert path.is_file(), f"missing prototype file: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load_module(PROTOTYPE_PATH, "track_parametric_prototype")


def _generator():
    return _load_module(GENERATOR_PATH, "track_parent_generator")


def test_parameter_contract_has_canonical_default_and_episode_selection():
    prototype = _prototype()
    assert prototype.ALLOWED_WALL_OFFSETS == (1, 2)
    assert prototype.ALLOWED_LENGTH_MEASURES == ("cell_count", "track_span")
    assert prototype.DEFAULT_SETTING == prototype.RuleSetting(1, "cell_count")
    assert len(prototype.ALL_SETTINGS) == 4
    assert [prototype.choose_setting(seed) for seed in range(4)] == list(
        prototype.ALL_SETTINGS
    )
    with pytest.raises((TypeError, ValueError), match="seed"):
        prototype.choose_setting(True)


def test_canonical_default_matches_parent_rule_for_every_exact_profile():
    prototype = _prototype()
    generator = _generator()
    for index, profile in enumerate(generator.SCENE_PROFILES):
        grid = generator.generate(9100 + index, index, scene_profile=profile)
        assert prototype.python_transform(grid, prototype.DEFAULT_SETTING) == generator.rule_mirror(grid)


def test_complete_episodes_hold_one_setting_and_demos_refute_all_parameter_rivals():
    prototype = _prototype()
    for setting in prototype.ALL_SETTINGS:
        episode = prototype.build_episode(seed=17, setting=setting)
        assert episode["parameter"] == setting.as_dict()
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        for pair in episode["train"]:
            expected = prototype.python_transform(pair["input"], setting)
            assert pair["output"] == expected
            for rival in prototype.ALL_SETTINGS:
                if rival != setting:
                    assert prototype.python_transform(pair["input"], rival) != expected


def test_public_challenge_hides_hidden_setting_and_query_answer():
    prototype = _prototype()
    episode = prototype.build_episode(
        seed=23,
        setting=prototype.RuleSetting(2, "track_span"),
    )
    public = prototype.public_challenge(episode)
    assert "parameter" not in public
    assert all("output" in pair for pair in public["train"])
    assert public["test"] and all("output" not in pair for pair in public["test"])


def test_materialized_racket_programs_are_exact_and_unique():
    prototype = _prototype()
    hashes = set()
    for setting in prototype.ALL_SETTINGS:
        path = prototype.rule_path(setting)
        text = prototype.racket_program(setting)
        assert path.is_file()
        assert path.read_text() == text
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        assert prototype.racket_sha256(setting) == digest
        hashes.add(digest)
    assert len(hashes) == len(prototype.ALL_SETTINGS)
    canonical = prototype.racket_program(prototype.DEFAULT_SETTING)
    assert "(define OUTPUT-WALL-OFFSET 1)" in canonical
    assert "(define LENGTH-MEASURE 'cell-count)" in canonical


@pytest.mark.skipif(shutil.which("racket") is None, reason="Racket runtime unavailable")
def test_racket_evidence_matches_labels_and_all_declared_rivals_are_distinguished():
    prototype = _prototype()
    evidence = prototype.build_evidence(seed=17)
    assert evidence["status"] == "prototype"
    assert evidence["canonical_default_replay"]["all_match"] is True
    assert evidence["canonical_default_replay"]["matched"] == evidence["canonical_default_replay"]["total"]
    assert len(evidence["settings"]) == 4
    assert all(item["all_pairs_match_racket"] for item in evidence["settings"].values())
    assert all(item["every_demo_refutes_all_rivals"] for item in evidence["settings"].values())
