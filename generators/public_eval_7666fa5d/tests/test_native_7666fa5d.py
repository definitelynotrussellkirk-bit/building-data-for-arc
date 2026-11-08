"""Behavioral checks for a general rule, not a lookup of official grids."""
from pathlib import Path
import copy, importlib.util, json
import pytest
HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]
BASE=HOME/'workspace/parametric'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

@pytest.fixture(scope='module')
def a():
    assert (BASE/'adapter.py').is_file(), 'Native adapter is not implemented'
    return load('tested_7666fa5d',BASE/'adapter.py')

@pytest.fixture(scope='module')
def rk():
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator
    with _local_imports(ROOT/'shared/runtime',BASE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        assert identity['backend']=='racket' and identity['protected']
        yield apply
        bridge.close()

def test_original_rule_is_implemented_and_matches_all_labels(rk):
    assert (HOME/'reference.rkt').is_file(), 'General reference rule is not implemented'
    program=(HOME/'reference.rkt').read_text()
    originals=json.loads((HOME/'tests/fixtures/original.json').read_text())
    for split in ('train','test'):
        for pair in originals[split]: assert rk(program,pair['input'])==pair['output']

@pytest.mark.parametrize('mode',['all_spans','equal_length'])
def test_claims_match_protected_racket(a,rk,mode):
    ep=a.generate(17,{'bracket_rule':mode},2,4)
    for pair in ep['train']+ep['test']:
        assert rk(ep['program_solution'],pair['input'])==pair['output']

def test_canonical_copy_is_exact(a):
    assert a.program({'bracket_rule':'all_spans'}).encode()==(HOME/'reference.rkt').read_bytes()==(BASE/'canonical.rkt').read_bytes()

def test_original_oracle_preserves_all_given_strokes(a):
    originals=json.loads((HOME/'tests/fixtures/original.json').read_text())
    for pair in originals['train']+originals['test']:
        assert a.model.solve(pair['input'],'all_spans')==pair['output']

def test_all_prefixes_settings_and_distinct_inputs(a):
    for seed in (0,17,43):
        for mode in ('all_spans','equal_length'):
            ep=a.generate(seed,{'bracket_rule':mode},6,4)
            for demos in range(2,7):
                for queries in range(1,5):
                    part=a.generate(seed,{'bracket_rule':mode},demos,queries)
                    assert part['train']==ep['train'][:demos]
                    assert part['test']==ep['test'][:queries]
            other=a.generate(seed,{'bracket_rule':'equal_length' if mode=='all_spans' else 'all_spans'},6,4)
            assert [p['input'] for p in ep['train']+ep['test']]==[p['input'] for p in other['train']+other['test']]
            assert len({json.dumps(p['input']) for p in ep['train']+ep['test']})==10
            assert any(ep['train'][i]['output']!=other['train'][i]['output'] for i in range(2))

def test_query_shuffle_is_not_fixed_by_ordinal(a):
    positions=set()
    for seed in range(16):
        ep=a.generate(seed,{'bracket_rule':'all_spans'},2,4)
        positions.add(next(i for i,p in enumerate(ep['test']) if len(p['input'])==len(p['input'][0])==30))
    assert len(positions)>1

def test_30_stress_has_real_content_and_reaches_edge(a,rk):
    for mode in ('all_spans','equal_length'):
        ep=a.generate(43,{'bracket_rule':mode},2,4)
        p=next(p for p in ep['test'] if len(p['input'])==len(p['input'][0])==30)
        assert sum(v!=8 for row in p['input'] for v in row)>=75
        assert sum(v!=8 for row in p['output'] for v in row)>=250
        assert rk(ep['program_solution'],p['input'])==p['output']
        assert any(v!=8 for v in p['output'][0]+p['output'][-1]) or any(row[0]!=8 or row[-1]!=8 for row in p['output'])

@pytest.mark.parametrize('d,q',[(1,4),(7,4),(2,0),(2,5),(True,4),(2,True),(2.0,4)])
def test_count_validation(a,d,q):
    with pytest.raises((TypeError,ValueError)):a.generate(1,{'bracket_rule':'all_spans'},d,q)

@pytest.mark.parametrize('setting',[{}, {'bracket_rule':'bad'}, {'bracket_rule':True},{'bracket_rule':'all_spans','extra':1},None])
def test_setting_validation(a,setting):
    with pytest.raises((TypeError,ValueError)):a.program(setting)

@pytest.mark.parametrize('seed',[True,-1,1.5,'17',2**63])
def test_seed_validation(a,seed):
    with pytest.raises((TypeError,ValueError)):a.generate(seed,{'bracket_rule':'all_spans'},2,4)

def test_public_views_ignore_all_private_metadata(a):
    ep=a.generate(17,{'bracket_rule':'all_spans'},2,4)
    before=copy.deepcopy(ep);view=a.public_view(ep,0)
    assert set(view)=={'train','test'} and set(view['test'][0])=={'input'}
    ep['settings']={'secret':'x'};ep['program_solution']='secret';ep['seed']=999
    ep['test'][0]['output']=[[9]];ep['test'][1:]=[{'input':[[9]],'output':[[9]]}]
    assert a.public_view(ep,0)==view
    view['train'][0]['input'][0][0]=99
    assert ep['train']==before['train']

def test_finite_minimum_lesson_no_dangerous_rival(a):
    for seed in range(32):
        for mode in ('all_spans','equal_length'):
            ep=a.generate(seed,{'bracket_rule':mode},2,4)
            for rival in a.model.RIVALS:
                fits=all(a.model.solve(p['input'],mode,rival)==p['output'] for p in ep['train'])
                assert not fits or all(a.model.solve(p['input'],mode,rival)==p['output'] for p in ep['test']), (seed,mode,rival)

def test_rival_programs_are_total_and_match_claims(a,rk):
    for mode in ('all_spans','equal_length'):
        ep=a.generate(17,{'bracket_rule':mode},2,4)
        for rival in a.model.RIVALS:
            p=ep['train'][0]
            assert rk(a.rival_program({'bracket_rule':mode},rival),p['input'])==a.model.solve(p['input'],mode,rival)

def test_wrong_intermediate_changes_output(a,rk):
    ep=a.generate(17,{'bracket_rule':'all_spans'},2,4);p=ep['train'][0]
    wrong=a.rival_program({'bracket_rule':'all_spans'},'point_spans')
    assert rk(wrong,p['input'])!=p['output']

def test_ordinary_entry_point(a,rk):
    gen=load('base_7666fa5d',HOME/'generator.py')
    for difficulty in ('easy','medium','hard'):
        g=gen.generate(seed=17,sample_index=1,difficulty=difficulty)
        assert gen.self_check(g)==[]
        assert rk(a.program({'bracket_rule':'all_spans'}),g)==a.model.solve(g,'all_spans')
    with pytest.raises((TypeError,ValueError)):gen.generate(seed=True)
    with pytest.raises((TypeError,ValueError)):gen.generate(seed=1,sample_index=-1)
    with pytest.raises((TypeError,ValueError)):gen.generate(seed=1,difficulty='bogus')

def test_public_writer_is_visible_byte_ordered_and_duplicate_rejecting(a,tmp_path):
    assert (BASE/'audit_native.py').exists(), 'Reusable audit/export tool not implemented'
    tool=load('audit_7666fa5d',BASE/'audit_native.py')
    episodes=[a.generate(s,{'bracket_rule':'all_spans'},2,4) for s in (17,43)]
    left=tool.materialize_views(episodes,tmp_path/'left')
    right=tool.materialize_views(list(reversed(episodes)),tmp_path/'right')
    assert left['view_ids']==sorted(left['view_ids'])==right['view_ids']
    assert left['files_written']==8
    assert [(p.name,p.read_bytes()) for p in sorted((tmp_path/'left/public').iterdir())]==[(p.name,p.read_bytes()) for p in sorted((tmp_path/'right/public').iterdir())]
    with pytest.raises(ValueError,match='duplicate'):
        tool.materialize_views([episodes[0],episodes[0]],tmp_path/'duplicates')
    assert not (tmp_path/'duplicates').exists()
    with pytest.raises(ValueError):tool.materialize_views(episodes,tmp_path/'left')


def test_continuous_diagonal_span_fills_between_discrete_rays(a,rk):
    g=[[8]*7 for _ in range(7)]
    for r,c in [(0,2),(1,1),(2,0)]:g[r][c]=4
    for r,c in [(3,5),(4,4),(5,3)]:g[r][c]=7
    want=copy.deepcopy(g)
    for r,c in [(1,2),(1,3),(2,1),(2,2),(2,3),(2,4),(3,1),(3,2),(3,3),(3,4),(4,2),(4,3)]:want[r][c]=2
    for mode in ('all_spans','equal_length'):
        assert a.model.solve(g,mode)==want
        assert rk(a.program({'bracket_rule':mode}),g)==want
        assert a.model.solve(g,mode,'endpoint_rays')!=want

def test_equal_length_rejects_an_unequal_pair(a,rk):
    g=[[8]*8 for _ in range(8)]
    for r,c in [(0,2),(1,1),(2,0),(2,6),(3,5),(4,4),(5,3)]:g[r][c]=9
    assert a.model.solve(g,'all_spans')[2][2]==2
    assert a.model.solve(g,'equal_length')==g
    assert rk(a.program({'bracket_rule':'equal_length'}),g)==g

def test_pairing_uses_separate_collinear_segments(a):
    g=[[8]*10 for _ in range(10)]
    for r,c in [(0,8),(1,7),(6,2),(7,1)]:g[r][c]=3
    segments=a.model.analyze(g)
    assert [(s['u'],s['lo'],s['hi'],s['length']) for s in segments]==[(8,-8,-6,2),(8,4,6,2)]
    assert a.model.solve(g,'all_spans')==g

@pytest.mark.parametrize('name,old,new',[
    ('first_four','(define segments (if first-pair-only? (take eligible (min 2 (length eligible))) eligible))','(define segments (take eligible (min 4 (length eligible))))'),
    ('length_thirteen','(define max-length 60)','(define max-length 13)')])
def test_minimum_lesson_rejects_unseen_count_and_length_thresholds(a,rk,name,old,new):
    ep=a.generate(17,{'bracket_rule':'all_spans'},2,4)
    assert ep['program_solution'].count(old)==1
    rival=ep['program_solution'].replace(old,new)
    assert not all(rk(rival,p['input'])==p['output'] for p in ep['train']),name

def test_retained_shortcuts_fit_old_demos_fail_query_and_new_lesson(a,rk):
    saved=json.loads((HOME/'tests/fixtures/count-length-counterexample.json').read_text())
    ep=a.generate(17,{'bracket_rule':'all_spans'},2,4)
    for row in saved['rivals'].values():
        assert [rk(row['program'],p['input'])==p['output'] for p in saved['pairs']]==[True,True,False]
        assert rk(row['program'],ep['train'][1]['input'])!=ep['train'][1]['output']
