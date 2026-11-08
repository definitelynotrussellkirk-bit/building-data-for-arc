#!/usr/bin/env python3
"""Findings-only probes for this packet's two immutable audit targets."""
from __future__ import annotations
from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
from probe import ROOT, canonical, load_generator, pairs, racket_outputs, sha256

TASKS=('99d5bc858270','b7e4aaffabac')

def signature(g):return json.dumps(g,separators=(',',':'))

def shadow_rival(g):
    """Keep only the farthest caster per light-ray projection (deliberately wrong)."""
    h,w=len(g),len(g[0])
    lr,lc=next((r,c) for r,row in enumerate(g) for c,v in enumerate(row)
               if v==4 and (r in (0,h-1) or c in (0,w-1)))
    dr,dc=(0,1) if lc==0 else (0,-1) if lc==w-1 else (1,0) if lr==0 else (-1,0)
    selected={}
    for r,row in enumerate(g):
        for c,v in enumerate(row):
            if not v or (r,c)==(lr,lc):continue
            key=r if dc else c
            if key not in selected or r*dr+c*dc > selected[key][0]*dr+selected[key][1]*dc:
                selected[key]=(r,c,v)
    out=[[0]*w for _ in range(h)]
    for r,c,v in selected.values():
        rr,cc=r+dr,c+dc
        while 0<=rr<h and 0<=cc<w:
            out[rr][cc]=4;rr+=dr;cc+=dc
    for r,c,v in selected.values():out[r][c]=v
    return out


def all_canonical(task):
    entries=[]
    for line in (ROOT/'shared/data/canonical/puzzles.jsonl').read_text().splitlines():
        row=json.loads(line)
        if row.get('task_id')!=task:continue
        for split in ('train','test'):
            seq=row.get(split,[])
            if isinstance(seq,dict):seq=[seq]
            for i,p in enumerate(seq):
                if 'output' not in p:continue
                entries.append({'source':row.get('source'),'split':split,'index':i,
                                **{k:[[int(v) for v in line] for line in p[k]] for k in ('input','output')}})
    return entries


def run(out, count):
    result={'schema':'findings-only-audit-v1','targets':{},'scope':'No audit-target source changes. Racket labels only; explicit rivals are diagnostic hypotheses.'}
    for task in TASKS:
        module=load_generator(task=task)
        cp=all_canonical(task)
        rule=canonical(task)['program_solution']
        hashes={'generator_sha256':sha256(ROOT/f'generators/{task}/generator.py'),
                'rule_text_sha256':hashlib.sha256(rule.encode()).hexdigest()}
        by_grid={signature(p['input']):p['input'] for p in cp}
        generated=[];generation_errors=[]
        for band in ('easy','medium','hard'):
            for seed in range(count):
                for index in range(4):
                    try:g=module.generate(seed,index,difficulty=band)
                    except Exception as exc:
                        generation_errors.append({'band':band,'seed':seed,'sample_index':index,'exception':repr(exc)});continue
                    by_grid[signature(g)]=g
                    generated.append({'band':band,'seed':seed,'sample_index':index,'input':g})
        grids=list(by_grid.values())
        actual=racket_outputs(grids,task=task,timeout=300)
        output_map={signature(g):y for g,y in zip(grids,actual)}
        canonical_map={signature(p['input']):p['output'] for p in cp}
        def rival(g):
            return shadow_rival(g) if task=='99d5bc858270' else canonical_map.get(signature(g),g)
        canonical_results=[]
        for p in cp:
            g=p['input'];y=output_map[signature(g)]
            canonical_results.append({**{k:p[k] for k in ('source','split','index')},
                                      'self_check_errors':module.self_check(g),'stored_matches_racket':y==p['output'],
                                      'rival_matches_racket':rival(g)==y})
        bands={}
        for band in ('easy','medium','hard'):
            samples=[p for p in generated if p['band']==band]
            cc=Counter();unique=set();lookup_lessons=[]
            for p in samples:
                g=p['input'];y=output_map[signature(g)];unique.add(signature(g))
                cc['draws']+=1;cc['exact_canonical_replays']+=signature(g) in canonical_map
                cc['self_check_failures']+=bool(module.self_check(g));cc['rival_matches']+=rival(g)==y
            by_seed={seed:sorted([p for p in samples if p['seed']==seed],key=lambda p:p['sample_index']) for seed in range(count)}
            for seed,pp in by_seed.items():
                if len(pp)!=4:continue
                cc['raw_consecutive_lessons']+=1
                survives=all(rival(p['input'])==output_map[signature(p['input'])] for p in pp[:3])
                harmful=survives and rival(pp[3]['input'])!=output_map[signature(pp[3]['input'])]
                cc['rival_survives_demos']+=survives;cc['rival_wrong_on_query']+=harmful
                if harmful:
                    lookup_lessons.append({'seed':seed,'demo_sample_indices':[0,1,2],'query_sample_index':3,
                                           'demo_input_hashes':[hashlib.sha256(signature(p['input']).encode()).hexdigest() for p in pp[:3]]})
            bands[band]={**dict(cc),'unique_inputs':len(unique),'harmful_examples':lookup_lessons[:3]}
        candidates=cp if task=='99d5bc858270' else [p for p in generated if signature(p['input']) not in canonical_map]
        ce=None
        for p in candidates:
            g=p['input'];y=output_map[signature(g)];prediction=rival(g)
            if prediction!=y:
                ce={'task_id':task,**hashes,'seed':p.get('seed'),'sample_index':p.get('sample_index'),
                    'band':p.get('band'),'canonical_location':{k:p[k] for k in ('source','split','index') if k in p},
                    'overrides':{},'input':g,'actual_racket_output':y,'rival_output':prediction,
                    'rival':'farthest_caster_per_projection' if task=='99d5bc858270' else 'canonical_lookup_else_identity',
                    'validator_errors':module.self_check(g),'in_documented_generator_domain':not bool(module.self_check(g)),
                    'canonical_domain':task=='99d5bc858270',
                    'reproduction':{'cwd':'packet_root','argv':['python3','run_with_racket.py','python3','generators/779c7c31edc3/workspace/audit_targets.py','--out','../checks/audits','--lessons',str(count)]}}
                break
        entry={**hashes,'canonical_occurrences':len(cp),'unique_canonical_inputs':len(canonical_map),
               'canonical_checks':canonical_results,'bands':bands,'unique_racket_executions':len(grids),
               'generation_errors':generation_errors,'raw_lesson_policy':'seed=0..N-1; sample_index=0,1,2 demonstrations; 3 query; no rejection or duplicate filtering',
               'rival':'farthest_caster_per_projection' if task=='99d5bc858270' else 'canonical_lookup_else_identity'}
        result['targets'][task]=entry
        if ce:(out/f'{task}-counterexample.json').write_text(json.dumps(ce,indent=2)+'\n')
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    # Findings are successful probe completion, not a claim that targets pass.
    return 0


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--lessons',type=int,default=100)
    args=p.parse_args()
    if args.lessons<1:p.error('--lessons must be positive')
    args.out.mkdir(parents=True,exist_ok=True)
    return run(args.out,args.lessons)
if __name__=='__main__':raise SystemExit(main())
