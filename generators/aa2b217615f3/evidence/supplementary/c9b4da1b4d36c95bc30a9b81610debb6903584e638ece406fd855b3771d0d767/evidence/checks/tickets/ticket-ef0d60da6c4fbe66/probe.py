#!/usr/bin/env python3
"""Bounded peer audit: test the row/column-compression shortcut on canonical pairs."""
from __future__ import annotations
import hashlib, json, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
GEN=ROOT/'repo/generators/aa2b217615f3/generator.py'
SOL=ROOT/'repo/shared/data/base/solutions/training/6ad5bdfd__aa2b217615f3.json'
OUT=Path(__file__).with_name('witness.json')
EXPECTED_GEN='87493e2b00ab6370892cb5179a8a177e161191c83fc99f03f3249aca3aedd119'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def direction(g):
    h,w=len(g),len(g[0])
    if all(x==2 for x in g[0]): return 'up'
    if all(x==2 for x in g[-1]): return 'down'
    if all(row[0]==2 for row in g): return 'left'
    if all(row[-1]==2 for row in g): return 'right'
    raise ValueError('not a lawful single-edge-line input')

def compress_lanes(g):
    """Shortcut rival: compact each row/column independently toward the red edge."""
    h,w=len(g),len(g[0]); d=direction(g); out=[[0]*w for _ in range(h)]
    if d=='left':
        for r in range(h):
            out[r][0]=2
            vals=[g[r][c] for c in range(1,w) if g[r][c] not in (0,2)]
            for c,v in enumerate(vals,1): out[r][c]=v
    elif d=='right':
        for r in range(h):
            out[r][-1]=2
            vals=[g[r][c] for c in range(w-1) if g[r][c] not in (0,2)]
            for c,v in zip(range(w-2,w-2-len(vals),-1),reversed(vals)): out[r][c]=v
    elif d=='up':
        for c in range(w):
            out[0][c]=2
            vals=[g[r][c] for r in range(1,h) if g[r][c] not in (0,2)]
            for r,v in enumerate(vals,1): out[r][c]=v
    else:
        for c in range(w):
            out[-1][c]=2
            vals=[g[r][c] for r in range(h-1) if g[r][c] not in (0,2)]
            for r,v in zip(range(h-2,h-2-len(vals),-1),reversed(vals)): out[r][c]=v
    return out

def main():
    started=time.monotonic()
    assert sha(GEN)==EXPECTED_GEN
    record=json.loads(SOL.read_text())
    samples=json.loads(record['visible_context']['samples_text'])
    checked=0; chosen=None
    for i,pair in enumerate(samples['train']):
        checked+=1
        rival=compress_lanes(pair['input'])
        if rival != pair['output']:
            diffs=[{'row':r,'col':c,'authority':pair['output'][r][c],'rival':rival[r][c]}
                   for r in range(len(rival)) for c in range(len(rival[0]))
                   if rival[r][c] != pair['output'][r][c]]
            chosen={'pair_index':i,'direction':direction(pair['input']),'input':pair['input'],
                    'authority_output':pair['output'],'shortcut_output':rival,
                    'mismatch_cells':diffs,'mismatch_count':len(diffs)}
            break
    report={
      'schema':'arcpuzzles-peer-witness-v1','ticket_id':'ticket-ef0d60da6c4fbe66',
      'task_id':'aa2b217615f3','generator_sha256':sha(GEN),'rule_hash':'5b3e7ca4f11c',
      'shortcut':'compress each row/column independently toward the red edge, ignoring rigid-object connectivity',
      'canonical_pairs_checked':checked,'witness_found':chosen is not None,
      'witness':chosen,'elapsed_seconds':time.monotonic()-started,
      'source':'repo/shared/data/base/solutions/training/6ad5bdfd__aa2b217615f3.json visible canonical training pair'}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'witness_found':report['witness_found'],'pair_index':chosen and chosen['pair_index'],
                      'direction':chosen and chosen['direction'],'mismatch_count':chosen and chosen['mismatch_count'],
                      'elapsed_seconds':report['elapsed_seconds']},sort_keys=True))
    raise SystemExit(0 if chosen else 2)
if __name__=='__main__': main()
