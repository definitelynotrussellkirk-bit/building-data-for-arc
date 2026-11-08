"""Portable source-bound domain census; authoring only, never a solve helper."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root

TASK = '6c8eefa043e1'

def load_generator():
    source = Path(__file__).resolve().parent.parent / 'generator.py'
    spec = importlib.util.spec_from_file_location('review_flood_generator', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source

def components(grid):
    remaining = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v != 5}
    result = []
    while remaining:
        p = min(remaining); remaining.remove(p); comp = {p}; queue = [p]
        for r,c in queue:
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in remaining:
                    remaining.remove(q); comp.add(q); queue.append(q)
        result.append(comp)
    return result

def domain_counts(grid):
    comps = components(grid)
    seeds = [[(r,c,grid[r][c]) for r,c in comp if grid[r][c] not in (0,5)] for comp in comps]
    return {'components':len(comps), 'seed_counts':sorted(map(len,seeds)),
            'collision_components':sum(len(s)>1 for s in seeds),
            'seedless_components':sum(not s for s in seeds),
            'seedless_area':sum(len(c) for c,s in zip(comps,seeds) if not s),
            'growing_seeded_components':sum(len(s)==1 and len(c)>1 for c,s in zip(comps,seeds))}

def oracle(grid):
    """Independent sequential zero-cell flood; checked separately against Racket."""
    out=[list(row) for row in grid]; h,w=len(out),len(out[0])
    seeds=[(r,c,v) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (0,5)]
    for r,c,color in seeds:
        out[r][c]=0; stack=[(r,c)]
        while stack:
            rr,cc=stack.pop()
            if not (0<=rr<h and 0<=cc<w) or out[rr][cc]!=0:
                continue
            out[rr][cc]=color
            stack.extend(((rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)))
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--per-band',type=int,default=100)
    parser.add_argument('--seed',type=int,default=20261005)
    parser.add_argument('--phase',required=True)
    args=parser.parse_args(); mod,source=load_generator()
    pairs=canonical_pairs(TASK,root=find_root(__file__),labeled_only=True)
    canonical_unique={json.dumps(p['input'],separators=(',',':')) for p in pairs}
    summaries={}; first_collision=None; unique=set(); hashes=[]; samples=[]
    for band in ('easy','medium','hard'):
        counts=Counter()
        for index in range(args.per_band):
            g=mod.generate(args.seed,index,difficulty=band)
            encoded=json.dumps(g,separators=(',',':')); unique.add(encoded)
            stats=domain_counts(g); errors=mod.self_check(g)
            counts['draws']+=1; counts['selfcheck_rejected']+=bool(errors)
            counts['collision_grids']+=bool(stats['collision_components'])
            counts['no_seedless_component']+=stats['seedless_components']==0
            counts['exact_profile_hits']+=(len(g),len(g[0]),len({v for row in g for v in row})) in ((7,7,5),(9,9,4),(9,9,5))
            counts['canonical_input_replays']+=encoded in canonical_unique
            if first_collision is None and stats['collision_components']:
                first_collision={'seed':args.seed,'sample_index':index,'difficulty':band,'input':g,'self_check_errors':errors,'domain_counts':stats}
            if index<10: samples.append(g)
            hashes.append(hashlib.sha256(encoded.encode()).hexdigest())
        summaries[band]=dict(counts)
    rival_report={}
    for namespace in ('CANONICAL_SHORTCUTS','LESSON_COMPETITORS','SEMANTIC_RIVALS'):
        for name,rival in getattr(mod,namespace,{}).items():
            fit=sum(rival(p['input'])==p['output'] for p in pairs)
            generated_refutations=sum(rival(g)!=oracle(g) for g in samples)
            rival_report[f'{namespace}:{name}']={'canonical_matches':fit,'canonical_total':len(pairs),'generated_refutations':generated_refutations,'generated_total':len(samples)}
    result={'task_id':TASK,'phase':args.phase,'generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'rule_hash':getattr(mod,'RULE_HASH',None),'seed':args.seed,'indices':f'0..{args.per_band-1}',
            'per_band':summaries,'unique_inputs':len(unique),'total_inputs':len(hashes),'input_hashes':hashes,
            'first_collision':first_collision,'canonical_pairs':len(pairs),'unique_canonical_inputs':len(canonical_unique),
            'canonical_selfcheck_accepted':sum(not mod.self_check(p['input']) for p in pairs),
            'independent_oracle_canonical_matches':sum(oracle(p['input'])==p['output'] for p in pairs),
            'rivals':rival_report}
    args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('input_hashes','first_collision')},indent=2))
    if first_collision:
        print('FIRST COLLISION', {k:v for k,v in first_collision.items() if k!='input'})

if __name__=='__main__': main()
