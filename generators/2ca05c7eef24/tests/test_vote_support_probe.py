"""Authoring-tool tests. Synthetic receipt fixtures test parsing, not Racket authority."""
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys

import pytest

TOOL = Path(__file__).resolve().parents[1] / 'workspace/probe_vote_support.py'

def load_tool():
    assert TOOL.is_file(), 'authoring vote-support tool has not been implemented'
    spec=importlib.util.spec_from_file_location('vote_support_probe',TOOL)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.fixture(scope='session')
def tool():
    if not TOOL.is_file(): pytest.skip('prepare behavior test reports missing authoring artifact')
    return load_tool()

@pytest.fixture
def prepared(tool,tmp_path):
    path=tmp_path/'votes.json'
    meta=tool.prepare(path)
    return path,meta

def test_prepare_exhausts_ordered_alphabet_with_lawful_geometry(tmp_path):
    tool=load_tool()
    path=tmp_path/'votes.json'
    meta=tool.prepare(path)
    request=json.loads(path.read_text())
    assert set(request)=={'inputs'}
    assert len(request['inputs'])==18
    assert len(meta['mapping'])==729
    assert [tuple(item['votes']) for item in meta['mapping']]==list(itertools.product((0,1,2,3,4,6,7,8,9),repeat=3))
    for grid in request['inputs']:
        assert len(grid)==7 and all(len(row)==20 for row in grid)
        assert all(row[6]==5 and row[13]==5 for row in grid)
    for item in meta['mapping']:
        grid=request['inputs'][item['grid_index']]
        assert [grid[item['row']][i*7+item['col']] for i in range(3)]==item['votes']
    assert meta['canonical']['rule_hash']=='92b2f8e4de94'
    assert meta['request_sha256']==tool.file_sha256(path)
    assert path.with_suffix('.meta.json').is_file()

@pytest.mark.parametrize('votes,expected',[( (0,0,0),0),((0,0,9),0),((2,2,9),2),((9,2,2),2),((0,2,7),7),((1,4,9),9),((6,6,6),6)])
def test_independent_vote_count_and_tie_expectation(tool,votes,expected):
    assert tool.expected_vote(votes)==expected

@pytest.mark.parametrize('votes,expected',[((0,0,0),'empty'),((0,3,0),'singleton'),((2,0,2),'pair_same'),((2,0,7),'pair_distinct'),((3,3,3),'triple_same'),((2,9,2),'triple_majority'),((1,2,9),'triple_distinct')])
def test_vote_equality_classes(tool,votes,expected):
    assert tool.vote_class(votes)==expected

def synthetic_parsing_receipt(tool,path,meta):
    """Never authority evidence: an in-memory fixture for rejection-path tests only."""
    inputs=json.loads(path.read_text())['inputs']
    results=[]
    for i,g in enumerate(inputs):
        output=[[tool.expected_vote([g[r][p*7+c] for p in range(3)]) for c in range(6)] for r in range(7)]
        results.append({'index':i,'input':g,'input_sha256':tool.grid_sha256(g),'output':output,'output_sha256':tool.grid_sha256(output),'valid_output':True,'error':None})
    return {'schema':'arcpuzzles-apply-v1','task_id':tool.TASK_ID,'rule_task_id':tool.TASK_ID,'reference':'canonical','rule_file':'data/canonical/puzzles.jsonl','executed_rule_hash':meta['canonical']['rule_hash'],'catalog_rule_hash':meta['canonical']['rule_hash'],'rule_hash_matches_catalog':True,'rule_text_sha256':tool.CALLABLE_RULE_SHA256,'generator_sha256':meta['generator_sha256'],'results':results,'fixture_notice':'SYNTHETIC PARSING TEST ONLY; NOT RACKET EVIDENCE'}

@pytest.mark.parametrize('fault',['missing_result','reverse_order','wrong_index','wrong_input','wrong_input_type','input_digest','output_digest','error','dimensions','wrong_rule','wrong_task','stale_generator','wrong_vote'])
def test_synthetic_parsing_receipt_corruption_is_rejected(tool,prepared,tmp_path,fault):
    path,meta=prepared
    receipt=synthetic_parsing_receipt(tool,path,meta)
    if fault=='missing_result': receipt['results'].pop()
    elif fault=='reverse_order': receipt['results'].reverse()
    elif fault=='wrong_index': receipt['results'][0]['index']=4
    elif fault=='wrong_input': receipt['results'][0]['input'][0][0]=9
    elif fault=='wrong_input_type': receipt['results'][0]['input'][0][0]=False
    elif fault=='input_digest': receipt['results'][0]['input_sha256']='0'*64
    elif fault=='output_digest': receipt['results'][0]['output_sha256']='0'*64
    elif fault=='error': receipt['results'][0].update(valid_output=False,error='synthetic parsing fault')
    elif fault=='dimensions': receipt['results'][0]['output']=[[0]]
    elif fault=='wrong_rule': receipt['executed_rule_hash']='000000000000'
    elif fault=='wrong_task': receipt['task_id']='wrong_task'
    elif fault=='stale_generator': receipt['generator_sha256']='0'*64
    elif fault=='wrong_vote':
        receipt['results'][0]['output'][0][0]=9
        receipt['results'][0]['output_sha256']=tool.grid_sha256(receipt['results'][0]['output'])
    ref=tmp_path/'synthetic-parsing-negative.json'
    ref.write_text(json.dumps(receipt))
    with pytest.raises(ValueError): tool.score(path,ref,tmp_path/'score.json')
    assert not (tmp_path/'score.json').exists()

@pytest.mark.parametrize('fault',['mapping','resealed_mapping','request','sidecar_digest','source_binding','canonical_binding'])
def test_tampered_preparation_is_rejected(tool,prepared,tmp_path,fault):
    path,meta=prepared
    receipt=synthetic_parsing_receipt(tool,path,meta)
    ref=tmp_path/'synthetic-parsing-negative.json'
    ref.write_text(json.dumps(receipt))
    sidecar=path.with_suffix('.meta.json')
    if fault=='request':
        data=json.loads(path.read_text()); data['inputs'][0][0][0]=9; path.write_text(json.dumps(data))
    else:
        if fault in ('mapping','resealed_mapping'): meta['mapping'][0]['votes']=[9,9,9]
        elif fault=='sidecar_digest': meta['metadata_sha256']='0'*64
        elif fault=='source_binding': meta['generator_sha256']='0'*64
        elif fault=='canonical_binding': meta['canonical']['rule_hash']='000000000000'
        if fault=='resealed_mapping':
            meta.pop('metadata_sha256')
            meta['metadata_sha256']=tool.grid_sha256(meta)
        sidecar.write_text(json.dumps(meta))
    with pytest.raises(ValueError): tool.score(path,ref,tmp_path/'score.json')

@pytest.mark.parametrize('fault',['mapping_false_for_zero','mapping_float_for_int',
                                  'alphabet_false_for_zero','triple_count_float'])
@pytest.mark.parametrize('reseal',[False,True],ids=['unchanged_digest','recomputed_digest'])
def test_type_altered_sidecar_is_rejected_in_synthetic_parsing_test(tool,prepared,tmp_path,fault,reseal):
    """Regression for Python numeric equality; synthetic fixture is not authority."""
    path,meta=prepared
    receipt=synthetic_parsing_receipt(tool,path,meta)
    ref=tmp_path/'synthetic-parsing-negative.json'
    ref.write_text(json.dumps(receipt))
    if fault=='mapping_false_for_zero': meta['mapping'][0]['votes'][0]=False
    elif fault=='mapping_float_for_int': meta['mapping'][1]['triple_index']=1.0
    elif fault=='alphabet_false_for_zero': meta['alphabet'][0]=False
    elif fault=='triple_count_float': meta['triple_count']=729.0
    if reseal:
        meta.pop('metadata_sha256')
        meta['metadata_sha256']=tool.grid_sha256(meta)
    path.with_suffix('.meta.json').write_text(json.dumps(meta))
    with pytest.raises(ValueError): tool.score(path,ref,tmp_path/'score.json')
    assert not (tmp_path/'score.json').exists()

def test_score_cli_fails_nonzero_for_synthetic_parsing_fault(tool,prepared,tmp_path):
    path,meta=prepared
    receipt=synthetic_parsing_receipt(tool,path,meta)
    receipt['results']=[]
    ref=tmp_path/'synthetic-parsing-negative.json'
    ref.write_text(json.dumps(receipt))
    out=tmp_path/'must-not-exist.json'
    run=subprocess.run([sys.executable,str(TOOL),'score','--prepared',str(path),'--racket',str(ref),'--out',str(out)],capture_output=True,text=True)
    assert run.returncode==1
    assert 'probe failed' in run.stderr
    assert not out.exists()

def test_coverage_is_explicitly_python_proxy_and_counts_cells(tool):
    report=tool.coverage(seeds=[17],indices=range(1),bands=[None])
    assert report['measurement']=='independent Python vote proxy; not Racket authority'
    assert report['input_count']==1
    assert sum(report['vote_classes'].values())==report['cell_count']
    assert set(report['vote_classes'])=={'empty','singleton','pair_same','pair_distinct','triple_same','triple_majority','triple_distinct'}
    assert report['generator_sha256']==tool.file_sha256(TOOL.parent.parent/'generator.py')

def test_coverage_uses_dynamic_declared_competitors(tool,monkeypatch):
    """Controlled namespace tests coverage dispatch, not generator or Racket semantics."""
    grid=[[0,0,5,0,0,5,0,0] for _ in range(3)]
    namespace={'generate':lambda *a,**kw:grid,'self_check':lambda *a,**kw:[],
               'LESSON_COMPETITORS':{'all_nines':lambda g:[[9,9] for _ in range(3)]}}
    monkeypatch.setattr(tool.runpy,'run_path',lambda path:namespace)
    report=tool.coverage(seeds=[1],indices=[0],bands=[None])
    assert report['rival_source']=='generator LESSON_COMPETITORS'
    assert report['rival_cell_disagreements']=={'all_nines':6}
    assert report['rival_input_disagreements']=={'all_nines':1}
