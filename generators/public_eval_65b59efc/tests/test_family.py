from pathlib import Path
import importlib.util
import json
import pytest

HOME=Path(__file__).resolve().parents[1]
BASE=HOME/'workspace/parametric'

def module(name):
    path=BASE/(name+'.py')
    assert path.is_file(), f"missing implementation: {path.name}"
    spec=importlib.util.spec_from_file_location('_table_'+name, path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

G=[[1,0,5,0,2,5],[1,1,5,2,2,5],[5,0,5,5,0,5],
   [2,0,5,0,1,5],[0,1,5,2,0,5],[5,0,5,5,0,5],[0,6,5,8,0,5]]

@pytest.mark.parametrize('mode,want',[
 ('as_drawn',[[0,8,6,0],[8,8,6,6],[0,8,6,0],[8,8,6,6]]),
 ('clockwise',[[8,0,6,6],[8,8,6,0],[8,0,6,6],[8,8,6,0]])])
def test_literal_color_lookup_overlay_and_tile_rotation(mode,want):
    assert module('prototype').solve(G,mode)==want

@pytest.mark.parametrize('split,index',[('train',0),('train',1),('train',2),('test',0),('test',1)])
def test_original_pairs(split,index):
    p=json.loads((HOME/'tests/fixtures/original.json').read_text())[split][index]
    assert module('prototype').solve(p['input'],'as_drawn')==p['output']

def test_overlay_conflict_is_rejected():
    bad=[r[:] for r in G];bad[3][3]=1
    with pytest.raises(ValueError,match='conflict'):module('prototype').analyse(bad)

def test_repeated_legend_swatch_is_one_mapping():
    g=[r[:] for r in G];g[-1][0]=6;g[-1][4]=8
    assert module('prototype').solve(g)==module('prototype').solve(G)

@pytest.mark.parametrize('bad',[[],[[True]],[[0],[0,0]],[[10]]])
def test_invalid_grid(bad):
    with pytest.raises(ValueError):module('prototype').analyse(bad)

def test_counts_matched_inputs_and_prefixes():
    a=module('adapter')
    for seed in [0,4,17,43]:
        full=a.generate(seed,{'tile_orientation':'as_drawn'},6,4)
        assert len({json.dumps(p['input']) for s in ('train','test') for p in full[s]})==10
        assert len(full['test'][3]['input'])==len(full['test'][3]['input'][0])==30
        for n in range(2,7):
            for q in range(1,5):
                e=a.generate(seed,{'tile_orientation':'as_drawn'},n,q)
                assert e['train']==full['train'][:n] and e['test']==full['test'][:q]
        alt=a.generate(seed,{'tile_orientation':'clockwise'},6,4)
        assert [p['input'] for s in ('train','test') for p in alt[s]]==[p['input'] for s in ('train','test') for p in full[s]]

@pytest.mark.parametrize('seed,settings,demos,queries',[(True,{'tile_orientation':'as_drawn'},2,4),(1,{},2,4),(1,{'tile_orientation':True},2,4),(1,{'tile_orientation':'as_drawn'},1,4),(1,{'tile_orientation':'as_drawn'},7,4),(1,{'tile_orientation':'as_drawn'},2,0),(1,{'tile_orientation':'as_drawn'},2,5)])
def test_invalid_requests(seed,settings,demos,queries):
    with pytest.raises(ValueError):module('adapter').generate(seed,settings,demos,queries)

def test_default_program_is_exact_reference():
    a=module('adapter')
    assert a.program({'tile_orientation':'as_drawn'}).encode()==(HOME/'reference.rkt').read_bytes()==(BASE/'canonical.rkt').read_bytes()

def test_public_turn_is_whitelisted():
    a=module('adapter'); e=a.generate(17,{'tile_orientation':'clockwise'},2,4)
    want=a.public_view(e,0)
    e['train'][0]['hidden']='secret';e['settings']={'private':1};e['test'][0]['output']=[[9]];e['test'][1]['input']=[[9]]
    assert a.public_view(e,0)==want
    assert set(want)=={'train','test'} and set(want['test'][0])=={'input'}

def test_minimum_lessons_reject_declared_query_changing_rivals():
    a=module('adapter')
    for seed in range(16):
        for mode in a.MODES:
            e=a.generate(seed,{'tile_orientation':mode},2,4)
            assert not a.teaching_audit(e,mode)['query_disagreeing_survivors']


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
