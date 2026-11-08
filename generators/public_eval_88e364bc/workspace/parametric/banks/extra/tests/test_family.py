from pathlib import Path
import importlib.util
import json
import sys
import pytest
HOME=Path(__file__).resolve().parents[1]
BASE=HOME/'workspace/parametric'

def load(name):
    p=BASE/(name+'.py')
    assert p.is_file(),f'Missing implemented module: {p.name}'
    spec=importlib.util.spec_from_file_location('_88e_test_'+name,p)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize('index',range(5))
def test_original_label(index):
    p=json.loads((HOME/'tests/originals.json').read_text())[index]
    assert load('model').solve(p['input'])==p['output']

def hand_scene():
    g=[[0]*13 for _ in range(9)]
    for r in range(4):
        for c in range(5):g[r][c]=5
    for r in (1,2):g[r][1:4]=[1,1,2]
    for r in range(4,9):
        for c in range(6,13):
            if r in (4,8) or c in (6,12):g[r][c]=5
    g[6][7]=4
    return g

def test_literal_wall_distance_and_halfway():
    import copy
    model=load('model');g=hand_scene()
    expected=copy.deepcopy(g);expected[6][7]=0;expected[6][11]=4
    assert model.solve(g)==expected
    expected[6][11]=0;expected[6][9]=4
    assert model.solve(g,'halfway')==expected
    record=model.analyze(g)['particles'][0]
    assert record['direction']==(0,1) and record['distance']==4


def test_invalid_grids_and_modes():
    model=load('model')
    for g in ([],[[1],[2,3]],[[False]],[[11]]):
        with pytest.raises(ValueError):model.solve(g)
    with pytest.raises(ValueError):model.solve(hand_scene(),'unknown')


def test_diagonal_step_must_not_cut_a_wall_corner():
    model=load('model')
    g=[[0,5,0],[0,0,0],[0,0,0]]
    assert model.free_run(g,(0,0),(1,1))==0
    assert model.free_run([[0]*3 for _ in range(3)],(0,0),(1,1))==2


@pytest.mark.parametrize('seed', [0, 4, 17])
def test_counts_prefixes_and_matched_inputs(seed):
    adapter=load('adapter')
    a=adapter.generate(seed, {'motion_extent':'to_wall'}, 6, 4)
    b=adapter.generate(seed, {'motion_extent':'halfway'}, 6, 4)
    assert a['program_solution'] == (HOME/'reference.rkt').read_text()
    assert (BASE/'canonical.rkt').read_bytes() == (HOME/'reference.rkt').read_bytes()
    for split in ('train','test'):
        assert [p['input'] for p in a[split]] == [p['input'] for p in b[split]]
    keys=[json.dumps(p['input']) for sp in ('train','test') for p in a[sp]]
    assert len(keys)==len(set(keys))==10
    for n in range(2,7):
        for q in range(1,5):
            small=adapter.generate(seed, {'motion_extent':'to_wall'}, n, q)
            assert small['train']==a['train'][:n]
            assert small['test']==a['test'][:q]
            assert len(small['private']['query_bank'])==4
    assert all(a['train'][i]['output'] != b['train'][i]['output'] for i in range(2))
    stress=a['test'][3]['input']
    assert len(stress)==len(stress[0])==30
    assert sum(v!=0 for row in stress for v in row)>=200


def test_strict_request_validation():
    adapter=load('adapter')
    for settings in ({}, {'motion_extent':'bogus'}, {'motion_extent':'to_wall','extra':1}):
        with pytest.raises(ValueError): adapter.generate(0,settings,2,4)
    for n,q in ((True,4),(1,4),(7,4),(2,0),(2,5),(2,True)):
        with pytest.raises(ValueError): adapter.generate(0,{'motion_extent':'to_wall'},n,q)


def test_public_projection_drops_every_private_field():
    import copy
    adapter=load('adapter')
    ep=adapter.generate(17,{'motion_extent':'halfway'},3,4)
    before=adapter.public_view(ep,0,11)
    changed=copy.deepcopy(ep)
    changed['settings']={'hidden':'secret'};changed['seed']=777;changed['program_solution']='private'
    for pair in changed['train']: pair['metadata']={'secret':42}
    for pair in changed['test']: pair['output']=[[9]];pair['metadata']={'secret':42}
    for pair in changed['private']['query_bank']: pair['output']=[[9]]
    assert adapter.public_view(changed,0,11)==before
    assert set(before)=={'train','test'} and len(before['test'])==1
    assert all(set(p)=={'input','output'} for p in before['train'])
    assert set(before['test'][0])=={'input'}
    assert before==adapter.public_view(adapter.generate(17,{'motion_extent':'halfway'},3,1),0,11)
    firsts={json.dumps(adapter.public_view(ep,0,s)['test']) for s in range(20)}
    assert len(firsts)==4


def test_future_inputs_do_not_change_first_turn():
    import copy,random
    adapter=load('adapter');ep=adapter.generate(21,{'motion_extent':'to_wall'},2,4)
    order=list(range(4));random.Random(7).shuffle(order)
    mutated=copy.deepcopy(ep)
    for i in order[1:]: mutated['private']['query_bank'][i]['input']=[[9]]
    assert adapter.public_view(ep,0,7)==adapter.public_view(mutated,0,7)




def test_one_step_rival_has_literal_wrong_answer():
    import copy
    g=hand_scene();expected=copy.deepcopy(g);expected[6][7]=0;expected[6][8]=4
    assert load('audit').rivals(g,'to_wall')['one_step']==expected
    assert expected!=load('model').solve(g)


def test_source_binding_rejects_drift(tmp_path):
    import hashlib
    audit=load('audit');p=tmp_path/'implementation.py';p.write_text('x = 1\n')
    binding={'files':[{'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}
    audit.assert_binding(tmp_path,binding);p.write_text('x = 2\n')
    with pytest.raises(ValueError,match='Source drift'):audit.assert_binding(tmp_path,binding)


@pytest.mark.parametrize('mode',['to_wall','halfway'])
def test_minimum_lesson_teaches_corner_collision(mode):
    adapter=load('adapter');audit=load('audit')
    for seed in (0,17,43):
        ep=adapter.generate(seed,{'motion_extent':mode},2,4)
        assert any(audit.rivals(p['input'],mode)['corner_cutting']!=p['output'] for p in ep['train'])


def test_witness_serializer_matches_return_contract():
    import hashlib
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    audit=load('audit')
    assert callable(getattr(audit, 'make_witness', None)), 'Missing contract-safe witness serializer'
    # Hand-built serialization fixture only: this test makes no execution claim.
    binding={'task_id':audit.adapter.TASK,'files':[]}
    settings={audit.PARAMETER:audit.MODES[-1]}
    program='(lambda (g) g)'
    case={'input':[[0]],'settings':settings,'intermediate_value':[0],
          'program':program,'output':[[0]],'counterfactual_program':'(lambda (g) (list (list 1)))',
          'counterfactual_output':[[1]],'ablation':'wrong_intermediate'}
    identity={'backend':'racket','protected':True,'schema':'fixture-not-execution',
              'binary_sha256':'0'*64}
    witness=audit.make_witness(binding,identity,case)
    assert witness['runtime_identity']==identity
    key=json.dumps(settings,sort_keys=True,separators=(',',':'))
    receipt={'source_binding':binding,'programs':{key:hashlib.sha256(program.encode()).hexdigest()}}
    progress={'sequential_dependency':dict(audit.DEPENDENCY,witness_path='witness.json')}
    result=validate_sequential_witness(progress,receipt,lambda name:json.dumps(witness).encode())
    assert result['status']=='source_bound_reviewer_reported' and result['cases']==1
    for invalid in ({'backend':'python','protected':True},{'backend':'racket','protected':False}):
        with pytest.raises(ValueError,match='protected Racket'):
            audit.make_witness(binding,invalid,case)
