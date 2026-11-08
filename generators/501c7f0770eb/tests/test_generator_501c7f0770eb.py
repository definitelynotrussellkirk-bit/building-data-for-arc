from __future__ import annotations

import importlib.util
import os
from pathlib import Path


def _load_generator():
    explicit = os.environ.get("GENERATOR_UNDER_TEST")
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidates.extend(
            [
                parent / "generators" / "501c7f0770eb" / "generator.py",
                parent / "puzzle_generators" / "per_puzzle" / "501c7f0770eb" / "generator.py",
            ]
        )
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        raise RuntimeError("could not locate generator.py under test")
    spec = importlib.util.spec_from_file_location("generator_501c7f0770eb", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _frame(height: int = 5, width: int = 7) -> list[list[int]]:
    grid = [[0] * (width + 2) for _ in range(height + 2)]
    for column in range(1, width + 1):
        grid[1][column] = 5
        grid[height][column] = 5
    for row in range(1, height + 1):
        grid[row][1] = 5
        grid[row][width] = 5
    return grid


def test_validator_rejects_a_superficial_frame_without_the_full_task_contract():
    grid = _frame()
    grid[3][4] = 1

    errors = gen.self_check(grid)

    assert errors, "one frame, one seed color, and no blocker must not be accepted"


def test_mixed_touching_profile_has_one_active_chamber_and_two_inactive_frames():
    grid = gen.generate(
        0,
        0,
        difficulty="easy",
        grid_h=10,
        grid_w=16,
        layout_kind="mixed_touching",
        blocker_style="mixed",
    )

    assert gen.self_check(grid) == []
    observed = gen.observe_overrides(grid)
    assert observed["layout_kind"] == "mixed_touching"
    assert len(gen._rectangle_frames(grid)) == 3
    assert len(gen._active_frames(grid)) == 1


def test_all_canonical_pairs_are_in_contract_and_match_the_independent_python_mirror():
    from reviewer_support import canonical_pairs, find_root

    pairs = canonical_pairs("501c7f0770eb", root=find_root(__file__), labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        identity = f"{pair['split']}[{pair['pair_index']}]"
        assert gen.self_check(pair["input"]) == [], identity
        assert gen._component_rule_model(pair["input"]) == pair["output"], identity


def test_isolated_profile_covers_both_canonical_frame_counts():
    counts = {
        len(gen._rectangle_frames(gen.generate(seed, 0, difficulty="hard", layout_kind="isolated")))
        for seed in range(24)
    }

    assert counts == {2, 3}


def test_schedule_does_not_cancel_when_seed_equals_sample_index():
    layouts = {
        gen.observe_overrides(gen.generate(index, index, difficulty="medium"))["layout_kind"]
        for index in range(6)
    }

    assert layouts == {"isolated", "mixed_touching"}


def test_declared_schedule_profiles_are_the_values_reported_by_the_schedule():
    observed = {
        gen.schedule_profile(0, index)
        for index in range(gen.LESSON_SCHEDULE_PERIOD)
    }

    assert observed == set(gen.SCHEDULE_PROFILES)


def test_even_seed_defaults_anchor_an_exact_canonical_profile_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in (0, 1):
            grid = gen.generate(2, sample_index, difficulty=difficulty)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            assert profile == (12, 18, 5), (difficulty, sample_index, profile)


def test_observer_reuses_one_frame_scan():
    grid = gen.generate(3, 1, difficulty="medium")
    original = gen._rectangle_frames
    calls = 0

    def counted(candidate):
        nonlocal calls
        calls += 1
        return original(candidate)

    gen._rectangle_frames = counted
    try:
        observed = gen.observe_overrides(grid)
    finally:
        gen._rectangle_frames = original

    assert observed["layout_kind"] in gen.LAYOUT_KINDS
    assert calls == 1


def test_validator_reuses_one_frame_scan():
    grid = gen.generate(3, 1, difficulty="medium")
    original = gen._rectangle_frames
    calls = 0

    def counted(candidate):
        nonlocal calls
        calls += 1
        return original(candidate)

    gen._rectangle_frames = counted
    try:
        errors = gen.self_check(grid)
    finally:
        gen._rectangle_frames = original

    assert errors == []
    assert calls == 1
