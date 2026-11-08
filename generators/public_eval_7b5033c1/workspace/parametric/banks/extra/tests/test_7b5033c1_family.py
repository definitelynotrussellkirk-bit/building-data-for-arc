"""Path linearization and length-addressed sequence composition."""
from pathlib import Path
import importlib.util
import json
import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]
BASE=HOME/'workspace/parametric'

def load(filename='family.py'):
    path=BASE/filename
    assert path.is_file(),f'Missing implemented {filename}'
    spec=importlib.util.spec_from_file_location('_7b5033c1_'+path.stem,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def original_pairs():
    raw=ROOT/'shared/data/raw'
    parent=json.loads((raw/'arc-agi_evaluation_challenges.json').read_text())['7b5033c1']
    gold=json.loads((raw/'arc-agi_evaluation_solutions.json').read_text())['7b5033c1']
    return parent['train']+[{'input':p['input'],'output':g}for p,g in zip(parent['test'],gold)]

@pytest.mark.parametrize('index',[0,1,2])
def test_original_python_labels(index):
    p=original_pairs()[index]
    assert load().solve(p['input'])==p['output']


def test_original_protected_racket_labels():
    path=HOME/'reference.rkt'
    assert path.exists(),'Missing general Racket rule'
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,_,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        for p in original_pairs():assert apply(path.read_text(),p['input'])==p['output']
    finally:bridge.close()


def test_bent_repeated_color_path_is_not_a_histogram_or_row_major_scan():
    g=[[0]*7 for _ in range(5)]
    route=[(0,1),(1,1),(2,1),(2,2),(2,3),(1,3),(0,3)]
    for p,v in zip(route,[1,1,2,2,3,1,1]):g[p[0]][p[1]]=v
    assert load().solve(g)==[[1],[1],[2],[2],[3],[1],[1]]


def test_header_two_selects_second_following_run_not_every_matching_color():
    # Sequence runs: 1x2, 2x2, 3x2 (selected), 2x1, 3x2.
    g=[[0]*11 for _ in range(3)]
    g[1][1:10]=[1,1,2,2,3,3,2,3,3]
    assert load().solve(g,'length_addressed_run')==[[1],[1],[2],[2],[9],[9],[2],[3],[3]]

@pytest.mark.parametrize('bad',[
    [],[[]],[[True]],[[1.0]],[[10]],[[0],[0,0]],
    [[0]*5 for _ in range(5)],
    [[0,1,0],[1,1,1],[0,0,0]],
    [[1,1,0],[1,1,0],[0,0,0]],
    [[1,0,0,1],[0,0,0,0],[0,0,0,0]],
])
def test_rejects_malformed_nonpath_or_ambiguous_input(bad):
    with pytest.raises(ValueError):load().solve(bad)

@pytest.mark.parametrize('seed',[0,1,17,43,104,156,2**63-1])
def test_constructed_oracle_counts_settings_and_prefixes(seed):
    a=load('adapter.py');family=load()
    e=a.generate(seed,{'finish':'unroll'},6,4)
    other=a.generate(seed,{'finish':'length_addressed_run'},6,4)
    assert e['program_solution']==(HOME/'reference.rkt').read_text()
    inputs=[p['input'] for split in ('train','test') for p in e[split]]
    assert len({json.dumps(g)for g in inputs})==10
    assert len(inputs[6])==len(inputs[6][0])==30
    assert len(e['test'][0]['output'])==30
    headers=[]
    for i in range(6):headers.append(family.stages(e['train'][i]['input'])['address'])
    assert len(set(headers[:2]))==2,'A fixed header must not fit the two demos'
    for split in ('train','test'):
        for p,q in zip(e[split],other[split]):
            assert p['input']==q['input'] and p['output']!=q['output']
            assert family.self_check(p['input'])==[]
    for demos in range(2,7):
        for queries in range(1,5):
            short=a.generate(seed,{'finish':'unroll'},demos,queries)
            assert short['train']==e['train'][:demos]
            assert short['test']==e['test'][:queries]
    for index in (0,1,1000):
        grid,blueprint=family.construct(seed,index,stress=index==1000)
        assert family.solve(grid)==[[v]for v in blueprint['sequence']]
        k=blueprint['run_lengths'][0]
        expected=[[9 if n==k else color]for n,(color,length)in enumerate(zip(blueprint['run_colors'],blueprint['run_lengths']))for _ in range(length)]
        assert family.solve(grid,'length_addressed_run')==expected

@pytest.mark.parametrize('args',[
    (-1,{'finish':'unroll'},2,4),(True,{'finish':'unroll'},2,4),
    (0,{},2,4),(0,{'finish':'unknown'},2,4),(0,{'finish':'unroll','secret':1},2,4),
    (0,{'finish':'unroll'},1,4),(0,{'finish':'unroll'},7,4),
    (0,{'finish':'unroll'},2,0),(0,{'finish':'unroll'},2,5),
    (0,{'finish':'unroll'},2.0,4),(0,{'finish':'unroll'},2,True),
])
def test_native_api_rejects_invalid_requests(args):
    with pytest.raises(ValueError):load('adapter.py').generate(*args)


def test_native_resources_work_without_parent_files(tmp_path):
    import shutil
    dest=tmp_path/'native'
    shutil.copytree(BASE,dest,ignore=shutil.ignore_patterns('__pycache__','evidence'))
    spec=importlib.util.spec_from_file_location('standalone_path_adapter',dest/'adapter.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.generate(17,{'finish':'unroll'},2,4)['program_solution']==(HOME/'reference.rkt').read_text()


def test_declared_rivals_are_rejected_by_demos_with_protected_racket():
    a=load('adapter.py')
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,_,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        for finish in a.SETTINGS:
            setting={'finish':finish};e=a.generate(17,setting,2,4)
            for name,program in a.rival_programs(setting).items():
                labels=[apply(program,p['input']) for p in e['train']]
                assert any(x!=p['output']for x,p in zip(labels,e['train'])),name
            for pair in e['test']:
                assert apply(e['program_solution'],pair['input'])==pair['output']
    finally:bridge.close()


def test_owner_rule_id_is_literal():
    from arcpuzzles.review_public_creation import validate_reference_id
    assert (HOME/'generator.py').is_file()
    assert validate_reference_id(HOME/'generator.py','7b5033c1')=='ee_7b5033c1'


def test_seed_5_demonstrations_reject_total_leading_color_count():
    a=load('adapter.py');episode=a.generate(5,{'finish':'length_addressed_run'},2,4)
    def wrong(grid):
        state=a.family.stages(grid);seq=state['sequence'];address=seq.count(seq[0])
        return [[9 if i==address else c]for i,run in enumerate(state['runs'])for c in run]
    assert any(wrong(p['input'])!=p['output']for p in episode['train']), 'Total leading-color count fits both demos'


def test_total_header_color_counterfactual_is_distinct_from_consecutive_length():
    grid=[[0]*14 for _ in range(3)]
    grid[1][1:13]=[1,1,2,2,3,3,1,1,4,4,3,3]
    assert load().solve(grid,'length_addressed_run',selector='all_header_color')==[[1],[1],[2],[2],[3],[3],[1],[1],[9],[9],[3],[3]]


def test_public_first_turn_shuffles_complete_bank_and_strips_private_metadata(tmp_path):
    import copy
    a=load('adapter.py');pub=load('public_views.py')
    e=a.generate(17,{'finish':'unroll'},2,4)
    one,order=pub.project(e,29,1);four,all_order=pub.project(e,29,4)
    assert one==four[:1] and order==all_order[:1]
    changed=copy.deepcopy(e);changed['seed']='PRIVATE';changed['program_solution']='PRIVATE'
    for p in changed['train']:p['metadata']='PRIVATE'
    for p in changed['test']:p['output']=[[9]];p['metadata']='PRIVATE'
    assert pub.project(changed,29,4)==(four,all_order)
    assert len({pub.project(e,s,1)[1][0]for s in range(16)})>1
    assert 'PRIVATE' not in json.dumps(pub.project(changed,29,4))
    assert all(set(v)=={'train','test'} and set(v['test'][0])=={'input'}for v in four)

@pytest.mark.parametrize('bad',[True,1.0,'1',-1,10])
def test_bad_public_cells_fail_before_writing(tmp_path,bad):
    e=load('adapter.py').generate(17,{'finish':'unroll'},2,4);e['train'][0]['output'][0][0]=bad
    with pytest.raises(ValueError,match='grid'):load('public_views.py').export(e,tmp_path/'invalid',0)
    assert not (tmp_path/'invalid').exists()


def test_entire_public_batch_is_sorted_and_duplicate_batch_never_writes(tmp_path,monkeypatch):
    a=load('adapter.py');pub=load('public_views.py')
    e=a.generate(17,{'finish':'unroll'},2,4);f=a.generate(43,{'finish':'length_addressed_run'},2,4)
    events=[];real_write=Path.write_bytes
    def recording(path,data):
        events.append(path.name);return real_write(path,data)
    monkeypatch.setattr(Path,'write_bytes',recording)
    receipt=pub.export_batch([(e,3),(f,7)],tmp_path/'public')
    assert events==sorted(events) and len(events)==8
    assert pub.verify(tmp_path/'public',receipt['physical_creation_order'])['files']==8
    with pytest.raises(ValueError,match='Duplicate'):pub.export_batch([(e,3),(e,7)],tmp_path/'duplicate')
    assert not (tmp_path/'duplicate').exists()


def test_public_verifier_rejects_tampered_bytes_and_missing_file(tmp_path):
    pub=load('public_views.py');e=load('adapter.py').generate(17,{'finish':'unroll'},2,4)
    receipt=pub.export(e,tmp_path/'public',0)
    ids=receipt['physical_creation_order'];path=tmp_path/'public'/f'{ids[0]}.json'
    raw=path.read_bytes();path.write_bytes(raw+b' ')
    with pytest.raises(ValueError):pub.verify(tmp_path/'public',ids)
    path.unlink()
    with pytest.raises(ValueError):pub.verify(tmp_path/'public',ids)


def test_truncated_query_bank_cannot_change_first_turn_sampling():
    e=load('adapter.py').generate(17,{'finish':'unroll'},2,1)
    with pytest.raises(ValueError,match='four-query'):load('public_views.py').project(e,0,1)


def test_structural_auditor_checks_minimum_demo_curriculum():
    auditor=load('audit.py');report=auditor.structural([5,17])
    assert report['episodes']==4 and report['pairs']==40
    assert report['public_turns']==16 and report['harmful_survivors']==0
    assert report['teaching_checks']>0


def test_public_files_match_the_packet_serialization_contract(tmp_path):
    from reviewer_support import public_challenge_bytes, public_challenge_id
    pub=load('public_views.py');episode=load('adapter.py').generate(17,{'finish':'unroll'},2,4)
    pub.export(episode,tmp_path/'public',17)
    for path in (tmp_path/'public').glob('*.json'):
        value=json.loads(path.read_bytes())
        assert path.read_bytes()==public_challenge_bytes(value)
        assert path.stem==public_challenge_id(value)
