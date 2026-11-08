"""Native parametric behavior; independent literal labels and real Racket checks."""
import importlib.util
import json
from pathlib import Path

import pytest


def adapter():
    path = Path(__file__).resolve().parent.parent / 'workspace/parametric/adapter.py'
    assert path.is_file(), 'native adapter has not been implemented'
    spec = importlib.util.spec_from_file_location('ray_partition_adapter_tests', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


G = [[2,0,0,0,0], [0,0,1,0,0], [5,5,5,5,5], [0,2,0,0,0], [0,0,0,1,0]]
RAYS = [[2,0,1,0,0], [2,0,1,0,0], [5,5,5,5,5], [0,2,0,0,0], [0,0,0,1,0]]
FLOOD = [[2,0,1,0,0], [2,0,1,0,0], [5,5,5,5,5], [8,2,8,8,8], [8,8,8,1,8]]


def test_literal_ray_completion_and_dependent_flood():
    a = adapter()
    assert a.predict(G, 'rays_only') == RAYS
    assert a.predict(G, 'largest_region') == FLOOD
    assert a.predict(G, 'input_region') != FLOOD
    assert G[0] == [2,0,0,0,0]


def test_exact_canonical_default():
    from arcpuzzles import Catalog
    from reviewer_support import find_root
    a = adapter()
    root = find_root(__file__)
    expected = {v['program_solution'] for v in Catalog(root).get(a.TASK)['variants']}
    assert expected == {a.program({'region_policy': 'rays_only'})}


@pytest.mark.parametrize('demos', [2,3,4,5,6])
def test_count_setting_independence_and_four_query_prefix(demos):
    a = adapter()
    for seed in (0,17,41):
        episodes = [a.generate(seed, {'region_policy': s}, demos, 4) for s in a.SETTINGS]
        for e in episodes:
            assert len(e['train']) == demos and len(e['test']) == 4
            keys = [json.dumps(p['input']) for p in e['train'] + e['test']]
            assert len(set(keys)) == len(keys)
            assert any(len(p['input']) == len(p['input'][0]) == 30 for p in e['test'])
        assert [p['input'] for p in episodes[0]['train'] + episodes[0]['test']] == [p['input'] for p in episodes[1]['train'] + episodes[1]['test']]
        for q in (1,2,3):
            short = a.generate(seed, {'region_policy': a.SETTINGS[1]}, demos, q)
            assert short['train'] == episodes[1]['train']
            assert short['test'] == episodes[1]['test'][:q]
        assert a.generate(seed, {'region_policy': a.SETTINGS[1]}, 6, 4)['train'][:demos] == episodes[1]['train']


def test_public_projection_is_masked_and_detached():
    a = adapter()
    e = a.generate(3, {'region_policy':'largest_region'}, 3, 4)
    p = a.public_turn(e, 0)
    assert set(p) == {'train','test'} and len(p['test']) == 1
    assert set(p['test'][0]) == {'input'}
    assert a.public_turn(a.generate(3, {'region_policy':'largest_region'}, 3, 1), 0) == p
    p['train'][0]['input'][0][0] = 9
    assert e['train'][0]['input'][0][0] != 9
    with pytest.raises(ValueError): a.public_turn(e, -1)
    with pytest.raises(ValueError): a.public_turn(e, True)


@pytest.mark.parametrize('kwargs', [dict(demos=True),dict(demos=3.5),dict(demos=1),dict(demos=7),dict(queries=0),dict(queries=5),dict(queries=True),dict(seed=-1),dict(seed=True),dict(settings={'region_policy':'bad'}),dict(settings={'region_policy':'rays_only','typo':1})])
def test_invalid_requests_fail_before_sampling(kwargs):
    a = adapter()
    args = dict(seed=0, settings={'region_policy':'rays_only'}, demos=3, queries=4)
    args.update(kwargs)
    with pytest.raises(ValueError): a.generate(**args)


def test_two_demos_reject_declared_shortcuts_and_stress_has_real_content():
    a = adapter()
    for seed in (0,17,41):
        e = a.generate(seed, {'region_policy':'largest_region'}, 2, 4)
        for rival in a.RIVALS:
            assert any(a.predict(p['input'], rival) != p['output'] for p in e['train']), rival
        for p in e['test']:
            if len(p['input']) != 30: continue
            g = p['input']
            cells = [(r,c) for r in range(30) for c in range(30) if g[r][c]]
            assert min(r for r,c in cells) == min(c for r,c in cells) == 0
            assert max(r for r,c in cells) == max(c for r,c in cells) == 29
            assert {(r//15,c//15) for r,c in cells} == {(0,0),(0,1),(1,0),(1,1)}
            assert sum(v in (1,2) for row in g for v in row) >= 20
            base = a.predict(g,'rays_only')
            assert sum(base[r][c] != g[r][c] for r in range(30) for c in range(30)) >= 60


def test_live_protected_racket_selected_and_rival_labels():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    a = adapter()
    bridge = RacketBridge()
    try:
        assert bridge.runtime_identity['protected'] is True
        modes = list(a.SETTINGS) + list(a.RIVALS)
        e = a.generate(0, {'region_policy':'largest_region'}, 2, 4)
        for mode in dict.fromkeys(modes):
            src = wrap_rule(a.rule(mode))
            for g in [G] + [p['input'] for p in e['train']]:
                literal = "'(" + ' '.join('('+' '.join(map(str,row))+')' for row in g) + ')'
                assert bridge.eval_text(f'({src} {literal})') == a.predict(g,mode), mode
    finally:
        bridge.close()


def test_all_regions_rival_is_a_distinct_executable_hypothesis():
    a = adapter()
    expected = [[2,8,1,8,8], [2,8,1,8,8], [5,5,5,5,5], [8,2,8,8,8], [8,8,8,1,8]]
    assert a.predict(G,'all_regions') == expected
    assert expected != FLOOD


def audit_module():
    path = Path(__file__).resolve().parent.parent / 'workspace/parametric/audit.py'
    assert path.is_file(), 'reusable audit is not implemented'
    spec = importlib.util.spec_from_file_location('ray_partition_audit_tests', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_audit_sweep_checks_each_count_and_matched_setting():
    result = audit_module().sweep(adapter(), [0])
    assert result['episodes'] == 40
    assert result['pairs'] == 260
    assert result['matched_input_comparisons'] == 20
    assert result['public_turns'] == 100
    assert result['failures'] == []


def test_audit_writer_hashes_only_single_turn_public_bytes(tmp_path):
    from reviewer_support import public_challenge_bytes
    import hashlib
    a, audit = adapter(), audit_module()
    e = a.generate(0, {'region_policy':'largest_region'}, 3, 4)
    names = audit.write_turns(a, e, tmp_path)
    assert len(names) == 4
    for i,name in enumerate(names):
        data = (tmp_path/name).read_bytes()
        assert hashlib.sha256(data).hexdigest()+'.json' == name
        assert data == public_challenge_bytes(a.public_turn(e,i))
    e['settings'] = {'private':'changed'}
    e['test'][0]['output'][0][0] = 9
    assert audit.write_turns(a,e,tmp_path) == names
