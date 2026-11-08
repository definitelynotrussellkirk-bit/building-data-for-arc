from pathlib import Path
import importlib.util
import json
import pytest
HOME=Path(__file__).resolve().parents[1]
BASE=HOME/'workspace/parametric'
def module(name):
    p=BASE/(name+'.py');assert p.is_file(),f"missing implementation: {p.name}"
    spec=importlib.util.spec_from_file_location('_reflected_'+name,p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def fixture():
    g=[[4]*13 for _ in range(11)]
    g[5]=[1]*13
    for row in g:row[6]=1
    for r,c in [(2,2),(2,9),(8,2),(8,9)]:g[r][c]=2
    for r,c,v in [(1,2,3),(2,1,8),(3,3,9)]:g[r][c]=v
    return g

@pytest.mark.parametrize('mode,additions',[
 ('panel_reflections',[(1,9,3),(2,10,8),(3,8,9),(9,2,3),(8,1,8),(7,3,9),(9,9,3),(8,10,8),(7,8,9)]),
 ('preserve_orientation',[(1,9,3),(2,8,8),(3,10,9),(7,2,3),(8,1,8),(9,3,9),(7,9,3),(8,8,8),(9,10,9)])])
def test_literal_panel_relative_transforms(mode,additions):
    g=fixture();want=[r[:] for r in g]
    for r,c,v in additions:want[r][c]=v
    assert module('prototype').solve(g,mode)==want

@pytest.mark.parametrize('split,index',[('train',0),('train',1),('test',0)])
def test_original_pairs(split,index):
    p=json.loads((HOME/'tests/fixtures/original.json').read_text())[split][index]
    assert module('prototype').solve(p['input'])==p['output']

def test_scaling_and_panel_clipping_have_literal_expected_cells():
    g=fixture()
    for r in (2,3):
        for c in (9,10):g[r][c]=2
    out=module('prototype').solve(g)
    assert all(out[r][c]==3 for r in (0,1) for c in (9,10))
    assert all(out[r][c]==8 for r in (2,3) for c in (11,12))
    assert [out[4][c] for c in (7,8)]==[9,9]
    assert out[5]==[1]*13 and all(row[6]==1 for row in out)

def test_blue_inside_source_is_not_global_divider():
    g=fixture();g[1][2]=1
    assert module('prototype').solve(g)[1][9]==1

def test_black_is_a_decoration_not_empty():
    g=fixture();g[1][2]=0
    assert module('prototype').solve(g)[1][9]==0

def test_source_can_move_to_another_quadrant():
    p=module('prototype');g=fixture();expected=p.solve(g)
    assert p.solve([r[::-1] for r in g])==[r[::-1] for r in expected]
    assert p.solve(g[::-1])==expected[::-1]

def test_ambiguous_source_rejected():
    g=fixture();g[0][8]=3
    with pytest.raises(ValueError,match='decorated'):module('prototype').analyse(g)

@pytest.mark.parametrize('bad',[[],[[True]],[[0],[0,0]],[[10]]])
def test_invalid_grid(bad):
    with pytest.raises(ValueError):module('prototype').analyse(bad)

def test_counts_matched_inputs_and_prefixes():
    a=module('adapter')
    for seed in [0,4,17,43]:
        full=a.generate(seed,{'orientation':'panel_reflections'},6,4)
        assert len({json.dumps(p['input']) for s in ('train','test') for p in full[s]})==10
        assert len(full['test'][3]['input'])==len(full['test'][3]['input'][0])==30
        for n in range(2,7):
            for q in range(1,5):
                ep=a.generate(seed,{'orientation':'panel_reflections'},n,q)
                assert ep['train']==full['train'][:n] and ep['test']==full['test'][:q]
        alt=a.generate(seed,{'orientation':'preserve_orientation'},6,4)
        assert [p['input'] for s in ('train','test') for p in alt[s]]==[p['input'] for s in ('train','test') for p in full[s]]

@pytest.mark.parametrize('seed,settings,demos,queries',[(True,{'orientation':'panel_reflections'},2,4),(1,{},2,4),(1,{'orientation':True},2,4),(1,{'orientation':'panel_reflections'},1,4),(1,{'orientation':'panel_reflections'},7,4),(1,{'orientation':'panel_reflections'},2,0),(1,{'orientation':'panel_reflections'},2,5)])
def test_invalid_requests(seed,settings,demos,queries):
    with pytest.raises(ValueError):module('adapter').generate(seed,settings,demos,queries)

def test_default_program_is_exact_reference():
    a=module('adapter')
    assert a.program({'orientation':'panel_reflections'}).encode()==(HOME/'reference.rkt').read_bytes()==(BASE/'canonical.rkt').read_bytes()

def test_public_turn_is_whitelisted():
    a=module('adapter');e=a.generate(17,{'orientation':'preserve_orientation'},2,4);want=a.public_view(e,0)
    e['train'][0]['hidden']='secret';e['settings']={'private':1};e['test'][0]['output']=[[9]];e['test'][1]['input']=[[9]]
    assert a.public_view(e,0)==want and set(want['test'][0])=={'input'}

def test_minimum_lessons_reject_declared_query_changing_rivals():
    a=module('adapter')
    for seed in range(16):
        for mode in a.MODES:
            ep=a.generate(seed,{'orientation':mode},2,4)
            assert not a.teaching_audit(ep,mode)['query_disagreeing_survivors']


def test_audit_rejects_stale_source(tmp_path):
    audit=module('audit'); file=tmp_path/'x.py';file.write_text('ok')
    pre={'status':'passed','owner_accepted':False,'source_binding':{'files':[{'path':'x.py','sha256':audit.sha(file.read_bytes())}]}}
    audit.check_binding(pre,root=tmp_path)
    file.write_text('changed')
    with pytest.raises(ValueError,match='stale'):audit.check_binding(pre,root=tmp_path)


def test_audit_refuses_source_path_escape(tmp_path):
    audit=module('audit')
    pre={'status':'passed','owner_accepted':False,'source_binding':{'files':[{'path':'../outside.py','sha256':'0'*64}]}}
    with pytest.raises(ValueError):audit.check_binding(pre,root=tmp_path)


def test_audit_requires_protected_runtime_identity():
    audit=module('audit')
    with pytest.raises(ValueError):audit.make_witness({'source_binding':{}},{'backend':'python'}, {},{})


def test_audit_serializes_native_witness_identity():
    audit=module('audit'); description={k:k for k in ('step_a','intermediate','step_b','why_b_depends_on_a')}
    witness=audit.make_witness({'source_binding':{}},{'backend':'racket','protected':True,'binary_sha256':'bound'},description,{'case':'test only'})
    assert witness['racket']=={'backend':'racket','protected':True}
    assert witness['racket_identity']['binary_sha256']=='bound' and witness['owner_accepted'] is False


def test_racket_programs_parse_as_one_rule():
    from puzzle_generators.rule_wrap import wrap_rule
    for filename in ('canonical.rkt','preserve_orientation.rkt','wrong_intermediate.rkt'):
        assert wrap_rule((BASE/filename).read_text())


def test_fixed_corner_regression_seed_14_has_contrasting_source_panels():
    a=module('adapter');ep=a.generate(14,{'orientation':'panel_reflections'},2,4)
    assert len({tuple(a.P.analyse(p['input'])['source']['panel']) for p in ep['train']})==2


def test_native_scale_is_input_dependent_in_minimum_prefix():
    a=module('adapter');ep=a.generate(14,{'orientation':'panel_reflections'},2,4)
    assert len({a.P.analyse(p['input'])['source']['size'] for p in ep['train']})==2


def test_retained_corner_counterexample_is_source_hash_pinned(tmp_path):
    audit=module('audit');reg=audit.load_regression();p=module('prototype')
    assert len(reg['train'])==2 and len(reg['test'])==1
    for pair in reg['train']+reg['test']:
        assert p.solve(pair['input'])==pair['output']
    assert all(p.policy_outputs(pair['input'])['panel_reflections:source_topleft']==pair['output'] for pair in reg['train'])
    assert p.policy_outputs(reg['test'][0]['input'])['panel_reflections:source_topleft']!=reg['test'][0]['output']
    changed=tmp_path/'changed.json';changed.write_text('{}')
    with pytest.raises(ValueError,match='regression'):audit.load_regression(changed)
