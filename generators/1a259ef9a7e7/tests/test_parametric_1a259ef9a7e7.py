"""Native mirror/component family: independent literal and boundary regressions."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import pytest
from reviewer_support import find_root, public_challenge_bytes


def load():
    f=find_root(Path(__file__))/'generators/1a259ef9a7e7/workspace/parametric/prototype.py'
    assert f.is_file(), 'native mirror prototype is missing'
    s=importlib.util.spec_from_file_location('mirror_native_tests',f)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return m


def test_canonical_mirror_left_and_stack_phase():
    p=load()
    g=[[0,0],[0,5],[5,0]]
    expected=[[0,5,5,0],[5,0,0,5],[0,0,0,0],
              [0,0,0,0],[5,0,0,5],[0,5,5,0],
              [0,5,5,0],[5,0,0,5],[0,0,0,0]]
    before=deepcopy(g)
    assert p.solve(g,'all_components')==expected
    assert g==before


def test_components_merge_at_the_mirror_seam():
    p=load()
    g=[[2,0,0],[2,0,2],[0,0,2]]
    s=[0,0,2,2,0,0];z=[0]*6
    assert p.solve(g,'largest_mirrored')==[z,s,s,s,s,z,z,s,s]


def test_first_row_major_max_component_not_all_ties():
    p=load()
    g=[[0,0,2],[0,0,2],[0,0,0]]
    s=[2,0,0,0,0,0];z=[0]*6
    assert p.solve(g,'largest_mirrored')==[z,s,s,s,s,z,z,s,s]


def test_seam_merging_reverses_original_component_ranking():
    p=load()
    g=[[0,0,0,2,0],[0,0,0,2,2],[0]*5,[2,0,0,0,0],[2,0,0,0,0]]
    out=p.solve(g,'largest_mirrored')
    assert sum(v!=0 for row in out for v in row)==12
    assert {c for row in out for c,v in enumerate(row) if v}=={4,5}
    assert out!=p.predict(g,'before')


@pytest.mark.parametrize('settings',[None,{}, {'mode':False},{'mode':'bad'},{'mode':'all_components','secret':1}])
def test_bad_settings_fail_closed(settings):
    with pytest.raises(ValueError):load().generate(0,settings,3,4)


@pytest.mark.parametrize('key,value',[('seed',True),('seed',-1),('seed',2**63),('demos',2),('demos',7),('demos',3.0),('queries',0),('queries',5)])
def test_bad_requests_fail_closed(key,value):
    kw=dict(seed=0,settings={'mode':'all_components'},demos=3,queries=4);kw[key]=value
    with pytest.raises(ValueError):load().generate(**kw)


@pytest.mark.parametrize('g', [[],[[]],[[True,0]],[[10,0]],[[1,0],[1]],[[0]*16 for _ in range(3)],[[0]*2 for _ in range(11)]])
def test_illegal_grid_or_output_size_is_rejected(g):
    with pytest.raises(ValueError):load().solve(g,'all_components')


def test_counts_prefixes_matched_inputs_and_source_bytes():
    p=load();a=p.generate(17,{'mode':'all_components'},3,4);b=p.generate(17,{'mode':'largest_mirrored'},6,4)
    assert a==p.generate(17,{'mode':'all_components'},3,4)
    assert [x['input'] for x in a['train']]==[x['input'] for x in b['train'][:3]]
    assert [x['input'] for x in a['test']]==[x['input'] for x in b['test']]
    assert a['test'][:1]==p.generate(17,{'mode':'all_components'},6,1)['test']
    assert len({repr(x['input']) for x in b['train']+b['test']})==10
    assert a['program_solution']==Path(p.__file__).with_name('canonical.rkt').read_text()


def test_finite_teaching_and_substantive_30x30_output():
    p=load()
    for seed in range(8):
        for mode in p.MODES:
            e=p.generate(seed,{'mode':mode},3,4)
            assert p.teaching_check(e)['failures']==[]
            g,out=e['test'][3]['input'],e['test'][3]['output']
            assert (len(g),len(g[0]))==(10,15)
            assert (len(out),len(out[0]))==(30,30)
            assert sum(v!=0 for row in g for v in row)>=50
            assert sum(v!=0 for row in out for v in row)>=200
            assert all(any(row) for row in out)
            assert any(out[0]) and any(out[-1]) and any(row[0] for row in out) and any(row[-1] for row in out)


def test_public_projection_is_metadata_independent():
    p=load();e=p.generate(0,{'mode':'largest_mirrored'},3,4)
    raw=public_challenge_bytes(p.public_turn(e,0))
    e['train'][0]['settings']={'secret':True};e['test'][0]['output']=[[9]];e['program_solution']='secret'
    assert public_challenge_bytes(p.public_turn(e,0))==raw
    assert set(p.public_turn(e,0)['test'][0])=={'input'}


def test_racket_literal_seam_tie_and_wrong_order():
    # Legacy staged tests may preload the execution-layout namespace. Isolate
    # exact same-checkout imports, then restore it for the remaining tests.
    from arcpuzzles.parametric_worker import _real_evaluator, _local_imports
    root = find_root(Path(__file__))
    with _local_imports(root / 'shared/runtime', root / 'generators/1a259ef9a7e7/workspace/parametric'):
        from arc_repl.parser import parse_all
        p=load();apply,identity,bridge=_real_evaluator(find_root(Path(__file__))/'shared/runtime')
        try:
            assert identity['protected'] is True
            for mode in p.MODES:assert len(parse_all(p.program({'mode':mode})))==1
            g=[[2,0,0],[2,0,2],[0,0,2]]
            s=[0,0,2,2,0,0];z=[0]*6
            assert apply(p.program({'mode':'largest_mirrored'}),g)==[z,s,s,s,s,z,z,s,s]
            tie=[[0,0,2],[0,0,2],[0,0,0]]
            left=[2,0,0,0,0,0]
            assert apply(p.program({'mode':'largest_mirrored'}),tie)==[z,left,left,left,left,z,z,left,left]
            for policy,kw in [('before',{'order':'before'}),('before_then_after',{'order':'before_then_after'}),
                              ('eight',{'selector':'eight'}),('bbox',{'selector':'bbox'}),('all_max',{'selector':'all_max'}),
                              ('last_tie',{'selector':'last_tie'}),('stack_then_largest',{'order':'stack_then_largest'})]:
                for pair in p.generate(0,{'mode':'largest_mirrored'},3,4)['train']:
                    assert apply(p.racket_policy(**kw),pair['input'])==p.predict(pair['input'],policy)
        finally:bridge.close()

def test_three_demo_minimum_refutes_eight_neighbor_shortcut():
    p=load();e=p.generate(0,{'mode':'largest_mirrored'},3,4)
    assert all(p.predict(pair['input'],'eight')==pair['output'] for pair in e['train'][:2])
    assert any(p.predict(pair['input'],'eight')!=pair['output'] for pair in e['test'])
    assert p.predict(e['train'][2]['input'],'eight')!=e['train'][2]['output']


def test_lowest_component_is_not_a_substitute_for_largest():
    p=load();e=p.generate(0,{'mode':'largest_mirrored'},3,4)
    def lowest_rival(g):
        wide=p.mirror(g);groups=p.components(wide)
        keep=set(max(groups,key=lambda cells:max(r for r,c in cells)))
        masked=[[v if (r,c) in keep else 0 for c,v in enumerate(row)] for r,row in enumerate(wide)]
        return p.stack(masked)
    assert any(lowest_rival(pair['input'])!=pair['output'] for pair in e['train'])
