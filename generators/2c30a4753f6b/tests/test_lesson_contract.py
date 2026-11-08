"""Regression tests for observable size/color teaching and scalar boundaries."""
from __future__ import annotations

import itertools

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
TASK = "2c30a4753f6b"
MODULE, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)


def _gold(grid):
    return [list(row) + list(reversed(row)) for row in grid]


def _width3(grid):
    return [list(row) + list(reversed(row[:3])) for row in grid]


def _orange_only(grid):
    return [list(row) + [value if value == 7 else 0 for value in reversed(row)]
            for row in grid]


def _orange_repaint(grid):
    return [list(row) + [7 if value else 0 for value in reversed(row)]
            for row in grid]


def _fixed3x3(grid):
    crop = [(list(row) + [0, 0, 0])[:3] for row in grid[:3]]
    crop.extend([[0, 0, 0] for _ in range(3 - len(crop))])
    return _gold(crop)


RIVALS = (_width3, _orange_only, _orange_repaint, _fixed3x3)


def _lesson(seed, start, band):
    """Use accepted distinct inputs, not an assumed consecutive window."""
    pairs, seen = [], set()
    for index in range(start, start + 64):
        grid = MODULE.generate(seed, index, difficulty=band)
        key = tuple(map(tuple, grid))
        if key in seen:
            continue
        seen.add(key)
        pairs.append({"input": grid, "output": _gold(grid)})
        if len(pairs) == 4:
            return pairs
    pytest.fail("could not materialize four distinct inputs")


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", None, [], {}])
def test_seed_requires_literal_integer(bad):
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(bad, 0)


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", None, [], {}, -1])
def test_sample_index_requires_nonnegative_literal_integer(bad):
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(0, bad)


def test_negative_integer_seed_remains_deterministic():
    assert MODULE.generate(-17, 11) == MODULE.generate(-17, 11)


def test_canonical_shortcuts_really_fit_all_canonical_labels():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        for rival in RIVALS:
            assert rival(pair["input"]) == pair["output"]
    assert getattr(MODULE, "CANONICAL_SHORTCUTS", None), "missing executable shortcuts"
    for rival in MODULE.CANONICAL_SHORTCUTS.values():
        for pair in pairs:
            assert rival(pair["input"]) == pair["output"]


@pytest.mark.parametrize("seed", [1, 639])
def test_reproduced_ambiguous_lessons_are_repaired(seed):
    pairs = _lesson(seed, 0, "easy")
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        query = pairs[query_index]
        for rival in RIVALS:
            assert (any(rival(pair["input"]) != pair["output"] for pair in demos)
                    or rival(query["input"]) == query["output"]), (
                        seed, query_index, rival.__name__, pairs)


def test_declared_contract_detects_a_visible_ambiguity():
    assert callable(getattr(MODULE, "lesson_identifiable", None)), "missing lesson contract"
    demos = canonical_pairs(TASK, root=ROOT)[:3]
    grid = [[0, 0, 2, 0], [0, 3, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    reasons = MODULE.lesson_identifiable(demos, {"input": grid, "output": _gold(grid)})
    assert reasons, "canonical-only demos do not identify noncanonical color/width behavior"
    assert all(isinstance(reason, str) for reason in reasons)


def test_default_lesson_windows_identify_declared_rivals_in_all_rotations():
    assert callable(getattr(MODULE, "lesson_identifiable", None)), "missing lesson contract"
    for band, seed, start in itertools.product(("easy", "medium", "hard"), range(8), range(6)):
        pairs = _lesson(seed, start, band)
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert MODULE.lesson_identifiable(demos, pairs[query_index]) == [], (
                band, seed, start, query_index)


def test_explicit_profiles_are_honored_at_both_schedule_positions():
    for profile, index in itertools.product(MODULE.SCENE_PROFILES, (0, 1)):
        grid = MODULE.generate(41, index, difficulty="hard", scene_profile=profile)
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_hard_tall_profile_reaches_30_by_30_output_with_content():
    grids = [MODULE.generate(seed, 0, difficulty="hard", scene_profile="tall_asymmetric")
             for seed in range(120)]
    boundaries = [grid for grid in grids if len(grid) == 30 and len(grid[0]) == 15]
    assert boundaries, "hard tall support never reaches the lawful 30x30 output boundary"
    assert any(sum(value != 0 for row in grid for value in row) >= 10 for grid in boundaries)
    assert all(not MODULE.self_check(grid) for grid in grids)
    assert all(len(_gold(grid)) <= 30 and len(_gold(grid)[0]) <= 30 for grid in grids)


def test_teaching_witnesses_remain_near_canonical_area_and_object_count():
    # The first schedule repair taught the rule but displaced the canonical
    # morphology. A small two-color witness suffices; dense noise does not.
    for band, seed in itertools.product(("easy", "medium", "hard"), range(30)):
        grid = MODULE.generate(seed, 0, difficulty=band)
        assert len(grid) * len(grid[0]) <= 36
        assert len(grid[0]) > 3
        assert len({v for row in grid for v in row if v}) >= 2
        assert len(MODULE._components(grid)) <= 2


def test_default_mixture_retains_substantial_canonical_scale_support():
    grids = [MODULE.generate(seed, seed, difficulty="hard") for seed in range(500)]
    canonical = [grid for grid in grids
                 if len(grid) == len(grid[0]) == 3 and len({v for row in grid for v in row}) == 2]
    assert len(canonical) >= 150, (len(canonical), len(grids))
