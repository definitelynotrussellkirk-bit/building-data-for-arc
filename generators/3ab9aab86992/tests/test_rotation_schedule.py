"""Regression tests for rotation-safe default lesson cardinality."""
from collections import Counter
import importlib.util
from pathlib import Path
import sys

import pytest

TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT / "shared/runtime"))
_spec = importlib.util.spec_from_file_location(
    "reviewed_generator_3ab9_rotation", TASK_ROOT / "generator.py"
)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)


def _component_count(grid):
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != background
    }
    components = 0
    while unseen:
        components += 1
        stack = [unseen.pop()]
        while stack:
            row, col = stack.pop()
            color = grid[row][col]
            for point in (
                (row - 1, col), (row + 1, col),
                (row, col - 1), (row, col + 1),
            ):
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    stack.append(point)
    return components


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_four_pair_windows_survive_every_query_rotation(difficulty):
    """Alternating partial/full draws leave a partial witness in all rotations."""
    assert gen.LESSON_SCHEDULE_PERIOD == 2
    assert tuple(gen.SCHEDULE_PROFILES) == ("partial", "complete")

    for seed in range(12):
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            counts = [
                _component_count(gen.generate(seed, start + offset, difficulty=difficulty))
                for offset in range(4)
            ]
            expected = [
                4
                if gen.schedule_profile(seed, start + offset, difficulty=difficulty) == "complete"
                else None
                for offset in range(4)
            ]
            assert [
                gen.schedule_profile(seed, start + offset, difficulty=difficulty)
                for offset in range(4)
            ] in [
                ["partial", "complete", "partial", "complete"],
                ["complete", "partial", "complete", "partial"],
            ]
            for count, target in zip(counts, expected):
                if target is None:
                    assert 1 <= count < 4
                else:
                    assert count == target
            for query_index in range(4):
                demos = [count for index, count in enumerate(counts) if index != query_index]
                assert any(count < 4 for count in demos), (difficulty, seed, start, counts)


def _labeled_pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_lesson_identifiable_rejects_the_complete_all_corners_shortcut():
    demos = [
        _labeled_pair(gen.generate(41, index, n_corners=4))
        for index in range(3)
    ]
    query = _labeled_pair(gen.generate(41, 3, n_corners=1))

    reasons = gen.lesson_identifiable(demos, query)

    assert any("complete_all_corners" in reason for reason in reasons)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_lesson_identifiable_accepts_every_default_query_rotation(difficulty):
    for seed in range(8):
        pairs = [
            _labeled_pair(gen.generate(seed, index, difficulty=difficulty))
            for index in range(4)
        ]
        for query_index in range(4):
            query = pairs[query_index]
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == [], (
                difficulty,
                seed,
                query_index,
            )


@pytest.mark.parametrize("bad_seed", [True, False, 1.5, "1", None])
def test_generate_rejects_non_integer_or_boolean_seed(bad_seed):
    with pytest.raises(ValueError):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, -1, 1.5, "1", None])
def test_generate_rejects_invalid_sample_index(bad_index):
    with pytest.raises(ValueError):
        gen.generate(0, bad_index)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_complete_default_profile_uses_canonical_five_color_palette(difficulty):
    for seed in range(6):
        complete_indices = [
            index
            for index in range(4)
            if gen.schedule_profile(seed, index, difficulty=difficulty) == "complete"
        ]
        assert complete_indices
        for index in complete_indices:
            grid = gen.generate(seed, index, difficulty=difficulty)
            assert len({value for row in grid for value in row}) == 5


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_seed_equals_sample_index_census_reaches_both_schedule_profiles(difficulty):
    profiles = {
        gen.schedule_profile(seed, seed, difficulty=difficulty)
        for seed in range(1, 41)
    }
    assert profiles == set(gen.SCHEDULE_PROFILES)
    assert any(
        len({value for row in gen.generate(seed, seed, difficulty=difficulty) for value in row}) == 5
        for seed in range(1, 41)
    )
