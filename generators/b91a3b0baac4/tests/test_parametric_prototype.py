"""Focused tests for the separate blocker-mode rule prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
PROTOTYPE = ROOT / "prototype.py"


def _load():
    assert PROTOTYPE.is_file(), "parametric prototype must be retained"
    spec = importlib.util.spec_from_file_location("b91_parametric", PROTOTYPE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_blocker_mode_is_chosen_once_per_episode_and_defaults_to_canonical():
    mod = _load()
    assert mod.ALLOWED_BLOCKER_MODES == ("stop", "pass")
    assert mod.DEFAULT_BLOCKER_MODE == "stop"
    for seed in range(8):
        episode = mod.build_episode(seed)
        assert episode["parameter"]["blocker_mode"] == mod.choose_blocker_mode(seed)
        assert len({episode["parameter"]["blocker_mode"]}) == 1
        assert len(episode["train"]) == 2 and len(episode["test"]) == 1


def test_every_demo_distinguishes_stop_from_pass():
    mod = _load()
    for mode in mod.ALLOWED_BLOCKER_MODES:
        episode = mod.build_episode(17, blocker_mode=mode)
        other = next(candidate for candidate in mod.ALLOWED_BLOCKER_MODES if candidate != mode)
        for pair in episode["train"]:
            assert pair["output"] == mod.python_beam(pair["input"], mode)
            assert pair["output"] != mod.python_beam(pair["input"], other)


def test_public_challenge_omits_hidden_parameter_and_query_answer():
    mod = _load()
    public = mod.public_challenge(mod.build_episode(17, blocker_mode="stop"))
    assert "parameter" not in public
    assert all("output" in pair for pair in public["train"])
    assert all("output" not in pair for pair in public["test"])
    json.dumps(public)


def test_materialized_racket_sources_match_exact_program_text():
    mod = _load()
    for mode in mod.ALLOWED_BLOCKER_MODES:
        path = mod.rule_path(mode)
        assert path.read_text(encoding="utf-8") == mod.racket_program(mode)
        assert f'(define STOP-AT-BLOCKER? {"#t" if mode == "stop" else "#f"})' in path.read_text()


def test_actual_racket_execution_when_available():
    mod = _load()
    if mod.shutil.which("racket") is None:
        pytest.skip("Racket is not on PATH outside the packet runtime")
    episode = mod.build_episode(23, blocker_mode="stop")
    for mode in mod.ALLOWED_BLOCKER_MODES:
        for pair in episode["train"] + episode["test"]:
            assert mod.run_racket(mode, pair["input"]) == mod.python_beam(pair["input"], mode)
