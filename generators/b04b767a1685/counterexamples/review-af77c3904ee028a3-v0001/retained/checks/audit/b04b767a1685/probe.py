#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, sys
from collections import deque
from pathlib import Path

TASK='b04b767a1685'
work=Path(__file__).resolve().parents[3]
repo=work/'repo'
sys.path[:0]=[str(repo/'src'),str(repo/'shared/runtime')]
from reviewer_support import canonical_pairs, find_root

src=repo/'generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audit_b04',src)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def components(grid):
    h,w=len(grid),len(grid[0]); unseen={(r,c) for r in range(h) for c in range(w) if grid[r][c]!=0}; out=[]
    while unseen:
        start=min(unseen); unseen.remove(start); q=deque([start]); comp=[start]
        while q:
            r,c=q.popleft()
            for nr,nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if (nr,nc) in unseen:
                    unseen.remove((nr,nc)); q.append((nr,nc)); comp.append((nr,nc))
        out.append(comp)
    return out

def crop_cells(grid,cells):
    if not cells: return [[0]]
    r0=min(r for r,c in cells); r1=max(r for r,c in cells); c0=min(c for r,c in cells); c1=max(c for r,c in cells)
    return [row[c0:c1+1] for row in grid[r0:r1+1]]

def rival(grid):
    comps=components(grid)
    # Largest component; deterministic row-major tie break.
    chosen=min(comps,key=lambda comp:(-len(comp),min(comp))) if comps else []
    return crop_cells(grid,chosen)

def first_diff(a,b):
    if (len(a),len(a[0]))!=(len(b),len(b[0])): return {'shape_truth':[len(a),len(a[0])],'shape_rival':[len(b),len(b[0])]}
    for r,(ra,rb) in enumerate(zip(a,b)):
        for c,(x,y) in enumerate(zip(ra,rb)):
            if x!=y:return {'row':r,'column':c,'truth':x,'rival':y}
    return None
pairs=canonical_pairs(TASK,root=find_root(repo))
canon=[rival(p['input'])==p['output'] for p in pairs]
rows=[]
for band in ('easy','medium','hard'):
    for i in range(200):
        g=mod.generate(120000+i,i,difficulty=band)
        nonzero=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v]
        truth=crop_cells(g,nonzero)
        rows.append({'band':band,'match':rival(g)==truth})
ce=mod.generate(1,2,texture='multiple_motifs')
receipt=json.loads((work/'checks/audit'/TASK/'racket.json').read_text())
truth=receipt['results'][0]['output']
report={
 'schema':'arcpuzzles-audit-counterexample-v1','task_id':TASK,
 'finding':'Default and canonical scenes allow “crop only the largest nonzero 4-connected component” to replace the intended global nonzero bounding box.',
 'generator_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
 'executed_rule_hash':receipt['executed_rule_hash'],
 'canonical_check':{'pairs':len(canon),'rival_matches':sum(canon),'fits_all':all(canon)},
 'default_check':{'draws':len(rows),'bands':['easy','medium','hard'],'per_band':200,'rival_matches':sum(x['match'] for x in rows)},
 'counterexample':{'source':'generate(seed=1,sample_index=2,texture="multiple_motifs")','input':ce,'self_check':mod.self_check(ce),'racket_output':truth,'rival_output':rival(ce),'first_difference':first_diff(truth,rival(ce))},
 'domain_note':'The counterexample is emitted by the advertised texture override and passes self_check, although the prose invariant describes only one motif.',
 'apply_command':receipt['command'],'apply_cwd':receipt['cwd']}
out=work/'checks/audit'/TASK/'finding.json'; out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('generator_sha256','canonical_check','default_check','counterexample')},indent=2))
assert ce==receipt['results'][0]['input']
assert all(canon) and report['default_check']['rival_matches']==600 and truth!=rival(ce) and not mod.self_check(ce)
