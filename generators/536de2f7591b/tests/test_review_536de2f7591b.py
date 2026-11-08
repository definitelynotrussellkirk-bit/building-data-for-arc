"""Task-local regression tests; execute explicitly (not in repo testpaths)."""
from pathlib import Path
import importlib.util
import json
import sys
import pytest

from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
spec = importlib.util.spec_from_file_location('review_536de2f7591b', ROOT / 'generators/536de2f7591b/generator.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def canonical():
    return next(
        json.loads(line)
        for line in canonical_path(ROOT).read_text(encoding='utf-8').splitlines()
        if json.loads(line).get('task_id') == '536de2f7591b'
    )

@pytest.mark.parametrize('index', range(4))
def test_accepts_canonical_block_inputs(index):
    row = canonical()
    assert gen.self_check((row['train'] + row['test'])[index]['input']) == []

def test_default_population_contains_two_cell_blocks():
    grids = [gen.generate(17, i, difficulty='medium') for i in range(12)]
    assert any(any(row.count(3) >= 2 for row in g) for g in grids)



@pytest.mark.parametrize('seed', [True, False, 1.0, 1.75, '1'])
def test_rejects_non_integer_seed_scalars(seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, 0)


@pytest.mark.parametrize('sample_index', [True, False, -1, 1.0, '1'])
def test_rejects_invalid_sample_index_scalars(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, sample_index)


def test_unknown_control_is_not_silently_swallowed():
    with pytest.raises(ValueError):
        gen.generate(0, 0, typo_control=1)

def test_validator_rejects_ragged_and_invalid_colors_without_crashing():
    for g in ([[0,3],[8]], [[0]*6 for _ in range(5)], [[False,8,0,0,0,3]]*5,
              [[0,8,0,0,99,3]]*5):
        assert gen.self_check(g)

def test_selected_authority_is_exact_canonical_text():
    base = json.loads((ROOT/'shared/data/base/solutions/training/9c56f360__536de2f7591b.json').read_text())
    assert base['racket_target']['target_code'] == canonical()['program_solution']

@pytest.mark.parametrize('band', [None, 'easy', 'medium', 'hard'])
def test_default_cycles_supply_every_declared_witness(band):
    for seed in range(20):
        for start in range(4):
            grids = [gen.generate(seed, start+i, difficulty=band) for i in range(gen.EXAMPLES_NEEDED)]
            assert all(gen.self_check(g) == [] for g in grids)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                assert any(witness(g) for g in grids), (seed, start, name)


@pytest.mark.parametrize('band', [None, 'easy', 'medium', 'hard'])
def test_every_query_rotation_of_five_default_pairs_keeps_each_rival_witness(band):
    for seed in range(20):
        for start in range(4):
            grids = [gen.generate(seed, start+i, difficulty=band) for i in range(gen.EXAMPLES_NEEDED + 1)]
            for query_index in range(len(grids)):
                demonstrations = [g for i, g in enumerate(grids) if i != query_index]
                for name, witness in gen.SEMANTIC_WITNESSES.items():
                    assert any(witness(g) for g in demonstrations), (
                        seed, start, query_index, band, name
                    )

@pytest.mark.parametrize('band', [None, 'easy', 'medium', 'hard'])
def test_exact_controls_at_crossed_boundaries(band):
    from itertools import product
    for h, w, count, width, distractors in product((5, 6, 18), (6, 20), (1, 5, 6), (1, 2, 3), (0, 3)):
        ov = dict(grid_h=h, grid_w=w, n_green_rows=count, max_block_width=width, n_distractors=distractors)
        for start in range(4):
            if count > h:
                with pytest.raises(ValueError):
                    gen.generate(271, start, difficulty=band, **ov)
                continue
            g = gen.generate(271, start, difficulty=band, **ov)
            assert gen.self_check(g) == [], (ov, gen.self_check(g))
            assert gen.observe_overrides(g) == ov
            assert g == gen.generate(271, start, difficulty=band, **ov)

@pytest.mark.parametrize('name', ['grid_h', 'grid_w', 'n_green_rows', 'max_block_width', 'n_distractors'])
@pytest.mark.parametrize('value', [True, 2.5, '2', -1, 100])
def test_invalid_exact_values_are_rejected(name, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{name: value})

def test_canonical_shortcuts_actually_fit_every_canonical_pair():
    row = canonical()
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(p['input']) == p['output'] for p in row['train'] + row['test']), name

@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_core_profiles_keep_canonical_size_support(band):
    for seed in range(10):
        for index in (0, 3):
            g = gen.generate(seed, index, difficulty=band)
            assert (len(g), len(g[0])) in {(7, 6), (7, 8), (9, 8), (9, 9)}
