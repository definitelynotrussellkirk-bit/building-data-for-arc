"""Findings-only audit replay; does not modify either assigned audit target.

From packet: python3 run_with_racket.py python3 ../checks/audits/reproduce_audits.py --out ../checks/audits/replay
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

TASKS = ('60527b695836', '57870373a67e')


def rule_a(g):
    out = deepcopy(g)
    for r in range(len(g) - 1):
        for c in range(len(g[0]) - 1):
            cells = [(r+dr,c+dc) for dr in (0,1) for dc in (0,1)]
            if sum(g[y][x] == 8 for y,x in cells) == 3:
                for y,x in cells:
                    if g[y][x] == 0:
                        out[y][x] = 1
    return out


def rule_b(g):
    out = deepcopy(g)
    for r,row in enumerate(g):
        for c,v in enumerate(row):
            if v == 0 and ((1 in row[:c] and 1 in row[c+1:]) or
                           (any(g[y][c] == 1 for y in range(r)) and
                            any(g[y][c] == 1 for y in range(r+1,len(g))))):
                out[r][c] = 8
    return out


def l_count(g):
    return sum(g[r][c] != v for r,row in enumerate(rule_a(g)) for c,v in enumerate(row))


def bracket_lines(g):
    def rows(a):
        count=0
        for row in a:
            ones=[c for c,v in enumerate(row) if v == 1]
            count += bool(ones and 0 in row[min(ones):max(ones)])
        return count
    return {'rows':rows(g),'columns':rows(list(map(list,zip(*g))))}


def bbox_rival(g):
    out=deepcopy(g)
    todo={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==8}
    while todo:
        first=todo.pop();component={first};stack=[first]
        while stack:
            r,c=stack.pop()
            nb={(r-1,c),(r+1,c),(r,c-1),(r,c+1)}&todo
            todo-=nb;component|=nb;stack.extend(nb)
        for r in range(min(r for r,c in component),max(r for r,c in component)+1):
            for c in range(min(c for r,c in component),max(c for r,c in component)+1):
                if out[r][c]==0:out[r][c]=1
    return out


def worker(out):
    from scripts.canonical_profile_gate import canonical_pairs,canonical_rule_source
    from puzzle_generators import runner
    result={'schema':'two-target-adversarial-audit-v1','targets':{}}
    for tid, mirror in zip(TASKS,(rule_a,rule_b)):
        gen=importlib.import_module(f'puzzle_generators.per_puzzle.{tid}.generator')
        source=canonical_rule_source(tid)
        bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(source))
        counts=Counter();samples=[];failures=[]
        def exercise(grid, context, expected=None):
            counts['racket_calls']+=1
            actual=runner._apply_rule(bridge,name,grid)
            if actual != mirror(grid):failures.append({'context':context,'kind':'mirror/reference mismatch','input':grid})
            if expected is not None and actual != expected:failures.append({'context':context,'kind':'canonical/reference mismatch','input':grid})
            return actual
        try:
            canonical=canonical_pairs(tid)
            for index,pair in enumerate(canonical):
                exercise(pair['input'],{'canonical':index},pair['output']);counts['canonical_rows']+=1
                counts['canonical_selfcheck_rejections']+=bool(gen.self_check(pair['input']))
            if tid==TASKS[0]:
                for band in ('easy','medium','hard'):
                    for seed in range(64):
                        grid=gen.generate(seed,0,difficulty=band)
                        actual=exercise(grid,{'seed':seed,'difficulty':band})
                        counts['default_generated']+=1
                        counts['default_checker_rejections']+=bool(gen.self_check(grid))
                        counts['default_single_L']+=l_count(grid)==1
                        counts['bbox_rival_matches']+=bbox_rival(grid)==actual
                grid=gen.generate(0,0,n_patterns=4,position_bias='center')
                samples.append({'finding':'requested four patterns, emitted one, self_check accepted',
                                'call':{'seed':0,'sample_index':0,'n_patterns':4,'position_bias':'center'},
                                'observed_pattern_count':l_count(grid),'self_check':gen.self_check(grid),
                                'input':grid,'output':exercise(grid,{'reproducer':'center'})})
                invalid_ranges=[]
                for value in (1,6):
                    try:gen.generate(0,0,n_patterns=value)
                    except Exception as exc:invalid_ranges.append({'requested':value,'error':str(exc)})
                decoy=[[0]*5 for _ in range(4)]
                for r,c in ((1,1),(1,2),(1,3),(2,1)):decoy[r][c]=8
                samples.append({'finding':'bbox-completion shortcut counterexample under reference rule; not a claim of observed canonical failure',
                                'input':decoy,'output':exercise(decoy,{'reproducer':'bbox-decoy'}),'rival_output':bbox_rival(decoy),
                                'self_check':gen.self_check(decoy)})
                extra={'valid_override_rejections':invalid_ranges,'bbox_rival_canonical_matches':sum(bbox_rival(p['input'])==p['output'] for p in canonical)}
            else:
                dots=Counter()
                for band in ('easy','medium','hard'):
                    for seed in range(64):
                        grid=gen.generate(seed,0,difficulty=band)
                        exercise(grid,{'seed':seed,'difficulty':band});counts['default_generated']+=1
                        counts['default_checker_rejections']+=bool(gen.self_check(grid))
                        lines=bracket_lines(grid)
                        counts['default_fewer_than_two_bracket_rows_and_cols']+=lines['rows']<2 and lines['columns']<2
                grid=gen.generate(0,0,grid_h=7,grid_w=7,n_dots=12,dot_distribution='diagonal')
                samples.append({'finding':'requested 12 blue dots, emitted 11 due to duplicated diagonal crossing',
                                'call':{'seed':0,'sample_index':0,'grid_h':7,'grid_w':7,'n_dots':12,'dot_distribution':'diagonal'},
                                'actual_dots':sum(v==1 for row in grid for v in row),'self_check':gen.self_check(grid),
                                'input':grid,'output':exercise(grid,{'reproducer':'diagonal-count'})})
                grid=gen.generate(0,0,dot_distribution='clustered',min_brackets=4)
                other=gen.generate(0,0,dot_distribution='clustered',min_brackets=1)
                samples.append({'finding':'min_brackets ignored; not read or validated',
                                'call':{'seed':0,'sample_index':0,'dot_distribution':'clustered','min_brackets':4},
                                'same_as_min_brackets_1':grid==other,'bracket_lines':bracket_lines(grid),
                                'self_check':gen.self_check(grid),'input':grid,'output':exercise(grid,{'reproducer':'brackets'})})
                invalid_ranges=[]
                for value in (4,30):
                    try:gen.generate(0,0,n_dots=value)
                    except Exception as exc:invalid_ranges.append({'requested':value,'error':str(exc)})
                extra={'valid_override_rejections':invalid_ranges}
        finally:bridge.shutdown()
        result['targets'][tid]={'source_sha256':hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
            'rule_hash':hashlib.sha256(' '.join(source.split()).encode()).hexdigest()[:12],
            'counts':dict(counts),'failures':failures,'reproducers':samples,**extra}
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({t:{'counts':v['counts'],'label_failures':len(v['failures'])} for t,v in result['targets'].items()},indent=2))
    return int(any(v['failures'] for v in result['targets'].values()))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--worker',action='store_true')
    args=p.parse_args()
    if args.worker:return worker(args.out)
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'repo/src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime,run_process
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='arc-findings-only-') as d:
        stage=Path(d);prepare_runtime(Catalog(root/'repo'),stage,task_ids=list(TASKS))
        shutil.copyfile(__file__,stage/'reproduce_audits.py')
        run=run_process([sys.executable,'reproduce_audits.py','--worker','--out',str(out/'report.json')],stage,timeout=240)
        (out/'process.json').write_text(json.dumps(run,indent=2)+'\n')
        print(run['stdout'],end='');print(run['stderr'],file=sys.stderr,end='')
        return int(run['exit_code']!=0 or run['timed_out'])


if __name__=='__main__':raise SystemExit(main())
