"""Read-only reproducers for the two immutable audit assignments.

Run through run_with_racket.py from the packet root. Every reference answer is
obtained with the supported arcpuzzles apply CLI and its source-bound receipt.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from arcpuzzles import Catalog


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def load(task):
    path = Path('generators') / task / 'generator.py'
    spec = importlib.util.spec_from_file_location('audit_' + task, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, hashlib.sha256(path.read_bytes()).hexdigest()


def center_shortcut(grid):
    """Deliberately weak rival: fill center of each colored 3x3 component bbox."""
    out = [row[:] for row in grid]
    seen = set()
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r,c) in seen:
                continue
            color = grid[r][c]
            stack = [(r,c)]; seen.add((r,c)); points = []
            while stack:
                p = stack.pop(); points.append(p)
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    q = (p[0]+dr,p[1]+dc)
                    if 0 <= q[0] < h and 0 <= q[1] < w and q not in seen and grid[q[0]][q[1]] == color:
                        seen.add(q); stack.append(q)
            rs=[p[0] for p in points]; cs=[p[1] for p in points]
            if max(rs)-min(rs) == max(cs)-min(cs) == 2:
                out[min(rs)+1][min(cs)+1] = color
    return out


def run_reference(task, grids, destination):
    destination.mkdir(parents=True)
    source = destination / 'input.json'
    source.write_text(json.dumps(grids, indent=2) + '\n')
    target = destination / 'racket.json'
    command = [sys.executable, '-m', 'arcpuzzles', 'apply', task, '--input', str(source), '--out', str(target)]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (destination/'apply.log').write_text(result.stdout)
    if result.returncode:
        raise RuntimeError(result.stdout)
    return json.loads(target.read_text()), {'cwd':'repo', 'actual_cwd':str(Path.cwd()), 'argv':command, 'exit_code':result.returncode}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args=parser.parse_args()
    if args.out.exists():
        parser.error('output must not already exist; retain earlier evidence')
    args.out.mkdir(parents=True)
    catalog=Catalog(Path.cwd())
    summary={}
    task='dfa5c1702b4c'
    gen, sha=load(task)
    controls={'grid_h':20, 'grid_w':20, 'n_distinct_colors':7}
    plain=gen.generate(0,0,difficulty='easy')
    grid=gen.generate(0,0,difficulty='easy',**controls)
    observed={'grid_h':len(grid), 'grid_w':len(grid[0]), 'n_distinct_colors':len({v for row in grid for v in row}-{0})}
    receipt, command=run_reference(task, [grid], args.out/task)
    record={'finding_id':'A1', 'task_id':task, 'generator_sha256':sha,
            'rule_hash':catalog.describe(task)['rule_hash'], 'seed':0, 'sample_index':0,
            'difficulty':'easy', 'overrides':controls, 'observed':observed,
            'same_as_no_overrides':grid==plain, 'input_sha256':digest(grid), 'input':grid,
            'self_check_errors':gen.self_check(grid), 'documented_domain':True,
            'racket_output':receipt['results'][0]['output'], 'rival_output':None,
            'rival_note':'Exact-control defect; no competing transformation needed.', 'command':command}
    assert observed != controls and not record['self_check_errors']
    assert receipt['results'][0]['error'] is None
    (args.out/task/'counterexample.json').write_text(json.dumps(record,indent=2)+'\n')
    summary[task]={k:record[k] for k in ('finding_id','generator_sha256','rule_hash','observed','overrides','same_as_no_overrides')}
    task='3f9bb51d528b'
    gen,sha=load(task)
    controls={'grid_h':8,'grid_w':9,'n_rings':4}
    scan=[]; bad=None
    for seed in range(64):
        grid=gen.generate(seed,0,difficulty='medium',**controls)
        count=sum(v!=0 for row in grid for v in row)//8
        scan.append({'seed':seed,'sample_index':0,'observed_rings':count,'input_sha256':digest(grid)})
        if count!=4 and bad is None:
            bad=(seed,grid,count)
    assert bad is not None
    seed,grid,count=bad
    partial=[[0]*11 for _ in range(11)]
    for r0,c0,color,missing in ((1,1,4,True),(6,6,6,False)):
        for dr in range(3):
            for dc in range(3):
                if (dr,dc)!=(1,1) and not (missing and (dr,dc)==(0,0)):
                    partial[r0+dr][c0+dc]=color
    assert not gen.self_check(partial)
    receipt, command=run_reference(task,[grid,partial],args.out/task)
    assert all(x['error'] is None for x in receipt['results'])
    for index,(finding,source) in enumerate((('A2',grid),('A3',partial))):
        record={'finding_id':finding,'task_id':task,'generator_sha256':sha,
                'rule_hash':catalog.describe(task)['rule_hash'], 'input':source,'input_sha256':digest(source),
                'self_check_errors':gen.self_check(source), 'racket_output':receipt['results'][index]['output'],
                'rival_output':center_shortcut(source), 'command':command, 'receipt_result_index':index}
        if index==0:
            record.update(seed=seed,sample_index=0,difficulty='medium',overrides=controls,
                          observed_rings=count, documented_domain=True,
                          finding='Exact requested ring count silently underfilled.')
        else:
            record.update(seed=None,sample_index=None,overrides=None,documented_domain=False,
                          construction='One valid eight-cell ring plus a seven-cell partial ring; normal validator accepts both.',
                          finding='False-positive normal validation; a bbox-center shortcut disagrees with Racket on partial ring.')
            assert record['racket_output']!=record['rival_output']
        (args.out/task/f'counterexample-{finding}.json').write_text(json.dumps(record,indent=2)+'\n')
    (args.out/task/'ring-count-scan.json').write_text(json.dumps(scan,indent=2)+'\n')
    summary[task]={'generator_sha256':sha,'rule_hash':catalog.describe(task)['rule_hash'],
                   'seed_range':[0,63],'draws':64,'exact_count_failures':sum(x['observed_rings']!=4 for x in scan),
                   'first_bad_seed':seed,'first_bad_count':count,'partial_ring_validator_accepts':True,
                   'partial_ring_rival_disagrees':True}
    for task,row in summary.items():
        assert load(task)[1]==row['generator_sha256'], 'audit target changed during probe'
    (args.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
