from __future__ import annotations

import hashlib
import importlib

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "4e79c276ce9d"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
CANONICAL_PROFILES = {
    (10, 12, 4),
    (11, 11, 5),
    (9, 13, 4),
    (12, 10, 4),
    (10, 10, 5),
}


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def test_rule_pin_and_public_contract_are_explicit():
    assert GEN.RULE_HASH == "5d74c60efd43"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 6
    assert set(GEN.AXES) == {"grid_h", "grid_w"}
    assert set(GEN.SEMANTIC_RIVALS) == set(GEN.LESSON_COMPETITORS)
    assert set(GEN.CANONICAL_SHORTCUTS) <= set(GEN.SEMANTIC_RIVALS)


def test_every_canonical_pair_is_accepted_and_matches_the_python_mirror():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_every_declared_canonical_shortcut_really_fits_all_canonical_pairs():
    pairs = _canonical_pairs()
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_schedule_stays_on_exact_canonical_profiles(difficulty):
    for sample_index in range(GEN.LESSON_SCHEDULE_PERIOD):
        grid = GEN.generate(20261008, sample_index, difficulty=difficulty)
        profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        assert profile in CANONICAL_PROFILES
        assert GEN.self_check(grid) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_each_witness_profile_refutes_every_declared_lesson_competitor(difficulty):
    for sample_index in (1, 2, 4, 5):
        grid = GEN.generate(9173, sample_index, difficulty=difficulty)
        expected = GEN.rule_mirror(grid)
        assert GEN.schedule_profile(9173, sample_index, difficulty) != "canonical"
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert rival(grid) != expected, name


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_cyclic_query_rotation_retains_a_refuting_demonstration(difficulty):
    for start in range(GEN.LESSON_SCHEDULE_PERIOD):
        lesson = []
        for offset in range(GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(441, start + offset, difficulty=difficulty)
            lesson.append({"input": grid, "output": GEN.rule_mirror(grid)})
        for query_index in range(len(lesson)):
            demos = [pair for index, pair in enumerate(lesson) if index != query_index]
            query = lesson[query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert not all(
                    rival(pair["input"]) == pair["output"] for pair in demos
                ), (start, query_index, name)


def test_joint_exact_dimension_controls_and_unknown_keys():
    seen = set()
    for grid_h in range(9, 13):
        for grid_w in range(10, 14):
            grid = GEN.generate(
                77,
                grid_h * 100 + grid_w,
                difficulty="hard",
                grid_h=grid_h,
                grid_w=grid_w,
            )
            assert (len(grid), len(grid[0])) == (grid_h, grid_w)
            assert GEN.observe_overrides(grid) == {
                "grid_h": grid_h,
                "grid_w": grid_w,
            }
            assert GEN.self_check(
                grid,
                meta={"overrides": {"grid_h": grid_h, "grid_w": grid_w}},
            ) == []
            seen.add(hashlib.sha256(repr(grid).encode()).hexdigest())
    assert len(seen) == 16

    with pytest.raises(TypeError):
        GEN.generate(0, 0, typo_axis=1)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, grid_h=True)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, grid_h=8)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, grid_w=14)


def test_generation_is_deterministic_and_does_not_alias_rows():
    first = GEN.generate(123456, 5, difficulty="medium")
    second = GEN.generate(123456, 5, difficulty="medium")
    assert first == second
    assert len({id(row) for row in first}) == len(first)


def test_default_dimensions_are_recorded_as_keyed_draws(monkeypatch):
    captured = []
    real_gen_ctx = GEN.gen_ctx

    def capture_ctx(**kwargs):
        ctx = real_gen_ctx(**kwargs)
        captured.append(ctx)
        return ctx

    monkeypatch.setattr(GEN, "gen_ctx", capture_ctx)
    for sample_index in range(GEN.LESSON_SCHEDULE_PERIOD):
        grid = GEN.generate(915, sample_index, difficulty="medium")
        drawn = captured[-1].recorded_draws()
        assert drawn["grid_h"] == len(grid)
        assert drawn["grid_w"] == len(grid[0])
