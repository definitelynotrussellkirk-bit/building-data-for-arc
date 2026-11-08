#!/usr/bin/env python3
"""Visible-only overlay lesson gate: reject surviving rivals that disagree on a query.

This task-local gate does not access the generator, reference rules or private
query labels. Passing identifies query predictions only within SIX explicit
candidates, not among all possible programs. Use as an opt-in authoring check:
  python3 lesson_palette_gate.py --challenge challenge.json --out gate.json
Exit 0: candidate agreement; 1: ambiguous; 2: unsupported/malformed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

CANDIDATES = ('bottom_overlay','top_overlay','copy_top','copy_bottom',
              'nonzero_minimum','numeric_maximum')


def rectangle(grid):
    if not isinstance(grid,list) or not grid or not isinstance(grid[0],list) or not grid[0]:
        raise ValueError('Expected a nonempty integer grid')
    width=len(grid[0])
    if any(not isinstance(row,list) or len(row)!=width for row in grid):
        raise ValueError('Expected rectangular rows')
    if any(type(v) is not int or not 0<=v<=9 for row in grid for v in row):
        raise ValueError('Expected integer ARC colors')
    return len(grid),width


def predict(grid, rule):
    height,width=rectangle(grid)
    if height<3 or height%2!=1:
        raise ValueError('Expected two equal panels and a central separator')
    mid=height//2
    if grid[mid][0]==0 or len(set(grid[mid]))!=1:
        raise ValueError('Expected a uniform nonzero separator')
    def cell(a,b):
        if rule=='bottom_overlay': return b if b else a
        if rule=='top_overlay': return a if a else b
        if rule=='copy_top': return a
        if rule=='copy_bottom': return b
        if rule=='nonzero_minimum': return min([v for v in (a,b) if v] or [0])
        if rule=='numeric_maximum': return max(a,b)
        raise ValueError(f'Unknown candidate: {rule}')
    return [[cell(grid[r][c],grid[mid+1+r][c]) for c in range(width)] for r in range(mid)]


def analyze_challenge(challenge):
    if not isinstance(challenge,dict):
        raise ValueError('Expected an ARC challenge object')
    demos,queries=challenge.get('train'),challenge.get('test')
    if not isinstance(demos,list) or not demos or not isinstance(queries,list) or not queries:
        raise ValueError('Expected nonempty train and test lists')
    for demo in demos:
        if not isinstance(demo,dict) or 'input' not in demo or 'output' not in demo:
            raise ValueError('Each demonstration needs input and output')
        ih,iw=rectangle(demo['input'])
        if rectangle(demo['output'])!=(ih//2,iw):
            raise ValueError('Demonstration output has unexpected dimensions')
    for query in queries:
        if not isinstance(query,dict) or 'input' not in query or 'output' in query:
            raise ValueError('Queries must contain input and no private output labels')
        predict(query['input'],'bottom_overlay')
    fits={name:sum(predict(demo['input'],name)==demo['output'] for demo in demos) for name in CANDIDATES}
    survivors=[name for name,count in fits.items() if count==len(demos)]
    reports=[]
    for index,query in enumerate(queries):
        predictions={name:predict(query['input'],name) for name in survivors}
        baseline=predictions[survivors[0]] if survivors else None
        differences={name:sum(a!=b for ar,br in zip(pred,baseline) for a,b in zip(ar,br))
                     for name,pred in predictions.items()} if baseline is not None else {}
        reports.append({'index':index,'ambiguous':len({json.dumps(p) for p in predictions.values()})>1,
                        'disagreeing_cells_vs_first_survivor':differences})
    count=sum(row['ambiguous'] for row in reports)
    return {'schema':'overlay-palette-gate-v1','status':'unsupported' if not survivors else 'ambiguous' if count else 'passed',
            'train_count':len(demos),'visible_exact_matches':fits,'surviving_candidates':survivors,
            'ambiguous_query_count':count,'queries':reports,
            'scope':'Visible-only, finite-candidate agreement; no private query labels or reference execution.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--challenge',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists(): parser.error('Output exists; retain earlier gate evidence')
    try:
        report=analyze_challenge(json.loads(args.challenge.read_text()))
    except (ValueError, OSError) as error:
        parser.error(str(error))
    report['challenge_sha256']=hashlib.sha256(args.challenge.read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as handle:
        json.dump(report,handle,indent=2);handle.write('\n')
    print(json.dumps(report,indent=2))
    return {'passed':0,'ambiguous':1,'unsupported':2}[report['status']]


if __name__=='__main__':
    raise SystemExit(main())
