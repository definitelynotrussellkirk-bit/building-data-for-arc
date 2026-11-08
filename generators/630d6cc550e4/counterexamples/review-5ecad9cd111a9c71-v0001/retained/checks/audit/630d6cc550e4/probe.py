"""Bounded findings-only probe; uses same-checkout generator and public Racket labels."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = '630d6cc550e4'
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / 'repo'
sys.path.insert(0, str(REPO / 'shared/runtime'))
spec = importlib.util.spec_from_file_location('audited_generator', REPO / 'generators' / TASK / 'generator.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def rival(grid):
    """Exploit generator's fixed row lattice; no search for blocks/centers."""
    result = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    mapping = {(0,0):(0,2),(0,1):(1,0),(0,2):(2,2),(1,0):(2,1),
               (1,2):(0,1),(2,0):(0,0),(2,1):(1,2),(2,2):(2,0)}
    for r0 in range(1, h-2, 4):
        for c0 in sorted({1, w-4}):
            if c0 < 0 or c0+2 >= w or grid[r0][c0] == 7:
                continue
            for (dr,dc),(sr,sc) in mapping.items():
                result[r0+dr][c0+dc] = grid[r0+sr][c0+sc]
    return result


def prepare():
    records = []
    for band in ('easy','medium','hard'):
        for seed in (0,1):
            for sample_index in (0,1):
                overrides = {} if sample_index == 0 else {'grid_w':9, 'position_bias':'right', 'anchor_corner':True}
                grid = gen.generate(seed, sample_index, difficulty=band, **overrides)
                records.append({'kind':'generated','difficulty':band,'seed':seed,
                                'sample_index':sample_index,'overrides':overrides,
                                'input':grid,'validator_errors':gen.self_check(grid,difficulty=band,meta=overrides),
                                'rival_output':rival(grid)})
    for line in (REPO/'shared/data/canonical/puzzles.jsonl').open():
        row = json.loads(line)
        if row.get('task_id') == TASK:
            break
    else:
        raise ValueError('canonical row missing')
    for i,pair in enumerate(row['train']):
        records.append({'kind':'canonical_train','pair_index':i,'input':pair['input'],
                        'validator_errors':gen.self_check(pair['input']),
                        'rival_output':rival(pair['input'])})
    (HERE/'input.json').write_text(json.dumps({'inputs':[r['input'] for r in records]})+'\n')
    (HERE/'probe_records.json').write_text(json.dumps(records,indent=2)+'\n')
    print('Prepared %d generated + %d canonical training grids' % (12,len(row['train'])))


def analyze():
    records=json.loads((HERE/'probe_records.json').read_text())
    racket=json.loads((HERE/'racket.json').read_text())
    assert len(records)==len(racket['results'])==15
    rows=[]
    for record, actual in zip(records,racket['results']):
        assert actual['valid_output'] and actual['error'] is None
        assert record['input']==actual['input']
        rows.append({'kind':record['kind'],'seed':record.get('seed'),
                     'sample_index':record.get('sample_index'),
                     'difficulty':record.get('difficulty'),
                     'pair_index':record.get('pair_index'),
                     'shape':[len(record['input']),len(record['input'][0])],
                     'validator_errors':record['validator_errors'],
                     'rival_matches_racket':record['rival_output']==actual['output']})
    report={'generated_count':12,'generated_unique_inputs':len({json.dumps(r['input']) for r in records[:12]}),
            'generated_rival_matches':sum(r['rival_matches_racket'] for r in rows[:12]),
            'canonical_train_count':3,
            'canonical_train_rival_matches':sum(r['rival_matches_racket'] for r in rows[12:]),
            'validator_pass_count':sum(not r['validator_errors'] for r in rows),
            'valid_racket_output_count':15,'rows':rows}
    assert report['generated_rival_matches']==12
    assert report['canonical_train_rival_matches']==0
    assert report['validator_pass_count']==15
    (HERE/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('mode',choices=['prepare','analyze']); args=parser.parse_args()
    if args.mode=='prepare': prepare()
    else: analyze()
