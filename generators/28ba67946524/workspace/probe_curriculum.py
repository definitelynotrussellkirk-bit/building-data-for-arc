#!/usr/bin/env python3
"""Source-bound input census, independent oracle, and all cyclic lesson holdouts.

Uses only portable public support. Python outputs are diagnostics, NOT Racket
labels. Pass --source to compare a retained baseline; never use during a solve.
"""
from __future__ import annotations
import argparse
from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK = '28ba67946524'


def graph(grid):
    components=[]; owner={}; h=len(grid);w=len(grid[0])
    for r,row in enumerate(grid):
        for c,color in enumerate(row):
            if color==0 or (r,c) in owner: continue
            i=len(components);todo=[(r,c)];owner[r,c]=i;cells=[]
            while todo:
                p=todo.pop();cells.append(p)
                for q in ((p[0]-1,p[1]),(p[0]+1,p[1]),(p[0],p[1]-1),(p[0],p[1]+1)):
                    y,x=q
                    if 0<=y<h and 0<=x<w and q not in owner and grid[y][x]==color:
                        owner[q]=i;todo.append(q)
            components.append((color,cells))
    edges=[set() for _ in components]
    for (r,c),i in owner.items():
        for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
            j=owner.get(p)
            if j is not None and i!=j: edges[i].add(j)
    seeds=[i for i,(color,_) in enumerate(components) if color==1]
    if len(seeds)!=1: raise ValueError('expected one seed component')
    dist={seeds[0]:0};q=deque(seeds)
    while q:
        i=q.popleft()
        for j in edges[i]:
            if j not in dist: dist[j]=dist[i]+1;q.append(j)
    out=[[0]*w for _ in range(h)]
    for i,d in dist.items():
        if d==2:
            for r,c in components[i][1]: out[r][c]=8
    return components,edges,dist,out


def digest(value):
    return hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--source',type=Path)
    parser.add_argument('--seeds',type=int,default=100)
    parser.add_argument('--samples',type=int,default=10)
    args=parser.parse_args()
    if args.out.exists(): parser.error('output must be new')
    if args.seeds<1 or args.samples<1: parser.error('positive sample counts required')
    root=find_root(__file__)
    source=args.source or root/'generators'/TASK/'generator.py'
    if not source.exists() and args.source is None:
        source=root/'puzzle_generators'/'per_puzzle'/TASK/'generator.py'
    spec=importlib.util.spec_from_file_location('probe_generator',source)
    gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
    canon=canonical_pairs(TASK,root=root)
    profiles={(len(p['input']),len(p['input'][0]),len(set(sum(p['input'],[])))) for p in canon}
    rivals=getattr(gen,'LESSON_COMPETITORS',{})
    result={'schema':'contact-curriculum-probe/v1','task_id':TASK,'source':str(source),
            'generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'declared_rule_hash':getattr(gen,'RULE_HASH',None),
            'oracle':'independent Python 4-connected pixel ownership and BFS; NOT reference labels',
            'seed_range':[0,args.seeds-1],'sample_index_range':[0,args.samples-1],
            'canonical_oracle_matches':sum(graph(p['input'])[3]==p['output'] for p in canon),
            'canonical_pairs':len(canon),'bands':{},'errors':[],'witness_examples':[],
            'canonical_shortcut_fits':{name:all(r(p['input'])==p['output'] for p in canon)
                for name,r in getattr(gen,'CANONICAL_SHORTCUTS',{}).items()}}
    saved=set()
    for band in ('easy','medium','hard'):
        counts=Counter();target_counts=Counter();unique=set();witnesses=Counter();mismatches=Counter()
        for seed in range(args.seeds):
            for index in range(args.samples):
                try:
                    g=gen.generate(seed,index,difficulty=band)
                    comps,edges,dist,out=graph(g)
                    failures=gen.self_check(g)
                    if failures: raise ValueError(str(failures))
                except Exception as exc:
                    result['errors'].append({'band':band,'seed':seed,'index':index,'error':repr(exc)})
                    continue
                unique.add(digest(g));counts['accepted']+=1
                profile=(len(g),len(g[0]),len(set(sum(g,[]))))
                counts['canonical_size_palette_hits']+=profile in profiles
                targets=[i for i,d in dist.items() if d==2]
                target_counts[len(targets)]+=1
                counts['reachable_cycle']+=sum(len(edges[i]) for i in dist)//2>=len(dist)
                counts['input_contains_8']+=any(8 in row for row in g)
                counts['repeated_component_colors']+=len({c for c,_ in comps})<len(comps)
                for name,witness in getattr(gen,'SEMANTIC_WITNESSES',{}).items():
                    hit=bool(witness(g));witnesses[name]+=hit
                    if hit and name not in saved:
                        saved.add(name);result['witness_examples'].append({'witness':name,'seed':seed,
                            'sample_index':index,'difficulty':band,'input_sha256':digest(g),
                            'input':g,'python_oracle_output':out})
                for name,rival in rivals.items(): mismatches[name]+=rival(g)!=out
        result['bands'][band]={'requested':args.seeds*args.samples,'unique_inputs':len(unique),
                              **counts,'target_component_counts':dict(target_counts),
                              'witness_hits':dict(witnesses),'rival_disagreements':dict(mismatches)}
    # Exhaustive residues for a period-two schedule, plus overlapping windows.
    windows=rotations=0;ambiguities=[]
    if rivals:
        for band in ('easy','medium','hard'):
            for seed in range(min(args.seeds,20)):
                for start in range(4):
                    pairs=[]
                    for i in range(4):
                        g=gen.generate(seed,start+i,difficulty=band)
                        pairs.append({'input':g,'output':graph(g)[3]})
                    predictions={name:[r(p['input']) for p in pairs] for name,r in rivals.items()}
                    windows+=1
                    for q in range(4):
                        rotations+=1
                        for name,outputs in predictions.items():
                            if all(outputs[i]==pairs[i]['output'] for i in range(4) if i!=q) and outputs[q]!=pairs[q]['output']:
                                ambiguities.append({'band':band,'seed':seed,'start':start,'query':q,'rival':name,'pairs':pairs})
    result['cyclic_windows']={'seeds_per_band':min(args.seeds,20),'starts':[0,1,2,3],
        'windows':windows,'rotations':rotations,'ambiguities':ambiguities,
        'declared_rivals':sorted(rivals),
        'scope':f'independent Python oracle; overlapping windows; {len(rivals)} declared rivals only',
        'status':'not_declared' if not rivals else ('fail' if ambiguities else 'pass')}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('witness_examples','errors')},indent=2))
    return 1 if result['errors'] or ambiguities else 0


if __name__=='__main__':raise SystemExit(main())
