"""Replayable task-local probes, run from the library with the packet wrapper.

The Python frame specification is a testing oracle, not a source of training
labels. Retained lesson counterexamples are re-executed by canonical Racket via
the public Catalog.apply API. No private runner functions or sibling imports.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK = '51cb5336f078'


def load(path):
    spec = importlib.util.spec_from_file_location('probe_generator', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pixels(grid):
    return {(r,c) for r,row in enumerate(grid) for c,value in enumerate(row) if value}


def edges(grid):
    cells = pixels(grid)
    r0, r1 = min(r for r,c in cells), max(r for r,c in cells)
    c0, c1 = min(c for r,c in cells), max(c for r,c in cells)
    return {(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)
            if r in (r0,r1) or c in (c0,c1)}


def spec_frame(grid):
    occupied = pixels(grid)
    r,c = min(occupied)
    edge = edges(grid)
    return [[grid[r][c] if (i,j) in edge else 0 for j in range(len(grid[0]))]
            for i in range(len(grid))]


def overlay(grid):
    out = [list(row) for row in grid]
    r,c = min(pixels(grid))
    for i,j in edges(grid): out[i][j] = grid[r][c]
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generator', type=Path)
    parser.add_argument('--baseline-counterexample', action='store_true')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = find_root(__file__)
    source = args.generator or root / 'generators' / TASK / 'generator.py'
    gen = load(source)
    report = dict(task_id=TASK, generator_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  generator_path=str(source), sampler='generate(seed, consecutive sample_index, difficulty=band)',
                  oracle='independent Python specification, separately checked against canonical Racket')
    if args.baseline_counterexample:
        hit = None
        for band,seed,start in itertools.product(('easy','medium','hard'), range(100), range(8)):
            grids = [gen.generate(seed,start+i,difficulty=band) for i in range(4)]
            if all(overlay(g)==spec_frame(g) for g in grids[:3]) and overlay(grids[3])!=spec_frame(grids[3]):
                hit = (band,seed,start,grids); break
        if hit is None: raise RuntimeError('no baseline overlay ambiguity found in requested search')
        band,seed,start,grids = hit
        applied = Catalog(root).apply(TASK, grids)
        assert all(row['output']==spec_frame(g) for row,g in zip(applied['results'],grids))
        report.update(band=band, seed=seed, sample_indices=list(range(start,start+4)),
                      overrides={}, source_kind='pinned_baseline_inputs',
                      note='apply receipt binds the currently selected generator; input source is generator_sha256 above',
                      racket=applied, rival='overlay_frame', rival_outputs=[overlay(g) for g in grids],
                      fits_demonstrations=True, query_differs=True,
                      validators=[gen.self_check(g) for g in grids])
    else:
        counts=Counter(); inputs=set(); residual=Counter(); failed=[]
        rivals = {}
        for namespace in ('SEMANTIC_RIVALS','LESSON_COMPETITORS','CANONICAL_SHORTCUTS'):
            for name,fn in getattr(gen,namespace,{}).items(): rivals[f'{namespace}.{name}']=fn
        canonical=canonical_pairs(TASK,root=root)
        report['canonical_rival_fit']={name: all(fn(p['input'])==p['output'] for p in canonical)
                                       for name,fn in rivals.items()}
        # Exhaust all advertised size combinations at both color endpoints in
        # all bands and both schedule residues. Colors 2..8 are separately tested.
        for h,w,size,color,band,index in itertools.product(range(5,13),range(5,13),range(3,19),(1,9),('easy','medium','hard'),range(2)):
            ov=dict(grid_h=h,grid_w=w,motif_size=size,color=color)
            grid=gen.generate(73,index,difficulty=band,**ov)
            if gen.self_check(grid) or gen.observe_overrides(grid)!=ov or grid==spec_frame(grid):
                failed.append(dict(overrides=ov,band=band,index=index,input=grid))
            counts['joint_override_draws']+=1
        reference_grids=[]
        for band,seed in itertools.product(('easy','medium','hard'),range(100)):
            grids=[gen.generate(seed,i,difficulty=band) for i in range(12)]
            for g in grids:
                inputs.add(json.dumps(g,separators=(',',':')))
                counts['default_draws']+=1
                counts['interior_erase_draws']+=bool(pixels(g)-edges(g))
                h,w=len(g),len(g[0]);cells=pixels(g)
                counts['border_touch_draws']+=any(r in (0,h-1) or c in (0,w-1) for r,c in cells)
                counts['not_border_touch_draws']+=not any(r in (0,h-1) or c in (0,w-1) for r,c in cells)
                if gen.self_check(g) or g==spec_frame(g): failed.append(dict(band=band,seed=seed,input=g))
            if seed<5: reference_grids.extend(grids[:4])
            for start in range(8):
                block=grids[start:start+4]
                counts['consecutive_windows']+=1
                for q in range(4):
                    demos=[g for i,g in enumerate(block) if i!=q]
                    counts['rotations']+=1
                    for name,fn in rivals.items():
                        if all(fn(g)==spec_frame(g) for g in demos):
                            status='ambiguous' if fn(block[q])!=spec_frame(block[q]) else 'survived_all'
                            residual[f'{name}:{status}']+=1
                            if status=='ambiguous': failed.append(dict(band=band,seed=seed,start=start,query_index=q,rival=name,inputs=block))
        applied=Catalog(root).apply(TASK,reference_grids)
        mismatch=[i for i,row in enumerate(applied['results']) if row['output']!=spec_frame(reference_grids[i])]
        report.update(counts=dict(counts), default_seed_range=[0,99],default_sample_indices=[0,11],
                      cyclic_start_range=[0,7],joint_override_seed=73,unique_default_inputs=len(inputs),
                      rival_survivals=dict(residual),failures=failed,racket=applied,
                      racket_python_spec_mismatches=mismatch,
                      status='pass' if not failed and not mismatch else 'fail',
                      caveat='Finite declared-rival checks; overlapping windows are not independent lessons. Explicit size 3/4 overrides disable default teaching guarantees.')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k in ('generator_sha256','status','counts','unique_default_inputs','seed','band','sample_indices')},indent=2))
    return int(bool(report.get('failures') or report.get('racket_python_spec_mismatches')))

if __name__=='__main__': raise SystemExit(main())
