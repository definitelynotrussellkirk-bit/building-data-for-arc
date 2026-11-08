"""Regressions for unsafe path placement and truthful generator controls."""
from pathlib import Path
import importlib.util
import json
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p / 'shared/runtime').exists() or (p / 'arc_repl').exists())
sys.path.insert(0, str(ROOT / 'shared/runtime' if (ROOT / 'shared/runtime').exists() else ROOT))
spec = importlib.util.spec_from_file_location('path_probe', HOME / 'workspace/path_probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
gen = probe.load_generator(HOME / 'generator.py')


def test_rejects_reproduced_unsafe_inputs():
    fixtures = json.loads((HOME / 'workspace/unsafe_inputs.json').read_text())
    for name, grid in fixtures.items():
        assert gen.self_check(grid), name


@pytest.mark.parametrize('grid', [[], [[]], [[0], [0, 1]], [[0, 10]], [[False, 2]], [[0, 0]], [[2, 2]], [[2, 2], [2, 2]]])
def test_malformed_or_nonlesson_grids_reject_without_raising(grid):
    assert gen.self_check(grid)


def test_canonical_inputs_still_accepted():
    task = probe.canonical(ROOT)
    for pair in task['train'] + task['test']:
        assert gen.self_check(pair['input']) == []
        assert probe.inspect_grid(pair['input'])['geometric_output'] == pair['output']


def test_all_difficulty_bands_are_geometrically_safe_and_deterministic():
    for band in ('easy', 'medium', 'hard'):
        for i in range(120):
            grid = gen.generate(i // 12, i % 12, difficulty=band)
            assert grid == gen.generate(i // 12, i % 12, difficulty=band)
            assert gen.self_check(grid) == []
            assert probe.inspect_grid(grid)['problems'] == [], (band, i)


def test_distribution_recovers_core_and_teaches_anchor_and_color_reuse():
    info = [probe.inspect_grid(gen.generate(i // 10, i % 10)) for i in range(120)]
    assert sum(row['shape'][0] == 3 for row in info) >= 40
    assert sum(row['repeated_color'] for row in info) >= 20
    assert any(2 in row['path_lengths'] for row in info)
    assert any(max(row['path_lengths']) > 4 for row in info)
    assert len({row['n_paths'] for row in info}) == 4


@pytest.mark.parametrize('kwargs', [{'grid_h':3}, {'grid_h':12}, {'grid_w':8}, {'grid_w':30},
                                   {'n_paths':2}, {'n_paths':5}, {'n_distinct_colors':1},
                                   {'n_distinct_colors':5}, {'gap':1}, {'gap':3},
                                   {'anchor_col':0}, {'anchor_col':3}])
def test_each_supported_axis_is_realized(kwargs):
    for i in range(4):
        grid = gen.generate(71, i, **kwargs)
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        assert all(observed[key] == value for key, value in kwargs.items())


def test_unknown_and_impossible_overrides_reject_explicitly():
    with pytest.raises(TypeError):
        gen.generate(0, 0, nonexistent_axis=1)
    with pytest.raises(ValueError) as exc:
        gen.generate(0, 0, grid_w=8, n_paths=5)
    assert set(exc.value.incompatible_axes) >= {'grid_w', 'n_paths'}
    with pytest.raises(ValueError):
        gen.generate(0, 0, n_paths=2, n_distinct_colors=3)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, grid_h=True)


def test_selected_authorities_are_exactly_canonical():
    task = probe.canonical(ROOT)
    data = ROOT / 'shared/data' if (ROOT / 'shared/data').exists() else ROOT / 'data'
    for rel in ('training/d017b73f__664a918eb273.json', 'augmented/d017b73f__c4ec5396853f.json'):
        record = json.loads((data / 'base/solutions' / rel).read_text())
        assert record['racket_target']['target_code'] == task['program_solution']


def test_every_witness_has_an_executable_disagreeing_rival():
    assert set(gen.WITNESS_RIVALS) == set(gen.SEMANTIC_WITNESSES)
    hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for i in range(90):
        grid = gen.generate(i // 10, i % 10)
        expected = probe.inspect_grid(grid)['geometric_output']
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            if witness(grid):
                hits[name] += 1
                assert any(gen.SEMANTIC_RIVALS[rival](grid) != expected
                           for rival in gen.WITNESS_RIVALS[name]), (name, i)
    assert all(hits.values())


def test_left_justify_shortcut_fits_canonical_but_not_generated_margin():
    task = probe.canonical(ROOT)
    rival = gen.CANONICAL_SHORTCUTS['left_justify_packed_chain']
    assert all(rival(pair['input']) == pair['output'] for pair in task['train'] + task['test'])
    grid = gen.generate(17, 1, grid_h=3, grid_w=11, n_paths=3,
                        n_distinct_colors=2, gap=1, anchor_col=1)
    assert rival(grid) != probe.inspect_grid(grid)['geometric_output']


def test_portable_verdict_rejects_incomplete_or_semantically_bad_probe():
    import copy
    pspec = importlib.util.spec_from_file_location('portable_check', HOME / 'workspace/portable_check.py')
    portable = importlib.util.module_from_spec(pspec)
    pspec.loader.exec_module(portable)
    good = {'samples_requested': 600, 'samples_generated': 600,
            'counts': {'invalid_geometry': 0, 'selfcheck_rejects': 0},
            'generation_errors': [],
            'racket': {'checked': 90, 'pixel_loss': 0, 'geometric_mismatches': 0,
                       'errors': [], 'canonical_matches': 5}}
    assert portable.probe_passed(good)
    assert not portable.probe_passed(None)
    for branch, key, value in [('', 'samples_generated', 599),
                               ('', 'generation_errors', ['failed']),
                               ('counts', 'invalid_geometry', 1),
                               ('counts', 'selfcheck_rejects', 1),
                               ('racket', 'checked', 89),
                               ('racket', 'pixel_loss', 1),
                               ('racket', 'geometric_mismatches', 1),
                               ('racket', 'canonical_matches', 4),
                               ('racket', 'errors', ['failed'])]:
        bad = copy.deepcopy(good)
        (bad[branch] if branch else bad)[key] = value
        assert not portable.probe_passed(bad), (branch, key)
    assert not portable.probe_passed({})
