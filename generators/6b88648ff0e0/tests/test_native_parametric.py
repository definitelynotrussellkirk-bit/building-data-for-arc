"""Native strip family: input-derived key, stable ordering, counts and exports."""
import copy
import importlib.util
from pathlib import Path
import pytest
from reviewer_support import find_root


def adapter():
    path = find_root(__file__) / 'generators/6b88648ff0e0/workspace/parametric/adapter.py'
    assert path.is_file(), 'native strip adapter is missing'
    spec = importlib.util.spec_from_file_location('_strip_native_test',path)
    mod = importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def fixture(strips):
    grid = [[9]*8 for _ in range(8)]
    for i,strip in enumerate(strips):
        for dr in (0,1):
            r = 3*i+dr
            for c in (0,1,5,6):grid[r][c]=8
            grid[r][2:5] = strip[dr][:]
    return grid


def test_crop_then_key_frequency_changes_whole_strip_order():
    a = adapter()
    s0 = [[2,5,2],[2,3,4]]
    s1 = [[5,5,5],[2,3,4]]
    s2 = [[2,2,2],[2,2,6]]
    g = fixture([s0,s1,s2])
    assert a.analyze(g)['key'] == 2
    assert a.claim(g,'key_frequency') == s2+s0+s1
    assert a.claim(g,'top_to_bottom') == s0+s1+s2
    assert a.claim(g,'bottom_to_top') == s2+s1+s0
    assert a.claim(g,'global_mode') != s2+s0+s1


def test_equal_key_counts_preserve_marker_row_order():
    a = adapter()
    s0 = [[2,5,2],[2,3,4]]
    s1 = [[5,5,5],[2,3,4]]
    s2 = [[2,2,6],[3,2,7]]
    assert a.claim(fixture([s0,s1,s2]),'key_frequency') == s0+s2+s1


def test_bad_requests_and_malformed_markers_fail_closed():
    a = adapter()
    for changes in ({'seed':True},{'seed':-1},{'demos':1},{'demos':7},
                    {'queries':True},{'queries':0},{'queries':5},{'demos':2.0},
                    {'settings':{}},{'settings':{'stack_order':'bad'}},
                    {'settings':{'stack_order':'key_frequency','extra':1}}):
        args = dict(seed=0,settings={'stack_order':'key_frequency'},demos=3,queries=4)
        args.update(changes)
        with pytest.raises(ValueError):a.generate(**args)
    e = a.generate(0,{'stack_order':'key_frequency'},3,4)
    g = copy.deepcopy(e['train'][0]['input'])
    g[0][0] = True
    with pytest.raises(ValueError):a.analyze(g)
    for g in ([],[[]],[[8]*8 for _ in range(8)],[[0]*8 for _ in range(8)]):
        with pytest.raises(ValueError):a.analyze(g)


@pytest.mark.parametrize('seed',[0,17,63])
def test_count_prefixes_paired_settings_and_finite_teaching(seed):
    a = adapter()
    e2 = a.generate(seed,{'stack_order':'key_frequency'},2,4)
    e6 = a.generate(seed,{'stack_order':'key_frequency'},6,4)
    assert e2['train'] == e6['train'][:2]
    assert e2['test'] == e6['test']
    assert len({str(p['input']) for p in e6['train']+e6['test']}) == 10
    assert a.analyze(e2['train'][0]['input'])['key'] != a.analyze(e2['train'][1]['input'])['key']
    for mode in a.SETTINGS:
        e = a.generate(seed,{'stack_order':mode},2,4)
        assert [p['input'] for p in e['train']+e['test']] == [p['input'] for p in e2['train']+e2['test']]
        assert a.teaching_check(e) == []
    assert a.generate(seed,{'stack_order':'key_frequency'},2,1)['test'] == e2['test'][:1]


def test_thirty_boundary_has_eight_wide_strips_not_padding():
    a = adapter()
    e = a.generate(17,{'stack_order':'key_frequency'},3,4)
    g = e['test'][-1]['input'];info=a.analyze(g)
    assert len(g)==len(g[0])==30
    assert len(info['strips']) == 8 and len(info['strips'][0][0]) == 26
    assert len(e['test'][-1]['output']) == 16 and len(e['test'][-1]['output'][0]) == 26
    assert sum(v != 0 for r in g for v in r) > 600
    assert info['groups'][0][0]==0 and info['groups'][-1][0]==28


def test_public_projection_does_not_reveal_current_answer_or_future_input():
    a=adapter();e=a.generate(0,{'stack_order':'key_frequency'},3,4)
    v=a.public_turn(e,0)
    assert set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'}
    changed=copy.deepcopy(e);changed['settings']={'secret':4};changed['program_solution']='secret'
    for p in changed['test']:p['output']=[[1]]
    changed['test'][1]['input']=[[2]]
    assert a.public_turn(changed,0)==v
    assert a.public_turn(a.generate(0,{'stack_order':'key_frequency'},3,1),0)==v
    for index in (True,-1,4):
        with pytest.raises(ValueError):a.public_turn(e,index)

@pytest.mark.parametrize('seed,mode',[(1,'bottom_to_top'),(19,'key_frequency')])
def test_two_demo_lesson_refutes_lexical_and_row_sum_regressions(seed,mode):
    a=adapter()
    e=a.generate(seed,{'stack_order':mode},2,4)
    assert a.teaching_check(e)==[]
