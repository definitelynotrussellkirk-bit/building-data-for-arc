#!/usr/bin/env python3
"""Reproduce the two assigned findings-only audits without changing their sources."""
from __future__ import annotations
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

TARGETS=('5ffd8d801705','6027a830c96e')

def digest(data):return hashlib.sha256(data).hexdigest()
def mod3_mask(g):return [[v if r%3==c%3 else 0 for c,v in enumerate(row)] for r,row in enumerate(g)]

def worker(args):
    from puzzle_generators import runner
    rows={}
    for line in Path('data/canonical/puzzles.jsonl').read_text().splitlines():
        row=json.loads(line)
        if row['task_id'] in TARGETS:rows[row['task_id']]=row
    for task in TARGETS:
        mod=importlib.import_module(f'puzzle_generators.per_puzzle.{task}.generator')
        row=rows[task];rule=row['program_solution']
        bridge,fn=runner._open_bridge_with_rule(runner.wrap_rule(rule))
        def execute(g):
            try:return {'output':runner._apply_rule(bridge,fn,g),'error':None}
            except Exception as exc:return {'output':None,'error':f'{type(exc).__name__}: {exc}'}
        report={'task_id':task,'generator_sha256':digest(Path(mod.__file__).read_bytes()),
                'canonical_rule_sha256':digest(rule.encode()), 'runtime_directory':str(Path.cwd()),
                'command':{'cwd':'packet_root','argv':['python3','run_with_racket.py','python3',
                    'generators/0f26224a6da3/workspace/audit_assigned.py','--out','../checks/audits']},
                'findings':[]}
        try:
            if task==TARGETS[0]:
                count=0;matches=0;failures=[];unique=set()
                for band in (None,'easy','medium','hard'):
                    for seed in range(10):
                        for i in range(3):
                            g=mod.generate(seed,i,difficulty=band); a=execute(g)
                            count+=1;unique.add(digest(json.dumps(g).encode()))
                            matches+=int(a['error'] is None and a['output']==mod3_mask(g))
                            if a['error']:failures.append({'seed':seed,'sample_index':i,'difficulty':band,**a})
                canonical=row['train']+row['test']
                fits=sum(mod3_mask(p['input'])==p['output'] for p in canonical)
                p=canonical[0];actual=execute(p['input'])
                report['census']={'bands':[None,'easy','medium','hard'],'seeds':list(range(10)),
                                  'sample_indices':[0,1,2], 'draws':count,'unique_inputs':len(unique),
                                  'rival_matches_racket':matches,'execution_failures':failures,
                                  'canonical_rival_matches':fits,'canonical_pairs':len(canonical)}
                report['findings'].append({'id':'A1','kind':'generation_only_positional_shortcut',
                    'input':p['input'],'actual_racket_output':actual['output'],'actual_racket_error':actual['error'],
                    'rival_output':mod3_mask(p['input']), 'validator_errors':mod.self_check(p['input']),
                    'input_origin':'canonical train[0]','in_documented_generator_support':False,
                    'domain_note':'Lawful canonical blocks; not restricted to generator row/column multiples of three.',
                    'rival':'Keep each cell iff its global row and column residues modulo 3 agree.'})
            else:
                checked=0;errors=[];unique=set()
                for band in (None,'easy','medium','hard'):
                    for seed in range(3):
                        for i in range(2):
                            g=mod.generate(seed,i,difficulty=band);a=execute(g);v=mod.self_check(g)
                            checked+=1;unique.add(digest(json.dumps(g).encode()))
                            if a['error'] or v:errors.append({'seed':seed,'sample_index':i,'difficulty':band,'validator':v,**a})
                report['census']={'bands':[None,'easy','medium','hard'],'seeds':[0,1,2],
                                  'sample_indices':[0,1],'draws':checked,'unique_inputs':len(unique),'errors':errors}
                g=mod.generate(0,0,difficulty='easy');frames=mod._closed_frame_candidates(g)
                inside={(r,c) for _,top,left,bot,right in frames for r in range(top,bot+1) for c in range(left,right+1)}
                selector=next((r,c,v) for r,rowg in enumerate(g) for c,v in enumerate(rowg) if v and (r,c) not in inside)
                color,top,left,bot,right=next(f for f in frames if f[0]==selector[2])
                mutant=[list(r) for r in g];prior=mutant[top+1][left+1];mutant[top+1][left+1]=color
                a=execute(mutant)
                rival=[r[left+1:right] for r in mutant[top+1:bot]]
                report['findings'].append({'id':'A2','kind':'validator_accepts_reference_execution_failure',
                    'seed':0,'sample_index':0,'difficulty':'easy','overrides':{},'original_input':g,
                    'mutation':{'row':top+1,'col':left+1,'old':prior,'new':color}, 'input':mutant,
                    'validator_errors':mod.self_check(mutant),'actual_racket_output':a['output'],
                    'actual_racket_error':a['error'],'rival_output':rival,
                    'rival':'Geometric closed-border selection ignoring connected-object purity.',
                    'in_documented_generator_support':False,
                    'domain_note':'One-cell mutation introduces a border color into its own interior; actual sampler explicitly excludes all frame colors from content. Validator fails to enforce that restriction.'})
                overrides={'grid_h':11,'grid_w':13,'selector':9}
                g=mod.generate(0,0,difficulty='hard',**overrides);a=execute(g)
                frames=mod._closed_frame_candidates(g)
                inside={(r,c) for _,t,l,b,rt in frames for r in range(t,b+1) for c in range(l,rt+1)}
                sel=[(r,c,v) for r,rowg in enumerate(g) for c,v in enumerate(rowg) if v and (r,c) not in inside]
                report['findings'].append({'id':'A3','kind':'silently_ignored_overrides','seed':0,'sample_index':0,
                    'difficulty':'hard','overrides':overrides,'input':g,'observed_dimensions':[len(g),len(g[0])],
                    'observed_selector':sel,'validator_errors':mod.self_check(g),
                    'actual_racket_output':a['output'],'actual_racket_error':a['error'],
                    'rival_output':None,'rival_note':'Exact-control contract failure, not a competing output rule.',
                    'in_documented_generator_support':True,
                    'same_as_unoverridden':g==mod.generate(0,0,difficulty='hard')})
        finally:bridge.shutdown()
        path=args.out/f'{task}.json';path.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'task_id':task,'output':str(path),'findings':[f['id'] for f in report['findings']]}))
    return 0


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--worker',action='store_true');args=parser.parse_args()
    if args.worker:return worker(args)
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parents[3]
    with tempfile.TemporaryDirectory(prefix='assigned-audits-') as folder:
        runtime=Path(folder);prepare_runtime(Catalog(repo),runtime,task_ids=list(TARGETS))
        shutil.copy2(__file__,runtime/'audit.py')
        env=dict(os.environ);env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
        return subprocess.run([sys.executable,'audit.py','--worker','--out',str(out)],cwd=runtime,env=env,timeout=180).returncode

if __name__=='__main__':raise SystemExit(main())
