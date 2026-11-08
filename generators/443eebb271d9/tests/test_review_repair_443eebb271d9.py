"""Review regressions for the 443eebb271d9 lesson-ambiguity repair."""
from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator

TASK_ID = "443eebb271d9"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _component_count(grid: list[list[int]], color: int = 7) -> int:
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            row, col = stack.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def _pair(seed: int, sample_index: int, difficulty: str) -> dict[str, list[list[int]]]:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_generate_rejects_nonliteral_or_negative_call_scalars() -> None:
    for invalid in (True, 1.0, "1", None):
        with pytest.raises(TypeError, match="seed"):
            GEN.generate(invalid, 0)
        with pytest.raises(TypeError, match="sample_index"):
            GEN.generate(0, invalid)
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(0, -1)


def test_four_slot_schedule_declares_the_rotation_safe_curriculum() -> None:
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "canonical_connected",
        "disconnected_a",
        "general_connected",
        "disconnected_b",
    )
    for seed in (0, 1, 98_765):
        for difficulty in (None, "easy", "medium", "hard"):
            observed = [GEN.schedule_profile(seed, index, difficulty) for index in range(8)]
            assert observed[4:] == observed[:4]
            assert sorted(observed[:4]) == sorted(GEN.SCHEDULE_PROFILES)


def test_default_sample_index_zero_is_seed_diverse() -> None:
    grids = [GEN.generate(seed, 0) for seed in range(40)]
    assert len({tuple(map(tuple, grid)) for grid in grids}) >= 5


def test_every_four_pair_window_refutes_largest_component_rival_under_rotation() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(8):
            for start in range(8):
                episode = [
                    _pair(10_000 + seed, sample_index, difficulty)
                    for sample_index in range(start, start + 4)
                ]
                component_counts = [_component_count(pair["input"]) for pair in episode]
                assert sum(count > 1 for count in component_counts) == 2
                assert any(GEN.canonical_profile_signature(pair["input"]) for pair in episode)
                for query_index, query in enumerate(episode):
                    demos = [pair for index, pair in enumerate(episode) if index != query_index]
                    assert any(_component_count(pair["input"]) > 1 for pair in demos)
                    assert GEN.lesson_identifiable(demos, query) == []


def test_low_fragmentation_witness_slot_stays_near_canonical_object_count() -> None:
    grids = []
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            full_seed = 20_000 + seed
            sample_index = next(
                index
                for index in range(GEN.LESSON_SCHEDULE_PERIOD)
                if GEN.schedule_profile(full_seed, index, band) == "disconnected_a"
            )
            grids.append(GEN.generate(full_seed, sample_index, difficulty=band))
    counts = [_component_count(grid) for grid in grids]
    assert set(counts) == {2}
    assert len({tuple(map(tuple, grid)) for grid in grids}) >= 20


def test_declared_rival_and_witness_capture_the_retained_counterexample() -> None:
    rival_name = "largest_4_connected_component_only"
    assert set(GEN.LESSON_COMPETITORS) == {rival_name}
    assert set(GEN.SEMANTIC_RIVALS) == {rival_name}
    assert set(GEN.SEMANTIC_WITNESSES) == {"disconnected_source_glyph"}
    assert GEN.WITNESS_RIVALS == {"disconnected_source_glyph": [rival_name]}

    connected = GEN.generate(7, 0, scene_profile="hollow_square")
    disconnected = GEN.generate(7, 0, scene_profile="diamond")
    rival = GEN.LESSON_COMPETITORS[rival_name]
    witness = GEN.SEMANTIC_WITNESSES["disconnected_source_glyph"]

    assert rival(connected) == GEN.rule_mirror(connected)
    assert rival(disconnected) != GEN.rule_mirror(disconnected)
    assert not witness(connected)
    assert witness(disconnected)

    all_connected_demos = [
        {
            "input": GEN.generate(2, index, difficulty="medium", scene_profile=profile),
            "output": GEN.rule_mirror(
                GEN.generate(2, index, difficulty="medium", scene_profile=profile)
            ),
        }
        for index, profile in enumerate(("hollow_square", "aitch", "tee"))
    ]
    query_grid = GEN.generate(2, 3, difficulty="medium", scene_profile="diamond")
    reasons = GEN.lesson_identifiable(
        all_connected_demos,
        {"input": query_grid, "output": GEN.rule_mirror(query_grid)},
    )
    assert reasons == [
        "unrefuted declared rival changes query: largest_4_connected_component_only"
    ]


def test_strict_contract_accepts_every_declared_profile() -> None:
    assert GEN.strict_canonical_like(GEN.generate(0, 0, scene_profile="public_1")) == []
    for profile_index, profile in enumerate(GEN.SCENE_PROFILES):
        grid = GEN.generate(1_000 + profile_index, profile_index, scene_profile=profile)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []


def test_declared_scene_profile_enum_fits_framework_probe_cap() -> None:
    assert len(GEN.SCENE_PROFILES) <= 16
    assert len(set(GEN.SCENE_PROFILES)) == len(GEN.SCENE_PROFILES)


def test_strict_lint_stream_keeps_at_least_seventy_percent_unique_inputs() -> None:
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(seed, seed, difficulty=band) for seed in range(1, 21)]
        distinct = len({tuple(map(tuple, grid)) for grid in grids})
        assert distinct >= 14
