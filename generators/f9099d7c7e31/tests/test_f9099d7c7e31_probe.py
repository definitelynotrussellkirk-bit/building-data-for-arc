"""The independent probe must not use the generator's private object helpers."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest
from puzzle_generators.per_puzzle.f9099d7c7e31 import generator as gen


@pytest.fixture
def probe():
    path = Path(gen.__file__).parent / 'workspace/review_probe.py'
    assert path.is_file(), 'task-local reproducible probe is missing'
    spec = importlib.util.spec_from_file_location('f9099_review_probe', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_components_split_same_color_disconnected_bodies(probe):
    obs = probe.components([[1, 0, 1], [1, 0, 0]])
    assert sorted(o['size'] for o in obs) == [1, 2]


def test_components_do_not_merge_diagonal_or_foreign_neighbors(probe):
    assert len(probe.components([[1, 2], [0, 1]])) == 3


@pytest.mark.parametrize('grid', [[], [[]], [[1], [1, 2]], [[True]], [[10]], [[1.0]]])
def test_invalid_grids_fail_closed(probe, grid):
    with pytest.raises(ValueError):
        probe.components(grid)


def test_predictions_are_independent_pure_and_match_declared_rivals(probe):
    for i in range(4):
        grid = gen.generate(17, i, difficulty='medium')
        snapshot = copy.deepcopy(grid)
        preds = probe.predictions(grid)
        assert preds['width_then_size'] == gen._canonical_transform(grid)
        for name in probe.RIVALS:
            assert preds[name] == gen.SEMANTIC_RIVALS[name](grid), name
        assert grid == snapshot


def test_summary_reports_missing_coverage_and_real_counterexamples(probe):
    g = gen.generate(17, 0, difficulty='medium')
    row = {'input': g, 'output': gen._canonical_transform(g), 'kind': 'default',
           'seed': 17, 'sample_index': 0, 'difficulty': 'medium', 'errors': []}
    report = probe.summarize([row])
    assert not report['passed']
    assert report['missing_default_counterexamples']
    assert report['mirror_mismatches'] == 0


def test_summary_rejects_tampered_reference_label(probe):
    g = gen.generate(17, 0, difficulty='medium')
    row = {'input': g, 'output': [[0]], 'kind': 'default',
           'seed': 17, 'sample_index': 0, 'difficulty': 'medium', 'errors': []}
    assert probe.summarize([row])['mirror_mismatches'] == 1


def test_summary_requires_all_four_window_phases(probe):
    rows = []
    for i in range(8):
        g = gen.generate(431, i, difficulty='medium')
        rows.append({'input': g, 'output': gen._canonical_transform(g), 'kind': 'default',
                     'seed': 431, 'sample_index': i, 'difficulty': 'medium', 'errors': []})
    report = probe.summarize(rows)
    assert report['passed']
    assert report['windows_checked'] == 4
    assert not report['window_failures']
    assert all(n > 0 for n in report['default_disagreements'].values())
