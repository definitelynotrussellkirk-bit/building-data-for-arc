from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "586db18f9bd7"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.586db18f9bd7.generator"
)


def test_rule_hash_and_canonical_python_mirror() -> None:
    assert GEN.RULE_HASH == "a93fb42e6980"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(copy.deepcopy(pair["input"])) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_unknown_override_rejected_and_exact_axes_observable() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(7, 0, difficulty="easy", typo_axis=1)

    for panel_index in (1, 2, 3):
        for command in range(6):
            grid = GEN.generate(
                1000 + panel_index * 10 + command,
                command,
                difficulty="hard",
                panel_index=panel_index,
                command=command,
            )
            assert GEN.self_check(
                grid,
                meta={
                    "overrides": {
                        "panel_index": panel_index,
                        "command": command,
                    }
                },
            ) == []
            assert GEN.observe_overrides(grid) == {
                "panel_index": panel_index,
                "command": command,
            }


def test_every_five_demo_window_covers_all_controls() -> None:
    for start in range(len(GEN.SCHEDULE_PROFILES)):
        profiles = [GEN.schedule_profile(0, start + offset) for offset in range(5)]
        controls = [GEN._PROFILE_BY_NAME[profile] for profile in profiles]
        assert {panel_index for panel_index, _ in controls} == {1, 2, 3}
        assert len({command for _, command in controls}) == 5


def test_generated_shapes_rebut_fixed_panel_and_transform_shortcuts() -> None:
    for band in ("easy", "medium", "hard"):
        for sample_index in range(18):
            grid = GEN.generate(4000 + sample_index, sample_index, difficulty=band)
            assert GEN.strict_canonical_like(grid) == []
            official = GEN.rule_mirror(grid)
            analysis = GEN._analysis(grid)
            if analysis["index"] != 1:
                assert GEN.SEMANTIC_RIVALS["always_panel_1"](grid) != official
            if analysis["command"] != 0:
                assert GEN.SEMANTIC_RIVALS["ignore_transform_code"](grid) != official
            assert GEN.SEMANTIC_RIVALS["omit_rectangular_border"](grid) != official
            assert GEN.SEMANTIC_RIVALS["preserve_source_color"](grid) != official


def test_self_check_rejects_four_structural_impostors() -> None:
    base = GEN.generate(9001, 5, difficulty="medium")

    bad_header = copy.deepcopy(base)
    bad_header[0][0] = 0
    assert GEN.self_check(bad_header)

    bad_separator = copy.deepcopy(base)
    bad_separator[3][5] = 1
    assert GEN.self_check(bad_separator)

    empty_selected = copy.deepcopy(base)
    left = (0, 6, 12)[empty_selected[0][0] - 1]
    for row in range(1, 6):
        for col in range(left, left + 5):
            empty_selected[row][col] = 0
    assert GEN.self_check(empty_selected)

    disconnected = copy.deepcopy(base)
    for row in range(1, 6):
        for col in range(0, 5):
            disconnected[row][col] = 0
    disconnected[1][0] = 1
    disconnected[5][4] = 1
    assert GEN.self_check(disconnected)


def test_replay_fresh_returns_and_global_rng_preservation() -> None:
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(77, 8, difficulty="hard")
    after = random.getstate()
    assert before == after

    second = GEN.generate(77, 8, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 9
    assert second[0][0] != 9
