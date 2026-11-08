from pathlib import Path
import copy
import importlib.util
import json
import random
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p / 'shared/data/raw/arc-agi_evaluation_challenges.json').exists())
BASE = HOME / 'workspace/parametric'


def load(name):
    path = BASE / (name + '.py')
    assert path.exists(), f'missing implementation: {path.name}'
    spec = importlib.util.spec_from_file_location('_test_6e_' + name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def originals():
    raw = ROOT / 'shared/data/raw'
    p = json.loads((raw/'arc-agi_evaluation_challenges.json').read_text())['6e453dd6']
    gold = json.loads((raw/'arc-agi_evaluation_solutions.json').read_text())['6e453dd6']
    return p['train'] + [{'input': x['input'], 'output': y} for x,y in zip(p['test'],gold)]


@pytest.mark.parametrize('index', range(4))
def test_official_pairs(index):
    pair=originals()[index]
    assert load('core').solve(pair['input']) == pair['output']


@pytest.mark.parametrize('demos', [2,3,6])
@pytest.mark.parametrize('queries', [1,2,4])
def test_counts_prefix_and_matched_inputs(demos, queries):
    a=load('adapter')
    x=a.generate(17, {'projection':'all'}, demos, queries)
    y=a.generate(17, {'projection':'largest_hole'}, demos, queries)
    full=a.generate(17, {'projection':'all'}, 6, 4)
    assert len(x['train'])==demos and len(x['test'])==queries
    assert x['train']==full['train'][:demos] and x['test']==full['test'][:queries]
    assert [p['input'] for s in ('train','test') for p in x[s]]==[p['input'] for s in ('train','test') for p in y[s]]
    assert any(p['output']!=q['output'] for p,q in zip(x['train'],y['train']))
    inputs=[json.dumps(p['input']) for s in ('train','test') for p in full[s]]
    assert len(inputs)==len(set(inputs))


def test_default_exact_and_local_rng():
    a=load('adapter'); state=random.getstate()
    x=a.generate(43, {'projection':'all'}, 2, 4)
    assert random.getstate()==state
    assert x==a.generate(43, {'projection':'all'}, 2, 4)
    assert a.program({'projection':'all'}).encode()==(HOME/'reference.rkt').read_bytes()==(BASE/'canonical.rkt').read_bytes()


@pytest.mark.parametrize('settings', [{},{'projection':'other'},{'projection':True},{'projection':'all','extra':1}])
def test_settings_rejected(settings):
    with pytest.raises(ValueError): load('adapter').program(settings)


@pytest.mark.parametrize('seed,demos,queries', [(True,2,4),(-1,2,4),(2**63,2,4),(0,True,4),(0,1,4),(0,7,4),(0,2,False),(0,2,0),(0,2,5)])
def test_invalid_requests(seed,demos,queries):
    with pytest.raises(ValueError): load('adapter').generate(seed,{'projection':'largest_hole'},demos,queries)


@pytest.mark.parametrize('grid', [[],[[True]],[[1.0]],[[10]],[[1],[1,2]],[[0]*31]])
def test_strict_grid(grid):
    with pytest.raises(ValueError): load('core').solve(grid)


def test_stress_and_diverse_intermediates():
    a=load('adapter'); c=a.CORE; totals=set(); firsts=set()
    for seed in range(16):
        x=a.generate(seed,{'projection':'largest_hole'},2,4)
        firsts.add(json.dumps(x['test'][0]['input']))
        assert any(len(p['input'])==len(p['input'][0])==30 for p in x['test'])
        for p in x['train']+x['test']:
            meta=c.analyze(p['input']); totals.add(meta['eligible_count'])
            assert c.solve(p['input'],'largest_hole')==p['output']
        first_source=a.source_order(seed)[0]
        assert 0<=first_source<4
    assert len(firsts)>12 and len(totals)>=2
    assert len({a.source_order(s)[0] for s in range(16)})>=3


def test_public_no_private_data_and_detached():
    a=load('adapter'); e=a.generate(19,{'projection':'largest_hole'},2,4)
    view=a.public_view(e,0); frozen=copy.deepcopy(view)
    assert set(view)=={'train','test'} and len(view['test'])==1 and set(view['test'][0])=={'input'}
    e['settings']={'secret': True}; e['test'][0]['output']=[[9]]; e['test'][1]['input']=[[8]]; e['program_solution']='private'
    assert a.public_view(e,0)==frozen
    view['train'][0]['input'][0][0]=9
    assert a.public_view(e,0)==frozen


def test_largest_cavity_not_largest_bbox():
    c=load('core'); g=c.build(31,0)
    assert c.solve(g,'largest_hole') != c.rival(g,'bbox_area','largest_hole')


@pytest.mark.parametrize('seed', range(16))
def test_minimum_curriculum_defeats_declared_rivals(seed):
    a=load('adapter')
    for mode in a.CORE.MODES:
        e=a.generate(seed,{'projection':mode},2,4)
        for name in a.CORE.RIVALS:
            fits=all(a.CORE.rival(p['input'],name,mode)==p['output'] for p in e['train'])
            changes=any(a.CORE.rival(p['input'],name,mode)!=p['output'] for p in e['test'])
            assert not (fits and changes), (seed,mode,name)


def test_stress_witness_changes_under_raw_contact_ablation():
    a=load('adapter')
    e=a.generate(17,{'projection':'largest_hole'},2,4)
    p=next(p for p in e['test'] if len(p['input'])==len(p['input'][0])==30)
    # There can be incidental 30x30 scenes; the retained witness must exist.
    assert any(len(p['input'])==len(p['input'][0])==30 and
               a.CORE.solve(p['input'],'largest_hole',strategy='raw_contact')!=p['output']
               for p in e['test'])


def test_export_verifier_negative_controls():
    v=load('verify'); a=load('adapter')
    good=a.public_view(a.generate(17,{'projection':'largest_hole'},2,4),0)
    v.validate_public(good)
    for kind in ('answer','settings','bool','duplicate','query_count','bad_id'):
        with pytest.raises(ValueError): v.negative_case(good,kind)


def test_source_binding_detects_stale_bytes(tmp_path):
    v=load('verify'); p=tmp_path/'source.py'; p.write_text('pass\n')
    binding={'files':[{'path':'source.py','sha256':v.sha(p.read_bytes())}]}
    v.check_binding(tmp_path,binding)
    p.write_text('raise ValueError\n')
    with pytest.raises(ValueError): v.check_binding(tmp_path,binding)


def test_racket_sources_are_single_complete_expressions():
    from arcpuzzles.review_witness import _validate_programs
    for p in BASE.glob('*.rkt'):
        _validate_programs([{'program':p.read_text(),'counterfactual_program':p.read_text()}])


def test_sampler_exercises_already_docked_objects():
    c=load('core');seen=False
    for seed in range(8):
        a=c.analyze(c.build(seed,1))
        seen |= any(o['c2']==a['wall']-1 for o in a['objects'])
    assert seen


def test_rejects_gray_off_the_wall():
    c=load('core');g=c.build(17,0);a=c.analyze(g)
    r,col=next((r,col) for r,row in enumerate(g) for col,v in enumerate(row) if v==a['background'] and col<a['wall'])
    g[r][col]=5
    with pytest.raises(ValueError):c.analyze(g)


def test_open_notch_does_not_project_but_closed_rectangle_does():
    c=load('core');g=[[6]*12 for _ in range(10)]
    for row in g:row[8]=5
    for r in (0,2):
        for col in range(5):g[r][col]=0
    g[1][4]=0
    for r in range(4,8):
        for col in range(1,6):
            if r in (4,7) or col in (1,5):g[r][col]=0
    out=c.solve(g)
    assert [r for r in range(10) if out[r][9]==2]==[5,6]
    assert all(out[1][col]==6 for col in range(9,12))


def test_witness_payload_matches_owner_schema():
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    import hashlib
    v=load('verify')
    identity={'backend':'racket','protected':True,'binary_sha256':'a'*64}
    binding={'task_id':HOME.name,'files':[{'path':'dummy.py','sha256':'b'*64}]}
    program='(lambda (g) g)'
    settings={'unit_test':'only'}
    case={'input':[[0]],'settings':settings,'intermediate_value':1,'program':program,
          'output':[[0]],'counterfactual_program':'(lambda (g) (list (list 1)))',
          'counterfactual_output':[[1]],'ablation':'wrong_intermediate'}
    assert callable(getattr(v,'pack_witness',None)), 'owner-compatible witness producer is missing'
    witness=v.pack_witness(binding,identity,[case])
    assert witness['racket']=={'backend':'racket','protected':True}
    receipt={'source_binding':binding,'programs':{json.dumps(settings,sort_keys=True,separators=(',',':')):hashlib.sha256(program.encode()).hexdigest()}}
    dependency={**v.descriptions(),'witness_path':'witness.json'}
    checked=validate_sequential_witness({'sequential_dependency':dependency},receipt,lambda _:json.dumps(witness).encode())
    assert checked['cases']==1


def test_witness_requires_real_protected_identity():
    v=load('verify')
    assert callable(getattr(v,'pack_witness',None)), 'protected identity check is missing'
    for identity in ({'backend':'python','protected':True},{'backend':'racket','protected':False},{}):
        with pytest.raises(ValueError):v.pack_witness({'task_id':HOME.name},identity,[])
