from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root

ROOT = find_root(__file__)
HERE = ROOT / "generators" / "e282a664f807" / "workspace" / "parametric"
SPEC = importlib.util.spec_from_file_location("_e282_parametric", HERE / "adapter.py")
assert SPEC is not None and SPEC.loader is not None
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)

SETTINGS = (
    {"completion_policy": "single_box"},
    {"completion_policy": "largest_completed"},
)


def test_programs_and_episode_counts_are_exact():
    assert ADAPTER.program(SETTINGS[0]) == (HERE / "canonical.rkt").read_text()
    assert ADAPTER.program(SETTINGS[1]) == (HERE / "largest_completed.rkt").read_text()
    for settings in SETTINGS:
        for demos, queries in ((2, 1), (3, 4), (6, 4)):
            episode = ADAPTER.generate(17, settings, demos, queries)
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == queries
            assert episode["program_solution"] == ADAPTER.program(settings)
            pairs = episode["train"] + episode["test"]
            assert len({repr(pair["input"]) for pair in pairs}) == len(pairs)
            assert all(
                pair["output"] == ADAPTER.predict(pair["input"], settings["completion_policy"])
                for pair in pairs
            )


def test_counts_are_prefix_stable_and_independent():
    for settings in SETTINGS:
        short = ADAPTER.generate(991, settings, 2, 1)
        long = ADAPTER.generate(991, settings, 6, 4)
        assert short["train"] == long["train"][:2]
        assert short["test"] == long["test"][:1]


def test_alternate_is_real_fill_then_select_dependency():
    episode = ADAPTER.generate(23, SETTINGS[1], 3, 4)
    selected_colors = []
    for pair in episode["train"] + episode["test"]:
        intermediate = ADAPTER.intermediate(pair["input"])
        areas = ADAPTER.completed_areas(intermediate)
        assert len(areas) >= 3
        assert len({area for _, area in areas}) == len(areas)
        selected = max(areas, key=lambda item: item[1])[0]
        selected_colors.append(selected)
        assert any(9 in row for row in pair["output"])
        assert ADAPTER.wrong_order_predict(pair["input"]) != pair["output"]
    assert len(set(selected_colors)) >= 3


def test_settings_are_distinguished_by_every_generated_input():
    canonical = ADAPTER.generate(41, SETTINGS[0], 3, 4)
    alternate = ADAPTER.generate(41, SETTINGS[1], 3, 4)
    for episode in (canonical, alternate):
        for pair in episode["train"] + episode["test"]:
            outputs = [ADAPTER.predict(pair["input"], s["completion_policy"]) for s in SETTINGS]
            assert outputs[0] != outputs[1]


def test_query_bank_contains_substantive_30x30_case():
    for settings in SETTINGS:
        episode = ADAPTER.generate(7, settings, 2, 4)
        grid = episode["test"][-1]["input"]
        assert (len(grid), len(grid[0])) == (30, 30)
        assert sum(value != 0 for row in grid for value in row) >= 80


@pytest.mark.parametrize(
    "settings",
    [{}, {"completion_policy": "bad"}, {"completion_policy": 1}, {"completion_policy": "single_box", "extra": 1}],
)
def test_invalid_settings_are_rejected(settings):
    with pytest.raises(ValueError):
        ADAPTER.generate(1, settings, 2, 1)


@pytest.mark.parametrize("name,value", [("seed", True), ("demos", 1), ("demos", 7), ("queries", 0), ("queries", 5)])
def test_invalid_count_types_and_ranges_are_rejected(name, value):
    args = {"seed": 1, "settings": SETTINGS[0], "demos": 2, "queries": 1}
    args[name] = value
    with pytest.raises(ValueError):
        ADAPTER.generate(**args)
