"""Regression tests for demonstrated rotation meanings and portable semantics."""
from collections import Counter
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator('33c7c507a8ef', root=ROOT)


def label(grid):
    """Independent NumPy rotation for unit tests; full checks use Racket."""
    gray = [(r, c) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value == 5]
    top = min(r for r, _ in gray)
    bottom = max(r for r, _ in gray)
    left = min(c for _, c in gray)
    right = max(c for _, c in gray)
    interior = [row[left + 1:right] for row in grid[top + 1:bottom]]
    return np.rot90(interior, 1 - grid[0][0]).tolist()


def compact_gray_half_turn(grid):
    """A size-conditioned color cue that fits the intermediate v4 curriculum."""
    gray = [(r, c) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value == 5]
    top, bottom = min(r for r, _ in gray), max(r for r, _ in gray)
    left, right = min(c for _, c in gray), max(c for _, c in gray)
    interior = [row[left + 1:right] for row in grid[top + 1:bottom]]
    if ((len(grid), len(grid[0])) == (5, 6)
            and any(value == 5 for row in interior for value in row)):
        return np.rot90(interior, 2).tolist()
    return label(grid)


@pytest.fixture(scope='module')
def compact_schedule_seeds():
    # Discover public seeds from observed codes and the exposed schedule slot.
    # No literal compact/expanded table is copied into these checks.
    representatives = {}
    for seed in range(256):
        positions = {}
        for index in range(4):
            grid = GEN.generate(seed, index, difficulty='easy')
            positions[grid[0][0]] = GEN.schedule_profile(seed, index) % 4
        key = (positions[1], positions[3])
        representatives.setdefault(key, seed)
        if len(representatives) == 12:
            break
    assert set(representatives) == {(a, b) for a in range(4)
                                   for b in range(4) if a != b}
    return representatives


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
@pytest.mark.parametrize('seed', [0, 17, 918])
def test_every_eight_pair_window_demonstrates_each_code_twice(band, seed):
    # Independent draws used to omit the query code. Eight scheduled pairs
    # permit any one query holdout while still teaching all four meanings.
    grids = [GEN.generate(seed, i, difficulty=band) for i in range(23)]
    for start in range(16):
        window = grids[start:start + 8]
        assert Counter(g[0][0] for g in window) == {1: 2, 2: 2, 3: 2, 4: 2}
        assert len({tuple(map(tuple, g)) for g in window}) == 8
        for code in (1, 2, 3, 4):
            gray_states = {GEN.observe_overrides(g)['include_frame_color']
                           for g in window if g[0][0] == code}
            assert gray_states == {False, True}


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_schedule_preserves_all_three_linked_public_profiles(band):
    for seed in (0, 17, 918):
        signatures = [GEN.canonical_profile_signature(
            GEN.generate(seed, i, difficulty=band)) for i in range(16)]
        public = [signature for signature in signatures if signature is not None]
        assert len(public) == 3
        assert {signature[3] for signature in public} == {2, 3, 4}


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_compact_generalizations_preserve_size_palette_support(band):
    # A strict exact-role prior need not be the only source of small examples.
    # Ten cases retain the public 5x6/four-color envelope; seven of them vary
    # the interior beyond the public hook. Six expanded cases retain enough
    # fixed-crop counterexamples when any query position is held out.
    for seed in (0, 17, 918):
        grids = [GEN.generate(seed, i, difficulty=band) for i in range(16)]
        compact = [grid for grid in grids if len(grid) == 5 and len(grid[0]) == 6
                   and len({value for row in grid for value in row}) == 4]
        assert len(compact) == 10
        assert sum(GEN.canonical_profile_signature(grid) is not None
                   for grid in compact) == 3
        assert all(GEN.self_check(grid) == [] for grid in compact)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_compact_gray_states_cross_every_code_for_all_seed_orders(band, compact_schedule_seeds):
    for order_key, seed in compact_schedule_seeds.items():
        grids = [GEN.generate(seed, index, difficulty=band) for index in range(16)]
        compact = [grid for grid in grids if (len(grid), len(grid[0])) == (5, 6)]
        states = {code: set() for code in (1, 2, 3, 4)}
        for grid in compact:
            observed = GEN.observe_overrides(grid)
            states[observed['code']].add(observed['include_frame_color'])
        assert states == {code: {False, True} for code in (1, 2, 3, 4)}, (order_key, seed)
        assert len(compact) == 10, (order_key, seed)
        assert sum(GEN.canonical_profile_signature(grid) is not None
                   for grid in grids) == 3, (order_key, seed)


def test_compact_gray_rival_is_refuted_by_the_reproduced_seven_demo_lesson():
    demos = [GEN.generate(17, index, difficulty='easy') for index in range(7)]
    canonical_gray = next(pair['input'] for pair in canonical_pairs(GEN.TASK_ID, root=ROOT)
                          if pair['input'][0][0] == 3)
    query = deepcopy(canonical_gray)
    query[0][0] = 2
    assert GEN.self_check(query) == []
    assert compact_gray_half_turn(query) != label(query)
    assert any(compact_gray_half_turn(grid) != label(grid) for grid in demos)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_compact_and_fixed_crop_rivals_have_two_witnesses_in_every_eight_pair_window(
        band, compact_schedule_seeds):
    rivals = {'compact_gray_half_turn': compact_gray_half_turn,
              'fixed_public_crop': GEN.SEMANTIC_RIVALS['fixed_public_crop']}
    for order_key, seed in compact_schedule_seeds.items():
        grids = [GEN.generate(seed, index, difficulty=band) for index in range(23)]
        pairs = [(grid, label(grid)) for grid in grids]
        for start in range(16):
            for name, rival in rivals.items():
                refutations = sum(rival(grid) != expected
                                  for grid, expected in pairs[start:start + 8])
                # Holding out any one pair must leave a demonstrated refutation.
                assert refutations >= 2, (order_key, seed, start, name, refutations)


def test_canonical_support_and_declared_shortcuts_are_honest():
    pairs = canonical_pairs(GEN.TASK_ID, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair['input']) == []
        assert GEN.strict_canonical_like(pair['input']) == []
        assert label(pair['input']) == pair['output']
        for name, rival in GEN.CANONICAL_SHORTCUTS.items():
            assert rival(deepcopy(pair['input'])) == pair['output'], name


def test_query_coverage_uses_visible_examples_and_does_not_read_query_answer():
    # The query code must be demonstrated even if an arbitrary answer is passed.
    query_grid = GEN.generate(5, 10, scene_family='generalized', code=1)
    demos = [{'input': GEN.generate(5, i, scene_family='generalized', code=code)}
             for i, code in enumerate((2, 3, 4))]
    for demo in demos:
        demo['output'] = label(demo['input'])
    query = {'input': query_grid, 'output': [[9]]}
    assert GEN.lesson_identifiable(demos, query)
    seen = {'input': query_grid, 'output': label(query_grid)}
    assert GEN.lesson_identifiable(demos + [seen], query) == []


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_declared_rivals_do_not_leave_ambiguous_query_rotations(band):
    grids = [GEN.generate(17, i, difficulty=band) for i in range(23)]
    pairs = [{'input': grid, 'output': label(grid)} for grid in grids]
    for start in range(16):
        window = pairs[start:start + 8]
        for held in range(8):
            query = window[held]
            demos = window[:held] + window[held + 1:]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                fits = all(rival(deepcopy(p['input'])) == p['output'] for p in demos)
                assert not fits or rival(deepcopy(query['input'])) == query['output'], (
                    band, start, held, name)


def test_every_declared_schedule_profile_matches_the_generated_branch():
    assert GEN.EXAMPLES_NEEDED == 7
    assert GEN.LESSON_SCHEDULE_PERIOD == 16
    for seed in (0, 17, 918):
        for i in range(16):
            assert GEN.schedule_profile(seed, i) == GEN.schedule_profile(seed, i + 16)
        assert {GEN.schedule_profile(seed, i) for i in range(16)} == set(GEN.SCHEDULE_PROFILES)
