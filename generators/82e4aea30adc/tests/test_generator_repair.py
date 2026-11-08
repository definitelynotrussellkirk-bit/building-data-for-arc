"""Regressions for strict calls and the retained large-frame shortcut."""
from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "82e4aea30adc"
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=find_root(__file__))


@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed(value) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(value, 0, difficulty="medium")


@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index(value) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(991, value, difficulty="medium")


@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1"])
def test_schedule_profile_rejects_non_integer_seed(value) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.schedule_profile(value, 0, difficulty="medium")


@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1", -1])
def test_schedule_profile_rejects_invalid_sample_index(value) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.schedule_profile(991, value, difficulty="medium")


def _large_frame_witness() -> list[list[int]]:
    grid = [[0] * 11 for _ in range(7)]
    r0, c0, height, width, color = 2, 2, 3, 7, 3
    for row in range(r0, r0 + height):
        for col in range(c0, c0 + width):
            if row in (r0, r0 + height - 1) or col in (c0, c0 + width - 1):
                grid[row][col] = color
    return grid


def test_lawful_3x7_witness_refutes_size_capped_shortcut() -> None:
    grid = _large_frame_witness()
    assert GEN.self_check(grid) == []
    expected = GEN.rule_mirror(grid)
    rival = GEN.SEMANTIC_RIVALS["ignore_frames_larger_than_5"](grid)
    assert expected != rival
    assert expected[3][3:8] == [7, 7, 7, 7, 7]
    assert rival == grid


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_multi_only_profile_emits_large_frame_in_every_band(difficulty) -> None:
    for seed in range(8):
        grid = GEN.generate(
            seed,
            2,
            difficulty=difficulty,
            n_frames=1,
            branch_profile="multi_only",
        )
        profile = GEN.semantic_profile(grid)
        assert profile["valid"] is True
        assert profile["branch_profile"] == "multi_only"
        assert any(max(height, width) > 5 for height, width in profile["frame_sizes"])
        assert GEN.SEMANTIC_RIVALS["ignore_frames_larger_than_5"](grid) != GEN.rule_mirror(grid)


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": GEN.rule_mirror(grid)}


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_three_example_schedule_window_refutes_size_cap_rival(difficulty) -> None:
    for start in range(9):
        grids = [GEN.generate(314159, start + offset, difficulty=difficulty) for offset in range(4)]
        reasons = GEN.lesson_identifiable([_pair(grid) for grid in grids[:3]], _pair(grids[3]))
        assert reasons == []

@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_four_pair_query_rotation_refutes_size_cap_rival(difficulty) -> None:
    for start in range(9):
        grids = [
            GEN.generate(271828, start + offset, difficulty=difficulty)
            for offset in range(4)
        ]
        pairs = [_pair(grid) for grid in grids]
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            reasons = GEN.lesson_identifiable(demos, pairs[query_index])
            assert not any("ignore_frames_larger_than_5" in reason for reason in reasons)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_mixed_profile_also_emits_large_frame_in_every_band(difficulty) -> None:
    for seed in range(8):
        grid = GEN.generate(
            seed,
            1,
            difficulty=difficulty,
            n_frames=2,
            branch_profile="mixed",
        )
        profile = GEN.semantic_profile(grid)
        assert profile["valid"] is True
        assert profile["branch_profile"] == "mixed"
        assert any(max(height, width) > 5 for height, width in profile["frame_sizes"])
