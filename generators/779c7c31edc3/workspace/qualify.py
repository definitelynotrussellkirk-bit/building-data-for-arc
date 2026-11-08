#!/usr/bin/env python3
"""Measure the actual runner, not a synthetic stand-in for assembled lessons.

Example (packet root):
  python3 run_with_racket.py python3 generators/779c7c31edc3/workspace/qualify.py \
    --out ../checks/qualification-final.json
Use --generator ../.review/baseline/repo/generators/779c7c31edc3/generator.py
for a baseline comparison. Rivals always come from the selected final generator;
the measured generator and rival-source hashes are recorded separately.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile
from probe import ROOT, TASK, sha256

WORKER = r'''
from collections import Counter
import hashlib, importlib.util, json
from pathlib import Path
from puzzle_generators import runner
from scripts.canonical_profile_gate import canonical_pairs
from scripts.generator_semantic_gate import _lesson_plan

args=json.loads(Path('qualification-request.json').read_text())
task=args['task']
spec=importlib.util.spec_from_file_location('declared_rivals', 'review_rivals.py')
rivals_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(rivals_module)
rivals={**rivals_module.CANONICAL_SHORTCUTS, **rivals_module.LESSON_COMPETITORS}
bundle=runner._load_bundle(task)
module=bundle.generator_module
source_sha=hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
canonical=canonical_pairs(task)

def digest(g):return hashlib.sha256(json.dumps(g,separators=(',',':')).encode()).hexdigest()
def independent(g):
    out=[row[:] for row in g]
    for r in range(1,len(g)-1):
        for c in range(1,len(g[0])-1):
            x=g[r][c]
            if x and all(g[rr][cc]==x for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1))):out[r][c]=0
    return out

# Behavior-neutral instrumentation records attempts the runner normally hides.
original=module.generate
calls=[]
def traced(*a, **kw):
    try:g=original(*a,**kw)
    except Exception as exc:
        calls.append({'index':kw.get('sample_index'),'error':repr(exc)});raise
    calls.append({'index':kw.get('sample_index'),'input_sha256':digest(g)})
    return g
module.generate=traced
bridge,name=runner._open_bridge_with_rule(bundle.rule_callable_text)
result={'schema':'rectangle-review-qualification-v1','task_id':task,
        'generator_sha256':source_sha,'rival_source_sha256':args['rival_source_sha256'],
        'rule_text_sha256':args['rule_text_sha256'], 'phase':args['phase'],
        'sampler':'puzzle_generators.runner.run_one; shared bridge; n_train=3, n_test=1; trace-only generate wrapper',
        'canonical_pairs':len(canonical),'canonical_shortcuts':{},'bands':{},'counterexamples':{},'failures':[]}
for key, fn in rivals_module.CANONICAL_SHORTCUTS.items():
    result['canonical_shortcuts'][key]={'matches':sum(fn(p['input'])==p['output'] for p in canonical),'total':len(canonical)}
    if result['canonical_shortcuts'][key]['matches']!=len(canonical):result['failures'].append({'kind':'false_canonical_shortcut','name':key})
for band in ('easy','medium','hard'):
    result['bands'][band]={}
plans={
    'pinned':_lesson_plan(task,args['lessons_per_band']*3,bands=('easy','medium','hard'),pass_difficulty=True,legacy=False),
    'cyclic':[(band,seed,start,{'difficulty':band}) for band in ('easy','medium','hard')
              for seed in range(args['cyclic_seeds']) for start in range(len(rivals_module.SCHEDULE_PROFILES))]
}
try:
    for population,plan in plans.items():
        rows={}; unique={}; shapes={}; witnesses={}; records=[]
        for band in ('easy','medium','hard'):
            rows[band]=Counter();unique[band]=set();shapes[band]=set();witnesses[band]=Counter()
        for band,seed,start,axes in plan:
            counts=rows[band];counts['requested_lessons']+=1;calls.clear()
            try:episode=runner.run_one(task,seed,start,n_train=3,n_test=1,bundle=bundle,bridge=bridge,fn_name=name,**axes)
            except Exception as exc:
                result['failures'].append({'kind':'runner_error','population':population,'band':band,'seed':seed,'start':start,'exception':repr(exc),'calls':calls[:]})
                counts['runner_errors']+=1;continue
            counts['materialized_lessons']+=1
            counts['generation_attempts']+=len(calls)
            counts['unaccepted_attempts']+=len(calls)-4
            pp=episode['train']+episode['test']
            for pair in pp:
                g,y=pair['input'],pair['output'];unique[band].add(digest(g));shapes[band].add((len(g),len(g[0])))
                counts['pair_occurrences']+=1
                reasons=module.self_check(g)
                if reasons:result['failures'].append({'kind':'invalid_input','seed':seed,'start':start,'band':band,'input':g,'reasons':reasons})
                if independent(g)!=y:result['failures'].append({'kind':'racket_parity','seed':seed,'start':start,'band':band,'input':g,'actual_racket_output':y,'independent_output':independent(g)})
                counts['self_check_failures']+=bool(reasons)
                counts['oracle_mismatches']+=independent(g)!=y
                counts['nonidentity_pairs']+=g!=y
                for key,predicate in rivals_module.SEMANTIC_WITNESSES.items():
                    if predicate(g):
                        witnesses[band][key]+=1
                        if not any(rivals_module.SEMANTIC_RIVALS[r](g)!=y for r in rivals_module.WITNESS_RIVALS[key]):
                            result['failures'].append({'kind':'false_witness','witness':key,'input':g,'actual_racket_output':y})
                for key,fn in rivals.items():
                    prediction=fn(g)
                    if prediction!=y and key not in result['counterexamples']:
                        result['counterexamples'][key]={'task_id':task,'generator_sha256':source_sha,'rule_text_sha256':args['rule_text_sha256'],
                          'population':population,'band':band,'seed':seed,'lesson_start':start,'pair_index':pp.index(pair),
                          'generation_calls':calls[:],'validator_errors':reasons,'in_documented_domain':not bool(reasons),
                          'input':g,'actual_racket_output':y,'rival_output':prediction}
            survivors=[key for key,fn in rivals.items() if all(fn(p['input'])==p['output'] for p in episode['train'])]
            harmful=[key for key in survivors if any(rivals[key](p['input'])!=p['output'] for p in episode['test'])]
            counts['lessons_with_survivors']+=bool(survivors)
            counts['query_ambiguous_lessons']+=bool(harmful)
            for key in survivors:counts['surviving:'+key]+=1
            for key in harmful:counts['harmful:'+key]+=1
            if survivors and len([x for x in records if x.get('survivors')])<6:
                records.append({'band':band,'seed':seed,'start':start,'survivors':survivors,'wrong_on_query':harmful})
        result[population+'_examples']=records
        for band in rows:
            result['bands'][band][population]={**dict(rows[band]),'unique_inputs':len(unique[band]),'distinct_shapes':len(shapes[band]),'witness_pair_occurrences':dict(witnesses[band])}
    result['cyclic_policy']={'seeds':list(range(args['cyclic_seeds'])),'starts':list(range(len(rivals_module.SCHEDULE_PROFILES))),
                            'note':'All schedule starts, same seed per three overlapping windows; do not add unique-input counts across populations or bands.'}
    result['pinned_policy']={'seed_function':'scripts.canonical_profile_gate._pinned_seed(task, "lesson:"+band, k)',
                            'k_range':[0,args['lessons_per_band']-1],'start':'k * 11','lessons_per_band':args['lessons_per_band']}
finally:bridge.close()
result['passed']=not result['failures'] and not any(p['lessons_with_survivors'] for b in result['bands'].values() for p in b.values())
print(json.dumps(result))
'''


def main():
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    from probe import canonical
    import hashlib
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--generator',type=Path)
    parser.add_argument('--lessons-per-band',type=int,default=100)
    parser.add_argument('--cyclic-seeds',type=int,default=40)
    args=parser.parse_args()
    if args.lessons_per_band<1 or args.cyclic_seeds<1:parser.error('counts must be positive')
    current=ROOT/f'generators/{TASK}/generator.py'
    selected=(args.generator or current).resolve()
    with tempfile.TemporaryDirectory(prefix=f'{TASK}-qualification-') as directory:
        stage=Path(directory); prepare_runtime(Catalog(ROOT),stage,TASK)
        shutil.copy2(selected,stage/f'puzzle_generators/per_puzzle/{TASK}/generator.py')
        shutil.copy2(current,stage/'review_rivals.py')
        request={'task':TASK,'rival_source_sha256':sha256(current),
                 'rule_text_sha256':hashlib.sha256(canonical()['program_solution'].encode()).hexdigest(),
                 'phase':'before' if args.generator else 'final', 'lessons_per_band':args.lessons_per_band,'cyclic_seeds':args.cyclic_seeds}
        (stage/'qualification-request.json').write_text(json.dumps(request))
        (stage/'qualification_worker.py').write_text(WORKER)
        run=run_process([sys.executable,'-B','qualification_worker.py'],stage,timeout=600)
        if run['exit_code'] or run['timed_out']:
            result={'passed':False,'worker_failure':run,'generator_sha256':sha256(selected)}
        else:
            result=json.loads(run['stdout']); result['runtime_directory']=str(stage)
            result['worker_exit_code']=run['exit_code']
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result.get(key) for key in ('passed','generator_sha256','bands')},indent=2))
    return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
