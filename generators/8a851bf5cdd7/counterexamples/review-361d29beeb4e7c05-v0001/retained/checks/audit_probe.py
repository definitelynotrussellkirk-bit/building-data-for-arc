#!/usr/bin/env python3
"""Findings-only, source-bound probes for the two assigned audit targets.
Run from packet root via run_with_racket.py; the wrapper sets cwd to repo.
No generator changes, private runner imports, or hidden solve answers.
"""
from __future__ import annotations
import collections
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from arcpuzzles import Catalog

ROOT = Path.cwd()
OUT = ROOT.parent/'checks/audit'
TASKS = ('ad92d10d919c','8a851bf5cdd7')

def save(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')

def digest(value):
    return hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()

def load(tid):
    spec=importlib.util.spec_from_file_location('audit_'+tid,ROOT/'generators'/tid/'generator.py')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def canonical(catalog,tid):
    pairs=[]
    for v in catalog.get(tid)['variants']:
        for split in ('train','test'):
            data=v.get(split,[])
            if isinstance(data,dict): data=[data]
            pairs.extend({'input':[[int(c) for c in r] for r in p['input']],
                          'output':[[int(c) for c in r] for r in p['output']], 'split':split}
                         for p in data if 'input' in p and 'output' in p)
    return pairs

def diagonal(g, required=4):
    out=copy.deepcopy(g)
    for r in range(1,len(g)-1):
        for c in range(1,len(g[0])-1):
            vals=[g[r+dr][c+dc] for dr in (-1,1) for dc in (-1,1)]
            color,n=collections.Counter(vals).most_common(1)[0]
            if g[r][c]==0 and color!=0 and n>=required: out[r][c]=color
    return out

def panels(g):
    cuts=[c for c in range(len(g[0])) if all(row[c]==8 for row in g)]
    if len(cuts)!=2: raise ValueError('not two dividers')
    left,right=cuts
    return ([r[:left] for r in g],[r[left+1:right] for r in g],[r[right+1:] for r in g])

def stencil(g):
    a,b,c=panels(g)
    q=next((x for row in c for x in row if x),0)
    return [[0 if a[r][s] and not b[r][s] else q if b[r][s] and not a[r][s] else c[r][s]
             for s in range(len(c[0]))] for r in range(len(c))]

def recolor_b(g):
    a,b,c=panels(g)
    q=next((x for row in c for x in row if x),0)
    return [[q if x else 0 for x in row] for row in b]

def main():
    catalog=Catalog(ROOT)
    for tid in TASKS:
        home=OUT/tid; home.mkdir(parents=True,exist_ok=True)
        gen=load(tid); metadata=catalog.describe(tid); canon=canonical(catalog,tid)
        reference=diagonal if tid==TASKS[0] else stencil
        rival=(lambda g:diagonal(g,3)) if tid==TASKS[0] else recolor_b
        name='three_of_four_diagonals' if tid==TASKS[0] else 'recolor_after_panel'
        rows=[]; grids=[p['input'] for p in canon]
        for band in ('easy','medium','hard'):
            for seed in range(100):
                g=gen.generate(seed,0,difficulty=band)
                rows.append({'difficulty':band,'seed':seed,'sample_index':0,'overrides':{},
                             'input_sha256':digest(g),'validator':gen.self_check(g)})
                grids.append(g)
        report={'schema':'assigned-adversarial-audit-v1','phase':'audit-unchanged',
                'task_id':tid,'generator_sha256':metadata['generator_sha256'],
                'rule_hash':metadata['rule_hash'],'version':gen.VERSION,
                'cwd':str(ROOT),'argv':sys.argv,'samples':300,'seed_range':[0,99],
                'sample_index':0,'bands':['easy','medium','hard'],
                'unique_default_inputs':len({r['input_sha256'] for r in rows}),
                'rival':name,'canonical_pairs':len(canon),
                'canonical_rival_matches':sum(rival(p['input'])==p['output'] for p in canon),
                'canonical_oracle_matches':sum(reference(p['input'])==p['output'] for p in canon),
                'validator_rejections':[r for r in rows if r['validator']],
                'reference_errors':[],'oracle_mismatches':[], 'rival_default_matches':0}
        outputs=[]
        with (home/'racket-receipts.jsonl').open('w') as stream:
            for start in range(0,len(grids),64):
                receipt=catalog.apply(tid,grids[start:start+64],reference='canonical',timeout=300)
                receipt['batch_offset']=start; receipt['caller_argv']=sys.argv; receipt['caller_cwd']=str(ROOT)
                stream.write(json.dumps(receipt,separators=(',',':'))+'\n'); stream.flush()
                for j,res in enumerate(receipt['results']):
                    k=start+j
                    if not res.get('valid_output') or res.get('error'):
                        report['reference_errors'].append({'index':k,'error':res.get('error')})
                    elif reference(grids[k])!=res['output']:
                        report['oracle_mismatches'].append(k)
                    outputs.append(res.get('output'))
                print(tid,'checked',len(outputs),'/',len(grids),flush=True)
        report['racket_comparisons']=len(grids)
        for idx,row in enumerate(rows):
            predicted=rival(grids[len(canon)+idx])
            row['rival_matches']=predicted==outputs[len(canon)+idx]
            report['rival_default_matches']+=row['rival_matches']
        candidates=[]
        if tid==TASKS[0]:
            request={'grid_h':6,'grid_w':7,'motif_count':3}
            drops=[]
            for seed in range(100):
                g=gen.generate(seed,0,difficulty='easy',**request)
                count=len({x for r in g for x in r}-{0})
                if count!=3:
                    drops.append({'seed':seed,'sample_index':0,'difficulty':'easy','overrides':request,
                                  'observed_motifs':count,'validator':gen.self_check(g),'input':g})
            report['exact_count_probe']={'seed_range':[0,99],'sample_index':0,'difficulty':'easy',
                                        'overrides':request,'draws':100,'dropped_count':len(drops)}
            save(home/'count-drops.json',drops)
            partial=gen.generate(0,0,difficulty='easy',texture='partial_xs')
            candidates.append({'kind':'rival-counterexample','seed':0,'sample_index':0,'difficulty':'easy',
                  'overrides':{'texture':'partial_xs'},'input':partial,'rival_output':rival(partial),
                  'validator':gen.self_check(partial),
                  'domain':'Explicit documented partial_xs degenerate; not sampled by defaults.'})
            if drops:
                candidates.append(dict(drops[0],kind='silent-motif-count-drop',rival_output=rival(drops[0]['input']),
                                       domain='Feasible declared exact overrides; three disjoint 3x3 neighborhoods fit a 6x7 canvas.'))
        else:
            variants=[]
            for seed in range(100):
                variants.append(gen.generate(seed,0,difficulty='medium',variant=0)==
                                gen.generate(seed,0,difficulty='medium',variant=2))
            report['variant_probe']={'seed_range':[0,99],'draws':100,'sample_index':0,
                  'difficulty':'medium','same_bytes_for_variant_0_and_2':sum(variants)}
            pos=next(i for i,r in enumerate(rows) if not r['rival_matches'])
            candidates.append(dict(rows[pos],kind='already-refuted-canonical-shortcut',
                              input=grids[len(canon)+pos],rival_output=rival(grids[len(canon)+pos]),
                              domain='Unmodified default sampler output; core documented domain.'))
            bad=gen.generate(0,0,difficulty='easy',texture='no_separator')
            candidates.append({'kind':'advertised-degenerate-reference-error','seed':0,'sample_index':0,
                         'difficulty':'easy','overrides':{'texture':'no_separator'},'input':bad,
                         'validator':gen.self_check(bad),'rival_output':None,
                         'domain':'Advertised DEGENERATE_TEXTURES value; outside the three-separated-panels core invariant.',
                         'rival_note':'No rival claimed for an input on which reference execution itself fails.'})
            try:
                report['ragged_validator']= {'returned':gen.self_check([[8,0,8],[8]])}
            except Exception as exc:
                report['ragged_validator']={'exception':f'{type(exc).__name__}: {exc}'}
        save(home/'counterexample-plan.json',candidates)
        save(home/'input.json',[r['input'] for r in candidates])
        save(home/'canonical-fit.json',{'rival':name,'pairs':[dict(p,rival_output=rival(p['input'])) for p in canon]})
        save(home/'draws.json',rows)
        save(home/'summary.json',report)
        print(json.dumps(report,indent=2),flush=True)
        assert not report['reference_errors'] and not report['oracle_mismatches'], 'Default reference/oracle check failed'
        assert metadata['generator_sha256']==hashlib.sha256((ROOT/'generators'/tid/'generator.py').read_bytes()).hexdigest()

if __name__=='__main__': main()
