"""Behavioral contract for the proposed rolling-direction family."""
from __future__ import annotations
import copy
import importlib.util
import json
import random
from pathlib import Path
import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes

HOME = Path(__file__).resolve().parents[1]
BASE = HOME / 'workspace' / 'parametric'

@pytest.fixture(scope='module')
def prototype():
    path = BASE / 'prototype.py'
    assert path.is_file(), 'native rolling-direction implementation has not been built'
    spec = importlib.util.spec_from_file_location('_rolling_family_tests', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_adapter_and_canonical_default(prototype):
    contract = json.loads((BASE / 'promotion.json').read_text())
    assert contract['parameters'] == {'direction': ['right', 'left']}
    # Public mixture accepts prefixes; the unchanged source below still checks4.
    assert contract['limits'] == {'demos': [2, 6], 'queries': [1, 4]}
    sources = {r['program_solution'] for r in map(json.loads, canonical_path(find_root(__file__)).read_text().splitlines()) if r['task_id'] == 'ba32e05911b0'}
    assert sources == {prototype.program({'direction': 'right'})}
    assert prototype.program({'direction': 'left'}) not in sources


def test_two_roll_literal_fixture(prototype):
    grid = [[0] * 12 for _ in range(10)]
    grid[9][2] = 6
    grid[6][2:5] = [7, 7, 7]
    grid[3][5:7] = [7, 7]
    expected = [
        [0,0,0,0,0,0,0,6,0,0,0,0],
        [0,0,0,0,0,0,0,2,0,0,0,0],
        [0,0,0,0,0,0,0,2,0,0,0,0],
        [0,0,0,0,0,8,7,2,0,0,0,0],
        [0,0,0,0,0,4,2,3,0,0,0,0],
        [0,0,0,0,0,2,0,0,0,0,0,0],
        [0,0,8,7,7,2,0,0,0,0,0,0],
        [0,0,4,2,2,3,0,0,0,0,0,0],
        [0,0,2,0,0,0,0,0,0,0,0,0],
        [0,0,6,0,0,0,0,0,0,0,0,0],
    ]
    assert prototype.predict(grid, 'right') == expected
    assert prototype.predict([r[::-1] for r in grid], 'left') == [r[::-1] for r in expected]
    trace = prototype.trace(grid, 'right')[1]
    assert [(e['row'], e['col'], e['next_col']) for t in trace for e in t['events'] if e['kind'] == 'roll'] == [(6, 2, 5), (3, 5, 7)]


@pytest.mark.parametrize('demos', range(2, 7))
def test_matched_inputs_identifiable_lessons_and_counts(prototype, demos):
    for seed in range(12):
        right = prototype.generate(seed, {'direction': 'right'}, demos, 4)
        left = prototype.generate(seed, {'direction': 'left'}, demos, 4)
        assert len(right['train']) == demos and len(right['test']) == 4
        assert [p['input'] for p in right['train'] + right['test']] == [p['input'] for p in left['train'] + left['test']]
        keys = [json.dumps(p['input']) for p in right['train'] + right['test']]
        assert len(set(keys)) == demos + 4
        for ep in (right, left):
            report = prototype.teaching_check(ep['train'], ep['settings'])
            assert report['survivors'] == [ep['settings']['direction']]
            assert report['surviving_shortcuts'] == []


@pytest.mark.parametrize('direction', ['right', 'left'])
def test_supported_boundaries_and_substantive_stress(prototype, direction):
    ep = prototype.generate(17, {'direction': direction}, 2, 4)
    small, stress = ep['test'][0]['input'], ep['test'][3]['input']
    assert (len(small), len(small[0])) == (14, 14)
    assert (len(stress), len(stress[0])) == (30, 30)
    events = [e for t in prototype.trace(stress, direction)[1] for e in t['events']]
    rolls = [e for e in events if e['kind'] == 'roll']
    assert len(rolls) == 6
    assert max(e['row'] for e in rolls) - min(e['row'] for e in rolls) >= 20
    assert abs(rolls[-1]['next_col'] - rolls[0]['col']) >= 12
    assert sum(c == 7 for r in stress for c in r) >= 108
    assert sum(a != b for x, y in zip(stress, ep['test'][3]['output']) for a,b in zip(x,y)) >= 35
    kinds = {e['kind'] for pair in ep['train'] for t in prototype.trace(pair['input'], direction)[1] for e in t['events']}
    assert {'roll', 'top_exit', 'blocked_stop', 'edge_stop'} <= kinds


def test_queries_are_independent_of_demo_count_and_no_global_rng_changes(prototype):
    random.seed(510)
    state = random.getstate()
    a = prototype.generate(91, {'direction': 'right'}, 2, 4)
    b = prototype.generate(91, {'direction': 'right'}, 6, 4)
    assert a['test'] == b['test']
    assert random.getstate() == state
    a['train'][0]['input'][0][0] = 9
    assert prototype.generate(91, {'direction': 'right'}, 2, 4) != a


@pytest.mark.parametrize('settings', [{}, {'direction': 'up'}, {'direction': True}, {'direction': 'left', 'extra': 1}, None])
def test_settings_rejected(prototype, settings):
    with pytest.raises(ValueError):
        prototype.generate(0, settings, 3, 4)


@pytest.mark.parametrize('seed,demos,queries', [(True,3,4),(-1,3,4),(0,True,4),(0,1,4),(0,7,4),(0,3,1),(0,3,5),(0,3,True)])
def test_request_boundaries_rejected(prototype, seed, demos, queries):
    with pytest.raises(ValueError):
        prototype.generate(seed, {'direction': 'right'}, demos, queries)


def test_single_query_public_projection_is_private_metadata_invariant(prototype):
    ep = prototype.generate(22, {'direction': 'left'}, 3, 4)
    first = prototype.public_turn(ep, 0)
    single = copy.deepcopy(ep)
    single['test'] = single['test'][:1]
    assert prototype.public_turn(single, 0) == first
    for i in range(4):
        visible = prototype.public_turn(ep, i)
        assert set(visible) == {'train', 'test'} and len(visible['test']) == 1
        assert set(visible['test'][0]) == {'input'}
        assert visible['test'][0]['input'] == ep['test'][i]['input']
    mutated = copy.deepcopy(ep)
    mutated['settings'], mutated['seed'], mutated['program_solution'] = {}, -1, 'SECRET'
    mutated['test'][0]['output'] = [[9]]
    mutated['test'][1:] = []
    assert public_challenge_bytes(prototype.public_turn(mutated, 0)) == public_challenge_bytes(first)
    with pytest.raises(ValueError):
        prototype.public_turn(ep, -1)


def test_python_claims_match_all_canonical_pairs(prototype):
    rows = [r for r in map(json.loads, canonical_path(find_root(__file__)).read_text().splitlines()) if r['task_id'] == 'ba32e05911b0']
    for row in rows:
        tests = row['test'] if type(row['test']) is list else [row['test']]
        for pair in row['train'] + tests:
            assert prototype.predict(pair['input'], 'right') == pair['output']


@pytest.fixture(scope='module')
def verifier():
    path = BASE / 'verify.py'
    assert path.is_file(), 'Racket-backed export/replay tool has not been built'
    spec = importlib.util.spec_from_file_location('_rolling_verify_tests', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_verified_export_hash_names_and_one_query_views(prototype, verifier, tmp_path):
    import hashlib
    episodes = [prototype.generate(17, {'direction': d}, 2, 4) for d in prototype.DIRECTIONS]
    result = verifier.export_verified(episodes, tmp_path / 'export', find_root(__file__))
    assert result['racket']['backend'] == 'racket' and result['racket']['protected'] is True
    assert result['racket_evaluations'] == 12
    assert result['public_files'] == 8
    for file in (tmp_path / 'export' / 'public').glob('*.json'):
        raw = file.read_bytes()
        assert file.stem == hashlib.sha256(raw).hexdigest()
        value = json.loads(raw)
        assert len(value['test']) == 1 and set(value['test'][0]) == {'input'}
        assert raw == public_challenge_bytes(value)
    with pytest.raises(FileExistsError):
        verifier.export_verified(episodes, tmp_path / 'export', find_root(__file__))


def test_export_rejects_wrong_gold_before_writing(prototype, verifier, tmp_path):
    episode = prototype.generate(17, {'direction': 'right'}, 2, 4)
    episode['train'][0]['output'][0][0] = 9
    dest = tmp_path / 'bad'
    with pytest.raises(ValueError, match='label mismatch'):
        verifier.export_verified([episode], dest, find_root(__file__))
    assert not dest.exists()


def test_two_demo_lesson_refutes_fixed_roll_caps_needed_by_queries(prototype):
    """A two-roll-only lesson must not license an unseen six-roll query."""
    for direction in prototype.DIRECTIONS:
        episode = prototype.generate(17, {'direction': direction}, 2, 4)
        def max_rolls(pairs):
            return max(sum(e['kind']=='roll' for e in t['events'])
                       for p in pairs for t in prototype.trace(p['input'],direction)[1])
        assert max_rolls(episode['train']) >= max_rolls(episode['test']) == 6
