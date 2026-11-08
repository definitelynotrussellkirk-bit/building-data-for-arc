"""Focused review regressions; run explicitly, not through root discovery."""
from __future__ import annotations
import importlib.util
import itertools
from pathlib import Path
import pytest

HOME = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('review_generator', HOME / 'generator.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def blank(h=8, w=8):
    return [[0] * w for _ in range(h)]


def independent_expected(grid):
    # Enumerate every rectangle independently of the generator's graph routines.
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for a, b in itertools.combinations(range(h), 2):
        for x, y in itertools.combinations(range(w), 2):
            corners = [(a, x), (a, y), (b, x), (b, y)]
            if sum(grid[r][c] == 2 for r, c in corners) == 3:
                for r, c in corners:
                    if grid[r][c] == 0:
                        out[r][c] = 3
    return out


def test_non_aligned_reds_rejected():
    g = blank()
    for r, c in [(1, 1), (3, 4), (6, 7)]:
        g[r][c] = 2
    assert gen.self_check(g), 'Three non-aligned reds cannot form a rectangle witness'


def test_unrelated_color_does_not_disable_validation():
    g = blank()
    g[0][0] = 7
    assert gen.self_check(g), 'A distractor must not bypass red-geometry validation'


@pytest.mark.parametrize('value', [True, 2.5, '2', None, -1, 10])
def test_invalid_cell_types(value):
    g = blank()
    for r, c in [(1, 1), (1, 4), (4, 1)]:
        g[r][c] = 2
    g[0][0] = value
    assert gen.self_check(g)


@pytest.mark.parametrize('overrides', [
    {'typo_axis': 2}, {'grid_h': True}, {'grid_w': 7.5}, {'grid_h': 3},
    {'grid_w': 21}, {'layout': 'not_a_layout'}, {'n_blockers': 2},
    {'n_distractors': -1}, {'missing_corner': 'tl'}, {'texture': 'only_two_corners'},
])
def test_bad_or_retired_overrides_rejected(overrides):
    with pytest.raises(ValueError):
        gen.generate(42, 0, **overrides)


@pytest.mark.parametrize('layout', ['single', 'separate', 'shared', 'chain'])
@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_controls_and_geometry(layout, band):
    for index, (h, w, noise) in enumerate([(4, 4, 0), (9, 13, 3), (20, 20, 6)]):
        g = gen.generate(17, index, difficulty=band, grid_h=h, grid_w=w,
                         layout=layout, n_blockers=0, n_distractors=noise)
        assert gen.self_check(g) == []
        assert gen.observe_overrides(g) == {
            'grid_h': h, 'grid_w': w, 'layout': layout,
            'n_blockers': 0, 'n_distractors': noise,
        }


def test_incompatible_noise_capacity_rejected_structurally():
    with pytest.raises(ValueError) as exc:
        gen.generate(0, 0, grid_h=4, grid_w=4, layout='shared', n_distractors=6)
    assert set(exc.value.incompatible_axes) >= {'grid_h', 'grid_w', 'n_distractors'}


def test_blocked_single_rejected_instead_of_identity_demo():
    with pytest.raises(ValueError) as exc:
        gen.generate(0, 0, layout='single', n_blockers=1)
    assert set(exc.value.incompatible_axes) == {'layout', 'n_blockers'}


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_each_cyclic_three_demo_window_refutes_declared_rivals(band):
    for seed in [0, 1, 17, 999]:
        for start in range(3):
            grids = [gen.generate(seed, start+i, difficulty=band) for i in range(3)]
            for g in grids:
                assert not gen.self_check(g)
                assert independent_expected(g) != g
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(g) != independent_expected(g) for g in grids), (seed,start,name)


def test_geometry_helpers_agree_with_independent_rectangles():
    for layout in ['single', 'separate', 'shared', 'chain']:
        for i in range(12):
            g = gen.generate(90, i, grid_h=8, grid_w=9, layout=layout,
                             n_blockers=int(layout != 'single'), n_distractors=3)
            assert gen._diagnostic_one_pass(g) == independent_expected(g)
            before = [r[:] for r in g]
            for fn in gen.LESSON_COMPETITORS.values():
                fn(g)
                assert g == before


def test_default_is_deterministic_and_varied():
    grids = [gen.generate(777, i) for i in range(60)]
    assert grids == [gen.generate(777, i) for i in range(60)]
    assert len({str(g) for g in grids}) == 60
    assert {gen.observe_overrides(g)['layout'] for g in grids} == {'single','separate','shared','chain'}


def test_pin_matches_selected_authority():
    assert gen.RULE_HASH == 'bc2eb2b8f3e7'
