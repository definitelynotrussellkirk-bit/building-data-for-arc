import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import pytest

from arcpuzzles import review_public_coverage_cache as cache

def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))

@pytest.fixture
def source(tmp_path,monkeypatch):
    root=tmp_path/'root';tid='public_eval_1234abcd';pid='1234abcd'
    home=root/'generators'/tid;home.mkdir(parents=True)
    (home/'generator.py').write_text('# generator')
    write(root/'catalog/puzzles.jsonl',{'id':tid,'generator':f'generators/{tid}/generator.py'})
    write(root/'shared/data/canonical/puzzles.jsonl',{'task_id':tid,'program_solution':'(rule! g)'})
    for name in ('shared/runtime/module.py','src/arcpuzzles/helper.py','shared/tools/comment_solutions.py'):
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('# source')
    write(root/cache.SOURCE,{pid:{}});write(root/cache.SOLUTIONS,{pid:[]})
    proof=f'generators/{tid}/evidence/proof.json';preflight=f'generators/{tid}/evidence/preflight.json'
    write(root/proof,{'owner_preflight':preflight})
    for name in (preflight,f'generators/{tid}/evidence/original-pairs.json',f'generators/{tid}/evidence/execution.json'):
        write(root/name,{})
    entry={'status':'accepted','public_creation':{'task_id':tid,'public_task_id':pid},'owner_evidence':{'path':proof}}
    write(root/cache.REGISTRY,{'schema':'arcpuzzles-public-eval-coverage-v1','parents':{pid:entry}})
    calls=[]
    def verify(root,*,_candidate_ids=None):
        calls.append(_candidate_ids);return [pid]
    monkeypatch.setattr(cache,'verified_coverage',verify)
    return root,home,pid,calls

def test_warm_then_hit_and_authenticated_tamper_misses(source):
    root,home,pid,calls=source
    assert cache.fast_coverage(root)[0]==[pid]
    assert cache.fast_coverage(root)[1]['cache_hits']==1
    assert len(calls)==1
    path=root/'var/review/public-coverage-cache/current.json';raw=json.loads(path.read_text())
    raw['entries'][pid]['signature']='0'*64;write(path,raw)
    assert cache.fast_coverage(root)[1]['cache_hits']==0
    assert len(calls)==2

@pytest.mark.parametrize('mutation',['source','added','removed','runtime','helper','catalog','canonical','gold','proof','external_receipt','symlink'])
def test_dependency_changes_reverify(source,mutation):
    root,home,pid,calls=source
    cache.fast_coverage(root)
    paths={'source':home/'generator.py','runtime':root/'shared/runtime/module.py','helper':root/'src/arcpuzzles/helper.py',
        'gold':root/cache.SOLUTIONS,'proof':home/'evidence/proof.json'}
    if mutation in paths:
        path=paths[mutation]
        if path.suffix=='.json':
            value=json.loads(path.read_text());value['changed']=True;write(path,value)
        else:path.write_text('# changed')
    elif mutation=='added':(home/'new.py').write_text('# added')
    elif mutation=='removed':(home/'generator.py').unlink()
    elif mutation=='symlink':(home/'new.py').symlink_to(home/'generator.py')
    elif mutation=='catalog':
        path=root/'catalog/puzzles.jsonl';row=json.loads(path.read_text());row['semantic_veto']=True;write(path,row)
    elif mutation=='canonical':write(root/'shared/data/canonical/puzzles.jsonl',{'task_id':'public_eval_'+pid,'program_solution':'(rule! (flip-lr g))'})
    elif mutation=='external_receipt':
        proof=home/'evidence/proof.json';value=json.loads(proof.read_text());value['owner_preflight']='var/external/preflight.json';write(proof,value)
        for name in ('preflight.json','original-pairs.json','execution.json'):write(root/'var/external'/name,{})
    assert cache.fast_coverage(root)[1]['cache_hits']==0
    assert len(calls)==2

def test_unrelated_catalog_and_canonical_addition_does_not_invalidate(source):
    root,home,pid,calls=source;cache.fast_coverage(root)
    with (root/'catalog/puzzles.jsonl').open('a') as f:f.write('\n'+json.dumps({'id':'another','generator':None}))
    with (root/'shared/data/canonical/puzzles.jsonl').open('a') as f:f.write('\n'+json.dumps({'task_id':'another','program_solution':'(rule! g)'}))
    assert cache.fast_coverage(root)[1]['cache_hits']==1
    assert len(calls)==1

def test_malformed_cache_reverifies_and_no_cross_parent_replay(source):
    root,home,pid,calls=source;cache.fast_coverage(root)
    path=root/'var/review/public-coverage-cache/current.json';path.write_text('broken json')
    assert cache.fast_coverage(root)[1]['cache_hits']==0
    raw=json.loads(path.read_text());raw['entries'][pid]['payload']['public_task_id']='ffffffff';write(path,raw)
    assert cache.fast_coverage(root)[1]['cache_hits']==0


def test_source_changes_during_miss_cannot_seal_old_identity(source,monkeypatch):
    root,home,pid,calls=source
    def mutate(root,*,_candidate_ids=None):
        (home/'generator.py').write_text('# changed during validation')
        return [pid]
    monkeypatch.setattr(cache,'verified_coverage',mutate)
    assert cache.fast_coverage(root)[0]==[]
    stored=json.loads((root/'var/review/public-coverage-cache/current.json').read_text())
    assert stored['entries']=={}


@pytest.mark.parametrize('bad',[[],None,{'schema':cache.SCHEMA,'entries':[]}])
def test_unknown_cache_shapes_reverify(source,bad):
    root,home,pid,calls=source;cache.fast_coverage(root)
    write(root/'var/review/public-coverage-cache/current.json',bad)
    assert cache.fast_coverage(root)[1]['cache_hits']==0
    assert len(calls)==2


def test_external_original_receipt_mutation_invalidates_hit(source):
    root,home,pid,calls=source
    proof=home/'evidence/proof.json';value=json.loads(proof.read_text())
    value['owner_preflight']='var/external/preflight.json';write(proof,value)
    for name in ('preflight.json','original-pairs.json','execution.json'):write(root/'var/external'/name,{})
    cache.fast_coverage(root)
    assert cache.fast_coverage(root)[1]['cache_hits']==1
    write(root/'var/external/original-pairs.json',{'changed':True})
    assert cache.fast_coverage(root)[1]['cache_hits']==0


def test_creation_queue_cache_is_explicit_fast_only(source, monkeypatch):
    from arcpuzzles import review_public_creation as creation
    from arcpuzzles import review_public_admission as admission
    root, home, pid, calls = source
    full = []; fast = []
    monkeypatch.setattr(admission, 'verified_coverage', lambda root: full.append(root) or [pid])
    monkeypatch.setattr(cache, 'fast_coverage', lambda root: (fast.append(root) or [pid],
                        {'mode': 'exact_content_cache', 'fresh_execution': False}))
    receipt = {}
    assert creation.creation_queue(root, verification=receipt)[0]['needs_creation'] is False
    assert len(full) == 1 and not fast and receipt['mode'] == 'full'
    assert creation.creation_queue(root, fast=True, verification=receipt)[0]['needs_creation'] is False
    assert len(full) == 1 and len(fast) == 1 and receipt['fresh_execution'] is False
