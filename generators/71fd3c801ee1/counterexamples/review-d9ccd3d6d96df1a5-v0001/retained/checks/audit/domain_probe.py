#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, importlib.util, json
from collections import Counter, deque
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]/'repo'
TASKS=('786a759f780e','71fd3c801ee1')

def load(task):
    p=ROOT/'generators'/task/'generator.py'
    s=importlib.util.spec_from_file_location('audit_'+task,p)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m,p

def components(g):
    h,w=len(g),len(g[0]); seen=set(); out=[]
    for r in range(h):
        for c in range(w):
            if g[r][c]==0 or (r,c) in seen: continue
            q=[(r,c)]; seen.add((r,c)); cells=[]
            while q:
                rr,cc=q.pop(); cells.append((rr,cc))
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr,nc=rr+dr,cc+dc
                    if 0<=nr<h and 0<=nc<w and g[nr][nc]!=0 and (nr,nc) not in seen:
                        seen.add((nr,nc)); q.append((nr,nc))
            out.append({'cells':cells,'color':g[cells[0][0]][cells[0][1]]})
    return out

def norm(cells):
    r0=min(r for r,c in cells); c0=min(c for r,c in cells)
    return tuple(sorted((r-r0,c-c0) for r,c in cells))

def holes(cells):
    r0=min(r for r,c in cells); r1=max(r for r,c in cells)
    c0=min(c for r,c in cells); c1=max(c for r,c in cells)
    solid={(r-r0,c-c0) for r,c in cells}; h=r1-r0+1; w=c1-c0+1
    seen=set(); count=0
    for r in range(h):
        for c in range(w):
            if (r,c) in solid or (r,c) in seen: continue
            q=[(r,c)]; seen.add((r,c)); touch=r in (0,h-1) or c in (0,w-1)
            while q:
                rr,cc=q.pop()
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr,nc=rr+dr,cc+dc
                    if 0<=nr<h and 0<=nc<w and (nr,nc) not in solid and (nr,nc) not in seen:
                        seen.add((nr,nc)); q.append((nr,nc)); touch |= nr in (0,h-1) or nc in (0,w-1)
            if not touch: count+=1
    return count

def sym_class(cells):
    n=norm(cells); h=max(r for r,c in n)+1; w=max(c for r,c in n)+1; s=set(n)
    row=all((h-1-r,c) in s for r,c in n)
    col=all((r,w-1-c) in s for r,c in n)
    return 3 if row and col else 1 if row else 2 if col else 0

def feature(cells): return (len(cells),holes(cells),sym_class(cells))

def feature_output(g):
    cs=components(g); counts=Counter(feature(x['cells']) for x in cs); out=copy.deepcopy(g)
    for x in cs:
        if counts[feature(x['cells'])]>1:
            for r,c in x['cells']: out[r][c]=8
    return out

def exact_output(g):
    cs=components(g); counts=Counter(norm(x['cells']) for x in cs); out=copy.deepcopy(g)
    for x in cs:
        if counts[norm(x['cells'])]>1:
            for r,c in x['cells']: out[r][c]=8
    return out

def crop_component(g, comp):
    cells=comp['cells']; r0=min(r for r,c in cells); r1=max(r for r,c in cells); c0=min(c for r,c in cells); c1=max(c for r,c in cells)
    out=[[0]*(c1-c0+1) for _ in range(r1-r0+1)]
    for r,c in cells: out[r-r0][c-c0]=g[r][c]
    return out

def strip_output(g, *, ignore_holes=False):
    cs=components(g)
    keyed=[]
    for comp in cs:
        key=((0 if ignore_holes else holes(comp['cells'])),len(comp['cells']),comp['color'])
        keyed.append((key,crop_component(g,comp)))
    keyed.sort(key=lambda x:x[0]); crops=[x[1] for x in keyed]
    h=max(len(x) for x in crops); w=sum(len(x[0]) for x in crops)+len(crops)-1
    out=[[0]*w for _ in range(h)]; left=0
    for crop in crops:
        for r,row in enumerate(crop):
            for c,v in enumerate(row):
                if v: out[r][left+c]=v
        left+=len(crop[0])+1
    return out

report={'schema':'audit-domain-probe-v2','draws_per_band':100,'bands':['easy','medium','hard'],'tasks':{}}
for task in TASKS:
    m,p=load(task); entry={'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bands':{},'first_nonexact_feature_collision':None}
    for band in report['bands']:
        b={'draws':0,'self_check_rejections':0,'components':0,'max_component_area':0,'max_holes':0,'draws_with_any_hole':0,'exact_shape_rival_matches_feature_rule':0,'draws_with_nonexact_feature_collision':0,'ignore_holes_rival_matches_hole_rule':0}
        for i in range(100):
            g=m.generate(100000+i,i,difficulty=band); cs=components(g); feats=[feature(x['cells']) for x in cs]; shapes=[norm(x['cells']) for x in cs]
            b['draws']+=1; b['self_check_rejections']+=bool(m.self_check(g,difficulty=band)); b['components']+=len(cs)
            b['max_component_area']=max(b['max_component_area'],*(len(x['cells']) for x in cs))
            b['max_holes']=max(b['max_holes'],*(holes(x['cells']) for x in cs))
            b['draws_with_any_hole']+=any(holes(x['cells'])>0 for x in cs)
            exact=exact_output(g); intended=feature_output(g)
            b['exact_shape_rival_matches_feature_rule']+=exact==intended
            nonexact=False
            for a in range(len(cs)):
                for z in range(a+1,len(cs)):
                    if feats[a]==feats[z] and shapes[a]!=shapes[z]: nonexact=True
            b['draws_with_nonexact_feature_collision']+=nonexact
            b['ignore_holes_rival_matches_hole_rule'] += strip_output(g,ignore_holes=True)==strip_output(g,ignore_holes=False)
            if nonexact and entry['first_nonexact_feature_collision'] is None:
                entry['first_nonexact_feature_collision']={'band':band,'seed':100000+i,'sample_index':i,'input':g,'features':[list(x) for x in feats],'shapes':[list(map(list,x)) for x in shapes]}
        entry['bands'][band]=b
    report['tasks'][task]=entry
out=Path('../checks/audit/domain-probe.json'); out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps(report,indent=2,sort_keys=True)[:12000])
