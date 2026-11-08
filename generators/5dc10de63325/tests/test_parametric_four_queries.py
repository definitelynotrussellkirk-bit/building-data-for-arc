"""Regression for independent lesson sizes and exact public content identities."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import find_root, load_selected_generator, public_challenge_bytes, public_challenge_id

ROOT = find_root(__file__)
SOURCE = ROOT / 'generators/5dc10de63325/workspace/parametric/prototype.py'

@pytest.fixture(scope='module')
def proto():
    spec = importlib.util.spec_from_file_location('cyan_four_query_prototype', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_public_bytes_and_name_use_only_shared_visible_projection(proto):
    episode = {'train': [{'input': [[8]], 'output': [[0]], 'seed': 9}],
               'test': [{'input': [[0]], 'output': [[8]], 'parameters': {'secret': 2}}],
               'seed': 10, 'prototype_version': 'private'}
    expected = public_challenge_bytes(episode)
    assert proto.public_challenge(episode) == __import__('json').loads(expected)
    assert proto.public_filename(episode) == 'challenge-' + public_challenge_id(episode) + '.json'
    changed = deepcopy(episode)
    changed['train'][0]['seed'] = 100
    changed['test'][0]['output'] = [[3]]
    changed['prototype_version'] = 'different'
    assert proto.public_filename(changed) == proto.public_filename(episode)


def test_separate_counts_distinct_inputs_and_shared_input_seed(proto):
    generator, _, _ = load_selected_generator('5dc10de63325', root=ROOT)
    small = proto._build_inputs(generator, seed=123, n_train=3, n_test=4)
    larger = proto._build_inputs(generator, seed=123, n_train=5, n_test=2)
    assert len(small) == len(larger) == 7
    assert len({proto.digest(grid) for grid in small}) == 7
    assert len({proto.digest(grid) for grid in larger}) == 7
    assert small[:3] == larger[:3]
    assert small == proto._build_inputs(generator, seed=123, n_train=3, n_test=4)


@pytest.mark.parametrize('train,test', [(2,4),(3,0),(True,4),(3,True),(3,33)])
def test_unsupported_episode_sizes_raise_instead_of_shortening(proto, train, test):
    generator, _, _ = load_selected_generator('5dc10de63325', root=ROOT)
    with pytest.raises(ValueError, match='n_train|n_test'):
        proto._build_inputs(generator, seed=0, n_train=train, n_test=test)


def test_demos_refute_nearest_quarter_on_lawful_counts(proto):
    assert any(count // 4 != (count + 2) // 4 for count in proto.DEMO_COUNTS)


def test_rival_selection_never_borrows_query_answers(proto):
    generator, _, _ = load_selected_generator('5dc10de63325', root=ROOT)
    grids = proto._build_inputs(generator, seed=50, n_train=3, n_test=4)
    pairs = [{'input': grid, 'output': proto.python_reference(grid)} for grid in grids]
    episode = {'train': pairs[:3], 'test': pairs[3:]}
    correct = proto.rival_identifiability(episode)
    assert correct['passed']
    changed = deepcopy(episode)
    changed['test'][0]['output'] = [[0] * 5 for _ in range(5)]
    incorrect = proto.rival_identifiability(changed)
    assert incorrect['survivors_from_demos_only'] == correct['survivors_from_demos_only']
    assert not incorrect['passed']
    assert incorrect['queries'][0]['disagreeing_demo_survivors']


def test_maximum_supported_pair_request_has_no_duplicate_inputs(proto):
    generator, _, _ = load_selected_generator('5dc10de63325', root=ROOT)
    grids = proto._build_inputs(generator, seed=123, n_train=32, n_test=32)
    assert len(grids) == len({proto.digest(grid) for grid in grids}) == 64


def test_old_lesson_nearest_quarter_rival_with_executed_racket(proto):
    """A source-bound witness for the v1 demo-selection defect, not new labels."""
    import json
    from arc_repl.racket_bridge import RacketBridge
    source = proto.canonical_source(root=ROOT)
    rows = []
    with RacketBridge(timeout=30) as bridge:
        for count in (5, 9, 13, 10):
            grid = [[8 if r * 6 + c < count else 0 for c in range(6)] for r in range(6)]
            actual = proto.execute_rule(source, grid, bridge=bridge, root=ROOT)
            nearest = proto._glyph((count + 2) // 4, proto.FILL_ORDERS[proto.DEFAULT_FILL_ORDER])
            rows.append({'count': count, 'racket_output': actual,
                         'nearest_output': nearest, 'equal': actual == nearest})
    assert all(row['equal'] for row in rows[:3])
    assert not rows[3]['equal']
    print(json.dumps({'old_demo_rounding_witness': rows,
                      'canonical_source_sha256': proto.digest(source)}, sort_keys=True))
