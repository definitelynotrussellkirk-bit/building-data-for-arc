from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
)


def _load():
    assert PROTOTYPE_PATH.exists(), "parametric edge-mode prototype is missing"
    spec = importlib.util.spec_from_file_location(
        "parametric_e3be2a9d8ce2_edge_mode", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_is_exact_canonical_and_far_is_distinct():
    module = _load()
    canonical = module.canonical_record()["program_solution"]
    assert module.program_for("near") == canonical
    assert module.program_for("far") != canonical
    assert module.program_for("near") != module.program_for("far")


def test_parameter_is_chosen_once_and_both_values_are_reachable():
    module = _load()
    observed = {module.choose_edge_mode(seed) for seed in range(64)}
    assert observed == {"near", "far"}
    for seed in range(12):
        assert module.choose_edge_mode(seed) == module.choose_edge_mode(seed)


@pytest.mark.parametrize("mode", ["near", "far"])
def test_complete_episode_refutes_the_other_setting(mode):
    module = _load()
    episode = module.build_episode(20261021, edge_mode=mode)
    assert episode["meta"]["edge_mode"] == mode
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 1
    assert module.parameter_rival_findings(episode) == []
    rival = "far" if mode == "near" else "near"
    for pair in episode["train"] + episode["test"]:
        assert module.apply_python(pair["input"], mode) == pair["output"]
        assert module.apply_python(pair["input"], rival) != pair["output"]


def test_public_challenge_hides_parameter_program_and_query_answer():
    module = _load()
    private = module.build_episode(17, edge_mode="near")
    public = module.public_challenge(private)
    assert "meta" not in public
    assert "program" not in public
    assert all("output" in pair for pair in public["train"])
    assert all("output" not in pair for pair in public["test"])


@pytest.mark.parametrize("bad", [None, True, 0, "nearest", "NEAR"])
def test_invalid_edge_modes_reject(bad):
    module = _load()
    with pytest.raises(ValueError):
        module.program_for(bad)
