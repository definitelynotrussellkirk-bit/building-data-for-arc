#!/usr/bin/env python3
"""Reproduce two source-bound adversarial audits without changing their sources.

Uses a disposable relocated runtime and the canonical Racket authority. The
shape-table rival is intentionally wrong outside a small generator's support;
it is diagnostic code, not a training labeler or proposed inference solution.
"""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib
from itertools import product
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

TASKS=('252c3df06496','2e5c98d98eed')
BANDS=('easy','medium','hard')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def first_nonzero_rival(grid):
    """Wrong: use a row's leftmost nonzero cell, not specifically column zero."""
    return [[next((v for v in row if v),0)]*len(row) for row in grid]


def frame_table_rival(grid,table):
    """Wrong: infer the frame coordinates from canvas dimensions, ignoring 8s."""
    top,left,height,width=table[(len(grid),len(grid[0]))]
    color=next(v for row in grid for v in row if v not in (0,8))
    out=deepcopy(grid)
    for r in range(top+1,top+height-1):
        for c in range(left+1,left+width-1):out[r][c]=color
    return out


def worker(args):
    from puzzle_generators import runner
    from scripts.canonical_profile_gate import canonical_pairs,canonical_rule_source,normalized_rule_hash,_pinned_seed
    reports={}
    for task in TASKS:
        gen=importlib.import_module(f'puzzle_generators.per_puzzle.{task}.generator')
        source=Path(gen.__file__);program=canonical_rule_source(task)
        bridge,fn=runner._open_bridge_with_rule(runner.wrap_rule(program))
        failures=[];cache={};counts=Counter();unique=set()
        def actual(grid):
            key=digest(grid)
            if key not in cache:cache[key]=runner._apply_rule(bridge,fn,grid)
            return cache[key]
        base={'task_id':task,'generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
              'rule_hash':normalized_rule_hash(program),'canonical_rule_sha256':hashlib.sha256(program.encode()).hexdigest(),
              'runtime_cwd':str(Path.cwd()),'label_authority':'canonical Racket through persistent bridge',
              'target_sources_changed':False,'failures':failures}
        try:
            canon=canonical_pairs(task)
            if task==TASKS[0]:
                rival=first_nonzero_rival
                for band in BANDS:
                    for i in range(args.per_band):
                        seed=_pinned_seed(task,band,i);si=seed%7919+i
                        g=gen.generate(seed,si,difficulty=band)
                        unique.add(digest(g));counts['default_case_uses']+=1
                        if gen.self_check(g):failures.append({'kind':'validator','band':band,'index':i,'input':g})
                        if rival(g)!=actual(g):failures.append({'kind':'unexpected_rival_disagreement','band':band,'index':i,'input':g})
                        if not gen.strict_canonical_like(g):counts[f'strict:{band}']+=1
                original=deepcopy(canon[0]['input'])
                r=next(i for i,row in enumerate(original) if row[0]==0)
                g=deepcopy(original);g[r][2]=9
                construction={'base':'canonical pair 0 input','edit':{'row':r,'col':2,'value':9},
                              'seed':None,'sample_index':None,'overrides':None}
                domain='Outside the documented sparse-left-edge domain: a nonzero body distractor was added.'
                classification='domain_question_not_in_domain_label_bug'
                base['sampler']={'per_band':args.per_band,'bands':list(BANDS),'index_range':[0,args.per_band-1],
                    'seed':'canonical_profile_gate._pinned_seed(task, band, i)','sample_index':'seed % 7919 + i'}
                base['rival_definition']='Fill each row using its first nonzero value anywhere in the row.'
                base['scope_argument']='All emitted rows have zero body cells; first-nonzero and column-zero keys are therefore observationally identical on this declared grammar.'
            else:
                table={tuple(v[:2]):tuple(v[2:]) for v in gen._PROFILES.values()}
                if len(table)!=len(gen._PROFILES):raise AssertionError('Canvas sizes no longer uniquely determine frame geometry')
                rival=lambda grid:frame_table_rival(grid,table)
                # Exhaustive advertised profile x palette x seed-position support.
                combinations=list(product(gen.SCHEDULE_PROFILES,gen._SEED_COLORS,gen._SEED_POSITIONS))
                for band in BANDS:
                    for i,(profile,color,position) in enumerate(combinations):
                        controls={'scene_profile':profile,'seed_color':color,'seed_position':position}
                        g=gen.generate(173,i,difficulty=band,**controls)
                        unique.add(digest(g));counts['exhaustive_case_uses']+=1
                        if gen.self_check(g):failures.append({'kind':'validator','controls':controls,'input':g})
                        if rival(g)!=actual(g):failures.append({'kind':'unexpected_rival_disagreement','controls':controls,'input':g})
                        # A different seed/index must not change any fully pinned input.
                        if g!=gen.generate(997,101+i,difficulty=band,**controls):
                            failures.append({'kind':'nonfinite_extra_variation','controls':controls})
                controls={'scene_profile':'canonical_8x9_5x5','seed_color':3,'seed_position':'top_left'}
                original=gen.generate(173,0,difficulty='easy',**controls)
                g=[[0]*len(original[0]) for _ in original]
                for r,row in enumerate(original):
                    for c,v in enumerate(row):
                        if v:
                            if c==0:raise AssertionError('Cannot translate left without clipping')
                            g[r][c-1]=v
                construction={'seed':173,'sample_index':0,'difficulty':'easy','overrides':controls,
                              'mutation':'translate every nonzero cell one column left; keep canvas dimensions'}
                domain='Accepted by self_check and strict_canonical_like, and inside the documented frame grammar; outside the eight-profile emission support.'
                classification='reproduced_emission_support_shortcut_not_label_corruption'
                base['sampler']={'bands':list(BANDS),'exhaustive_axes':{'scene_profile':list(gen.SCHEDULE_PROFILES),
                    'seed_color':list(gen._SEED_COLORS),'seed_position':list(gen._SEED_POSITIONS)},
                    'seed':173,'sample_index':'Cartesian combination index 0..255',
                    'second_control_seed':997,'second_control_sample_index':'101 + combination index'}
                base['frame_table']={f'{h}x{w}':list(v) for (h,w),v in table.items()}
                base['rival_definition']='Get seed color from pixels, but look up the entire frame geometry by canvas height/width; ignore all frame positions.'
                base['scope_argument']='All generator variability is in the three pinned axes; each of eight unique canvas sizes selects one fixed frame geometry. Exhaustive support has 8 * 8 * 4 = 256 inputs.'
            matches=sum(rival(p['input'])==actual(p['input']) for p in canon)
            if matches!=len(canon):failures.append({'kind':'rival_not_canonical_fitting','matches':matches,'denominator':len(canon)})
            for i,p in enumerate(canon):
                if actual(p['input'])!=p['output']:failures.append({'kind':'canonical_disagreement','index':i})
            truth=actual(g);wrong=rival(g);accepted=not bool(gen.self_check(g));strict=not bool(gen.strict_canonical_like(g))
            if truth==wrong:failures.append({'kind':'counterexample_does_not_discriminate'})
            if accepted != (task==TASKS[1]):failures.append({'kind':'unexpected_domain_result','issues':gen.self_check(g)})
            evidence={**{k:base[k] for k in ('task_id','generator_sha256','rule_hash','canonical_rule_sha256','label_authority')},
                      'classification':classification,'construction':construction,'original_input':original,
                      'input':g,'actual_racket_output':truth,'rival_output':wrong,'rival_definition':base['rival_definition'],
                      'validator_accepts':accepted,'validator_issues':gen.self_check(g),'strict_accepts':strict,
                      'inside_documented_domain':task==TASKS[1],'inside_generator_emission_support':False,
                      'domain_statement':domain,'rival_disagrees':truth!=wrong,
                      'runtime_cwd':str(Path.cwd()),'worker_command':sys.argv}
            base.update({'classification':classification,'canonical_matches':matches,'canonical_pair_count':len(canon),
                         'counts':dict(counts),'unique_inputs':len(unique),'unique_racket_calls':len(cache),
                         'counterexample':evidence,'passed':not failures})
            reports[task]=base
            print(f'{task}: counts={dict(counts)} unique={len(unique)}; counterexample validator={accepted}',flush=True)
        finally:bridge.close()
    return {'schema':'source-bound-adversarial-audit-v1','targets':reports,'passed':all(x['passed'] for x in reports.values()),
            'limitation':'These probes establish specific support gaps, not universal failure rates or model accuracy.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--per-band',type=int,default=300)
    ap.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=ap.parse_args()
    if args.per_band<1:ap.error('--per-band must be positive')
    out=args.out.resolve();out.parent.mkdir(parents=True,exist_ok=True)
    if args.worker:
        report=worker(args);out.write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1
    root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime,run_process
    start=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='audit-relocated-probe-') as tmp:
        runtime=Path(tmp);prepare_runtime(Catalog(root),runtime,task_ids=list(TASKS))
        shutil.copy2(__file__,runtime/'audit_targets.py')
        command=[sys.executable,'-B','audit_targets.py','--worker','--per-band',str(args.per_band),'--out','audit.json']
        run=run_process(command,runtime,timeout=300,on_output=lambda s:print(s,end='',flush=True))
        if not (runtime/'audit.json').exists():
            out.write_text(json.dumps({'passed':False,'worker_failure':run,'runtime_cwd':str(runtime)},indent=2)+'\n');return 1
        report=json.loads((runtime/'audit.json').read_text());report.update({'worker_command':command,
            'worker_exit_code':run['exit_code'],'worker_timed_out':run['timed_out'],'elapsed_seconds':round(time.monotonic()-start,3)})
        report['passed']=report['passed'] and run['exit_code']==0 and not run['timed_out']
        # Give each counterexample the relocatable public reproduction command.
        outer=['python3','run_with_racket.py','python3','generators/a452b4b4f04a/workspace/audit_targets.py',
               '--per-band',str(args.per_band),'--out',str(args.out)]
        for task,entry in report['targets'].items():
            ev=entry['counterexample'];ev.update({'cwd':'packet_root','command':outer})
            (out.parent/f'audit_{task}_counterexample.json').write_text(json.dumps(ev,indent=2)+'\n')
        out.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'passed':report['passed'],'seconds':report['elapsed_seconds']}))
        return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
