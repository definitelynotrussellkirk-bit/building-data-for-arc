import copy
import importlib.util
import json
from pathlib import Path
import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]

@pytest.fixture(scope='module')
def a():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.is_file(), 'native comb adapter is missing'
    spec=importlib.util.spec_from_file_location('tested_4c3d4a41',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def literal(text):
    return [[int(v) if v!='.' else 0 for v in row] for row in text.split()]


def test_original_labels(a):
    d=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['4c3d4a41']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['4c3d4a41']
    for sp in ('train','test'):
        for i,p in enumerate(d[sp]):
            assert a.solve(p['input'],'insert')==(p['output'] if sp=='train' else gold[i]), (sp,i)


def test_literal_push_clip_caps_and_source_erasure(a):
    g=literal('''.....5555555
                 .....5.2.5.5
                 .5...5.2.3.5
                 .5.5...2...5
                 .555.......5
                 .....5.....5
                 .....5555555''')
    expected=literal('''.....5555555
                        .....5.2.5.5
                        .....5.5.3.5
                        .......5.5.5
                        .......555.5
                        .....5.....5
                        .....5555555''')
    before=copy.deepcopy(g)
    assert a.solve(g,'insert')==expected
    assert g==before
    marked=copy.deepcopy(expected);marked[1][7]=1
    assert a.solve(g,'longest_survivor')==marked  # survivor-count tie => leftmost


def test_default_exact_racket(a):
    assert a.program({'selection':'insert'})==(HOME/'reference.rkt').read_text()
    assert (HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()


@pytest.mark.parametrize('settings',[None,{}, {'selection':'other'}, {'selection':True}, {'selection':'insert','secret':1}])
def test_bad_settings(a,settings):
    with pytest.raises(ValueError):a.program(settings)


@pytest.mark.parametrize('field,value',[('seed',True),('seed',-1),('demos',1),('demos',7),('demos',2.0),('queries',0),('queries',5),('queries',True)])
def test_bad_requests(a,field,value):
    kw=dict(seed=0,settings={'selection':'insert'},demos=3,queries=4);kw[field]=value
    with pytest.raises(ValueError):a.generate(**kw)


def test_counts_prefixes_matched_inputs_and_real_stress(a):
    for seed in (0,17,43):
        full=a.generate(seed,{'selection':'insert'},6,4)
        alt=a.generate(seed,{'selection':'longest_survivor'},6,4)
        for sp in ('train','test'):
            assert [p['input'] for p in full[sp]]==[p['input'] for p in alt[sp]]
        for d in range(2,7):
            for q in range(1,5):
                ep=a.generate(seed,{'selection':'insert'},d,q)
                assert ep['train']==full['train'][:d] and ep['test']==full['test'][:q]
        gs=[p['input'] for sp in ('train','test') for p in full[sp]]
        assert len({json.dumps(g) for g in gs})==10
        stress=full['test'][3]['input']
        assert len(stress)==len(stress[0])==30
        assert sum(v!=0 for row in stress for v in row)>=200
        assert a.extract(stress)['capacity']>=20 and len(a.extract(stress)['lanes'])>=6


def test_rank_inversion_and_minimum_demo_teaching(a):
    for seed in range(16):
        for mode in a.MODES:
            ep=a.generate(seed,{'selection':mode},2,4)
            for rival in a.RIVALS:
                if all(a.rival(p['input'],rival)==p['output'] for p in ep['train']):
                    assert all(a.rival(p['input'],rival)==p['output'] for p in ep['test']), (seed,mode,rival)
        ep=a.generate(seed,{'selection':'longest_survivor'},2,4)
        assert any(a.counterfactual(p['input'])!=p['output'] for p in ep['train'])


def test_public_projection_private_invariance(a):
    ep=a.generate(17,{'selection':'insert'},3,4)
    order=a.query_order(7)
    for turn in range(4):
        before=a.public_turn(ep,turn,presentation_seed=7)
        mutated=copy.deepcopy(ep)
        mutated['settings']='secret';mutated['program_solution']='secret';mutated['seed']=-1
        for p in mutated['train']:p['secret']='x'
        for i,p in enumerate(mutated['test']):
            p['output']='secret';p['secret']='x'
            if i!=order[turn]:p['input']='future'
        assert a.public_turn(mutated,turn,presentation_seed=7)==before
        assert set(before)=={'train','test'} and len(before['test'])==1
        assert set(before['test'][0])=={'input'}
    assert {a.query_order(s)[0] for s in range(64)}=={0,1,2,3}
    with pytest.raises(ValueError):a.public_turn(ep,True)
    with pytest.raises(ValueError):a.public_turn(a.generate(17,{'selection':'insert'},2,1),0)


def test_base_api_findings_and_nonmutation(a):
    path=HOME/'generator.py';assert path.is_file()
    spec=importlib.util.spec_from_file_location('g_4c3d4a41',path)
    g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    for i in range(10):
        sample=g.generate(17,i,difficulty='medium');before=copy.deepcopy(sample)
        assert g.self_check(sample)==[] and before==sample
    for bad in ([],[[True]],[[1,2],[3]],[[0]*6 for _ in range(6)]):
        assert isinstance(g.self_check(bad),list) and g.self_check(bad)
    with pytest.raises(ValueError):g.generate(1,0,unknown=1)


def test_zero_tooth_and_complete_clipping_are_real_sampler_boundaries(a):
    for seed in range(8):
        teaching=a.extract(a.scene(seed,1))
        assert any(l['tooth']==0 for l in teaching['lanes']), 'missing flat comb segment'
        stress=a.scene(seed,8);spec=a.extract(stress)
        assert any(l['tooth']==spec['capacity'] for l in spec['lanes']), 'missing full overflow'
        assert any(not cells for cells in a.surviving(a.solve(stress),spec))


def test_racket_rival_probe_compares_real_outputs(a):
    path=HOME/'workspace/parametric/audit.py'
    spec=importlib.util.spec_from_file_location('audit_4c3d4a41_test',path)
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    assert hasattr(audit,'protected_rivals'), 'executable rival probe is missing'
    from arcpuzzles.parametric_worker import _real_evaluator, _grid
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    count=0
    def execute(program,g):
        nonlocal count
        count+=1
        return _grid(apply(program,g))
    try:
        report=audit.protected_rivals(a,execute,seeds=(0,17))
        assert count==60 and report['evaluations']==60
        assert report['harmful_survivors']==[] and len(report['checks'])==20
        assert identity['backend']=='racket' and identity['protected'] is True
    finally:bridge.close()


def test_bound_probe_rejects_stale_hash_and_symlink(tmp_path,monkeypatch):
    import hashlib
    path=HOME/'workspace/parametric/audit.py'
    spec=importlib.util.spec_from_file_location('audit_4c3d4a41_bound',path)
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    source=tmp_path/'adapter.py';source.write_text('original\n')
    pf={'status':'passed','owner_accepted':False,'source_binding':{'task_id':HOME.name,
        'files':[{'path':'adapter.py','sha256':hashlib.sha256(source.read_bytes()).hexdigest()}]}}
    monkeypatch.setattr(audit,'ROOT',tmp_path)
    assert audit.bound(pf)==pf['source_binding']
    source.write_text('changed\n')
    with pytest.raises(ValueError):audit.bound(pf)
    source.unlink();outside=tmp_path/'actual.py';outside.write_text('original\n');source.symlink_to(outside)
    with pytest.raises(ValueError):audit.bound(pf)


def test_teaching_changes_winners_original_rank(a):
    for seed in range(16):
        for index,rank in ((0,2),(1,3),(7,1)):
            g=a.scene(seed,index);spec=a.extract(g)
            groups=a.surviving(a.solve(g),spec)
            winner=max(range(len(groups)),key=lambda i:len(groups[i]))
            amounts=[l['amount'] for l in spec['lanes']]
            actual_rank=1+sum(n>amounts[winner] for n in amounts)
            assert actual_rank==rank,(seed,index,actual_rank,rank)
        ep=a.generate(seed,{'selection':'longest_survivor'},2,4)
        for name in ('source_second','source_third'):
            assert any(a.rival(p['input'],name)!=p['output'] for p in ep['train'])


def test_historical_source_rank_witness_is_now_refuted(a):
    fixture=HOME/'workspace/parametric/regression-source-rank.json'
    assert fixture.is_file(), 'retain the executable teaching failure'
    old=json.loads(fixture.read_text())
    for p in old['train']:
        assert a.rival(p['input'],'source_second')==p['output']
    assert a.rival(old['query']['input'],'source_second')!=old['query']['output']
    repaired=a.generate(old['seed'],old['settings'],2,4)
    assert any(a.rival(p['input'],'source_second')!=p['output'] for p in repaired['train'])
