"""Proposed mover family: exact labels, independent counts, and strict inputs."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles.parametric_worker import evaluate_contract, _real_evaluator
from reviewer_support import canonical_pairs, find_root, public_challenge_bytes

HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
PROTO = HOME / 'workspace' / 'parametric'


def load():
    path = PROTO / 'adapter.py'
    assert path.is_file(), 'the requested parametric adapter has not been built'
    spec = importlib.util.spec_from_file_location('tested_tailed_rectangle_adapter', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rotate(grid):
    return [list(row) for row in zip(*grid[::-1])]


def test_canonical_default_is_the_selected_rule_and_matches_literal_rotation_labels():
    adapter = load()
    rows = [json.loads(line) for line in (ROOT / 'shared/data/canonical/puzzles.jsonl').read_text().splitlines()]
    canonical = {row['program_solution'] for row in rows if row['task_id'] == '2aa2f3b2ed8f'}
    assert canonical == {adapter.program({'mover': 'body'})}
    # Hand-derived 2x4 minimum: body at columns 0..1; tail at column 2.
    inp = [[2, 2, 2, 3], [2, 2, 0, 0]]
    expected = {
        'body': [[0, 2, 2, 3], [0, 2, 2, 0]],
        'target': [[2, 2, 3, 0], [2, 2, 0, 0]],
    }
    apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
    try:
        assert identity['backend'] == 'racket' and identity['protected'] is True
        for _ in range(4):
            for mover in ('body', 'target'):
                assert apply(adapter.program({'mover': mover}), inp) == expected[mover]
            inp = rotate(inp)
            expected = {key: rotate(grid) for key, grid in expected.items()}
        for pair in canonical_pairs('2aa2f3b2ed8f', root=ROOT, labeled_only=True):
            assert apply(adapter.program({'mover': 'body'}), pair['input']) == pair['output']
    finally:
        bridge.close()


@pytest.mark.parametrize('demos', range(2, 7))
def test_counts_matched_inputs_distinctness_and_query_prefix(demos):
    adapter = load()
    body = adapter.generate(17, {'mover': 'body'}, demos, 4)
    target = adapter.generate(17, {'mover': 'target'}, demos, 4)
    one = adapter.generate(17, {'mover': 'body'}, demos, 1)
    assert len(body['train']) == demos and len(body['test']) == 4
    assert body['train'] == one['train'] and body['test'][:1] == one['test']
    inputs = [pair['input'] for split in ('train', 'test') for pair in body[split]]
    assert len({json.dumps(grid) for grid in inputs}) == demos + 4
    assert inputs == [pair['input'] for split in ('train', 'test') for pair in target[split]]
    assert all(a['output'] != b['output'] for split in ('train', 'test')
               for a, b in zip(body[split], target[split]))
    public_challenge_bytes(body)  # Strict integer grid validation.
    assert any(len(p['input']) == len(p['input'][0]) == 30 for p in body['test'])
    large = body['test'][-1]['input']
    assert sum(cell != 0 for row in large for cell in row) >= 350
    assert any(large[0]) and any(large[-1])
    assert any(row[0] for row in large) and any(row[-1] for row in large)


@pytest.mark.parametrize('seed', [0, 17])
@pytest.mark.parametrize('demos', [2, 3, 6])
def test_protected_racket_labels_and_demo_only_parameter_identification(seed, demos):
    load()
    contract = json.loads((PROTO / 'promotion.json').read_text())
    jobs = [dict(seed=seed, settings={'mover': mover}, demos=demos, queries=4)
            for mover in ('body', 'target')]
    result = evaluate_contract(ROOT, '2aa2f3b2ed8f', contract, jobs)
    assert result['racket']['protected'] is True
    assert len(result['checks']) == 2
    for check, job in zip(result['checks'], jobs):
        assert check['survivors'] == [job['settings']]
        assert check['label_count'] == demos + 4


@pytest.mark.parametrize('kwargs', [
    {'seed': True}, {'seed': -1}, {'seed': 2**63}, {'seed': 1.0},
    {'settings': {}}, {'settings': {'mover': True}},
    {'settings': {'mover': 'wall'}}, {'settings': {'mover': 'body', 'extra': 1}},
    {'demos': 1}, {'demos': 7}, {'demos': True}, {'demos': 3.0},
    {'queries': 0}, {'queries': 5}, {'queries': True}, {'queries': 4.0},
])
def test_invalid_controls_fail_before_generation(kwargs):
    adapter = load()
    request = dict(seed=17, settings={'mover': 'body'}, demos=3, queries=4)
    request.update(kwargs)
    with pytest.raises(ValueError):
        adapter.generate(**request)


@pytest.mark.parametrize('seed', [0, 1, 2, 3, 17])
def test_two_demos_reject_lower_and_higher_color_rank_rivals(seed):
    from reviewer_support import load_selected_generator
    geometry = load_selected_generator('2aa2f3b2ed8f', root=ROOT)[0]
    episode = load().generate(seed, {'mover': 'body'}, 2, 4)
    ranks = []
    for pair in episode['train']:
        scene = geometry._analyze_geometry(pair['input'])
        ranks.append(scene['moving_color'] < scene['target_color'])
    assert set(ranks) == {False, True}, 'both role/color-rank associations must be taught within two demos'
