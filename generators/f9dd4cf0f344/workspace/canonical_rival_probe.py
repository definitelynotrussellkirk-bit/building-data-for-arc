#!/usr/bin/env python3
"""Findings-only audit: compare sampled and canonical rival rejection coverage.

Run from the repository via run_with_racket.py. Does not alter audit targets.
Without --gate, exit zero only means measurement completed. With --gate,
exit 2 flags a canonical counterexample missing from a sampled difficulty band.
Python reference functions are checked against Racket for every input here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0,str(HOME/'workspace'))
from quality_probe import load_generator

RIVALS = {'8b595f6acd93': ('at_least_three_green',),
          'c36d1678a484': ('any_seven','any_singleton')}


def reference(task, grid):
    out = [r[:] for r in grid]
    if task == '8b595f6acd93':
        for r in range(1,len(grid)-1):
            for c in range(1,len(grid[0])-1):
                arms = (grid[r-1][c],grid[r+1][c],grid[r][c-1],grid[r][c+1])
                if grid[r][c] == 0 and all(v == 3 for v in arms):
                    out[r][c] = 4
    elif task == 'c36d1678a484':
        for r,row in enumerate(grid):
            if [v for v in row if v] == [7]:
                out[r] = [7]*len(row)
    else:
        raise ValueError(f'Unknown audit task: {task}')
    return out


def predict(task, name, grid):
    if name not in RIVALS[task]:
        raise ValueError(name)
    out = [r[:] for r in grid]
    if name == 'at_least_three_green':
        for r in range(1,len(grid)-1):
            for c in range(1,len(grid[0])-1):
                arms=(grid[r-1][c],grid[r+1][c],grid[r][c-1],grid[r][c+1])
                if grid[r][c] == 0 and arms.count(3) >= 3:
                    out[r][c]=4
    elif name == 'any_seven':
        out = [[7]*len(row) if 7 in row else row[:] for row in grid]
    else:
        for r,row in enumerate(grid):
            nz=[v for v in row if v]
            if len(nz) == 1:
                out[r]=[nz[0]]*len(row)
    return out



def coverage_gaps(stats):
    """Flag a known canonical distinction wholly absent in a sampled band.

    This is a finite known-rival coverage check, not proof of lesson uniqueness.
    A rival which canonical data never refutes is not evidence for a veto.
    """
    established = {name for pair in stats['canonical']
                   for name, exact in pair['rival_exact'].items() if not exact}
    return [{'band':band,'rival':name,'draws':values['draws']}
            for band,values in stats['bands'].items()
            for name in sorted(established)
            if values['draws'] > 0 and values['rival_exact_matches'][name] == values['draws']]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--count',type=int,default=256)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--gate',action='store_true',help='Exit 2 when a canonical-refuted rival survives every draw in any band')
    a=ap.parse_args()
    if a.count < 1:
        ap.error('--count must be positive')
    sys.path.insert(0,str(ROOT/'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    report={'schema':'canonical-rival-audit-v1','count_per_band':a.count,
            'seed_range':[0,a.count-1],'sample_index':'seed','tasks':{},
            'interpretation':'Completion is not approval; review documented coverage gaps.',
            'errors':[]}
    records={}
    for s in (ROOT/'shared/data/canonical/puzzles.jsonl').open():
        row=json.loads(s)
        if row['task_id'] in RIVALS:
            records[row['task_id']]=row
    with tempfile.TemporaryDirectory(prefix='canonical-rival-runtime-') as temp:
        rt=Path(temp)
        prepare_runtime(Catalog(ROOT),rt,task_ids=list(RIVALS))
        sys.path.insert(0,str(rt))
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        bridge=RacketBridge(prelude_path=str(rt/'arc_repl/racket_prelude/arc-prelude.rkt'))
        try:
            for task,names in RIVALS.items():
                path=ROOT/'generators'/task/'generator.py'
                gen=load_generator(path)
                row=records[task]
                source=row['program_solution']
                bridge.eval_text(f'(define audit_rule_{task} {wrap_rule(source)})')
                stats={'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                       'rule_sha256':hashlib.sha256(source.encode()).hexdigest(),
                       'racket_checked':0,'bands':{},'canonical':[],
                       'first_generated_counterexamples':{},'override_probe':{}}
                def expected(g):
                    bridge.define_grid('audit_input',g)
                    actual=bridge.eval_text(f'(audit_rule_{task} audit_input)')
                    stats['racket_checked']+=1
                    py=reference(task,g)
                    if actual != py:
                        raise AssertionError({'task':task,'input':g,'racket':actual,'python':py})
                    return actual
                for band in ('easy','medium','hard'):
                    bs={'draws':0,'unique_inputs':0,'rival_exact_matches':dict.fromkeys(names,0),
                        'self_check_rejections':0}
                    seen=set()
                    for seed in range(a.count):
                        g=gen.generate(seed,seed,difficulty=band)
                        out=expected(g)
                        bs['draws']+=1
                        seen.add(json.dumps(g,separators=(',',':')))
                        bs['self_check_rejections']+=bool(gen.self_check(g,difficulty=band))
                        for name in names:
                            pred=predict(task,name,g)
                            bs['rival_exact_matches'][name]+=(pred == out)
                            if pred != out and name not in stats['first_generated_counterexamples']:
                                stats['first_generated_counterexamples'][name]={'band':band,'seed':seed,
                                    'sample_index':seed,'input':g,'expected':out,'rival_output':pred}
                    bs['unique_inputs']=len(seen)
                    stats['bands'][band]=bs
                for split in ('train','test'):
                    for i,pair in enumerate(row.get(split,[])):
                        g=pair['input']; out=expected(g)
                        if out != pair['output']:
                            raise AssertionError(f'{task} {split}[{i}] canonical/Racket mismatch')
                        stats['canonical'].append({'split':split,'index':i,'input':g,'expected':out,
                            'self_check_messages':gen.self_check(g),
                            'rival_exact':{name:predict(task,name,g)==out for name in names},
                            'rival_outputs':{name:predict(task,name,g) for name in names}})
                pin=7 if task == '8b595f6acd93' else 3
                kw={'grid_h':pin}
                try:
                    g=gen.generate(0,0,difficulty='easy',**kw)
                    stats['override_probe']={'seed':0,'sample_index':0,'difficulty':'easy','overrides':kw,
                        'observed_height':len(g)}
                except ValueError as exc:
                    stats['override_probe']={'seed':0,'sample_index':0,'difficulty':'easy','overrides':kw,
                        'exception_type':type(exc).__name__,'message':str(exc)}
                stats['canonical_retention_gaps']=coverage_gaps(stats)
                report['tasks'][task]=stats
        except Exception as exc:
            report['errors'].append(repr(exc))
        finally:
            bridge.close()
    report['gate_status']=('ERROR' if report['errors'] else 'FAIL' if any(
        s['canonical_retention_gaps'] for s in report['tasks'].values()) else 'PASS')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    for task,s in report['tasks'].items():
        print(task,s['source_sha256'],s['bands'])
        for c in s['canonical']:
            print(c['split'],c['index'],'rivals',c['rival_exact'],'self_check',c['self_check_messages'])
        print('override:',s['override_probe'])
    print('errors',report['errors'],'gate_status',report['gate_status'])
    return 1 if report['errors'] else (2 if a.gate and report['gate_status']=='FAIL' else 0)

if __name__ == '__main__':
    raise SystemExit(main())
