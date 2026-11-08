#!/usr/bin/env python3
"""Source-bound distribution, rival-survival and actual Racket parity probe.

From packet_root:
  python3 run_with_racket.py python3 generators/98a65dc7fcb1/workspace/probe_distribution.py \
    --seeds 100 --indices 8 --exhaustive-local --out ../checks/probe_final

No GPU, network, installation or private solve files are used. --source can
point at the immutable baseline generator. Output directories must be new.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
import sys
import time
import tempfile

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'src'))
TASK = '98a65dc7fcb1'
BANDS = ('easy','medium','hard')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':')).encode()


def local_rule(grid, *, cardinal=False, mixed=False, overwrite=False):
    out = [row[:] for row in grid]
    for r in range(1,len(grid)-1):
        for c in range(1,len(grid[0])-1):
            cells = [(r-1,c),(r+1,c),(r,c-1),(r,c+1)] if cardinal else [
                (i,j) for i in range(r-1,r+2) for j in range(c-1,c+2) if (i,j)!=(r,c)]
            values = [grid[i][j] for i,j in cells]
            if (overwrite or grid[r][c]==0) and values[0] and (
                    all(values) if mixed else len(set(values))==1):
                out[r][c]=values[0]
    return out


def box_rule(grid):
    out = [row[:] for row in grid]
    unvisited={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v}
    while unvisited:
        start=min(unvisited); unvisited.remove(start)
        todo=[start]; part={start}; color=grid[start[0]][start[1]]
        while todo:
            r,c=todo.pop()
            for dr,dc in itertools.product((-1,0,1),repeat=2):
                p=(r+dr,c+dc)
                if p in unvisited and grid[p[0]][p[1]]==color:
                    unvisited.remove(p);part.add(p);todo.append(p)
        rs=[r for r,c in part];cs=[c for r,c in part]
        if max(rs)-min(rs)==max(cs)-min(cs)==2:
            for r in range(min(rs),max(rs)+1):
                for c in range(min(cs),max(cs)+1):out[r][c]=color
    return out


RIVALS = {
    'cardinal_only': lambda g: local_rule(g,cardinal=True),
    'any_nonzero_neighbors': lambda g: local_rule(g,mixed=True),
    'overwrite_center': lambda g: local_rule(g,overwrite=True),
    'component_box': box_rule,
}


def literal(grid):
    return "'("+' '.join('('+' '.join(map(str,row))+')' for row in grid)+')'


def racket_outputs(bridge, rule, inputs, batch_size=64):
    from puzzle_generators.rule_wrap import wrap_rule
    for offset in range(0,len(inputs),batch_size):
        batch=inputs[offset:offset+batch_size]
        expression=f'(let ([f {wrap_rule(rule)}]) (map f (list '+ ' '.join(literal(g) for g in batch)+')))'
        results=bridge.eval_text(expression)
        if not isinstance(results,list) or len(results)!=len(batch):
            raise RuntimeError(f'Racket batch failed at offset {offset}: {results!r}')
        yield from results


def load(path):
    spec=importlib.util.spec_from_file_location('measured_generator',path)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod
    spec.loader.exec_module(mod)
    return mod


def run(args):
    from arc_repl.racket_bridge import RacketBridge
    start=time.monotonic()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    source=Path(args.source) if args.source else REPO/f'generators/{TASK}/generator.py'
    gen=load(source)
    canonical=next(json.loads(line) for line in (REPO/'shared/data/canonical/puzzles.jsonl').open()
                   if json.loads(line)['task_id']==TASK)
    rule=canonical['program_solution']
    records=[];failures=[];stats={};outputs=[];exemplars={};all_hash=hashlib.sha256()
    report={'schema':'ring-review-probe-v1','task_id':TASK,'generator_sha256':digest(source),
            'probe_sha256':digest(__file__),'rule_sha256':hashlib.sha256(rule.encode()).hexdigest(),
            'seed_range_inclusive':[0,args.seeds-1],'sample_indices':list(range(args.indices)),
            'bands':BANDS,'phase':args.phase,'failures':failures}
    for band in BANDS:
        for seed in range(args.seeds):
            for index in range(args.indices):
                meta={'band':band,'seed':seed,'sample_index':index}
                try: grid=gen.generate(seed,index,difficulty=band)
                except Exception as e:
                    failures.append({**meta,'kind':'generation','error':repr(e)});continue
                records.append((meta,grid))
    with RacketBridge(timeout=30.0,max_calls_before_restart=256) as bridge:
        inputs=[g for _,g in records]
        for (meta,grid),answer in zip(records,racket_outputs(bridge,rule,inputs)):
            outputs.append(answer)
            all_hash.update(encoded([meta,grid,answer])+b'\n')
            band=meta['band'];b=stats.setdefault(band,{'draws':0,'unique_inputs':set(),
                'unique_outputs':set(),'shapes':Counter(),'changed_cells':Counter(),
                'rival_disagreements':Counter()})
            b['draws']+=1;b['unique_inputs'].add(encoded(grid));b['unique_outputs'].add(encoded(answer))
            b['shapes'][f'{len(grid)}x{len(grid[0])}']+=1
            if answer!=local_rule(grid):
                failures.append({**meta,'kind':'python_racket_parity','input':grid,'racket_output':answer,
                                 'python_output':local_rule(grid)})
            if gen.self_check(grid):
                failures.append({**meta,'kind':'self_check','input':grid,'errors':gen.self_check(grid)})
            b['changed_cells'][sum(x!=y for a,z in zip(grid,answer) for x,y in zip(a,z))]+=1
            for name,fn in RIVALS.items():
                rival=fn(grid)
                if rival!=answer:
                    b['rival_disagreements'][name]+=1
                    exemplars.setdefault(name,{**meta,'input':grid,'racket_output':answer,'rival_output':rival})
        report['corpus_sha256']=all_hash.hexdigest()
        report['generated_draws']=len(records)
        report['unique_inputs_global']=len({encoded(g) for _,g in records})
        # Every contiguous 3-demo + 1-query window inside each seed/band block.
        grouped={}
        for (meta,grid),answer in zip(records,outputs):
            grouped.setdefault((meta['band'],meta['seed']),{})[meta['sample_index']]=(grid,answer)
        windows=0;survival=Counter();ambiguous=Counter()
        for group in grouped.values():
            for begin in range(args.indices-3):
                if not all(i in group for i in range(begin,begin+4)):continue
                windows+=1
                for name,fn in RIVALS.items():
                    if all(fn(group[i][0])==group[i][1] for i in range(begin,begin+3)):
                        survival[name]+=1
                        q,a=group[begin+3]
                        if fn(q)!=a:ambiguous[name]+=1
        report['lesson_windows']={'denominator':windows,'overlapping':True,'demo_count':3,
            'surviving_rivals':{name:survival[name] for name in RIVALS},
            'surviving_and_wrong_on_query':{name:ambiguous[name] for name in RIVALS}}
        pairs=canonical['train']+([canonical['test']] if isinstance(canonical['test'],dict) else canonical['test'])
        canon_outputs=list(racket_outputs(bridge,rule,[p['input'] for p in pairs]))
        report['canonical']={'pairs':len(pairs),'racket_matches':sum(a==p['output'] for a,p in zip(canon_outputs,pairs)),
            'rival_matches':{name:sum(fn(p['input'])==p['output'] for p in pairs) for name,fn in RIVALS.items()}}
        if report['canonical']['racket_matches']!=len(pairs):
            failures.append({'kind':'canonical_parity'})
        if args.exhaustive_local:
            exhaustive=[ [list(flat[i:i+3]) for i in (0,3,6)]
                         for flat in itertools.product((0,1,2),repeat=9)]
            mismatches=0
            for idx,(grid,answer) in enumerate(zip(exhaustive,racket_outputs(bridge,rule,exhaustive,128))):
                if answer!=local_rule(grid):
                    mismatches+=1;failures.append({'kind':'exhaustive_local','index':idx,'input':grid,
                                                 'racket_output':answer,'python_output':local_rule(grid)})
            report['exhaustive_local']={'shape':[3,3],'alphabet':[0,1,2],
                'enumeration':'itertools.product((0,1,2), repeat=9), row-major',
                'denominator':len(exhaustive),'mismatches':mismatches}
            rng=random.Random(984241)
            fuzz=[]
            for i in range(300):
                h,w=rng.randint(1,25),rng.randint(1,25)
                g=[[rng.randrange(10) if rng.random()<0.6 else 0 for _ in range(w)] for _ in range(h)]
                if h>=3 and w>=3:
                    # Planted, overlapping/adjacent/damaged patches amid arbitrary noise.
                    for _ in range(1+i%4):
                        r,c=rng.randrange(h-2),rng.randrange(w-2);color=rng.randint(1,9)
                        for dr,dc in itertools.product(range(3),repeat=2):
                            g[r+dr][c+dc]=0 if (dr,dc)==(1,1) else color
                fuzz.append(g)
            count=0
            for idx,(grid,answer) in enumerate(zip(fuzz,racket_outputs(bridge,rule,fuzz))):
                if answer!=local_rule(grid):
                    count+=1;failures.append({'kind':'fuzz','index':idx,'input':grid,'racket_output':answer})
            report['off_distribution_fuzz']={'seed':984241,'denominator':300,'mismatches':count,
                'description':'1..25 rectangular grids, 0..9 noise, overlapping planted rings; not training draws'}
    for b in stats.values():
        b['unique_inputs']=len(b['unique_inputs']);b['unique_outputs']=len(b['unique_outputs'])
        b['rival_disagreements']={name:b['rival_disagreements'][name] for name in RIVALS}
    report['by_band']=stats
    report['duration_seconds']=time.monotonic()-start
    report['status']='PASS' if not failures else 'FAIL'
    (out/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (out/'counterexamples.json').write_text(json.dumps(exemplars,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ('status','phase','generator_sha256','generated_draws','unique_inputs_global','lesson_windows')},indent=2))
    return bool(failures)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seeds',type=int,default=100)
    p.add_argument('--indices',type=int,default=8)
    p.add_argument('--source')
    p.add_argument('--phase',default='final')
    p.add_argument('--exhaustive-local',action='store_true')
    p.add_argument('--out',required=True)
    args=p.parse_args()
    if args.seeds<1 or args.indices<4:p.error('--seeds >= 1 and --indices >= 4 are required')
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    # Use the project's real portable layout; rule_wrap needs scripts/, not
    # just shared/runtime on sys.path. This temporary copy is never returned.
    with tempfile.TemporaryDirectory(prefix='ring-review-probe-') as temporary:
        runtime = Path(temporary)
        prepare_runtime(Catalog(REPO), runtime, task_id=TASK)
        sys.path.insert(0, str(runtime))
        try:
            return run(args)
        finally:
            sys.path.remove(str(runtime))


if __name__=='__main__':
    raise SystemExit(main())
