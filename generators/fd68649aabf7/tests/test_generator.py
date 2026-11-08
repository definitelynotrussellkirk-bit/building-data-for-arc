"""Portable focused regressions, with actual canonical Racket lesson labels.

Reference execution uses the public Catalog API. Component counts below are
independent measurements, not values returned by generator metadata.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK = 'fd68649aabf7'
TASK_DIR = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fd68649aabf7_under_test', TASK_DIR / 'generator.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
BANDS = (None, 'easy', 'medium', 'hard')
RIVALS = {'centroid', 'left_edge', 'right_edge', 'floor_bbox', 'right_tie',
          'pixel', 'rank', 'eight_connected'}


def body_components(grid):
    marker_colors = set(grid[0]) - {0}
    seen = set()
    components = []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if not color or color in marker_colors or (r, c) in seen:
                continue
            queue = [(r, c)]
            seen.add((r, c))
            for rr, cc in queue:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < len(grid) and 0 <= nc < len(row)
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(queue)
    return components


def independently_observed(grid):
    return {'grid_h': len(grid), 'grid_w': len(grid[0]),
            'n_markers': sum(v != 0 for v in grid[0]),
            'n_blobs': len(body_components(grid))}


def accepts(result):
    return result is True or isinstance(result, list) and result == []


@pytest.fixture(scope='module')
def canonical():
    return canonical_pairs(TASK, root=find_root(__file__), labeled_only=True)


@pytest.mark.parametrize('band', BANDS)
def test_all_canonical_pairs_accepted_without_difficulty_restrictions(canonical, band):
    assert callable(getattr(gen, 'strict_canonical_like', None)), 'missing strict input contract'
    for pair in canonical:
        assert gen.self_check(pair['input'], difficulty=band) == [], pair
        assert accepts(gen.strict_canonical_like(pair['input'])), pair


CONFIGS = (
    {'grid_h': 7, 'grid_w': 9, 'n_markers': 2, 'n_blobs': 1},
    {'grid_h': 7, 'grid_w': 9, 'n_markers': 6, 'n_blobs': 10},
    {'grid_h': 20, 'grid_w': 24, 'n_markers': 6, 'n_blobs': 10},
)


@pytest.fixture(scope='module')
def exact_cases():
    return [(band, options, gen.generate(391, 8, difficulty=band, **options))
            for band in BANDS for options in CONFIGS]


def test_full_range_exact_controls_and_observable_counts_in_every_band(exact_cases):
    assert callable(getattr(gen, 'observe_overrides', None)), 'missing observable controls'
    for band, options, grid in exact_cases:
        assert independently_observed(grid) == options, (band, options)
        assert gen.observe_overrides(grid) == options, (band, options)
        assert gen.self_check(grid, difficulty=band) == [], (band, options)
        assert accepts(gen.strict_canonical_like(grid)), (band, options)


def test_exact_override_grids_have_actual_racket_outputs(exact_cases):
    applied = Catalog().apply(TASK, [g for _, _, g in exact_cases], timeout=120)
    assert applied['rule_hash_matches_catalog']
    assert all(r['valid_output'] and r['error'] is None for r in applied['results'])
    assert all(r['input'] != r['output'] for r in applied['results'])


@pytest.mark.parametrize('key,value', [
    ('grid_h', 6), ('grid_h', 21), ('grid_w', 8), ('grid_w', 25),
    ('n_markers', 1), ('n_markers', 7), ('n_blobs', 0), ('n_blobs', 11),
    ('grid_h', True), ('grid_w', 9.5), ('n_markers', '3'), ('n_blobs', False),
    ('palette_kind', 'warm'), ('texture', 'no_markers'), ('palette_size', 2),
    ('n_distinct_colors', 2), ('position_bias', 'row0_markers_blobs_below'),
    ('density', 'sparse'), ('unknown_axis', 1),
])
def test_invalid_or_retired_controls_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_none_override_values_retain_default_draw_convention():
    assert gen.generate(22, 1, grid_h=None, grid_w=None, n_markers=None, n_blobs=None) == gen.generate(22, 1)


@pytest.mark.parametrize('grid', [
    None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(7)],
    [[0] * 9], [[0] * 9 for _ in range(7)],
    [[0] * 8 + [10] for _ in range(7)], ['000000000'] * 7,
    [[2, 0, 4, 0, 0, 0, 0, 0, 0]],
])
def test_malformed_self_check_reports_reasons_without_exception(grid):
    result = gen.self_check(grid)
    assert isinstance(result, list) and result


def test_declared_shortcuts_really_fit_all_canonical_pairs(canonical):
    for name in RIVALS:
        for pair in canonical:
            assert gen.SEMANTIC_RIVALS[name](pair['input']) == pair['output'], name


def test_minimal_racket_witness_refutes_every_declared_shortcut():
    fixture = json.loads((TASK_DIR / 'counterexamples/joint_witness.json').read_text())
    assert gen.self_check(fixture['input']) == []
    for name in RIVALS:
        assert gen.SEMANTIC_RIVALS[name](fixture['input']) != fixture['racket_output'], name


@pytest.fixture(scope='module')
def default_lessons():
    # Six consecutive draws cover all three period residues and each 4-pair
    # window. Eighteen real reference labels are reused across all rotations.
    assert getattr(gen, 'EXAMPLES_NEEDED', None) == 3
    assert RIVALS <= set(getattr(gen, 'SEMANTIC_RIVALS', {}))
    grids = [gen.generate(761, i, difficulty=band)
             for band in ('easy', 'medium', 'hard') for i in range(6)]
    applied = Catalog().apply(TASK, grids, timeout=120)
    assert applied['rule_hash_matches_catalog']
    assert all(r['valid_output'] and r['error'] is None for r in applied['results'])
    return {band: applied['results'][6 * b:6 * (b + 1)]
            for b, band in enumerate(('easy', 'medium', 'hard'))}


def test_row2_support_and_lawful_deterministic_default_inputs(default_lessons):
    for band, pairs in default_lessons.items():
        assert any(r == 2 for p in pairs for blob in body_components(p['input']) for r, c in blob), band
        for i, pair in enumerate(pairs):
            grid = pair['input']
            assert gen.self_check(grid, difficulty=band) == []
            assert accepts(gen.strict_canonical_like(grid))
            assert grid == gen.generate(761, i, difficulty=band)


@pytest.mark.parametrize('band', ('easy', 'medium', 'hard'))
@pytest.mark.parametrize('start', range(3))
def test_every_three_demonstration_window_refutes_declared_rivals_and_rotations(default_lessons, band, start):
    pairs = default_lessons[band][start:start + 4]
    predictions = {}
    for name in sorted(RIVALS):
        fn = gen.SEMANTIC_RIVALS[name]
        predictions[name] = []
        for pair in pairs:
            original = deepcopy(pair['input'])
            prediction = fn(pair['input'])
            assert pair['input'] == original, f'{name} mutated its input'
            assert prediction == fn(deepcopy(original)), f'{name} is nondeterministic'
            predictions[name].append(prediction)
    for query in range(4):
        demos = [i for i in range(4) if i != query]
        for name, outputs in predictions.items():
            assert any(outputs[i] != pairs[i]['output'] for i in demos), (
                f'{band} start={start}, query={query}: {name} fits every demonstration')
