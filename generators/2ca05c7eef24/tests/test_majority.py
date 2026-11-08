"""Behavioral regressions for exact controls and three-panel voting.

Expectations come from literal vote examples, observed input structure, and
the immutable canonical pairs. Actual Racket parity is checked separately.
"""
import copy
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


@pytest.fixture(scope='module')
def gen():
    path = Path(__file__).resolve().parents[1] / 'generator.py'
    spec = importlib.util.spec_from_file_location('majority_review_subject', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def canonical():
    return canonical_pairs('2ca05c7eef24', root=find_root(__file__))


def scene(values):
    grid = [[0, 0, 5, 0, 0, 5, 0, 0] for _ in range(3)]
    for start, value in zip((0, 3, 6), values):
        grid[0][start] = value
    return grid


def votes(grid):
    width = (len(grid[0]) - 2) // 3
    return [tuple(grid[r][c + p * (width + 1)] for p in range(3))
            for r in range(len(grid)) for c in range(width)]


def colors(grid):
    return {v for row in grid for v in row} - {0, 5}


def panel_counts(grid):
    return tuple(sum(v[p] != 0 for v in votes(grid)) for p in range(3))


@pytest.mark.parametrize('values,want', [
    ((0, 0, 0), 0), ((2, 0, 0), 0), ((0, 9, 0), 0),
    ((2, 2, 0), 2), ((2, 7, 0), 7), ((7, 0, 2), 7),
    ((2, 2, 9), 2), ((9, 2, 2), 2), ((2, 9, 2), 2),
    ((2, 9, 9), 9), ((9, 2, 9), 9),
    ((1, 4, 9), 9), ((9, 1, 4), 9), ((6, 6, 6), 6),
])
def test_literal_votes_use_frequency_before_numeric_tie_break(gen, values, want):
    assert gen.apply_rule(scene(values)) == [[want, 0], [0, 0], [0, 0]]


def test_all_canonical_pairs_remain_accepted_and_exact(gen, canonical):
    for pair in canonical:
        assert gen.self_check(pair['input']) == []
        assert gen.apply_rule(pair['input']) == pair['output']


@pytest.mark.parametrize('bad', [None, 4, [], [[]], [None], ['00050005000'],
                                 [[5, 5]], [[5, 5, 5]], [[0, 5, 0], [0, 5]],
                                 [[0] * 11 for _ in range(3)]])
def test_validator_rejects_malformed_or_missing_panel_geometry(gen, bad):
    result = gen.self_check(bad)
    assert isinstance(result, list) and result


@pytest.mark.parametrize('value', [True, False, 1.0, '1', [], {}, None, -1, 10, 5])
def test_validator_rejects_noninteger_or_separator_foreground_cells(gen, value):
    grid = scene((2, 2, 0))
    grid[1][0] = value
    assert gen.self_check(grid)


def test_metadata_cannot_bypass_structural_validation(gen):
    assert gen.self_check([[1]], meta={'texture': 'no_separators'})


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
@pytest.mark.parametrize('height,width', [(3, 2), (3, 6), (7, 2), (7, 6)])
def test_dimension_endpoints_work_in_every_band(gen, band, height, width):
    grid = gen.generate(23, 3, difficulty=band, h=height, pw=width)
    assert (len(grid), len(grid[0])) == (height, 3 * width + 2)
    assert gen.self_check(grid) == []


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
@pytest.mark.parametrize('count', [1, 2, 6, 18])
def test_requested_cell_count_is_exact_in_each_panel(gen, band, count):
    grid = gen.generate(11, 3, difficulty=band, n_cells=count)
    assert panel_counts(grid) == (count, count, count)
    assert gen.observe_overrides(grid)['n_cells'] == count


@pytest.mark.parametrize('axis', ['palette_size', 'n_distinct_colors'])
@pytest.mark.parametrize('count', [1, 2, 3, 8])
def test_foreground_palette_controls_are_observable(gen, axis, count):
    grid = gen.generate(31, 3, **{axis: count})
    assert len(colors(grid)) == count
    assert gen.observe_overrides(grid)[axis] == count


@pytest.mark.parametrize('texture', ['no_overlap', 'all_overlap'])
def test_lawful_edge_textures_honor_other_exact_controls(gen, texture):
    grid = gen.generate(19, 3, difficulty='easy', texture=texture,
                        h=7, pw=6, n_cells=2, palette_size=3)
    assert (len(grid), len(grid[0])) == (7, 20)
    assert panel_counts(grid) == (2, 2, 2)
    assert len(colors(grid)) == 3
    active = [sum(x != 0 for x in row) for row in votes(grid) if any(row)]
    assert set(active) == ({1} if texture == 'no_overlap' else {3})
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid)['texture'] == texture


@pytest.mark.parametrize('options', [
    {'palette_size': 2, 'n_distinct_colors': 3},
    {'palette_size': 8, 'n_cells': 1},
    {'h': 3, 'pw': 2, 'n_cells': 6},
    {'h': 3, 'pw': 2, 'n_cells': 3, 'texture': 'no_overlap'},
])
def test_impossible_joint_requests_are_structured_rejections(gen, options):
    with pytest.raises(ValueError) as info:
        gen.generate(13, 3, **options)
    axes = set(getattr(info.value, 'incompatible_axes', ()))
    assert len(axes) >= 2 and axes <= set(options)


@pytest.mark.parametrize('options', [
    {'h': True}, {'h': 3.0}, {'h': '3'}, {'pw': 2.0},
    {'n_cells': False}, {'n_cells': 1.5}, {'palette_size': True},
    {'n_distinct_colors': '2'}, {'palette_kind': 'unknown'},
    {'position_bias': 'unknown'}, {'texture': 'no_separators'},
    {'density': 'sparse'}, {'unknown_control': 3},
])
def test_invalid_types_and_obsolete_or_unknown_controls_reject(gen, options):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(9, 3, **options)


def test_none_retains_the_public_no_override_convention(gen):
    assert gen.generate(17, 3) == gen.generate(17, 3, h=None, pw=None, palette_size=None)


def test_explicit_default_descriptors_preserve_the_ordinary_curriculum(gen):
    for band in ('easy', 'medium', 'hard'):
        for i in range(8):
            assert gen.generate(0, i, difficulty=band) == gen.generate(
                0, i, difficulty=band, texture='default', palette_kind='default',
                position_bias='three_panels_5col_split')


def test_ordinary_samples_expose_color_voting_not_only_color_count(gen):
    drawn = [gen.generate(0, i, difficulty='medium') for i in range(16)]
    assert any(any(len(set(v) - {0}) >= 2 for v in votes(g)) for g in drawn)
    assert any(any(len(set(v)) == 3 and 0 not in v for v in votes(g)) for g in drawn)
    assert any(len(colors(g)) == 1 for g in drawn)


def test_each_rotated_ordinary_lesson_refutes_declared_rivals(gen):
    for band in ('easy', 'medium', 'hard'):
        grids = [gen.generate(0, i, difficulty=band) for i in range(12)]
        for start in range(8):
            pairs = [{'input': g, 'output': gen.apply_rule(g)} for g in grids[start:start + 4]]
            for held in range(4):
                demos = pairs[:held] + pairs[held + 1:]
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(p['input']) != p['output'] for p in demos), (band, start, held, name)
                assert gen.lesson_identifiable(demos, pairs[held]['input']) == []


def test_canonical_only_lesson_reports_a_color_shortcut(gen, canonical):
    reasons = gen.lesson_identifiable(canonical[:2], scene((2, 2, 9)))
    assert any('threshold_max' in reason for reason in reasons)


def test_every_band_keeps_both_canonical_geometry_profiles(gen):
    for band in ('easy', 'medium', 'hard'):
        found = set()
        for i in range(20):
            grid = gen.generate(0, i, difficulty=band)
            if len(colors(grid)) == 1:
                found.add((len(grid), len(grid[0])))
        assert {(3, 11), (4, 14)} <= found


def test_each_eight_draw_window_retains_three_canonical_scale_monochrome_inputs(gen):
    for band in ('easy', 'medium', 'hard'):
        for seed in range(4):
            for start in range(8):
                grids = [gen.generate(seed, i, difficulty=band) for i in range(start, start + 8)]
                mono = [g for g in grids if len(colors(g)) == 1]
                assert len(mono) >= 3
                assert all((len(g), len(g[0])) in {(3, 11), (4, 14)} for g in mono)
                assert any(len(colors(g)) == 2 for g in grids)


def test_unconstrained_panel_count_has_truthful_public_draw_provenance(gen):
    from puzzle_generators.base import set_ctx_observer
    for band in ('easy', 'medium', 'hard'):
        for i in range(16):
            captured = []
            set_ctx_observer(captured.append)
            try:
                grid = gen.generate(0, i, difficulty=band)
            finally:
                set_ctx_observer(None)
            assert len(captured) == 1
            draws = captured[0].recorded_draws()
            assert 'n_cells' in draws
            assert draws['n_cells'] == gen.observe_overrides(grid)['n_cells']


def test_generation_and_voting_do_not_mutate_prior_inputs(gen):
    grid = gen.generate(101, 2, difficulty='hard')
    frozen = copy.deepcopy(grid)
    gen.apply_rule(grid)
    gen.observe_overrides(grid)
    assert grid == frozen == gen.generate(101, 2, difficulty='hard')
    assert any(gen.generate(11, i, difficulty='easy') != gen.generate(11, i, difficulty='hard')
               for i in range(8))


@pytest.mark.parametrize('name', ['global_rarity_tie', 'first_seen_tie'])
def test_retained_reference_lesson_ambiguities_are_reported(gen, name):
    path = Path(__file__).resolve().parents[1] / 'counterexamples' / (name + '_lesson.json')
    lesson = json.loads(path.read_text())
    rival = gen.LESSON_COMPETITORS[name]
    for pair in lesson['demos']:
        assert gen.apply_rule(pair['input']) == pair['output']
        assert rival(pair['input']) == pair['output']
    query = lesson['query']
    assert gen.apply_rule(query['input']) == query['output']
    assert rival(query['input']) == query['rival_output'] != query['output']
    assert any(name in reason for reason in gen.lesson_identifiable(lesson['demos'], query))


def test_three_color_draws_refute_global_frequency_and_scan_priority(gen):
    names = {'global_rarity_tie', 'global_commonness_tie', 'first_seen_tie', 'last_seen_tie'}
    assert names <= set(gen.LESSON_COMPETITORS)
    for band in ('easy', 'medium', 'hard'):
        for seed in range(6):
            for i in range(8):
                grid = gen.generate(seed, i, difficulty=band)
                if len(colors(grid)) == 3:
                    expected = gen.apply_rule(grid)
                    assert all(rival(grid) != expected for rival in gen.LESSON_COMPETITORS.values())


def test_unlucky_scan_order_has_a_bounded_lawful_fallback(gen, monkeypatch):
    from puzzle_generators.base import GenCtx
    original = GenCtx.draw_rng
    calls = []

    class UnluckyLayout:
        def sample(self, population, k):
            calls.append(k)
            assert len(calls) < 1000, 'generation must have a bounded fallback'
            return ([2, 1, 0] if k == 3 else
                    [2, 3, 4, 5, 1, 0, 6] + list(range(7, len(population))))

        def choice(self, population):
            return 0

    def controlled_rng(self, label):
        return UnluckyLayout() if label == 'voting_layout' else original(self, label)

    monkeypatch.setattr(GenCtx, 'draw_rng', controlled_rng)
    grid = gen.generate(0, 2, difficulty='hard')
    assert gen.self_check(grid) == [] and len(colors(grid)) == 3
    assert len(calls) > 2
    expected = gen.apply_rule(grid)
    assert all(rival(grid) != expected for rival in gen.LESSON_COMPETITORS.values())
