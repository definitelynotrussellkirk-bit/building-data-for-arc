#!/usr/bin/env python3
"""Findings-only, source-bound probes for the two assigned audit targets.

Canonical outputs come from the supplied labels or public Catalog APIs. The
independent transform/component routines define counterfactual inputs or rivals,
not intended training labels. No audit target is modified.
"""
from __future__ import annotations
import argparse, copy, hashlib, importlib.util, json, sys
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / 'repo'
sys.path[:0] = [str(REPO/'src'), str(REPO/'shared/runtime')]
OUT = ROOT/'checks/audit'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(p,x): p.write_text(json.dumps(x,indent=2)+'\n')
def load(task):
    path=REPO/'generators'/task/'generator.py'
    spec=importlib.util.spec_from_file_location('audit_'+task,path)
    mod=importlib.util.module_from_spec(spec); sys.modules[spec.name]=mod
    spec.loader.exec_module(mod)
    row=next(json.loads(line) for line in (REPO/'shared/data/canonical/puzzles.jsonl').open() if json.loads(line).get('task_id')==task)
    identity={'task_id':task,'version':mod.VERSION,'generator_sha256':sha(path),
              'canonical_program_sha256':digest(row['program_solution']),
              'rule_hash':hashlib.sha256(' '.join(row['program_solution'].split()).encode()).hexdigest()[:12],
              'probe_sha256':sha(Path(__file__))}
    return mod,row,identity

def transform(g,code):
    if code=='id': return copy.deepcopy(g)
    if code=='r1': return [list(row) for row in zip(*g[::-1])]
    if code=='r2': return [row[::-1] for row in g[::-1]]
    if code=='r3': return [list(row) for row in zip(*g)][::-1]
    if code=='fh': return [row[::-1] for row in g]
    if code=='fv': return copy.deepcopy(g[::-1])
    if code=='tr': return [list(row) for row in zip(*g)]
    if code=='atr': return [list(row)[::-1] for row in zip(*g)][::-1]
    raise ValueError(code)

def panels(g):
    s=(len(g[0])-3)//4
    return [[r[k*(s+1):k*(s+1)+s] for r in g] for k in range(4)]
def components(g):
    seen=set(); found=[]
    for r,row in enumerate(g):
        for c,v in enumerate(row):
            if not v or (r,c) in seen: continue
            todo=[(r,c)]; seen.add((r,c)); cells=[]
            while todo:
                a,b=todo.pop(); cells.append((a,b))
                for da,db in ((-1,0),(1,0),(0,-1),(0,1)):
                    x,y=a+da,b+db
                    if 0<=x<len(g) and 0<=y<len(g[0]) and (x,y) not in seen and g[x][y]==v:
                        seen.add((x,y)); todo.append((x,y))
            found.append({'size':len(cells),'r':min(a for a,b in cells),'c':min(b for a,b in cells),'color':v,'cells':cells})
    return sorted(found,key=lambda o:(-o['size'],o['r'],o['c']))
def second_distinct(g):
    objects=components(g); sizes=sorted({o['size'] for o in objects},reverse=True)
    if len(sizes)<2: return copy.deepcopy(g)
    target=next(o for o in objects if o['size']==sizes[1]); result=copy.deepcopy(g)
    for r,c in target['cells']: result[r][c]=8
    return result

def prepare():
    # Known non-symmetric matrix makes geometry regressions visible.
    a=[[1,2,3],[4,5,6],[7,8,9]]
    assert transform(a,'r3')==[[3,6,9],[2,5,8],[1,4,7]]
    assert transform(a,'atr')==[[9,6,3],[8,5,2],[7,4,1]]
    task='d2f8cb1c91b2'; mod,canonical,identity=load(task)
    folder=OUT/task; folder.mkdir(exist_ok=True)
    exact={code:mod.generate(17,0,difficulty='easy',transform=code) for code in ('r3','tr','atr')}
    original=exact['r3']; ex,demo,x,y=panels(original)
    records=[{'kind':'generated_transform_r3','seed':17,'sample_index':0,'difficulty':'easy','overrides':{'transform':'r3'},'input':original}]
    for code in ('r3','atr'):
        repaired=copy.deepcopy(original); s=len(ex); new_demo=transform(ex,code)
        for r in range(s): repaired[r][s+1:2*s+1]=new_demo[r]
        records.append({'kind':'counterfactual_demo_'+code,'derived_from':0,'only_change':'panel1 follows independently implemented '+code,'input':repaired})
    for row in records:
        row['self_check']=mod.self_check(row['input'])
        p=panels(row['input'])
        row['observed_transform_matches']=[code for code in ('id','r1','r2','r3','fh','fv','tr','atr') if transform(p[0],code)==p[1]]
    small=mod.generate(23,0,difficulty='easy',palette_size=4)
    large=mod.generate(23,0,difficulty='easy',palette_size=7)
    metadata={**identity,'domain':'Four square panels and valid dividers. Generated r3 violates its advertised transform; counterfactuals stay in the intended panel grammar. All pass the target validator.',
              'transform_pins_identical':exact['r3']==exact['tr']==exact['atr'],
              'pinned_input_hashes':{k:digest(v) for k,v in exact.items()},
              'ignored_palette_probe':{'seed':23,'sample_index':0,'difficulty':'easy','pins':[4,7], 'inputs_identical':small==large,'visible_color_count':len({v for r in small for v in r}), 'input_sha256':digest(small),'input':small,'self_check':mod.self_check(small)},
              'examples':records}
    write(folder/'input.json',[r['input'] for r in records]); write(folder/'generated.json',metadata)
    task='351de765e33f'; mod,canonical,identity=load(task); folder=OUT/task; folder.mkdir(exist_ok=True)
    pairs=[]
    for split in ('train','test'):
        vals=canonical.get(split,[]); vals=[vals] if isinstance(vals,dict) else vals
        pairs.extend({'split':split,'index':i,**pair} for i,pair in enumerate(vals) if 'output' in pair)
    records=[]
    for index in (0,6,7):
        g=mod.generate(17,index,difficulty='medium')
        records.append({'kind':'generated','seed':17,'sample_index':index,'difficulty':'medium','overrides':{},'scene_profile':mod.observe_overrides(g)['scene_profile'],'input':g,'rival_output':second_distinct(g),'self_check':mod.self_check(g)})
    metadata={**identity,'rival':'second-largest distinct object size; first by top/left on ties; identity if all sizes equal',
              'domain':'All generated witnesses pass self_check and use existing linked scene profiles.',
              'canonical_results':[{'split':p['split'],'index':p['index'],'input_sha256':digest(p['input']),'fits':second_distinct(p['input'])==p['output']} for p in pairs],
              'examples':records}
    write(folder/'input.json',[r['input'] for r in records]); write(folder/'generated.json',metadata)
    print('Prepared source-bound witnesses for both audit targets.')

def check_receipts():
    for task in ('d2f8cb1c91b2','351de765e33f'):
        folder=OUT/task; m=json.loads((folder/'generated.json').read_text()); ref=json.loads((folder/'racket.json').read_text())
        _,_,identity=load(task)
        if not m['generator_sha256']==identity['generator_sha256']==ref['generator_sha256']: raise ValueError('source mismatch')
        if not ref['rule_hash_matches_catalog'] or ref['executed_rule_hash']!=m['rule_hash']: raise ValueError('rule mismatch')
        if len(m['examples'])!=len(ref['results']): raise ValueError('count mismatch')
        rows=[]
        for ex,actual in zip(m['examples'],ref['results'],strict=True):
            if ex['input']!=actual['input'] or actual['error'] or not actual['valid_output']: raise ValueError('invalid reference')
            row={**ex,'racket_output':actual['output']}
            if task=='351de765e33f': row['rival_disagrees']=row['rival_output']!=actual['output']
            else:
                row['rival_output']=ref['results'][0]['output']
                row['original_transpose_output_differs']=actual['output']!=ref['results'][0]['output']
            rows.append(row)
        write(folder/'verified.json',{**identity,'domain':m['domain'],'reference_receipt_sha256':sha(folder/'racket.json'),
              'canonical_fit_results':m.get('canonical_results'), 'command_cwd':'packet_root',
              'reference_command':['python3','run_with_racket.py','python3','-m','arcpuzzles','apply',task,'--input',f'../checks/audit/{task}/input.json','--out',f'../checks/audit/{task}/racket.json'],
              'examples':rows})
        print(task, json.dumps([{k:v for k,v in r.items() if k in ('kind','rival_disagrees','original_transpose_output_differs','observed_transform_matches')} for r in rows]))

def public_sampler():
    from arcpuzzles import Catalog
    task='351de765e33f'; mod,_,identity=load(task); result={**identity,'seed_range':[3000,3099],'n_train':5,'n_test':2,'public_api':'Catalog.generate','bands':{}}
    catalog=Catalog(REPO)
    for band in ('easy','medium','hard'):
        episodes=catalog.generate(task,count=100,seed=3000,difficulty=band,n_train=5,n_test=2,allow_unapproved=True,timeout=600)
        lessons=[]; train_hist=Counter(); query_hist=Counter(); unique=set(); errors=[]
        for ep in episodes:
            if ep['provenance']['generator_sha256']!=identity['generator_sha256'] or ep['executed_rule_hash']!=identity['rule_hash']: raise ValueError('identity mismatch')
            if ep.get('rejections'): raise ValueError('unexpected rejected input')
            pp=ep['train']+ep['test']; profiles=[mod.observe_overrides(p['input'])['scene_profile'] for p in pp]
            disagreements=[second_distinct(p['input'])!=p['output'] for p in pp]
            for p in pp:
                unique.add(digest(p['input'])); errors.extend(mod.self_check(p['input']))
            train_hist.update(profiles[:5]); query_hist.update(profiles[5:])
            lessons.append({'seed':ep['seed'],'sample_indices':ep['sample_indices'],'profiles':profiles,
                            'rival_survives_train':not any(disagreements[:5]),'rival_fails_query':any(disagreements[5:]),
                            'pair_hashes':[{'input':digest(p['input']),'racket_output':digest(p['output'])} for p in pp]})
        result['bands'][band]={'lessons':lessons,'lesson_count':len(lessons),'unique_input_hashes':len(unique),'self_check_errors':errors,
                              'train_profile_histogram':dict(train_hist),'query_profile_histogram':dict(query_hist),
                              'surviving_rival_lessons':sum(r['rival_survives_train'] for r in lessons),
                              'unrefuted_wrong_query_lessons':sum(r['rival_survives_train'] and r['rival_fails_query'] for r in lessons)}
        print(band, {k:v for k,v in result['bands'][band].items() if k!='lessons'},flush=True)
    result['source_unchanged']=sha(REPO/'generators'/task/'generator.py')==identity['generator_sha256']
    write(OUT/task/'public_sampler.json',result)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['prepare','check','sampler']); a=p.parse_args()
    {'prepare':prepare,'check':check_receipts,'sampler':public_sampler}[a.action]()
