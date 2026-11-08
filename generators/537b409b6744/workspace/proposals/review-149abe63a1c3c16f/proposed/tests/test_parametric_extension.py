"""Focused contract for the task-local candidate-selection prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HERE / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert PROTOTYPE_PATH.is_file()
    spec = importlib.util.spec_from_file_location("selection_parametric_prototype", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_canonical_default_program():
    prototype = load_prototype()
    assert prototype.SETTINGS == ("nearest", "farthest")
    assert prototype.DEFAULT_SETTING == "nearest"
    assert prototype.PARAMETER_SPEC["name"] == "candidate_selection"
    assert prototype.PARAMETER_SPEC["canonical_default"] == "nearest"
    assert prototype.program_for("nearest") == prototype.canonical_program()
    assert prototype.program_for("farthest") != prototype.program_for("nearest")
    with pytest.raises(ValueError):
        prototype.program_for("middle")


def test_episode_parameter_is_deterministic_and_chosen_once():
    prototype = load_prototype()
    chosen = [prototype.choose_setting(seed) for seed in range(32)]
    assert chosen == [prototype.choose_setting(seed) for seed in range(32)]
    assert set(chosen) == set(prototype.SETTINGS)
    for seed in range(8):
        episode = prototype.build_episode(seed)
        assert episode["private"]["candidate_selection"] == prototype.choose_setting(seed)
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1


def test_materialized_evidence_uses_racket_and_hides_private_query_data(tmp_path):
    prototype = load_prototype()
    manifest = prototype.materialize(seed=19073, out_dir=tmp_path)
    assert manifest["status"] == "proposed_unapproved"
    assert manifest["parameter"]["chosen_once_per_episode"] is True
    assert manifest["default_program_exactly_canonical"] is True
    assert manifest["counts"]["episodes"] == 2
    assert manifest["counts"]["racket_executions"] == 16
    assert manifest["counts"]["distinguishing_train_pairs"] == 6
    assert {row["selected_setting"] for row in manifest["episodes"]} == {
        "nearest",
        "farthest",
    }

    public_paths = sorted((tmp_path / "public").glob("episode-*.json"))
    private_paths = sorted((tmp_path / "private").glob("episode-*.json"))
    assert len(public_paths) == len(private_paths) == 2
    for path in public_paths:
        public = json.loads(path.read_text())
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert "private" not in public
        text = path.read_text()
        assert "candidate_selection" not in text
        assert "program" not in text

    for setting in prototype.SETTINGS:
        source = (tmp_path / "rules" / f"{setting}.rkt").read_text()
        assert source == prototype.program_for(setting)
