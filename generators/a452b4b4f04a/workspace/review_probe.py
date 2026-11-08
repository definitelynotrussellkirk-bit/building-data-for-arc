#!/usr/bin/env python3
"""Source-bound Racket census and actual-runner lesson audit.

From the repository: python generators/a452b4b4f04a/workspace/review_probe.py
  --per-band 600 --lessons 100 --cycles 20 --out ../checks/qualification.json
Requires the packet's run_with_racket.py wrapper (or a local Racket installation).
Builds a disposable standalone runtime, uses the repository's pinned seeds and
real lesson assembler, and fails nonzero on any observed discrepancy. It never
uses a Python output implementation to label training data.
"""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
from itertools import product
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

TASK='a452b4b4f04a'
BANDS=('easy','medium','hard')


def digest(value):
    return hashlib.sha256(json.dumps(value,separators=(',',':'),sort_keys=True).encode()).hexdigest()


def geometry(grid):
    """Independent audit calculation, never the authoritative returned label."""
    groups={}
    for r,row in enumerate(grid):
        for c,color in enumerate(row):
            if color:groups.setdefault(color,[]).append((r,c))
    out=[[0]*len(grid[0]) for _ in grid]
    for color,coords in groups.items():
        rs,cs=zip(*coords); a,b,x,y=min(rs),max(rs),min(cs),max(cs)
        for r in range(a,b+1):out[r][x]=out[r][y]=color
        for c in range(x,y+1):out[a][c]=out[b][c]=color
    return out


def run_worker(args):
    import importlib
    from puzzle_generators import runner
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source, normalized_rule_hash, _pinned_seed
    from scripts.generator_semantic_gate import evaluate_competitors

    gen=importlib.import_module(f'puzzle_generators.per_puzzle.{TASK}.generator')
    source=Path(gen.__file__)
    program=canonical_rule_source(TASK)
    bundle=runner._load_bundle(TASK)
    if bundle.rule_source != program:
        raise RuntimeError('Actual runner authority is not byte-identical to canonical')
    bridge,fn=runner._open_bridge_with_rule(bundle.rule_callable_text)
    report={
        'schema':'bbox-qualification-v1','task_id':TASK,
        'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'census_policy':{'bands':list(BANDS),'draws_per_band':args.per_band,
                         'index_range':[0,args.per_band-1],
                         'seed':'canonical_profile_gate._pinned_seed(task, band, i)',
                         'sample_index':'seed % 7919 + i','overrides':{}},
        'generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'rule_hash':normalized_rule_hash(program),'rule_source_sha256':hashlib.sha256(program.encode()).hexdigest(),
        'runtime_cwd':str(Path.cwd()),'label_authority':'selected canonical Racket, via real runner',
        'lesson_policy':{'demos':gen.EXAMPLES_NEEDED,'queries':1,'standard_lessons_per_band':args.lessons,
                         'seed':'canonical_profile_gate._pinned_seed(task, lesson:band, i)',
                         'sample_index':'11*i','cycles_seeds':f'0..{args.cycles-1}',
                         'cycle_starts':list(range(len(gen.SCHEDULE_PROFILES))),
                         'all_cyclic_starts_checked':True,
                         'default_only':'Exact overrides supersede the scheduled teaching contract.'},
        'failures':[],'per_band':{},'canonical':{},'witness_examples':{},'lessons':[],
    }
    failures=report['failures']; cache={}; authority_calls=0
    def output(g):
        nonlocal authority_calls
        key=digest(g)
        if key not in cache:
            cache[key]=runner._apply_rule(bridge,fn,g);authority_calls+=1
        return cache[key]
    def check_grid(g,where):
        issues=gen.self_check(g)
        if issues:failures.append({'kind':'domain','where':where,'issues':issues,'input':g})
        truth=output(g)
        if truth!=geometry(g):failures.append({'kind':'racket_geometry_mismatch','where':where,'input':g,'racket_output':truth,'python_audit_output':geometry(g)})
        return truth
    try:
        canon=canonical_pairs(TASK)
        report['canonical']['pairs']=len(canon)
        report['canonical']['shortcut_matches']={}
        for i,pair in enumerate(canon):
            truth=check_grid(pair['input'],{'canonical_index':i})
            if truth!=pair['output']:failures.append({'kind':'canonical_label_mismatch','index':i})
            if gen.strict_canonical_like(pair['input']):failures.append({'kind':'canonical_strict_rejection','index':i})
        if not canon:failures.append({'kind':'missing_canonical_pairs'})
        for name,rival in gen.CANONICAL_SHORTCUTS.items():
            hits=sum(rival(deepcopy(p['input']))==p['output'] for p in canon)
            report['canonical']['shortcut_matches'][name]={'matches':hits,'denominator':len(canon)}
            if hits!=len(canon):failures.append({'kind':'misdeclared_canonical_shortcut','name':name})
        all_inputs=set()
        for band in BANDS:
            unique=set();colors=set();profiles=Counter();shapes=Counter();strict=0
            witness_hits=Counter();witness_refuted=Counter();rival_diff=Counter()
            for i in range(args.per_band):
                seed=_pinned_seed(TASK,band,i);si=seed%7919+i
                loc={'band':band,'seed':seed,'sample_index':si,'census_index':i,'overrides':{}}
                g=gen.generate(seed,si,difficulty=band)
                truth=check_grid(g,loc)
                if g!=gen.generate(seed,si,difficulty=band):failures.append({'kind':'nondeterminism','where':loc})
                unique.add(digest(g));all_inputs.add(digest(g));colors.update(v for row in g for v in row if v)
                profiles[gen.schedule_profile(seed,si,band)]+=1
                shapes[f'{len(g)}x{len(g[0])}']+=1
                strict += not bool(gen.strict_canonical_like(g))
                for name,rival in gen.SEMANTIC_RIVALS.items():
                    wrong=rival(deepcopy(g))
                    if wrong!=truth:
                        rival_diff[name]+=1
                        if name not in report['witness_examples']:
                            report['witness_examples'][name]={**loc,'validator_accepts':not bool(gen.self_check(g)),
                                'inside_documented_domain':True,'input':g,'actual_racket_output':truth,'rival_output':wrong,
                                'generator_sha256':report['generator_sha256'],'rule_hash':report['rule_hash']}
                for name,predicate in gen.SEMANTIC_WITNESSES.items():
                    if predicate(deepcopy(g)):
                        witness_hits[name]+=1
                        names=gen.WITNESS_RIVALS.get(name,[])
                        refuted=any(gen.SEMANTIC_RIVALS[n](deepcopy(g))!=truth for n in names)
                        witness_refuted[name]+=refuted
                        if not refuted:failures.append({'kind':'false_witness_claim','name':name,'where':loc})
            if strict/args.per_band < gen.MIN_STRICT_FRAC:failures.append({'kind':'strict_floor','band':band,'hits':strict,'draws':args.per_band})
            report['per_band'][band]={'draws':args.per_band,'unique_inputs':len(unique),'strict_hits':strict,
                'strict_fraction':strict/args.per_band,'colors':sorted(colors),'schedule_profiles':dict(profiles),
                'shape_count':len(shapes),'witness_hits':dict(witness_hits),'verified_witness_refutations':dict(witness_refuted),
                'rival_disagreements':dict(rival_diff)}
            print(f'{band}: {args.per_band} Racket census cases; strict={strict}',flush=True)
        report['census_unique_inputs']=len(all_inputs)
        # Reference parity at the exact-control boundary, in all bands.
        exact_count=0
        for band,h,w,n,k in product(BANDS,(6,8,20),(6,8,20),(1,2,3),(2,3,4)):
            overrides=dict(grid_h=h,grid_w=w,n_colors=n,corner_count=k)
            g=gen.generate(991,exact_count,difficulty=band,**overrides)
            check_grid(g,{'band':band,'seed':991,'sample_index':exact_count,'overrides':overrides})
            if gen.observe_overrides(g)!=overrides:failures.append({'kind':'override_mismatch','request':overrides,'input':g})
            exact_count+=1
        report['racket_exact_control_cases']=exact_count
        lesson_inputs={'standard':set(),'cyclic':set()}; uses=Counter();summary={}
        competitors=dict(gen.LESSON_COMPETITORS)
        competitors.update(gen.CANONICAL_SHORTCUTS)
        for band in BANDS:
            for population,plan in (
                ('standard',[(_pinned_seed(TASK,f'lesson:{band}',i),11*i) for i in range(args.lessons)]),
                ('cyclic',list(product(range(args.cycles),range(len(gen.SCHEDULE_PROFILES)))))):
                ss={'lessons':0,'refuted':{n:0 for n in competitors},'survived_demos':{n:0 for n in competitors},
                    'query_discriminates':{n:0 for n in competitors},'assembler_index_drift':0}
                for seed,start in plan:
                    inst=runner.run_one(TASK,seed=seed,sample_index=start,n_train=gen.EXAMPLES_NEEDED,n_test=1,
                                        bundle=bundle,bridge=bridge,fn_name=fn,difficulty=band)
                    pair_list=inst['train']+inst['test'];ss['lessons']+=1
                    for i,p in enumerate(pair_list):
                        lesson_inputs[population].add(digest(p['input']));uses[population]+=1
                        if p['input']!=gen.generate(seed,start+i,difficulty=band):
                            ss['assembler_index_drift']+=1
                            failures.append({'kind':'assembler_index_drift','band':band,'seed':seed,'start':start,'pair':i})
                        if p['output']!=geometry(p['input']):failures.append({'kind':'lesson_label_mismatch','band':band,'seed':seed,'start':start})
                    lesson={'demos':inst['train'],'query':inst['test'][0]}
                    score=evaluate_competitors(competitors,lesson)
                    reasons=gen.lesson_identifiable(inst['train'],{'input':inst['test'][0]['input']})
                    if reasons or score['errors'] or score['survived_demos']:
                        failures.append({'kind':'lesson_rival_failure','band':band,'seed':seed,'start':start,
                                         'population':population,'reasons':reasons,'score':score,'lesson':lesson})
                    for category in ('refuted','survived_demos','query_discriminates'):
                        for name in score[category]:ss[category][name]+=1
                    report['lessons'].append({'population':population,'band':band,'seed':seed,'sample_index':start,
                        'pair_input_sha256':[digest(p['input']) for p in pair_list],
                        'pair_output_sha256':[digest(p['output']) for p in pair_list],
                        'refuted':score['refuted'],'survived_demos':score['survived_demos']})
                summary[f'{population}:{band}']=ss
                print(f'{population}:{band}: {ss["lessons"]} real-runner lessons',flush=True)
        report['lesson_summary']=summary
        report['lesson_pair_uses']=dict(uses)
        report['lesson_unique_inputs']={k:len(v) for k,v in lesson_inputs.items()}
        report['lesson_overlap_inputs']=len(lesson_inputs['standard'] & lesson_inputs['cyclic'])
        report['direct_cached_racket_calls']=authority_calls
        report['actual_runner_racket_pair_calls']=sum(uses.values())
        report['passed']=not failures
        return report
    finally:
        bridge.close()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--per-band',type=int,default=600)
    ap.add_argument('--lessons',type=int,default=100,help='Per band, not total')
    ap.add_argument('--cycles',type=int,default=20)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=ap.parse_args()
    if min(args.per_band,args.lessons,args.cycles)<1:ap.error('Counts must be positive')
    out=args.out.resolve();out.parent.mkdir(parents=True,exist_ok=True)
    if args.worker:
        report=run_worker(args)
        out.write_text(json.dumps(report,indent=2)+'\n')
        return 0 if report['passed'] else 1
    root=Path(__file__).resolve().parents[3]
    sys.path.insert(0,str(root/'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    started=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='bbox-relocated-probe-') as tmp:
        runtime=Path(tmp)
        prepare_runtime(Catalog(root),runtime,TASK)
        shutil.copy2(__file__,runtime/'review_probe.py')
        command=[sys.executable,'-B','review_probe.py','--worker','--per-band',str(args.per_band),
                 '--lessons',str(args.lessons),'--cycles',str(args.cycles),'--out','result.json']
        run=run_process(command,runtime,timeout=600,on_output=lambda x:print(x,end='',flush=True))
        if not (runtime/'result.json').exists():
            out.write_text(json.dumps({'passed':False,'worker_failure':run,'runtime_cwd':str(runtime)},indent=2)+'\n')
            return 1
        report=json.loads((runtime/'result.json').read_text())
        report['worker_command']=command;report['worker_exit_code']=run['exit_code'];report['worker_timed_out']=run['timed_out']
        report['seconds']=round(time.monotonic()-started,3)
        report['passed']=report['passed'] and run['exit_code']==0 and not run['timed_out']
        out.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:report[k] for k in ('passed','generator_sha256','seconds')}))
        return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
