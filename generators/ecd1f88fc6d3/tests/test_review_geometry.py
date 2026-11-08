"""Regression tests for review-201ae2dcbb09941c (independent rivals)."""
from test_generator_ecd1f88fc6d3 import gen, _CANONICAL_PAIRS
import pytest


def geometry_only(grid):
    """Wrong rule: any adjacent code cell points away from any seed, ignoring code."""
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    # Order by marker, then seed: not the generator's analyzer/mirror.
    for r in range(h):
        for c in range(w):
            if grid[r][c] not in (1, 2, 3, 4):
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                sr, sc = r - dr, c - dc
                if 0 <= sr < h and 0 <= sc < w and grid[sr][sc] >= 5:
                    rr, cc = sr, sc
                    while 0 <= rr < h and 0 <= cc < w:
                        out[rr][cc] = grid[sr][sc]
                        rr += dr
                        cc += dc
    return out


def morphology(grid):
    return tuple(tuple(5 if v >= 5 else v for v in row) for row in grid)


def test_code_blind_geometry_rival_fits_all_public_examples():
    for grid, output in _CANONICAL_PAIRS:
        assert geometry_only(grid) == output


@pytest.mark.parametrize('profile', gen.SCHEDULE_PROFILES)
def test_fixed_shape_profiles_have_real_layout_diversity(profile):
    shapes = {morphology(gen.generate(s, 2, grid_h=7, grid_w=7,
                                     scene_profile=profile)) for s in range(80)}
    assert len(shapes) >= 60, (profile, len(shapes))


@pytest.mark.parametrize('band', [None, 'easy', 'medium', 'hard'])
def test_every_distractor_sample_refutes_code_blind_geometry(band):
    for seed in range(12):
        for h, w in ((7, 7), (7, 9), (9, 7), (9, 9)):
            grid = gen.generate(seed, 2, difficulty=band, grid_h=h, grid_w=w,
                                scene_profile='canonical_distractor')
            assert geometry_only(grid) != gen.rule_mirror(grid), (seed, h, w, band)


def test_nonoverlap_is_an_enforced_invariant_not_just_a_sampling_accident():
    # Still the 'small' signature, but active rays intersect at (2,3).
    grid = [[0] * 7 for _ in range(7)]
    grid[2][1], grid[2][2] = 5, 4
    grid[0][3], grid[1][3] = 6, 2
    assert gen.self_check(grid), 'crossing rays must not enter the no-precedence domain'


def test_none_overrides_are_consistently_treated_as_unspecified():
    # The shared GenCtx API treats None as no override.
    for name in gen.AXES:
        assert gen.generate(12, 2, **{name: None}) == gen.generate(12, 2)


@pytest.mark.parametrize('band', [None, 'easy', 'medium', 'hard'])
def test_geometry_rival_is_refuted_in_every_three_example_lesson(band):
    for seed in (0, 17, 223):
        for start in range(6):
            demos = [gen.generate(seed, start+i, difficulty=band) for i in range(3)]
            assert any(geometry_only(g) != gen.rule_mirror(g) for g in demos)


def test_all_small_crossproducts_stay_nonintersecting_and_observable():
    for profile in gen.SCHEDULE_PROFILES:
        for h in (7, 8, 9):
            for w in (7, 8, 9):
                for seed in range(4):
                    kw = dict(scene_profile=profile, grid_h=h, grid_w=w)
                    g = gen.generate(seed, 3, **kw)
                    assert gen.self_check(g, meta={'overrides': kw}) == []
                    assert gen.observe_overrides(g) == kw
                    rays = [set(e['ray']) for e in gen._analyze(g)['emitters']]
                    assert all(not a & b for i, a in enumerate(rays) for b in rays[i+1:])
