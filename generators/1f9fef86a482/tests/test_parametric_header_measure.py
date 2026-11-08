"""Focused contract tests for the header-measure parametric family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes


TASK_ID = "1f9fef86a482"
SETTINGS = (
    {"header_measure": "blue_cells"},
    {"header_measure": "blue_runs"},
)


def _root() -> Path:
    return find_root(__file__)


def _load(name: str):
    path = _root() / "generators" / TASK_ID / "workspace" / "parametric" / name
    assert path.is_file(), f"missing parametric implementation: {path}"
    spec = importlib.util.spec_from_file_location(
        f"_test_{TASK_ID}_{path.stem}_{hashlib.sha256(str(path).encode()).hexdigest()}",
        path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    matches = []
    with canonical_path(_root()).open(encoding="utf-8") as stream:
        for raw in stream:
            row = json.loads(raw)
            if row.get("task_id") == TASK_ID:
                matches.append(row["program_solution"])
    assert len(matches) == 1
    return matches[0]


def _all_inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in [*episode["train"], *episode["test"]]]


def test_programs_contract_and_adapter_are_exact_and_strict():
    prototype = _load("prototype.py")
    adapter = _load("adapter.py")
    contract_path = (
        _root()
        / "generators"
        / TASK_ID
        / "workspace"
        / "parametric"
        / "promotion.json"
    )
    contract = json.loads(contract_path.read_text())

    canonical = _canonical_program()
    assert prototype.program_for("blue_cells") == canonical
    assert adapter.program(SETTINGS[0]) == canonical
    assert prototype.program_for("blue_runs") == adapter.program(SETTINGS[1])
    assert prototype.program_for("blue_runs") != canonical
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/1f9fef86a482/workspace/parametric/adapter.py",
        "parameters": {"header_measure": ["blue_cells", "blue_runs"]},
        "default": {"header_measure": "blue_cells"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/1f9fef86a482/workspace/parametric/prototype.py",
            "generators/1f9fef86a482/workspace/parametric/canonical.rkt",
            "generators/1f9fef86a482/workspace/parametric/blue_runs.rkt",
        ],
    }

    for bad in ({}, {"header_measure": "bad"}, {"header_measure": "blue_cells", "x": 1}):
        with pytest.raises(ValueError):
            adapter.program(bad)


def test_two_demos_identify_both_settings_with_matched_inputs():
    prototype = _load("prototype.py")
    episodes = [
        prototype.generate_episode(44, setting, demos=2, queries=4)
        for setting in SETTINGS
    ]
    assert _all_inputs(episodes[0]) == _all_inputs(episodes[1])
    for setting, episode in zip(SETTINGS, episodes):
        assert prototype.teaching_survivors(episode) == [setting]
        assert prototype.episode_errors(episode) == []

    # The first demo is intentionally compatible with both decoders; the second
    # is the visible evidence that makes the episode-fixed setting identifiable.
    first_input = episodes[0]["train"][0]["input"]
    second_input = episodes[0]["train"][1]["input"]
    assert prototype.header_values(first_input) == {"blue_cells": 2, "blue_runs": 2}
    assert prototype.header_values(second_input) == {"blue_cells": 3, "blue_runs": 1}


def test_counts_are_independent_query_prefixes_are_stable_and_stress_is_real():
    prototype = _load("prototype.py")
    setting = SETTINGS[1]
    two = prototype.generate_episode(91, setting, demos=2, queries=4)
    six = prototype.generate_episode(91, setting, demos=6, queries=4)
    one_query = prototype.generate_episode(91, setting, demos=3, queries=1)
    four_queries = prototype.generate_episode(91, setting, demos=3, queries=4)

    assert two["train"] == six["train"][:2]
    assert one_query["test"] == four_queries["test"][:1]
    assert len({_grid_key(grid) for grid in _all_inputs(six)}) == 10

    stress = four_queries["test"][3]["input"]
    assert len(stress) == 30 and len(stress[0]) == 30
    occupied = [
        (row, col)
        for row in range(2, 30)
        for col in range(30)
        if stress[row][col] != 0
    ]
    assert len(occupied) >= 55
    assert min(row for row, _ in occupied) == 2
    assert max(row for row, _ in occupied) == 29
    assert min(col for _, col in occupied) == 0
    assert max(col for _, col in occupied) == 29
    facts = prototype.analyze_input(stress)
    assert set(facts["degrees"]) == {0, 1, 2, 3, 4}
    assert facts["degree_histogram"][4] >= 5
    assert facts["degree_histogram"][2] >= 16

    for demos in (1, 7, True):
        with pytest.raises(ValueError, match="demos"):
            prototype.generate_episode(0, setting, demos=demos, queries=4)
    for queries in (0, 5, True):
        with pytest.raises(ValueError, match="queries"):
            prototype.generate_episode(0, setting, demos=3, queries=queries)


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def test_python_labels_use_the_selected_header_intermediate():
    prototype = _load("prototype.py")
    for setting in SETTINGS:
        episode = prototype.generate_episode(123, setting, demos=6, queries=4)
        measure = setting["header_measure"]
        for pair in [*episode["train"], *episode["test"]]:
            facts = prototype.analyze_input(pair["input"])
            target = facts[measure]
            assert pair["output"] == prototype.apply_python(pair["input"], setting)
            painted = {
                (row, col)
                for row, values in enumerate(pair["output"])
                for col, value in enumerate(values)
                if value == 8
            }
            expected = {
                cell
                for component, degree in zip(facts["components"], facts["degrees"])
                if degree == target
                for cell in component
            }
            assert painted == expected
            assert painted


def test_public_turn_hides_settings_program_answers_and_future_queries():
    prototype = _load("prototype.py")
    episode = prototype.generate_episode(7, SETTINGS[1], demos=3, queries=4)
    public = prototype.public_turn(episode, 0)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert public["test"] and set(public["test"][0]) == {"input"}
    assert b"header_measure" not in public_challenge_bytes(public)
    assert b"program" not in public_challenge_bytes(public)

    first_id = prototype.public_turn_id(episode, 0)
    private_change = deepcopy(episode)
    private_change["settings"] = SETTINGS[0]
    private_change["program_solution"] = "private replacement"
    private_change["test"][0]["output"][0][0] = 9
    assert prototype.public_turn_id(private_change, 0) == first_id

    future_change = deepcopy(episode)
    future_change["test"][3]["input"][29][29] = 0
    assert prototype.public_turn_id(future_change, 0) == first_id

    visible_change = deepcopy(episode)
    visible_change["test"][0]["input"][0][0] ^= 1
    assert prototype.public_turn_id(visible_change, 0) != first_id


def test_finite_self_audit_rejects_query_only_shortcuts():
    prototype = _load("prototype.py")
    for seed in range(16):
        for setting in SETTINGS:
            episode = prototype.generate_episode(seed, setting, demos=2, queries=4)
            audit = prototype.audit_episode(episode)
            assert audit["chosen_setting_survivors"] == [setting]
            assert audit["ambiguous_query_rivals"] == []
            assert audit["tested_rivals"] >= 7


def test_wrong_header_intermediate_changes_a_qualified_style_query():
    prototype = _load("prototype.py")
    episode = prototype.generate_episode(17, SETTINGS[1], demos=3, queries=4)
    pair = episode["test"][0]
    facts = prototype.analyze_input(pair["input"])
    assert facts["blue_runs"] != facts["blue_cells"]
    correct = prototype.apply_python(pair["input"], SETTINGS[1])
    wrong = prototype.apply_degree(pair["input"], facts["blue_cells"])
    assert correct == pair["output"]
    assert wrong != correct
