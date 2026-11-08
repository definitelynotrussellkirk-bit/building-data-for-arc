"""Original-label and constructive-grammar regressions for motif exchange."""
from collections import Counter
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
NATIVE = HOME / 'workspace' / 'parametric'


def load(path):
    assert path.is_file(), f'missing implementation: {path.name}'
    spec = importlib.util.spec_from_file_location('_c7_test_' + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def model():
    return load(NATIVE / 'prototype.py')


def original_pairs():
    raw = ROOT / 'shared/data/raw'
    challenge = json.loads((raw / 'arc-agi_evaluation_challenges.json').read_text())['c7f57c3e']
    gold = json.loads((raw / 'arc-agi_evaluation_solutions.json').read_text())['c7f57c3e']
    return challenge['train'] + [dict(input=p['input'], output=y) for p, y in zip(challenge['test'], gold)]


@pytest.mark.parametrize('pair', original_pairs(), ids=['train0', 'train1', 'test0'])
def test_original_label_inference(model, pair):
    grid = [[int(v) for v in row] for row in pair['input']]
    expected = [[int(v) for v in row] for row in pair['output']]
    assert model.solve(grid) == expected


@pytest.mark.parametrize('seed', [0, 17, 43, 101, 2**63 - 1])
def test_constructive_banks(model, seed):
    inputs = []
    for index in [0, 1, 2, 3, 4, 5, 100, 101, 102, 103]:
        grid = model.scene(seed, index, stress=index == 103)
        assert grid == model.scene(seed, index, stress=index == 103)
        model.validate_grid(grid)
        analysis = model.analyze(grid)
        assert len(analysis['templates']) == 2
        assert min(analysis['counts']) >= 1
        assert analysis['counts'][0] != analysis['counts'][1]
        assert len(analysis['components']) >= 3
        before = [row[:] for row in grid]
        swap = model.solve(grid, 'swap')
        minority = model.solve(grid, 'minority')
        assert grid == before
        assert swap != minority
        assert swap != grid
        model.validate_grid(swap)
        model.validate_grid(minority)
        assert (len(swap), len(swap[0])) == (len(grid), len(grid[0]))
        inputs.append(json.dumps(grid))
    assert len(set(inputs)) == 10


@pytest.mark.parametrize('seed', [0, 17, 43, 2**63 - 1])
def test_teaching_frequency_versus_area(model, seed):
    first = model.analyze(model.scene(seed, 0))
    second = model.analyze(model.scene(seed, 1))
    for analysis in (first, second):
        assert sorted(analysis['counts']) == [1, 3]
        assert {o['scale'] for o in analysis['components']} == {1, 3}
    def area(data):
        return [sum(len(o['cells']) for o in data['components'] if o['template_index'] == i) for i in range(2)]
    assert first['counts'].index(min(first['counts'])) != area(first).index(min(area(first)))
    assert second['counts'].index(min(second['counts'])) == area(second).index(min(area(second)))


@pytest.mark.parametrize('seed', [0, 17, 43, 2**63 - 1])
def test_large_scene_is_substantive(model, seed):
    grid = model.scene(seed, 103, stress=True)
    data = model.analyze(grid)
    bg = data['background']
    assert len(grid) == len(grid[0]) == 30
    assert sorted(o['scale'] for o in data['components']) == [1, 1, 2, 2, 2, 2, 4]
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != bg]
    assert len(points) >= 150
    assert max(r for r, c in points) - min(r for r, c in points) >= 28
    assert max(c for r, c in points) - min(c for r, c in points) >= 28
    assert Counter(v for row in grid for v in row)[bg] > 450


def literal_scene(anchors):
    grid = [[0] * 8 for _ in range(13)]
    for r, c, kind in anchors:
        for dr, dc in [(0, 1), (1, 0), (1, 2), (2, 1)]:
            grid[r + dr][c + dc] = 1
        grid[r + 1][c + 1] = 2 if kind == 0 else 3
        grid[r + (-1 if kind == 0 else 3)][c + 1] = 4 if kind == 0 else 5
    return grid


def test_overlapping_replacement_is_rejected(model):
    grid = literal_scene([(3, 1, 0), (7, 1, 1)])
    assert len(model.analyze(grid)['components']) == 2
    with pytest.raises(ValueError, match='overlap'):
        model.solve(grid)


def test_out_of_bounds_replacement_is_rejected(model):
    grid = literal_scene([(0, 0, 1), (10, 4, 0)])
    assert len(model.analyze(grid)['components']) == 2
    with pytest.raises(ValueError, match='bound'):
        model.solve(grid)


@pytest.mark.parametrize('bad', [[], [[True]], [[1.0]], [['1']], [[0], [0, 1]], [[-1]], [[10]], None])
def test_strict_grid_types(model, bad):
    with pytest.raises(ValueError):
        model.validate_grid(bad)


def test_minority_requires_unique_frequency(model):
    grid = literal_scene([(2, 0, 0), (8, 4, 1)])
    assert model.analyze(grid)['counts'] == [1, 1]
    with pytest.raises(ValueError, match='frequency'):
        model.solve(grid, 'minority')


def test_color_permutation_equivariance(model):
    for seed in (0, 17, 43):
        grid = model.scene(seed, 1)
        permutation = {color: (color + 3) % 10 for color in range(10)}
        remap = lambda g: [[permutation[v] for v in row] for row in g]
        for setting in ('swap', 'minority'):
            assert model.solve(remap(grid), setting) == remap(model.solve(grid, setting))


@pytest.mark.parametrize('bad', [True, False, -1, 2**63, 1.5, '3', None])
def test_strict_scene_seed(model, bad):
    with pytest.raises(ValueError):
        model.scene(bad, 0)


@pytest.mark.parametrize('bad', [True, False, -1, 2**63, 1.5, '3', None])
def test_strict_scene_index(model, bad):
    with pytest.raises(ValueError):
        model.scene(0, bad)


def test_ordinary_generator_axis_and_validation():
    generator = load(HOME / 'generator.py')
    assert generator.RULE_TASK_ID == 'ee_c7f57c3e'
    for count in range(3, 7):
        grid = generator.generate(17, 0, instance_count=count)
        assert grid == generator.generate(17, 0, instance_count=count)
        assert len(generator._model.analyze(grid)['components']) == count
        assert generator.self_check(grid) == []
    with pytest.raises(ValueError):
        generator.generate(17, 0, unknown=True)
    for bad in (True, 1.5, '4', 2, 7):
        with pytest.raises((ValueError, TypeError)):
            generator.generate(17, 0, instance_count=bad)
    assert generator.self_check([[True]])


def test_compact_canvas_reserves_background_for_every_replacement(model):
    # This compact three-instance draw originally violated the strict-majority
    # background guard. It must be constructively padded, never retried.
    grid = model.scene(5, 4)
    background = model.analyze(grid)['background']
    for candidate in (grid, model.solve(grid, 'swap'), model.solve(grid, 'minority')):
        assert sum(v == background for row in candidate for v in row) > len(candidate) * len(candidate[0]) // 2
    assert model.solve(model.solve(grid, 'swap'), 'swap') == grid


@pytest.mark.parametrize('seed', [0, 5, 17, 43, 2**63 - 1])
def test_swap_is_an_involution_on_admitted_scenes(model, seed):
    for index in (0, 1, 4, 100, 101, 102, 103):
        grid = model.scene(seed, index, stress=index == 103)
        assert model.solve(model.solve(grid, 'swap'), 'swap') == grid
