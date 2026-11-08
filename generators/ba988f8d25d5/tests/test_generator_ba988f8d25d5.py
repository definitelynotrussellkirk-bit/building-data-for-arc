"""Task-local regressions; runnable directly from the repository with pytest."""
from __future__ import annotations

import copy
import importlib.util
import itertools
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'shared/runtime'))
from arc_repl.grid_ops import find_objects, find_objects_multicolor

TASK = 'ba988f8d25d5'
SPEC = importlib.util.spec_from_file_location('smallest_generator', Path(__file__).parents[1] / 'generator.py')
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def objects(grid):
    return sorted(find_objects(grid, bg=0, connectivity=4), key=lambda obj: (obj['size'], obj['bbox']))


def crop(grid, obj):
    r1, c1, r2, c2 = obj['bbox']
    return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]


def area(obj):
    r1, c1, r2, c2 = obj['bbox']
    return (r2-r1+1)*(c2-c1+1)


def canonical():
    with (ROOT / 'shared/data/canonical/puzzles.jsonl').open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get('task_id') == TASK:
                return row
    raise AssertionError('missing canonical task')


def test_canonical_inputs_and_independent_outputs():
    row = canonical()
    for pair in row['train'] + row['test']:
        assert gen.self_check(pair['input']) == []
        assert crop(pair['input'], objects(pair['input'])[0]) == pair['output']


@pytest.mark.parametrize('band', [None, 'easy', 'medium', 'hard'])
def test_exact_overrides_across_difficulties(band):
    for h, w, n, s in itertools.product((10, 20), (10, 20), (3, 6), (1, 7)):
        requested = dict(grid_h=h, grid_w=w, n_objs=n, small_size=s)
        for index in range(3):
            grid = gen.generate(431, index, difficulty=band, **requested)
            obs = objects(grid)
            assert (len(grid), len(grid[0]), len(obs), obs[0]['size']) == (h, w, n, s)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize('kwargs', [
    {'small_szie': 3}, {'palette_kind': 'warm'}, {'texture': 'warm'},
    {'small_size': True}, {'small_size': 2.5}, {'small_size': '2'},
    {'grid_h': 9}, {'grid_w': 21}, {'n_objs': 2}, {'n_objs': 7},
    {'small_size': 0}, {'small_size': 8},
])
def test_invalid_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, **kwargs)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_every_three_draw_window_refutes_named_shortcuts(band):
    # The production change that would break this: drop the contrast or
    # diagonal profile, ignore sample_index, or use per-color counts.
    draws = []
    for index in range(48):
        grid = gen.generate(932, index, difficulty=band)
        expected = crop(grid, objects(grid)[0])
        assert gen.rule_mirror(grid) == expected
        draws.append({'input': grid, 'output': expected})
    for start in range(len(draws) - 3):
        demos, query = draws[start:start + 3], draws[start + 3]
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(p['input']) != p['output'] for p in demos), (start, name)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_scheduled_counterexamples_really_disagree(band):
    for seed in range(20):
        contrast = gen.generate(seed, 0, difficulty=band)
        obs = objects(contrast)
        target = obs[0]
        assert target['size'] >= 5
        assert any(area(o) < area(target) and o['size'] > target['size'] for o in obs)
        merged = min(find_objects_multicolor(contrast), key=lambda o: (o['size'], o['bbox']))
        assert crop(contrast, merged) != crop(contrast, target)
        diagonal = gen.generate(seed, 2, difficulty=band)
        target = objects(diagonal)[0]
        merged = min(find_objects(diagonal, connectivity=8), key=lambda o: (o['size'], o['bbox']))
        assert crop(diagonal, merged) != crop(diagonal, target)


@pytest.mark.parametrize('texture', ['equal_smallest', 'single_component', 'no_components'])
def test_negative_fixtures_are_rejected(texture):
    assert gen.self_check(gen.generate(32, 1, texture=texture))


@pytest.mark.parametrize('grid', [[], [[]], [[0, 1], [0]], [[False]], [[1.0]], [[-1]], [[10]], [[0]*10 for _ in range(10)]])
def test_malformed_and_blank_inputs_rejected_without_crash(grid):
    assert gen.self_check(grid)


def test_same_color_four_connectivity_not_all_foreground():
    # Three components, smallest color 2 touches larger color 3.
    grid = [[0]*10 for _ in range(10)]
    grid[1][1] = 2
    grid[1][2] = grid[2][2] = 3
    grid[6][5] = grid[6][6] = grid[7][6] = 4
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == [[2]]


def test_replay_and_input_purity():
    for band in ('easy', 'medium', 'hard'):
        for i in range(12):
            grid = gen.generate(101, i, difficulty=band)
            saved = copy.deepcopy(grid)
            assert gen.generate(101, i, difficulty=band) == grid
            gen.self_check(grid)
            gen.observe_overrides(grid)
            for rival in gen.SEMANTIC_RIVALS.values():
                rival(grid)
            assert grid == saved


def test_lesson_checker_rejects_unseparated_and_wrong_labels():
    row = canonical()
    assert gen.lesson_identifiable(row['train'][:3], row['test'][0])
    demos = [{'input': gen.generate(11, i), 'output': gen.rule_mirror(gen.generate(11, i))} for i in range(3)]
    query = {'input': gen.generate(11, 3)}
    assert gen.lesson_identifiable(demos, query) == []
    demos[0]['output'] = [[0]]
    assert gen.lesson_identifiable(demos, query)


def test_selected_rule_authority_and_hash_are_exactly_synchronized():
    import hashlib
    source = canonical()['program_solution']
    expected = hashlib.sha256(' '.join(source.split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == expected
    base = json.loads((ROOT / 'shared/data/base/solutions/banks/e2825ca16ace/E69__ba988f8d25d5.json').read_text())
    assert base['racket_target']['target_code'] == source
    assert base['racket_target']['raw_code'] == source


def test_default_dimensions_cover_broad_and_canonical_scales():
    observed_h, observed_w = set(), set()
    canonical_scale = 0
    for index in range(300):
        grid = gen.generate(556, index, difficulty='hard')
        observed_h.add(len(grid))
        observed_w.add(len(grid[0]))
        canonical_scale += int(10 <= len(grid) <= 12 and 10 <= len(grid[0]) <= 12)
    assert max(observed_h) == 20 and max(observed_w) == 20
    assert canonical_scale >= 150
