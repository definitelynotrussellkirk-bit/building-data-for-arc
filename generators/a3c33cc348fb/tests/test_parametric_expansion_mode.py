"""Contract tests for the task-local expansion-mode prototype.

The prototype is deliberately outside the production generator.  These tests
bind its public API, episode-level sampling unit, canonical default, public
redaction, and rotation-level identifiability.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root


TASK_ID = "a3c33cc348fb"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        f"parametric_expansion_mode_{TASK_ID}", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_rule() -> str:
    rows = [
        json.loads(line)
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]
    programs = {row["program_solution"] for row in rows}
    assert len(programs) == 1
    return programs.pop()


def test_parameter_contract_and_default_are_explicit():
    module = _load_prototype()
    assert module.ALLOWED_EXPANSION_MODES == ("bbox", "corridor")
    assert module.DEFAULT_EXPANSION_MODE == "bbox"
    assert module.TRAIN_COUNT == 3
    assert module.PAIR_COUNT == 4


def test_bbox_rule_is_exact_canonical_authority_and_invalid_modes_reject():
    module = _load_prototype()
    assert module.rule_source("bbox") == _canonical_rule()
    with pytest.raises(ValueError):
        module.rule_source("unknown")
    with pytest.raises(ValueError):
        module.rule_source(True)


def test_sampled_inputs_distinguish_both_declared_settings():
    module = _load_prototype()
    inputs = module.sample_inputs(20261022)
    assert len(inputs) == module.PAIR_COUNT
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == len(inputs)
    for grid in inputs:
        assert module.python_mirror(grid, "bbox") != module.python_mirror(grid, "corridor")


def test_hidden_parameter_is_selected_once_per_episode():
    module = _load_prototype()
    episode = module.sample_episode(20261022)
    chosen = episode["parameters"]["expansion_mode"]
    assert chosen in module.ALLOWED_EXPANSION_MODES
    assert episode["program"] == module.rule_source(chosen)
    assert len(episode["inputs"]) == module.PAIR_COUNT
    assert episode["train_count"] == module.TRAIN_COUNT
    pairs = [
        {"input": grid, "output": module.python_mirror(grid, chosen)}
        for grid in episode["inputs"]
    ]
    assert all(pair["output"] == module.python_mirror(pair["input"], chosen) for pair in pairs)


def test_seed_selection_covers_each_parameter_setting():
    module = _load_prototype()
    selection = module.select_seeds(20261022)
    assert set(selection["by_expansion_mode"]) == set(module.ALLOWED_EXPANSION_MODES)
    observed = {
        module.expansion_mode_for_seed(seed)
        for seed in selection["seeds"]
    }
    assert observed == set(module.ALLOWED_EXPANSION_MODES)


def test_every_query_rotation_refutes_the_alternate_setting_from_demos():
    module = _load_prototype()
    episode = module.sample_episode(20261022)
    chosen = episode["parameters"]["expansion_mode"]
    predictions = {
        mode: [module.python_mirror(grid, mode) for grid in episode["inputs"]]
        for mode in module.ALLOWED_EXPANSION_MODES
    }
    for query_index in range(module.PAIR_COUNT):
        row = module.score_rotation(predictions, chosen, query_index)
        assert row["query_pair_index"] == query_index
        assert len(row["rivals"]) == 1
        assert row["rivals"][0]["status"] == "refuted_by_demonstrations"
        assert row["rivals"][0]["demonstration_mismatches"]


def test_public_challenge_redacts_rule_parameters_and_query_output():
    module = _load_prototype()
    episode = module.sample_episode(20261022)
    chosen = episode["parameters"]["expansion_mode"]
    pairs = [
        {"input": grid, "output": module.python_mirror(grid, chosen)}
        for grid in episode["inputs"]
    ]
    public = module.public_challenge(pairs)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == module.TRAIN_COUNT
    assert len(public["test"]) == 1
    assert set(public["test"][0]) == {"input"}
    serialized = json.dumps(public, sort_keys=True)
    assert "expansion_mode" not in serialized
    assert "program" not in serialized
