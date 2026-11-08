#!/usr/bin/env python3
"""Source-bound Racket curriculum census, baseline comparison and cyclic lessons.

Run from the packet root:
 python3 run_with_racket.py python3 generators/0f26224a6da3/workspace/probe_curriculum.py \
   --out ../checks/curriculum.json --baseline ../checks/baseline_generator.py

The launcher copies an official isolated runtime, this probe, and optional baseline
source into a fresh /tmp directory, then runs there with PYTHONPATH removed.
Only JSON evidence is retained; no installed runtime is included in returns.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

TASK = '0f26224a6da3'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def fingerprint(grid):
    return sha(json.dumps(grid,separators=(',',':')).encode())

def worker(args):
    from puzzle_generators import runner
    mod=importlib.import_module(f'puzzle_generators.per_puzzle.{TASK}.generator')
    task=next(json.loads(line) for line in Path('data/canonical/puzzles.jsonl').read_text().splitlines()
              if json.loads(line)['task_id']==TASK)
    canonical=task['train']+task['test']
    rule=task['program_solution']
    bridge,fn=runner._open_bridge_with_rule(runner.wrap_rule(rule))
    cache={}
    failures=[]
    def actual(grid):
        key=fingerprint(grid)
        if key not in cache:
            cache[key]=runner._apply_rule(bridge,fn,grid)
        return cache[key]
    result={'schema':'isolated-singleton-curriculum-v1','task_id':TASK,
            'runtime_directory':str(Path.cwd()),'runtime_generator':str(Path(mod.__file__).resolve()),
            'generator_sha256':sha(Path(mod.__file__).read_bytes()),
            'canonical_rule_sha256':sha(rule.encode()),
            'census':{'seeds':list(range(args.seeds)),'sample_indices':list(range(9)),
                      'bands':[None,'easy','medium','hard']},
            'lesson_policy':{'demo_count':3,'query_count':1,'same_seed':True,
                             'start_indices':list(range(6)), 'cyclic_residues':[0,1,2],
                             'note':'Consecutive indices; lesson windows overlap. Counts are not independent trials.'},
            'canonical_checks':{},'populations':{},'counterexamples':{},'failures':failures}
    try:
        for name,rival in mod.CANONICAL_SHORTCUTS.items():
            hits=sum(rival(p['input'])==p['output'] for p in canonical)
            result['canonical_checks'][name]={'matches':hits,'pairs':len(canonical)}
            if hits!=len(canonical):failures.append({'kind':'false_canonical_shortcut','rival':name})
        for i,p in enumerate(canonical):
            if actual(p['input'])!=p['output']:failures.append({'kind':'canonical_label_mismatch','pair':i})
        populations=[('final',mod)]
        if args.baseline:
            spec=importlib.util.spec_from_file_location('baseline',args.baseline)
            old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
            populations.append(('before',old))
        for label,source in populations:
            counts=Counter();unique=set();residues=set();colors=set();pairs={};per_band={}
            examples={}
            for band in [None,'easy','medium','hard']:
                band_count=Counter()
                for seed in range(args.seeds):
                    for index in range(9):
                        grid=source.generate(seed,index,difficulty=band)
                        output=actual(grid)
                        pairs[(band,seed,index)]={'input':grid,'output':output}
                        counts['draws']+=1;band_count['draws']+=1;unique.add(fingerprint(grid))
                        active=mod._sources(grid);h,w=len(grid),len(grid[0])
                        residues.update((r%3,c%3) for r,c in active)
                        colors.update(v for row in grid for v in row if v)
                        features={
                            'valid_by_own_validator':source.self_check(grid)==[],
                            'valid_by_final_validator':mod.self_check(grid)==[],
                            'canonical_like':mod.strict_canonical_like(grid)==[],
                            'border_source':any(r in (0,h-1) or c in (0,w-1) for r,c in active),
                            'corner_source':any(r in (0,h-1) and c in (0,w-1) for r,c in active),
                            'off_old_lattice':any(r%3!=1 or c%3!=1 for r,c in active),
                            'inert_foreground':sum(v!=0 for row in grid for v in row)>len(active),
                            'python_mirror_matches_racket':mod.rule_mirror(grid)==output,
                        }
                        for k,v in features.items():
                            counts[k]+=int(v);band_count[k]+=int(v)
                        if label=='final' and not all(features[k] for k in ('valid_by_own_validator','python_mirror_matches_racket')):
                            failures.append({'kind':'final_pair_failure','band':band,'seed':seed,'index':index,'input':grid,'output':output})
                        for name,rival in mod.LESSON_COMPETITORS.items():
                            disagree=rival(grid)!=output
                            counts[f'refutes:{name}']+=int(disagree);band_count[f'refutes:{name}']+=int(disagree)
                            if disagree and name not in examples:
                                examples[name]={'task_id':TASK,'seed':seed,'sample_index':index,'difficulty':band,
                                                'input':grid,'racket_output':output,'rival_output':rival(grid),
                                                'validator_errors':source.self_check(grid)}
                per_band[str(band)]=dict(band_count)
            survivors=Counter();bad_lessons=[];lesson_count=0
            for band in [None,'easy','medium','hard']:
                for seed in range(args.seeds):
                    for start in range(6):
                        demos=[pairs[(band,seed,start+i)] for i in range(3)]
                        query=pairs[(band,seed,start+3)]
                        lesson_count+=1
                        remaining=[name for name,rival in mod.LESSON_COMPETITORS.items()
                                   if all(rival(p['input'])==p['output'] for p in demos)]
                        survivors.update(remaining)
                        if remaining:
                            bad_lessons.append({'band':band,'seed':seed,'start':start,'survivors':remaining})
                        if label=='final' and mod.lesson_identifiable(demos,query):
                            failures.append({'kind':'final_lesson_not_identifiable','band':band,'seed':seed,'start':start})
            result['populations'][label]={
                'generator_sha256':sha(Path(source.__file__).read_bytes()),'counts':dict(counts),
                'unique_input_count':len(unique),'active_modulo3_residues':sorted(residues),
                'foreground_colors':sorted(colors),'per_band':per_band,'lesson_count':lesson_count,
                'lessons_with_surviving_rivals':len(bad_lessons),'rival_survival_lesson_counts':dict(survivors),
                'failed_lesson_records':bad_lessons}
            result['counterexamples'][label]=examples
        result['racket_unique_input_executions']=len(cache)
        # Explicit collision diagnostic: valid in baseline self_check, excluded
        # from final helpful data; both ordering policies are shown, not learned.
        g=[[0]*7 for _ in range(7)];g[2][2]=2;g[2][4]=3
        result['collision_diagnostic']={'input':g,'racket_output':actual(g),
                                       'final_validator_errors':mod.self_check(g)}
    finally:
        bridge.shutdown()
    Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'output':str(args.out),'failures':len(failures),
                      'populations':{k:{'draws':v['counts']['draws'],'unique_inputs':v['unique_input_count'],
                                         'lessons':v['lesson_count'],'ambiguous':v['lessons_with_surviving_rivals']}
                                     for k,v in result['populations'].items()}},indent=2))
    return int(bool(failures))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--seeds',type=int,default=10)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.seeds<1:parser.error('--seeds must be positive')
    if args.worker:return worker(args)
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    repo=Path(__file__).resolve().parents[3]
    out=args.out.resolve();out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():raise FileExistsError(out)
    baseline=args.baseline.resolve() if args.baseline else None
    with tempfile.TemporaryDirectory(prefix='singletons-curriculum-') as folder:
        runtime=Path(folder)
        prepare_runtime(Catalog(repo),runtime,task_id=TASK)
        shutil.copy2(__file__,runtime/'probe.py')
        command=[sys.executable,'probe.py','--worker','--out',str(out),'--seeds',str(args.seeds)]
        if baseline:
            shutil.copy2(baseline,runtime/'baseline.py');command.extend(['--baseline','baseline.py'])
        env=dict(os.environ);env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
        return subprocess.run(command,cwd=runtime,env=env,timeout=240).returncode

if __name__=='__main__':
    raise SystemExit(main())
