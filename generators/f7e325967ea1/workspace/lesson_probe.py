"""Source-bound finite-rival lesson audit using the actual production runner.

Reusable for any per-puzzle generator declaring CANONICAL_SHORTCUTS and
LESSON_COMPETITORS. It copies a fresh standalone runtime, executes the canonical
Racket rule, checks every declared canonical shortcut, records actual input
uniqueness and all failures, and never substitutes Python for reference labels.
"""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import replace
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import shutil
import sys
import tempfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(grid):
    return sha(json.dumps(grid,separators=(',',':')).encode())


def worker(args):
    from puzzle_generators import runner
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source, normalized_rule_hash
    bundle=runner._load_bundle(args.task)
    source=canonical_rule_source(args.task)
    bundle=replace(bundle,rule_source=source,rule_callable_text=runner.wrap_rule(source),
                   rule_file='data/canonical/puzzles.jsonl#'+args.task)
    gen=bundle.generator_module
    generator_path=Path(gen.__file__)
    competitors=dict(getattr(gen,'LESSON_COMPETITORS',{}))
    competitors.update(getattr(gen,'CANONICAL_SHORTCUTS',{}))
    if not competitors:
        raise ValueError('No declared finite-rival set; this is not a semantic certification')
    shortcuts=dict(getattr(gen,'CANONICAL_SHORTCUTS',{}))
    pairs=canonical_pairs(args.task)
    pairs=[p for p in pairs if p.get('input') and p.get('output')]
    report={'schema':'finite-rival-lesson-probe-v1','task_id':args.task,
            'generator_sha256':sha(generator_path.read_bytes()),
            'canonical_rule_sha256':sha(source.encode()),'rule_hash':normalized_rule_hash(source),
            'probe_sha256':sha(Path(__file__).read_bytes()),'runtime_cwd':str(Path.cwd()),
            'sampler':'puzzle_generators.runner.run_one, n_train=3, n_test=1; normal validity and duplicate rejection',
            'seed_plan':{'first':20261002,'count_per_band':args.lessons_per_band,
                         'sample_index':'12 * lesson_index + lesson_index % 3','bands':['easy','medium','hard']},
            'scope':'Finite declared rivals only; not universal induction or training approval.',
            'canonical_pairs':len(pairs),'competitors':sorted(competitors),
            'canonical_shortcut_fit':{},'failures':[],'runs':{},'counterexample':None,
            'baseline_teaching_negatives':[],
            'negative_intent':'Named-rival diagnostic counterexamples, NOT natural model failures or captured model traces'}
    for name,fn in shortcuts.items():
        matches=sum(fn(p['input'])==p['output'] for p in pairs)
        report['canonical_shortcut_fit'][name]={'matches':matches,'denominator':len(pairs)}
        if not pairs or matches!=len(pairs):
            report['failures'].append({'type':'false_canonical_shortcut_claim','rival':name})
    bridge,fn_name=runner._open_bridge_with_rule(bundle.rule_callable_text)
    try:
        # Canonical data itself is checked against real execution, not only the mirror.
        for index,p in enumerate(pairs):
            actual=runner._apply_rule(bridge,fn_name,p['input'])
            if actual!=p['output']:
                report['failures'].append({'type':'canonical_authority_mismatch','index':index,'pair':p,'racket':actual})
        modules=[('final',gen,bundle)]
        if args.baseline:
            spec=importlib.util.spec_from_file_location('retained_baseline',args.baseline)
            base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
            modules.append(('baseline',base,replace(bundle,generator_module=base)))
        for phase,module,current_bundle in modules:
            all_unique=set();bands={}
            for band in ('easy','medium','hard'):
                unique=set();survivors=Counter();wrong_queries=Counter();disagreements=Counter()
                starts=Counter();materialized=0;observations=0;validator_errors=0;mirror_errors=0;hook_errors=0
                for i in range(args.lessons_per_band):
                    seed=20261002+i;start=12*i+i%3;starts[start%3]+=1
                    try:
                        lesson=runner.run_one(args.task,seed,start,n_train=3,n_test=1,difficulty=band,
                                             bundle=current_bundle,bridge=bridge,fn_name=fn_name)
                        materialized+=1
                        all_pairs=lesson['train']+lesson['test']
                        for p in all_pairs:
                            g,y=p['input'],p['output'];observations+=1
                            unique.add(fingerprint(g));all_unique.add(fingerprint(g))
                            errors=module.self_check(g) if callable(getattr(module,'self_check',None)) else []
                            if errors:
                                validator_errors+=1
                                report['failures'].append({'type':'validator','phase':phase,'band':band,'seed':seed,'start':start,'errors':errors,'pair':p})
                            if phase=='final' and callable(getattr(module,'_snapshot',None)) and module._snapshot(g)!=y:
                                mirror_errors+=1
                                report['failures'].append({'type':'mirror_parity','band':band,'seed':seed,'start':start,'pair':p})
                            mismatches={name:fn(g) for name,fn in competitors.items() if fn(g)!=y}
                            disagreements.update(mismatches.keys())
                            if phase=='final' and report['counterexample'] is None and len(mismatches)==len(competitors):
                                report['counterexample']={'band':band,'seed':seed,'lesson_start':start,
                                    'input':g,'racket_output':y,'rival_outputs':mismatches,
                                    'validator_errors':errors,'input_sha256':fingerprint(g)}
                        for name,fn in competitors.items():
                            if all(fn(p['input'])==p['output'] for p in lesson['train']):
                                survivors[name]+=1
                                if fn(lesson['test'][0]['input'])!=lesson['test'][0]['output']:
                                    wrong_queries[name]+=1
                                    if phase=='baseline':
                                        report['baseline_teaching_negatives'].append({
                                            'intent':'teaching_negative','phase':phase,'band':band,'seed':seed,'start':start,
                                            'rival':name,'lesson':lesson,
                                            'rival_query_output':fn(lesson['test'][0]['input'])})
                                if phase=='final':
                                    report['failures'].append({'type':'rival_survived','band':band,'seed':seed,'start':start,'rival':name,'lesson':lesson})
                        hook=getattr(module,'lesson_identifiable',None)
                        if callable(hook):
                            reasons=hook(lesson['train'],lesson['test'][0])
                            if reasons:
                                hook_errors+=1
                                report['failures'].append({'type':'lesson_hook','phase':phase,'band':band,'seed':seed,'start':start,'reasons':reasons})
                    except Exception as exc:
                        report['failures'].append({'type':'exception','phase':phase,'band':band,'seed':seed,'start':start,'error':repr(exc)})
                bands[band]={'lessons':materialized,'requested':args.lessons_per_band,
                    'start_residues':dict(starts),'input_observations':observations,'unique_inputs':len(unique),
                    'surviving_demo_lessons':{n:survivors[n] for n in competitors},
                    'survives_demos_wrong_query':{n:wrong_queries[n] for n in competitors},
                    'disagreeing_input_observations':{n:disagreements[n] for n in competitors},
                    'validator_available':callable(getattr(module,'self_check',None)),
                    'mirror_available':phase=='final' and callable(getattr(module,'_snapshot',None)),
                    'validator_errors':validator_errors,'mirror_errors':mirror_errors,'hook_errors':hook_errors}
            report['runs'][phase]={'generator_sha256':sha(Path(module.__file__).read_bytes()),
                                   'unique_inputs_across_bands':len(all_unique),'bands':bands}
        if args.stress:
            if args.task!='f7e325967ea1':raise ValueError('--stress is task-specific; omit for another task')
            count=0;reference_checks=0;failures=[]
            for h,w,n,band,start,seed in itertools.product((7,18),(7,18),range(3,10),(None,'easy','medium','hard'),range(3),range(10)):
                overrides={'grid_h':h,'grid_w':w,'n_distinct_colors':n}
                try:
                    g=gen.generate(seed,start,difficulty=band,**overrides);count+=1
                    errors=gen.self_check(g)
                    if errors or gen.observe_overrides(g)!=overrides:
                        failures.append({'seed':seed,'start':start,'band':band,'overrides':overrides,'input':g,'errors':errors})
                    if gen.schedule_profile(seed,start,band)=='counterexample':
                        y=runner._apply_rule(bridge,fn_name,g);reference_checks+=1
                        bad=[name for name,fn in competitors.items() if fn(g)==y]
                        if bad:failures.append({'seed':seed,'start':start,'band':band,'overrides':overrides,'survivors':bad,'input':g,'output':y})
                except Exception as exc:
                    failures.append({'seed':seed,'start':start,'band':band,'overrides':overrides,'error':repr(exc)})
            report['override_stress']={'generated':count,'planned':3360,'seeds':list(range(10)),
                                      'dimensions':[7,18],'foreground_colors':list(range(3,10)),
                                      'racket_counterexample_checks':reference_checks,'failures':failures}
            report['failures'].extend(failures)
    finally:
        bridge.close()
    report['passed']=not report['failures']
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'failures':len(report['failures']),
                      'lessons_per_band':args.lessons_per_band,'generator_sha256':report['generator_sha256']}))
    return 0 if report['passed'] else 1


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--task',default='f7e325967ea1')
    ap.add_argument('--lessons-per-band',type=int,default=120)
    ap.add_argument('--baseline',type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--stress',action='store_true')
    ap.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=ap.parse_args()
    if args.lessons_per_band<1:ap.error('--lessons-per-band must be positive')
    if args.worker:return worker(args)
    root=Path(__file__).resolve().parents[3]
    sys.path.insert(0,str(root/'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime,run_process
    args.out=args.out.resolve();args.out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='diagonal-lesson-probe-') as directory:
        stage=Path(directory)
        prepare_runtime(Catalog(root),stage,args.task)
        shutil.copy2(__file__,stage/'lesson_probe.py')
        argv=[sys.executable,'-B','lesson_probe.py','--worker','--task',args.task,
              '--lessons-per-band',str(args.lessons_per_band),'--out','report.json']
        if args.baseline:
            shutil.copy2(args.baseline.resolve(),stage/'baseline_generator.py')
            argv+=['--baseline','baseline_generator.py']
        if args.stress:argv+=['--stress']
        run=run_process(argv,stage,timeout=480)
        receipt={'runtime_cwd':str(stage),'runtime_manifest_sha256':sha((stage/'RUNTIME_MANIFEST.json').read_bytes()),
                 'execution':run,'reference':'canonical Racket via runner; no Python label fallback'}
        args.out.with_suffix('.execution.json').write_text(json.dumps(receipt,indent=2)+'\n')
        if (stage/'report.json').exists():shutil.copy2(stage/'report.json',args.out)
        else:args.out.write_text(json.dumps({'passed':False,'failure':'worker produced no report','execution':run},indent=2)+'\n')
        print(run['stdout']);print(run['stderr'],file=sys.stderr)
        return run['exit_code'] if not run['timed_out'] else 124

if __name__=='__main__':raise SystemExit(main())
