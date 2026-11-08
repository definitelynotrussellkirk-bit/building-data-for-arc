from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root

ROOT = find_root(__file__)
HERE = ROOT / "generators" / "67c14e0f76b1" / "workspace" / "parametric"
SPEC = importlib.util.spec_from_file_location("_gap_parametric", HERE / "adapter.py")
assert SPEC is not None and SPEC.loader is not None
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)

SETTINGS = (
    {"postprocess": "mark_only"},
    {"postprocess": "largest_marked"},
)


def test_programs_and_episode_counts_are_exact():
    assert ADAPTER.program(SETTINGS[0]) == (HERE / "canonical.rkt").read_text()
    assert ADAPTER.program(SETTINGS[1]) == (HERE / "largest_marked.rkt").read_text()
    for settings in SETTINGS:
        for demos, queries in ((2, 1), (3, 4), (6, 4)):
            episode = ADAPTER.generate(17, settings, demos, queries)
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == queries
            assert episode["program_solution"] == ADAPTER.program(settings)
            pairs = episode["train"] + episode["test"]
            assert len({repr(pair["input"]) for pair in pairs}) == len(pairs)
            assert all(
                pair["output"] == ADAPTER.predict(pair["input"], settings["postprocess"])
                for pair in pairs
            )


def test_counts_are_prefix_stable_and_setting_neutral():
    short = ADAPTER.generate(991, SETTINGS[0], 2, 1)
    long = ADAPTER.generate(991, SETTINGS[0], 6, 4)
    alternate = ADAPTER.generate(991, SETTINGS[1], 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    assert [p["input"] for p in long["train"] + long["test"]] == [
        p["input"] for p in alternate["train"] + alternate["test"]
    ]


def test_alternate_marks_then_selects_unique_largest_new_component():
    episode = ADAPTER.generate(23, SETTINGS[1], 3, 4)
    selected = []
    for pair in episode["train"] + episode["test"]:
        stage = ADAPTER.intermediate(pair["input"])
        components = ADAPTER.marked_components(stage)
        sizes = [len(cells) for cells in components]
        assert len(components) >= 3
        assert sizes.count(max(sizes)) == 1
        winner = max(components, key=len)
        selected.append(min(winner))
        assert all(pair["output"][r][c] == 8 for r, c in winner)
        assert any(2 in row for row in pair["output"])
        assert ADAPTER.wrong_order_predict(pair["input"]) != pair["output"]
    assert len(set(selected)) >= 3


def test_each_input_distinguishes_the_two_settings():
    episode = ADAPTER.generate(31, SETTINGS[0], 3, 4)
    for pair in episode["train"] + episode["test"]:
        assert ADAPTER.predict(pair["input"], "mark_only") != ADAPTER.predict(
            pair["input"], "largest_marked"
        )


def test_query_bank_contains_substantive_30x30_boundary_case():
    episode = ADAPTER.generate(7, SETTINGS[1], 2, 4)
    grid = episode["test"][-1]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value != 0 for row in grid for value in row) >= 100
    targets = ADAPTER.target_cells(grid)
    assert any(c == 1 for _, c in targets)
    assert any(c == 28 for _, c in targets)


@pytest.mark.parametrize(
    "settings",
    [{}, {"postprocess": "bad"}, {"postprocess": 1}, {"postprocess": "mark_only", "extra": 1}],
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


def test_three_demo_prefix_refutes_recolor_first_marked_shortcut():
    for seed in range(64):
        episode = ADAPTER.generate(seed, SETTINGS[1], 3, 1)
        assert any(
            max(ADAPTER.marked_components(ADAPTER.intermediate(pair["input"])), key=len)
            != ADAPTER.marked_components(ADAPTER.intermediate(pair["input"]))[0]
            for pair in episode["train"]
        ), seed
