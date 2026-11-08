"""Native adapter: behavior tests, not an acceptance receipt."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from arcpuzzles import Catalog
from reviewer_support import find_root, public_challenge_bytes
from arc_repl.racket_bridge import RacketBridge

ROOT = find_root(__file__)
HOME = ROOT / 'generators/144c5d002191/workspace/parametric'

@pytest.fixture(scope='module')
def adapter():
    path = HOME / 'adapter.py'
    assert path.is_file(), 'native adapter has not been built'
    spec = importlib.util.spec_from_file_location('native_stamp_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_canonical_and_retained_mirror(adapter):
    sources = {v['program_solution'] for v in Catalog(ROOT).get(adapter.TASK)['variants']
               if isinstance(v.get('program_solution'), str)}
    assert {adapter.program({'policy': 'identity'})} == sources
    assert adapter.program({'policy': 'horizontal_mirror'}) == adapter.prior.materialize_program('horizontal_mirror', root=ROOT)


@pytest.mark.parametrize('seed,demos,queries', [(True,3,4),(-1,3,4),(1.0,3,4),(0,True,4),(0,1,4),(0,7,4),(0,3,0),(0,3,5),(0,3,False)])
def test_invalid_requests_rejected(adapter, seed, demos, queries):
    with pytest.raises((TypeError,ValueError)):
        adapter.generate(seed, {'policy':'identity'}, demos, queries)


@pytest.mark.parametrize('settings', [{},{'policy':'bogus'},{'policy':'identity','extra':0}, {'policy':True}, None])
def test_invalid_settings_rejected(adapter,settings):
    with pytest.raises((TypeError,ValueError)):
        adapter.program(settings)


def test_literal_majority_tie_and_overwrite(adapter):
    # L template; two neighboring, differently colored anchors. At (4,4),
    # the later blue stamp overwrites the red one; blue wins visible area 3:2.
    g = [[0]*7 for _ in range(7)]
    g[0][0] = g[1][0] = g[1][1] = 5
    g[3][3], g[3][4] = 2, 1
    want = [[0]*7 for _ in range(7)]
    want[3][4] = want[4][4] = want[4][5] = 1
    assert adapter.predict(g, 'visible_majority') == want
    # Declared tie: smallest numeric color, independent of scan order.
    g[3][3], g[3][4], g[3][5] = 0, 0, 0
    g[3][0], g[3][4] = 3, 2
    want = [[0]*7 for _ in range(7)]
    want[3][4] = want[4][4] = want[4][5] = 2
    assert adapter.predict(g, 'visible_majority') == want


def test_counts_matched_inputs_query_prefix_and_substantive_boundary(adapter):
    for seed in range(8):
        base = adapter.generate(seed, {'policy':'identity'}, 6, 4)
        all_inputs = [p['input'] for p in base['train'] + base['test']]
        assert len({json.dumps(g) for g in all_inputs}) == 10
        assert all(not adapter.input_errors(g) for g in all_inputs)
        stress = base['test'][3]['input']
        assert (len(stress),len(stress[0])) == (30,30)
        assert sum(v != 0 for row in stress for v in row) >= 60
        assert all(stress[r][c] for r,c in [(0,0),(0,29),(29,0),(29,29)])
        for policy in adapter.POLICIES:
            ep = adapter.generate(seed, {'policy':policy}, 2, 4)
            assert [p['input'] for p in ep['train']] == all_inputs[:2]
            assert [p['input'] for p in ep['test']] == all_inputs[6:]
            assert sum(v != 0 for row in ep['test'][3]['output'] for v in row) >= 60
            for demos in (2,3,6):
                for queries in (1,4):
                    short = adapter.generate(seed, {'policy':policy}, demos, queries)
                    assert short['train'] == adapter.generate(seed, {'policy':policy},6,4)['train'][:demos]
                    assert short['test'] == ep['test'][:queries]


def test_two_demo_finite_teaching_audit(adapter):
    for seed in range(32):
        for policy in adapter.POLICIES:
            ep = adapter.generate(seed, {'policy':policy}, 2, 4)
            assert adapter.teaching_failures(ep) == []


def test_public_turn_is_private_invariant_and_prefix_stable(adapter):
    ep = adapter.generate(17, {'policy':'visible_majority'}, 3, 4)
    single = adapter.generate(17, {'policy':'visible_majority'}, 3, 1)
    assert adapter.public_turn(ep,0) == adapter.public_turn(single,0)
    original = adapter.public_turn(ep,0)
    dirty = copy.deepcopy(ep)
    dirty['settings'] = {'policy':'SECRET'}
    dirty['program_solution'] = 'SECRET'
    dirty['test'][0]['output'] = [[9]]
    dirty['test'][1:] = [{'input':[[9]],'output':[[9]]}]
    dirty['train'][0]['private_metadata'] = 'SECRET'
    assert adapter.public_turn(dirty,0) == original
    assert set(original) == {'train','test'}
    assert len(original['test']) == 1 and set(original['test'][0]) == {'input'}
    for bad in (-1,True,4):
        with pytest.raises((ValueError,TypeError)):
            adapter.public_turn(ep,bad)
    assert public_challenge_bytes(original)


def test_protected_racket_claims_and_wrong_intermediate(adapter):
    with RacketBridge(timeout=10,startup_timeout=60) as bridge:
        for policy in adapter.POLICIES:
            ep = adapter.generate(17, {'policy':policy}, 2, 4)
            for pair in ep['train']+ep['test']:
                actual = adapter.prior.execute_program(bridge, ep['program_solution'],pair['input'])
                assert actual == pair['output']
        pair = adapter.generate(17, {'policy':'visible_majority'},2,4)['train'][1]
        wrong = adapter.prior.execute_program(bridge, adapter.counterfactual_program(), pair['input'])
        assert wrong != pair['output']


def test_every_program_is_one_complete_expression(adapter):
    # The execution wrapper can tolerate trailing delimiters; standalone witness
    # and admission parsing must reject them. This checks the real parser.
    from arc_repl.parser import parse_all
    for source in [adapter.program({'policy':p}) for p in adapter.POLICIES] + [adapter.counterfactual_program()]:
        assert len(parse_all(source)) == 1
