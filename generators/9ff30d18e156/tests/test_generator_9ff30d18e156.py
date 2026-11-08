"""Task-local regression tests; run explicitly (not in root testpaths)."""
import importlib.util
from pathlib import Path
import sys
from collections import Counter

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'shared/runtime'))
SPEC = importlib.util.spec_from_file_location('review_9ff30d18e156', Path(__file__).resolve().parents[1] / 'generator.py')
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def groups(row):
    return {v: [i for i, x in enumerate(row) if x == v] for v, n in Counter(row).items() if v and n >= 2}


def active_rows(grid):
    return sum(any(any(row[c] != v for c in range(min(cs), max(cs) + 1)) for v, cs in groups(row).items()) for row in grid)


@pytest.mark.parametrize('height,width', [(7,10),(8,12),(9,11),(8,13),(3,8),(10,14)])
def test_documented_dimensions_are_supported(height, width):
    grid = gen.generate(17, 0, grid_h=height, grid_w=width)
    assert (len(grid), len(grid[0])) == (height, width)
    assert gen.self_check(grid) == []


@pytest.mark.parametrize('n', [1,2,3,4,5])
def test_active_row_override_is_exact(n):
    grid = gen.generate(13, 1, grid_h=8, n_pairs=n)
    assert active_rows(grid) == n


def test_one_cell_gap_is_a_lawful_nonidentity_example():
    assert gen.self_check([[0,0,0], [2,0,2], [0,0,0]]) == []


@pytest.mark.parametrize('bad', [[], [[]], [[0,2],[0]], [[-1,0],[0,0]], [[True,0,True]], [[2.0,0,2.0]], [[10,0,10]], '202'])
def test_validator_rejects_malformed_without_crashing(bad):
    assert gen.self_check(bad)


@pytest.mark.parametrize('kwargs', [{'typo':2},{'grid_h':True},{'grid_w':8.5},{'n_pairs':0},{'texture':'typo'}])
def test_bad_overrides_are_rejected(kwargs):
    with pytest.raises(ValueError):
        gen.generate(17, 2, **kwargs)


@pytest.mark.parametrize('texture', ['endpoints','multihit','multicolor','mixed'])
def test_texture_realizes_its_structure(texture):
    for seed in range(10):
        grid = gen.generate(seed, 1, texture=texture, grid_h=5, grid_w=8, n_pairs=3)
        assert gen.self_check(grid) == []
        assert active_rows(grid) == 3
        for row in grid:
            gs = groups(row)
            if not gs:
                continue
            if texture == 'endpoints':
                assert len(gs) == 1 and len(next(iter(gs.values()))) == 2
            elif texture == 'multihit':
                assert len(gs) == 1 and len(next(iter(gs.values()))) >= 3
            elif texture == 'multicolor':
                assert len(gs) == 2 and all(len(cs) == 2 for cs in gs.values())
            else:
                assert len(gs) == 2 and any(len(cs) >= 3 for cs in gs.values())
        assert gen.observe_overrides(grid)['texture'] == texture


def test_impossible_row_count_has_structured_rejection():
    with pytest.raises(ValueError) as caught:
        gen.generate(7, 0, grid_h=3, n_pairs=5)
    assert set(caught.value.incompatible_axes) == {'grid_h','n_pairs'}


def test_seeded_census_is_valid_deterministic_and_color_complete():
    colors = set()
    for band in ('easy','medium','hard'):
        for seed in range(20):
            for index in range(4):
                grid = gen.generate(seed, index, difficulty=band)
                assert grid == gen.generate(seed, index, difficulty=band)
                assert gen.self_check(grid) == []
                assert active_rows(grid) == 3
                colors.update(v for row in grid for v in row)
    assert colors == set(range(10))


def test_public_generation_never_emits_diagnostic_identity_textures():
    for name, grid in gen.mutation_fixtures():
        assert gen.self_check(grid), name
        with pytest.raises(ValueError):
            gen.generate(0, 0, texture=name)


def test_default_anchors_stay_close_to_canonical_geometry():
    for band in ('easy','medium','hard'):
        for seed in range(20):
            grid = gen.generate(seed, 0, difficulty=band)
            assert 7 <= len(grid) <= 9
            assert 10 <= len(grid[0]) <= 13
            active = [i for i, row in enumerate(grid) if groups(row)]
            assert all(b-a >= 2 for a, b in zip(active, active[1:]))


def test_difficulty_changes_defaults_but_not_override_legality():
    assert any(gen.generate(seed,0,difficulty='easy') != gen.generate(seed,0,difficulty='hard') for seed in range(10))
    for band in ('easy','medium','hard'):
        grid = gen.generate(1, 1, difficulty=band, grid_h=3, grid_w=8, n_pairs=1)
        assert (len(grid),len(grid[0]),active_rows(grid)) == (3,8,1)
