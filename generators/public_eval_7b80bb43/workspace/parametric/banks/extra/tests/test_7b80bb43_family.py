"""General diagonal-spur/line-restoration rule tested against every supplied label."""
import importlib.util
import json
from pathlib import Path
import pytest
HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]

def load():
    p=HOME/'generator.py';assert p.is_file(),'Missing general line restoration generator'
    s=importlib.util.spec_from_file_location('line_family_test',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def originals():
    raw=ROOT/'shared/data/raw'
    d=json.loads((raw/'arc-agi_evaluation_challenges.json').read_text())['7b80bb43']
    s=json.loads((raw/'arc-agi_evaluation_solutions.json').read_text())['7b80bb43']
    return d['train']+[dict(input=p['input'],output=o) for p,o in zip(d['test'],s)]

@pytest.mark.parametrize('index',range(3))
def test_original_python_labels(index):
    p=originals()[index];assert load().solve(p['input'])==p['output']

def test_original_protected_racket_labels():
    path=HOME/'reference.rkt';assert path.is_file(),'Missing general Racket reference'
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,_,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        for p in originals():assert apply(path.read_text(),p['input'])==p['output']
    finally:bridge.close()

def test_diagonal_noise_attached_to_middle_of_straight_stroke_is_fully_erased():
    grid=[[0]*9 for _ in range(8)]
    grid[2]=[3]*9;grid[3][3]=grid[4][4]=3
    expected=[[0]*9 for _ in range(8)];expected[2]=[3]*9
    assert load().solve(grid)==expected

def adapter():
    p=HOME/'workspace/parametric/adapter.py';assert p.exists(),'Missing native adapter'
    s=importlib.util.spec_from_file_location('line_adapter_test',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

@pytest.mark.parametrize('seed',[0,1,17,43,104,156])
def test_sampler_canonical_labels_counts_prefix_and_new_junctions(seed):
    a=adapter();e=a.generate(seed,{'finish':'straighten'},6,4)
    other=a.generate(seed,{'finish':'mark_new_junctions'},6,4)
    assert e['program_solution']==(HOME/'reference.rkt').read_text()
    inputs=[p['input'] for sp in ('train','test') for p in e[sp]]
    assert len({json.dumps(g) for g in inputs})==10
    assert any(len(g)==len(g[0])==30 for g in inputs)
    for sp in ('train','test'):
        for p,q in zip(e[sp],other[sp]):
            assert p['input']==q['input'] and p['output']!=q['output']
            assert p['output']==a.family.solve(p['input'])
            assert q['output']!=a.family.solve(q['input'],'mark_new_junctions',junction_mode='before')
    for demos in range(2,7):
        for queries in range(1,5):
            part=a.generate(seed,{'finish':'straighten'},demos,queries)
            assert part['train']==e['train'][:demos] and part['test']==e['test'][:queries]

@pytest.mark.parametrize('args',[(-1,{'finish':'straighten'},2,4),(True,{'finish':'straighten'},2,4),
 (0,{},2,4),(0,{'finish':'bad'},2,4),(0,{'finish':'straighten','extra':1},2,4),
 (0,{'finish':'straighten'},1,4),(0,{'finish':'straighten'},7,4),(0,{'finish':'straighten'},2,0),
 (0,{'finish':'straighten'},2,5),(0,{'finish':'straighten'},2.0,4),(0,{'finish':'straighten'},True,4)])
def test_invalid_api_rejected(args):
    with pytest.raises((ValueError,TypeError)):adapter().generate(*args)

def publisher():
    path=HOME/'workspace/parametric/public_views.py'
    assert path.exists(), 'Sequential public publisher is missing'
    spec=importlib.util.spec_from_file_location('line_public_under_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_public_first_turn_is_prefix_stable_and_private_invariant(tmp_path):
    import copy
    a=adapter();pub=publisher();e=a.generate(17,{'finish':'straighten'},2,4)
    one,order=pub.project(e,19,1);four,other=pub.project(e,19,4)
    assert one==four[:1] and order==other[:1]
    changed=copy.deepcopy(e);changed['settings']={'secret':'changed'};changed['program_solution']='secret'
    for p in changed['test']:p['output']=[[9]]
    assert pub.project(changed,19,4)==(four,other)
    for v in four:
        assert set(v)=={'train','test'} and len(v['test'])==1
        assert set(v['test'][0])=={'input'}
    firsts={pub.project(e,s,1)[1][0] for s in range(16)}
    assert len(firsts)>1
    receipt=pub.export(e,tmp_path/'public',19)
    assert len(receipt['mapping'])==4
    for row in receipt['mapping']:
        raw=(tmp_path/'public'/f"{row['id']}.json").read_bytes()
        import hashlib
        assert hashlib.sha256(raw).hexdigest()==row['id']
    assert receipt['physical_creation_order']==sorted(receipt['physical_creation_order'])

def test_publisher_rejects_duplicate_or_truncated_bank_before_writing(tmp_path):
    import copy
    e=adapter().generate(43,{'finish':'straighten'},2,4);pub=publisher()
    e['test'][1]=copy.deepcopy(e['test'][0])
    with pytest.raises(ValueError):pub.export(e,tmp_path/'duplicates',0)
    assert not (tmp_path/'duplicates').exists()
    e['test']=e['test'][:1]
    with pytest.raises(ValueError):pub.project(e,0,1)

def test_declared_rivals_execute_and_two_demos_reject_them():
    a=adapter()
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,_,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        for finish in a.SETTINGS:
            setting={'finish':finish};e=a.generate(17,setting,2,4)
            for name,program in a.rival_programs(setting).items():
                labels=[apply(program,p['input']) for p in e['train']]
                assert any(g!=p['output'] for g,p in zip(labels,e['train'])), name
    finally:bridge.close()

def test_reusable_structural_auditor_checks_real_episodes():
    path=HOME/'workspace/parametric/audit.py'
    assert path.is_file(), 'Reusable structural auditor is missing'
    spec=importlib.util.spec_from_file_location('line_auditor_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    result=m.structural([17])
    assert result['episodes']==2 and result['pairs']==20
    assert result['public_turns']==8 and result['failures']==[]

def test_native_folder_can_generate_without_task_parent_files(tmp_path):
    """Catches reads of HOME/reference.rkt and HOME/generator.py by native adapter."""
    import shutil
    source=HOME/'workspace/parametric';dest=tmp_path/'standalone'
    shutil.copytree(source,dest,ignore=shutil.ignore_patterns('__pycache__','evidence'))
    spec=importlib.util.spec_from_file_location('standalone_line_adapter',dest/'adapter.py')
    m=importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
        e=m.generate(17,{'finish':'straighten'},2,4)
    except (FileNotFoundError,ImportError) as exc:
        pytest.fail(f'Native folder is not self-contained: {exc}')
    assert e['program_solution']==(HOME/'reference.rkt').read_text()
    assert len(e['train'])==2 and len(e['test'])==4


def test_owner_can_resolve_literal_rule_id():
    from arcpuzzles.review_public_creation import validate_reference_id
    try:
        validate_reference_id(HOME/'generator.py','7b80bb43')
    except ValueError as exc:
        pytest.fail(str(exc))

@pytest.mark.parametrize('bad', [True,1.0,'1',-1,10])
def test_export_rejects_non_arc_cells_before_creating_destination(tmp_path,bad):
    e=adapter().generate(17,{'finish':'straighten'},2,4)
    e['train'][0]['output'][0][0]=bad
    with pytest.raises(ValueError,match='grid'):
        publisher().export(e,tmp_path/'invalid',1)
    assert not (tmp_path/'invalid').exists()


def test_public_projection_strips_demo_and_query_metadata():
    e=adapter().generate(17,{'finish':'straighten'},2,4)
    e['train'][0]['secret']='DO NOT EXPORT';e['test'][0]['future']='DO NOT EXPORT'
    views,_=publisher().project(e,0)
    assert 'DO NOT EXPORT' not in json.dumps(views)


def test_public_files_match_the_packet_serialization_contract(tmp_path):
    from reviewer_support import public_challenge_bytes, public_challenge_id
    pub=publisher();episode=adapter().generate(17,{'finish':'straighten'},2,4)
    pub.export(episode,tmp_path/'public',17)
    for path in (tmp_path/'public').glob('*.json'):
        value=json.loads(path.read_bytes())
        assert path.read_bytes()==public_challenge_bytes(value)
        assert path.stem==public_challenge_id(value)
