#!/usr/bin/env python3
"""One bounded, source-bound reverse-diagonal shortcut witness probe.

Run from WORK/repo with the packet's Racket wrapper:
  python3 ../run_with_racket.py python3 ../checks/tickets/ticket-b5bc1454dbe15c28/probe.py
The single invocation samples at most eight inputs and applies canonical Racket
only to the first lawful reverse-diagonal witness. It never edits source.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from collections import defaultdict

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]/'repo'
TASK='7a8926bd9d9f'
TICKET='ticket-b5bc1454dbe15c28'
SOURCE_SHA='3159c9b3a39d6992342525082632fcd2d341c4e5474ac12a9c7a090185a7b454'
RULE_HASH='e6d9cb6ee6d8'
SEED_HEX='1eeddec060b5207674d69ad7d0ad37eaf865c1f82f9a275ab31147237e2df686'


def inspect_lawfulness(grid):
    """Check declared geometric invariants independently of weak self_check."""
    assert 8 <= len(grid) <= 10 and 8 <= len(grid[0]) <= 10
    assert all(len(row)==len(grid[0]) for row in grid)
    cells=defaultdict(list)
    for r,row in enumerate(grid):
        for c,color in enumerate(row):
            assert type(color) is int and 0 <= color <= 9
            if color: cells[color].append((r,c))
    assert len(cells) in (2,3)
    reserved=set();rectangles=[]
    for color,points in sorted(cells.items()):
        assert len(points)==2
        (r0,c0),(r1,c1)=sorted(points)
        assert r0 != r1 and c0 != c1
        assert 2 <= r1-r0+1 <= 4 and 2 <= abs(c1-c0)+1 <= 5
        box={(r,c) for r in range(r0,r1+1) for c in range(min(c0,c1),max(c0,c1)+1)}
        assert not (reserved & box)
        reserved.update(box)
        rectangles.append({'color':color,'endpoints':points,'reverse_diagonal':c1<c0,
                           'bounding_box':[r0,min(c0,c1),r1,max(c0,c1)]})
    return rectangles


def shortcut(grid, rectangles):
    """Plausible faulty rival: fill TL/BR pairs, ignore TR/BL pairs."""
    out=[row[:] for row in grid]
    for rect in rectangles:
        if rect['reverse_diagonal']: continue
        r0,c0,r1,c1=rect['bounding_box']
        for r in range(r0,r1+1):
            for c in range(c0,c1+1):out[r][c]=rect['color']
    return out


def main():
    started=time.monotonic()
    result={'ticket_id':TICKET,'type':'adversarial_witness','task_id':TASK,
            'status':'unknown','seed_hex':SEED_HEX,'generator_sha256':SOURCE_SHA,
            'rule_hash':RULE_HASH,'targeted_probe_invocations':1,'reference_apply_calls':0,
            'candidate_budget':8,'candidates_generated':0,'reference_timeout_seconds':90,
            'shortcut':'Fill only TL/BR diagonal pairs; leave TR/BL pair interiors unfilled.',
            'scope':'One shortcut witness only; no battery, census, training admission, or general safety conclusion.'}
    try:
        source=REPO/'generators'/TASK/'generator.py'
        assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA,'pinned generator differs'
        sys.path[:0]=[str(REPO/'src'),str(REPO/'shared/runtime')]
        from arcpuzzles.catalog import Catalog
        from arcpuzzles.runtime import apply_rule
        catalog=Catalog(REPO);row=catalog.describe(TASK)
        assert row['generator_sha256']==SOURCE_SHA and row['rule_hash']==RULE_HASH
        spec=importlib.util.spec_from_file_location('ticket_generator',source)
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        selected=None
        for index in range(8):
            grid=module.generate(int(SEED_HEX,16),index)
            result['candidates_generated']+=1
            rectangles=inspect_lawfulness(grid)
            errors=module.self_check(grid)
            assert errors==[],repr(errors)
            if any(rect['reverse_diagonal'] for rect in rectangles):
                selected=(index,grid,rectangles);break
        if selected is None:
            result['summary']='No reverse-diagonal witness appeared within the predeclared eight-input budget.'
        else:
            index,grid,rectangles=selected
            # Keep all temporary runtime snapshots in this owned evidence subtree.
            tempfile.tempdir=str(HERE)
            result['reference_apply_calls']=1
            applied=apply_rule(catalog,TASK,[grid],reference='canonical',allow_unapproved=True,
                               timeout=90,check_generator_domain=True)
            result['reference_receipt']=applied
            actual=applied['results'][0]
            assert applied['executed_rule_hash']==RULE_HASH and applied['rule_hash_matches_catalog']
            assert actual['valid_output'] and actual['error'] is None
            assert actual['generator_domain']=={'status':'valid','errors':[]}
            rival=shortcut(grid,rectangles);expected=actual['output']
            differences=[{'row':r,'column':c,'shortcut':rival[r][c],'racket':expected[r][c]}
                         for r in range(len(grid)) for c in range(len(grid[0])) if rival[r][c]!=expected[r][c]]
            result['witness']={'sample_index':index,'input':grid,'racket_output':expected,
                'shortcut_output':rival,'rectangles':rectangles,'lawfulness':'all declared geometric invariants checked',
                'difference_count':len(differences),'differences':differences}
            assert differences,'chosen input did not refute shortcut'
            assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA,'generator changed during probe'
            result['status']='completed'
            result['summary']='Retained one lawful generated reverse-diagonal witness; canonical Racket output refutes the TL/BR-only shortcut. No source-bound safety defect found by this bounded probe.'
    except Exception as exc:
        result['error']=type(exc).__name__+': '+str(exc)
        result.setdefault('summary','Bounded probe could not establish a lawful authoritative witness; no retry was run.')
    result['probe_elapsed_seconds']=round(time.monotonic()-started,6)
    (HERE/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['ticket_id','status','summary','candidates_generated','reference_apply_calls','probe_elapsed_seconds']}))
    return 0 if result['status']=='completed' else 1

if __name__=='__main__':
    raise SystemExit(main())
