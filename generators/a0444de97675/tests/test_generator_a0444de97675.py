from __future__ import annotations

import copy
import random
import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "a0444de97675"
ROOT = find_root(__file__)
gen, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
AUDIT_INPUT = [
    [1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 2, 2, 3, 0, 0, 0, 0, 6, 0, 0, 0],
    [0, 0, 0, 3, 0, 0, 0, 0, 6, 6, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 4, 4, 5, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]
AUDIT_EXPECTED = [[4, 4, 4, 4] for _ in range(4)]


def _labeled(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_pin_and_all_canonical_pairs_match_the_python_mirror() -> None:
    assert gen.RULE_HASH == "e92da57c2394"
    assert len(CANONICAL) == 5
    for pair in CANONICAL:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_color_sensitive_connectivity_repairs_the_retained_audit_counterexample() -> None:
    grid = copy.deepcopy(AUDIT_INPUT)
    objects = gen._body_objects(grid)
    assert sorted(len(obj) for obj in objects) == [1, 2, 2, 3, 4]
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == AUDIT_EXPECTED


def test_four_profile_schedule_teaches_both_declared_rivals() -> None:
    assert gen.EXAMPLES_NEEDED == 3
    assert tuple(gen.SCHEDULE_PROFILES) == (0, 1, 2, 3)
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            lesson = [_labeled(7000 + start, start + offset, difficulty) for offset in range(4)]
            demos, query = lesson[:3], lesson[3]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_canonical_shortcut_really_fits_canonical_and_generated_data_refutes_it() -> None:
    rival = gen.CANONICAL_SHORTCUTS["count_all_header_nonzero"]
    assert all(rival(pair["input"]) == pair["output"] for pair in CANONICAL)
    for difficulty in ("easy", "medium", "hard"):
        grid = gen.generate(91, 1, difficulty=difficulty)
        assert gen.SEMANTIC_WITNESSES["non_one_header_cue"](grid)
        assert rival(grid) != gen.rule_mirror(grid)


def test_default_draws_are_lawful_observable_and_cover_profiles() -> None:
    for difficulty in ("easy", "medium", "hard"):
        profiles = set()
        exact_profile_hits = 0
        for sample_index in range(20):
            grid = gen.generate(1701, sample_index, difficulty=difficulty)
            assert gen.self_check(grid, difficulty=difficulty) == []
            observed = gen.observe_overrides(grid)
            assert observed["grid_h"] == len(grid)
            assert observed["grid_w"] == len(grid[0])
            assert observed["target_size"] == sum(value == 1 for value in grid[0])
            assert gen.rule_mirror(grid)
            profiles.add(gen.schedule_profile(1701, sample_index, difficulty=difficulty))
            if (len(grid), len(grid[0]), len({v for row in grid for v in row})) == (8, 9, 5):
                exact_profile_hits += 1
        assert profiles == set(gen.SCHEDULE_PROFILES)
        assert exact_profile_hits >= 8


def test_exact_overrides_round_trip_and_invalid_controls_fail_loudly() -> None:
    cases = (
        {
            "grid_h": 8,
            "grid_w": 9,
            "target_size": 3,
            "header_distractors": 0,
            "touching_mode": "separated",
            "target_color": 2,
        },
        {
            "grid_h": 14,
            "grid_w": 14,
            "target_size": 6,
            "header_distractors": 2,
            "touching_mode": "target_touching",
            "target_color": 9,
        },
    )
    for difficulty in ("easy", "medium", "hard"):
        for requested in cases:
            grid = gen.generate(303, 0, difficulty=difficulty, **requested)
            assert gen.self_check(grid, difficulty=difficulty) == []
            assert gen.observe_overrides(grid) == requested

    for bad_index in (True, False, 1.0, "1", -1):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, bad_index)
    for bad_value in (True, 3.0, "3", -1):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, 0, target_size=bad_value)
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=1)


def test_determinism_fresh_returns_and_global_random_state() -> None:
    random.seed(20261012)
    state = random.getstate()
    first = gen.generate(44, 7, difficulty="hard")
    second = gen.generate(45, 8, difficulty="easy")
    assert random.getstate() == state
    first_again = gen.generate(44, 7, difficulty="hard")
    assert first == first_again
    assert first is not first_again
    assert all(a is not b for a, b in zip(first, first_again))
    first_before, second_before = copy.deepcopy(first), copy.deepcopy(second)
    gen.rule_mirror(first)
    gen.rule_mirror(second)
    assert first == first_before
    assert second == second_before


def test_color_one_is_reserved_for_the_header() -> None:
    grid = [[0] * 9 for _ in range(8)]
    grid[0][0] = grid[0][1] = 1
    grid[1][0] = grid[1][1] = 1
    assert gen.self_check(grid), "a body color-1 object must not be accepted as a target"
