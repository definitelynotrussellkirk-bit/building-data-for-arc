"""Shorter-first obstacle routing; literal labels plus native contract checks."""
from pathlib import Path
import importlib.util
import copy
import json
import pytest
from reviewer_support import canonical_pairs, find_root

HOME=Path(__file__).resolve().parent.parent/'workspace/parametric'

def adapter():
    path=HOME/'adapter.py';assert path.is_file(),'Native routing adapter is missing'
    spec=importlib.util.spec_from_file_location('elbow_parametric_test',path)
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    return a


def fixture():
    g=[[0]*9 for _ in range(7)]
    g[1][1]=g[3][4]=4
    g[0][3]=g[6][7]=2
    return g


def test_completed_shorter_path_forces_the_later_bend():
    a=adapter();g=fixture();saved=copy.deepcopy(g)
    expected=[[0,0,0,2,2,2,2,2,0],
      [0,4,0,0,0,0,0,2,0], [0,4,0,0,0,0,0,2,0],
      [0,4,4,4,4,0,0,2,0],
      [0,0,0,0,0,0,0,2,0], [0,0,0,0,0,0,0,2,0], [0,0,0,0,0,0,0,2,0]]
    out,trace=a.route(g)
    assert out==expected
    assert [t['color'] for t in trace]==[4,2]
    assert [t['orientation'] for t in trace]==['vh','hv']
    assert trace[1]['vertical_collisions']==[[3,3]]
    assert a.solve(g,'canonical')!=expected
    assert a.route(g,avoid=False)[0]!=expected
    assert g==saved


def test_canonical_overwrites_in_original_reading_order():
    a=adapter();g=fixture();out=a.solve(g,'canonical')
    assert out[3][3]==4 and out[2][3]==2 and out[6][7]==2
    assert out[0][4]==0


def test_equal_lengths_use_reading_order_and_total_fallback():
    a=adapter();g=[[0]*8 for _ in range(8)]
    g[0][2]=g[3][3]=7;g[1][0]=g[3][2]=1
    out,trace=a.route(g)
    assert [t['distance'] for t in trace]==[4,4]
    assert [t['color'] for t in trace]==[7,1]
    assert trace[1]['fallback'] is True
    assert out[3][2]==1


def test_claim_model_preserves_every_canonical_pair():
    a=adapter()
    for pair in canonical_pairs('2dae2c34641b',root=find_root(__file__)):
        assert a.solve(pair['input'],'canonical')==pair['output']


def test_counts_prefixes_settings_neutrality_and_finite_teaching():
    a=adapter()
    for seed in (0,17,31):
        for demos in range(2,7):
            eps=[a.generate(seed,{'routing':m},demos,4) for m in a.MODES]
            for mode,e in zip(a.MODES,eps):
                assert len(e['train'])==demos and len(e['test'])==4
                keys=[json.dumps(p['input']) for p in e['train']+e['test']]
                assert len(set(keys))==demos+4
                assert e==a.generate(seed,{'routing':mode},demos,4)
                assert a.generate(seed,{'routing':mode},2,4)['train']==e['train'][:2]
                assert a.generate(seed,{'routing':mode},demos,1)['test']==e['test'][:1]
                assert a.teaching_audit(e)['query_disagreeing_survivors']==[]
                for pair in e['train']+e['test']:
                    a.validate_input(pair['input'])
                    assert not any(t['fallback'] for t in a.route(pair['input'])[1])
            assert [p['input'] for p in eps[0]['train']+eps[0]['test']]==[p['input'] for p in eps[1]['train']+eps[1]['test']]


def test_thirty_by_thirty_uses_the_canvas_and_all_nine_colors():
    a=adapter()
    for mode in a.MODES:
        e=a.generate(17,{'routing':mode},3,4);p=e['test'][3];g=p['input'];out=p['output']
        assert len(g)==len(g[0])==len(out)==len(out[0])==30
        assert sum(bool(v) for row in g for v in row)==18
        assert len({v for row in g for v in row if v})==9
        assert any(g[0]) and any(g[-1]) and any(r[0] for r in g) and any(r[-1] for r in g)
        assert sum(bool(v) for row in out for v in row)>=200
        assert any(t['orientation']=='hv' for t in a.route(g)[1])


@pytest.mark.parametrize('args',[(True,{'routing':'canonical'},3,4),(-1,{'routing':'canonical'},3,4),
 (0,{},3,4),(0,{'routing':'unknown'},3,4),(0,{'routing':'canonical','extra':1},3,4),
 (0,{'routing':'canonical'},1,4),(0,{'routing':'canonical'},7,4),(0,{'routing':'canonical'},3.0,4),
 (0,{'routing':'canonical'},3,0),(0,{'routing':'canonical'},3,5),(0,{'routing':'canonical'},3,True)])
def test_requests_are_strict(args):
    with pytest.raises(ValueError): adapter().generate(*args)


@pytest.mark.parametrize('g',[[],[[True]],[[0],[1,2]],[[10]],[[1,0],[0,0]],[[2,2],[0,0]]])
def test_malformed_or_aligned_pairs_are_rejected(g):
    with pytest.raises(ValueError): adapter().validate_input(g)


def test_public_projection_hides_private_data_and_future_queries():
    a=adapter();e=a.generate(8,{'routing':a.MODES[1]},3,4)
    expected=a.public_turn_bytes(e,0)
    assert expected==a.public_turn_bytes(a.generate(8,{'routing':a.MODES[1]},3,1),0)
    e['settings']={'secret':9};e['program_solution']='secret';e['queries_total']=4
    for p in e['train']: p['private']='secret'
    for p in e['test']: p['output']=[[9]];p['private']='secret'
    assert expected==a.public_turn_bytes(e,0)
    v=json.loads(expected)
    assert set(v)=={'train','test'} and len(v['test'])==1
    assert set(v['test'][0])=={'input'}
    with pytest.raises(ValueError):a.public_turn_bytes(e,-1)


def test_programs_are_single_complete_forms_and_default_is_byte_exact():
    from arc_repl.parser import parse_all
    a=adapter()
    assert a.program({'routing':'canonical'}).encode()==(HOME/'canonical.rkt').read_bytes()
    for mode in a.MODES:
        assert len(parse_all(a.program({'routing':mode})))==1
    assert len(parse_all(a.routing_program(avoid=False)))==1


def test_reusable_audit_exercises_all_demo_counts():
    path=HOME/'audit.py';assert path.is_file(),'Reusable audit is missing'
    spec=importlib.util.spec_from_file_location('elbow_audit_test',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    report=mod.run_sweep(2)
    assert report['episodes']==20 and report['labeled_pair_checks']==160
    assert report['failures']==[] and report['fallbacks']==0
    assert report['demo_counts']==[2,3,4,5,6]
