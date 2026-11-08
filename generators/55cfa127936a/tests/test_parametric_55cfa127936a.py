"""Focused contract tests for the task-local parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "55cfa127936a"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load_adapter():
    path = HOME / "adapter.py"
    spec = importlib.util.spec_from_file_location("_test_55cfa_parametric", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    row = next(item for item in rows if item.get("task_id") == TASK_ID)
    return row["program_solution"]


def _inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def test_programs_preserve_exact_canonical_and_validate_settings():
    adapter = _load_adapter()
    canonical = {"selection": "topmost"}
    alternate = {"selection": "singleton_anchor_nearest"}
    assert adapter.program(canonical) == _canonical_program()
    assert adapter.program(alternate) != adapter.program(canonical)
    for invalid in ({}, {"selection": "unknown"}, {"selection": True}, {"selection": "topmost", "x": 1}):
        with pytest.raises(ValueError):
            adapter.program(invalid)


def test_generate_is_matched_prefix_stable_distinct_and_stresses_30x30():
    adapter = _load_adapter()
    settings = [
        {"selection": "topmost"},
        {"selection": "singleton_anchor_nearest"},
    ]
    small = [adapter.generate(23, s, 2, 1) for s in settings]
    large = [adapter.generate(23, s, 6, 4) for s in settings]
    assert _inputs(large[0], "train") == _inputs(large[1], "train")
    assert _inputs(large[0], "test") == _inputs(large[1], "test")
    for index in range(2):
        assert small[index]["train"] == large[index]["train"][:2]
        assert small[index]["test"] == large[index]["test"][:1]
        all_inputs = _inputs(large[index], "train") + _inputs(large[index], "test")
        assert len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs}) == 10
        assert any(len(grid) == 30 and len(grid[0]) == 30 for grid in _inputs(large[index], "test"))


def test_minimum_lesson_identifies_setting_and_rejects_named_rivals():
    adapter = _load_adapter()
    for seed in (0, 17, 91):
        for selection in adapter.SELECTIONS:
            settings = {"selection": selection}
            episode = adapter.generate(seed, settings, 2, 4)
            check = adapter.teaching_check(episode)
            assert check["ok"] is True
            assert check["survivors"] == [selection]
            assert check["surviving_rivals"] == []


def test_singleton_anchor_is_input_dependent_and_ties_choose_upper_row():
    adapter = _load_adapter()
    episode = adapter.generate(0, {"selection": "singleton_anchor_nearest"}, 2, 4)
    anchors = []
    found_tie = False
    for pair in episode["train"]:
        facts = adapter.analyze(pair["input"])
        anchors.append(facts["anchor_row"])
        for column, rows in enumerate(facts["yellow_rows"]):
            if len(rows) >= 2:
                distances = [abs(row - facts["anchor_row"]) for row in rows]
                minimum = min(distances)
                tied = [row for row, distance in zip(rows, distances) if distance == minimum]
                if len(tied) >= 2:
                    found_tie = True
                    kept = [r for r in rows if pair["output"][r][column] == 4]
                    assert kept == [min(tied)]
    assert len(set(anchors)) == 2
    assert found_tie


def test_public_turn_omits_private_state_and_future_queries():
    adapter = _load_adapter()
    episode = adapter.generate(5, {"selection": "singleton_anchor_nearest"}, 3, 4)
    turn = adapter.public_turn(episode, 2)
    assert set(turn) == {"train", "test"}
    assert len(turn["test"]) == 1 and set(turn["test"][0]) == {"input"}
    assert turn["test"][0]["input"] == episode["test"][2]["input"]
    assert b"singleton_anchor_nearest" not in public_challenge_bytes(turn)



def test_declared_rival_programs_are_complete_and_distinct():
    adapter = _load_adapter()
    programs = [adapter.rival_program(name) for name in adapter.RIVALS]
    assert all(text.startswith("(rule!") for text in programs)
    assert len(programs) == len(set(programs))

def test_invalid_counts_and_seed_fail_closed():
    adapter = _load_adapter()
    settings = {"selection": "topmost"}
    for seed in (-1, True, 2**63):
        with pytest.raises(ValueError):
            adapter.generate(seed, settings, 2, 4)
    for demos in (1, 7, True):
        with pytest.raises(ValueError):
            adapter.generate(0, settings, demos, 4)
    for queries in (0, 5, True):
        with pytest.raises(ValueError):
            adapter.generate(0, settings, 2, queries)
