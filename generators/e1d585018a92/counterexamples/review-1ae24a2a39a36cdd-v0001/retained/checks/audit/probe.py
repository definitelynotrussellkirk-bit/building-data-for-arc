"""Findings-only: do not modify either randomly assigned target."""
import hashlib, importlib.util, json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root
ROOT=Path.cwd()
# In packet evidence, find_root locates repo via explicit current working directory.
OUT=ROOT.parent/'checks/audit'

def load(tid):
    path=ROOT/'generators'/tid/'generator.py'
    s=importlib.util.spec_from_file_location('audit_'+tid,path); m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return m,hashlib.sha256(path.read_bytes()).hexdigest()

def comps(grid, diagonal=False, target=None, ignore_marker=False):
    seen={(0,0)} if ignore_marker else set(); found=[]
    for r,row in enumerate(grid):
        for c,color in enumerate(row):
            if not color or (target is not None and color!=target) or (r,c) in seen:continue
            stack=[(r,c)];seen.add((r,c));cells=set()
            while stack:
                a,b=stack.pop();cells.add((a,b))
                offsets=[(i,j) for i in (-1,0,1) for j in (-1,0,1) if (i or j) and (diagonal or not (i and j))]
                for i,j in offsets:
                    x,y=a+i,b+j
                    if 0<=x<len(grid) and 0<=y<len(row) and grid[x][y]==color and (x,y) not in seen:
                        seen.add((x,y));stack.append((x,y))
            found.append((color,cells))
    return found

def crop_largest_ignoring_marker_color(grid):
    color,cells=max(comps(grid,ignore_marker=True),key=lambda p:len(p[1]))
    r0,r1=min(r for r,c in cells),max(r for r,c in cells)
    c0,c1=min(c for r,c in cells),max(c for r,c in cells)
    return [[color if (r,c) in cells else 0 for c in range(c0,c1+1)] for r in range(r0,r1+1)]

def every_blue_component_red_bbox(grid):
    out=[row[:] for row in grid]
    for color,cells in comps(grid,diagonal=True,target=1):
        r0,r1=min(r for r,c in cells),max(r for r,c in cells)
        c0,c1=min(c for r,c in cells),max(c for r,c in cells)
        for r in range(r0,r1+1):
            for c in range(c0,c1+1):out[r][c]=2
    return out

for tid,rival in [('e1d585018a92',crop_largest_ignoring_marker_color),('a74527c8b210',every_blue_component_red_bbox)]:
    gen,digest=load(tid)
    canon=canonical_pairs(tid,root=ROOT)
    cases=[dict(kind='canonical',canonical_pair_index=0,input=canon[0]['input'])]
    for band in ('easy','medium','hard'):
        for seed in range(6): cases.append(dict(kind='generated',seed=seed,sample_index=0,difficulty=band,overrides={},input=gen.generate(seed,0,difficulty=band)))
    if tid=='a74527c8b210':
        g=[[0]*7 for _ in range(7)];g[1][1]=g[1][2]=g[4][4]=g[5][5]=1
        cases.append(dict(kind='handmade',input=g,domain='validator admitted, lawful canonical rule, blue horizontal distractor absent from ordinary sampler'))
    for row in cases:row.update(validator_findings=gen.self_check(row['input']),rival_output=rival(row['input']))
    report=dict(task_id=tid,generator_sha256=digest,rival=rival.__name__,
                canonical_validator_results=[gen.self_check(p['input']) for p in canon],
                canonical_rival_match=[rival(p['input'])==p['output'] for p in canon],cases=cases)
    path=OUT/tid
    (path/'input.json').write_text(json.dumps([p['input'] for p in cases]))
    (path/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
    print(tid,'canonical validator',report['canonical_validator_results'],'rival matches',report['canonical_rival_match'])
