"""Behavioral contracts for panel XOR, explicit controls, and lessons.

The pixel oracle is independent of generator helpers. These finite regressions
do not replace the source-bound Racket execution and semantic-gate evidence.
"""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import sys

import pytest

# Resolve the portable helper from this test's own checkout or staged runtime.
for _ancestor in Path(__file__).resolve().parents:
    _helper_dir = _ancestor / 'shared/runtime'
    if (_helper_dir / 'reviewer_support.py').is_file():
        sys.path.insert(0, str(_helper_dir))
        break
    if (_ancestor / 'reviewer_support.py').is_file():
        sys.path.insert(0, str(_ancestor))
        break
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = 'af0ae766e671'
ROOT = find_root(__file__)
PATTERNS = ('random', 'blob', 'stripes', 'checker', 'border', 'diagonal')
BANDS = (None, 'easy', 'medium', 'hard')


@pytest.fixture(scope='module')
def gen():
    return load_selected_generator(TASK, root=ROOT)[0]


def occupancy(grid):
    half_h = len(grid) // 2
    return Counter((bool(grid[r][c]), bool(grid[r + half_h][c]))
                   for r in range(half_h) for c in range(len(grid[0])))


def xor_oracle(grid):
    half_h = len(grid) // 2
    return [[6 if bool(grid[r][c]) != bool(grid[r + half_h][c]) else 0
             for c in range(len(grid[0]))] for r in range(half_h)]


def assert_normal(gen, grid, *, half_h=None, width=None, top=None, bottom=None,
                  target=2):
    assert isinstance(grid, list) and len(grid) % 2 == 0
    assert grid and all(isinstance(row, list) and row for row in grid)
    assert len({len(row) for row in grid}) == 1
    assert all(type(value) is int and 0 <= value <= 9
               for row in grid for value in row)
    h = len(grid) // 2
    if half_h is not None:
        assert h == half_h
    if width is not None:
        assert len(grid[0]) == width
    top_palette = set(value for row in grid[:h] for value in row)
    bot_palette = set(value for row in grid[h:] for value in row)
    assert len(top_palette) == len(bot_palette) == 2
    assert 0 in top_palette and 0 in bot_palette
    assert len(top_palette | bot_palette) == 3
    if top is not None:
        assert top_palette == {0, top}
    if bottom is not None:
        assert bot_palette == {0, bottom}
    states = occupancy(grid)
    assert set(states) == {(False, False), (False, True), (True, False), (True, True)}
    assert states[(False, True)] + states[(True, False)] >= max(2, target)
    assert gen.self_check(deepcopy(grid)) == []


@pytest.mark.parametrize('pair', canonical_pairs(TASK, root=ROOT),
                         ids=lambda p: f"v{p['variant']}-{p['split']}-{p['pair_index']}")
def test_canonical_examples_are_in_domain_and_match_independent_xor(gen, pair):
    assert_normal(gen, pair['input'], half_h=3, width=5, top=9, bottom=4)
    assert xor_oracle(pair['input']) == pair['output']


@pytest.mark.parametrize('pattern', PATTERNS)
@pytest.mark.parametrize('densities', [(0, 0), (0, 1), (1, 0), (1, 1)])
def test_density_endpoints_and_structured_proposals_preserve_full_truth_table(gen, pattern, densities):
    grid = gen.generate(0, 0, half_h=3, grid_w=3, top_color=2, bot_color=4,
                        panel_pattern=pattern, top_density=densities[0],
                        bot_density=densities[1])
    assert_normal(gen, grid, half_h=3, width=3, top=2, bottom=4)


@pytest.mark.parametrize('shape', [(1, 4), (2, 2), (4, 1), (15, 30)])
@pytest.mark.parametrize('band', BANDS)
def test_exact_dimensions_include_area_four_boundaries_and_full_axis_range(gen, shape, band):
    h, w = shape
    grid = gen.generate(19, 3, difficulty=band, half_h=h, grid_w=w,
                        top_color=6, bot_color=9)
    assert_normal(gen, grid, half_h=h, width=w, top=6, bottom=9)


@pytest.mark.parametrize('target', [1, 2, 3, 7])
@pytest.mark.parametrize('pattern', PATTERNS)
def test_xor_target_is_a_lower_bound_and_repairs_filled_and_empty_agreements(gen, target, pattern):
    grid = gen.generate(0, 0, half_h=3, grid_w=3, top_color=2, bot_color=4,
                        panel_pattern=pattern, top_density=1, bot_density=1,
                        xor_target=target)
    assert_normal(gen, grid, half_h=3, width=3, top=2, bottom=4, target=target)


@pytest.mark.parametrize('kwargs', [
    {'seed': True}, {'seed': -1}, {'seed': 1.0}, {'seed': '1'},
    {'sample_index': True}, {'sample_index': -1}, {'sample_index': 1.0}, {'sample_index': '1'},
    {'difficulty': 'unknown'}, {'difficulty': False}, {'difficulty': 1},
])
def test_invalid_draw_identity_is_rejected_explicitly(gen, kwargs):
    call = {'seed': 0, 'sample_index': 0}
    call.update(kwargs)
    with pytest.raises(ValueError):
        gen.generate(**call)


@pytest.mark.parametrize('axis', ['half_h', 'grid_w', 'top_color', 'bot_color', 'xor_target'])
@pytest.mark.parametrize('value', [True, 1.0, '1', 0, -1])
def test_exact_integer_controls_reject_wrong_types_and_lower_out_of_range(gen, axis, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{axis: value})


@pytest.mark.parametrize('overrides', [
    {'half_h': 16}, {'grid_w': 31}, {'top_color': 10}, {'bot_color': 10},
    {'top_color': 2, 'bot_color': 2},
    {'half_h': 1, 'grid_w': 1}, {'half_h': 1, 'grid_w': 3},
    {'half_h': 3, 'grid_w': 3, 'xor_target': 8},
    {'panel_pattern': 'unknown'}, {'texture': 'unknown'}, {'unknown_control': 1},
])
def test_impossible_or_unknown_controls_are_rejected(gen, overrides):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize('axis', ['top_density', 'bot_density'])
@pytest.mark.parametrize('value', [True, '0.5', -0.01, 1.01, float('nan'),
                                  float('inf'), float('-inf')])
def test_density_proposals_require_finite_numbers_in_unit_interval(gen, axis, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{axis: value})


@pytest.mark.parametrize('axis', ['top_density', 'bot_density'])
def test_none_density_proposal_equals_omission(gen, axis):
    # GenCtx's public contract treats None as an omitted override.
    assert gen.generate(17, 3, **{axis: None}) == gen.generate(17, 3)


@pytest.mark.parametrize('grid', [
    None, [], [[]], [[0], [0, 1]], [[0]], [[False], [1]],
    [[0.0], [1]], [['0'], [1]], [[-1], [1]], [[10], [1]],
    [[0, 2], [2, 0], [0, 2], [2, 0]],
    [[0, 2], [2, 0], [3, 0], [0, 3]],
    [[0, 2], [2, 0], [0, 2], [2, 0]],
    [[0, 2], [3, 0], [0, 4], [4, 0]],
])
def test_self_check_reports_malformed_or_unteachable_grids_without_crashing(gen, grid):
    errors = gen.self_check(deepcopy(grid))
    assert isinstance(errors, list) and errors


@pytest.mark.parametrize('name', ['same_halves', 'disjoint_halves', 'all_filled'])
def test_negative_diagnostic_textures_are_rejected_by_self_check(gen, name):
    grid = gen.generate(0, 0, texture=name)
    assert gen.self_check(grid)
    assert name not in gen.AXES['texture']['valid'].split('|')


def test_seeded_draws_are_reproducible_without_shared_rng_state(gen):
    controls = dict(half_h=5, grid_w=9, top_color=2, bot_color=4, panel_pattern='random')
    original = gen.generate(42, 7, **controls)
    untouched = deepcopy(original)
    gen.generate(43, 8, **controls)
    assert original == untouched
    assert gen.generate(42, 7, **controls) == original
    diverse = [gen.generate(seed, 7, **controls) for seed in range(4)]
    assert len({str(grid) for grid in diverse}) > 1
    assert_normal(gen, gen.generate(2**32 - 1, 0, **controls))


@pytest.mark.parametrize('band', BANDS)
@pytest.mark.parametrize('start', range(4))
def test_default_schedule_has_shape_and_palette_transfer_in_each_three_demo_window(gen, band, start):
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    grids = [gen.generate(17, index, difficulty=band) for index in range(start, start + 3)]
    for index, grid in zip(range(start, start + 3), grids):
        assert_normal(gen, grid)
        canonical_shape = (len(grid), len(grid[0])) == (6, 5)
        assert canonical_shape == (index % 4 in (0, 1))
        h = len(grid) // 2
        foreground = next(v for row in grid[:h] for v in row if v)
        if index % 4 in (0, 2):
            assert_normal(gen, grid, top=9, bottom=4)
        else:
            assert foreground != 9
    assert any((len(g), len(g[0])) == (6, 5) for g in grids)
    assert any((len(g), len(g[0])) != (6, 5) for g in grids)


def test_explicit_shape_and_palette_controls_override_schedule(gen):
    for index in range(4):
        grid = gen.generate(17, index, half_h=4, grid_w=7, top_color=6, bot_color=8)
        assert_normal(gen, grid, half_h=4, width=7, top=6, bottom=8)


def test_canonical_shortcuts_fit_canonical_and_are_refuted_in_every_demo_window(gen):
    shortcuts = gen.CANONICAL_SHORTCUTS
    assert isinstance(shortcuts, dict) and len(shortcuts) >= 2
    pairs = canonical_pairs(TASK, root=ROOT)
    for name, rival in shortcuts.items():
        assert callable(rival), name
        assert all(rival(deepcopy(p['input'])) == p['output'] for p in pairs), name
        for start in range(4):
            grids = [gen.generate(17, index) for index in range(start, start + 3)]
            assert any(rival(deepcopy(g)) != xor_oracle(g) for g in grids), (name, start)


def test_full_truth_table_refutes_every_other_pointwise_boolean_operation(gen):
    grid = gen.generate(7, 0)
    states = occupancy(grid)
    assert len(states) == 4
    truth_table = [(False, False), (False, True), (True, False), (True, True)]
    xor_bits = (0, 1, 1, 0)
    for competitor_bits in range(16):
        bits = tuple((competitor_bits >> index) & 1 for index in range(4))
        if bits == xor_bits:
            continue
        assert any(bits[index] != xor_bits[index] and states[state]
                   for index, state in enumerate(truth_table))
