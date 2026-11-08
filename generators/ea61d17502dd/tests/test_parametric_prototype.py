"""Focused tests for the proposed vertical-bounds parametric prototype.

These tests do not change or approve the canonical per-puzzle generator. They
exercise only ``workspace/parametric/prototype.py`` and its retained evidence
contract.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"
REFERENCE_PATH = HOME / "workspace" / "reference_probe.py"


def _load(path: Path, name: str):
    assert path.exists(), f"missing proposed prototype: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(PROTOTYPE_PATH, "ea61d17502dd_parametric")


def _reference():
    return _load(REFERENCE_PATH, "ea61d17502dd_reference")


def test_canonical_mode_returns_exact_authority_program():
    prototype = _prototype()
    reference = _reference()
    assert prototype.DEFAULT_MODE == "all_markers"
    assert prototype.MODES == ("all_markers", "crossing_to_farthest")
    assert prototype.program_for("all_markers") == reference.canonical_program()
    assert prototype.normalized_program_hash(
        prototype.program_for("all_markers")
    ) == reference.RULE_HASH


def test_invalid_mode_is_rejected_loudly():
    prototype = _prototype()
    with pytest.raises(ValueError, match="vertical_bounds_mode"):
        prototype.program_for("nearest_only")


def test_racket_executes_both_modes_and_the_straddled_witness_differs():
    prototype = _prototype()
    inputs = prototype.episode_inputs(seed=314159, difficulty="medium")
    witness = inputs[1]
    assert prototype.input_profile(witness)["vertical_relation"] == "straddle"

    programs = [prototype.program_for(mode) for mode in prototype.MODES]
    outputs = [prototype.racket_outputs(program, [witness])[0] for program in programs]
    assert outputs[0] != outputs[1]
    assert outputs == [
        prototype.python_output(witness, mode) for mode in prototype.MODES
    ]


def test_each_complete_episode_holds_one_mode_and_refutes_its_rival():
    prototype = _prototype()
    for mode in prototype.MODES:
        episode = prototype.build_episode(
            seed=271828,
            mode=mode,
            difficulty="hard",
            execute_racket=True,
        )
        assert episode["parameter"] == {
            "name": prototype.PARAMETER_NAME,
            "value": mode,
            "default": prototype.DEFAULT_MODE,
        }
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["rival_survivors"] == []
        assert episode["distinguishing_train_indices"]
        assert episode["query_differs_between_modes"] is True
        assert all(
            pair["output"] == prototype.python_output(pair["input"], mode)
            for pair in [*episode["train"], *episode["test"]]
        )


def test_public_challenge_omits_hidden_mode_program_and_query_answer(tmp_path):
    prototype = _prototype()
    episode = prototype.build_episode(
        seed=161803,
        mode="crossing_to_farthest",
        difficulty="easy",
        execute_racket=True,
    )
    paths = prototype.write_episode(episode, tmp_path / "episode")
    public = json.loads(paths["public"].read_text(encoding="utf-8"))
    private = json.loads(paths["private"].read_text(encoding="utf-8"))

    serialized_public = json.dumps(public, sort_keys=True)
    assert prototype.PARAMETER_NAME not in serialized_public
    assert "crossing_to_farthest" not in serialized_public
    assert "program" not in public
    assert all("output" not in pair for pair in public["test"])

    assert private["parameter"]["value"] == "crossing_to_farthest"
    assert private["program"] == prototype.program_for("crossing_to_farthest")
    assert "output" in private["test"][0]
