from __future__ import annotations
import hashlib, importlib.util, json
from collections import Counter, deque
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT/'repo'
OUT=Path(__file__).resolve().parent/'distribution_probe.json'

def load(task):
    p=REPO/'generators'/task/'generator.py'
    spec=importlib.util.spec_from_file_location('audit_'+task,p)
    m=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(m)
    return m,p

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def comps_by_nonzero(grid):
    h,w=len(grid),len(grid[0]); unseen={(r,c) for r in range(h) for c in range(w) if grid[r][c]!=0}; out=[]
    while unseen:
        s=min(unseen); unseen.remove(s); q=deque([s]); cells=[]
        while q:
            r,c=q.popleft(); cells.append((r,c))
            for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                p=(r+dr,c+dc)
                if p in unseen: unseen.remove(p); q.append(p)
        out.append(cells)
    return out

def comps_by_color(grid, banned=()):
    h,w=len(grid),len(grid[0]); seen=set(); out=[]
    for r0 in range(h):
        for c0 in range(w):
            color=grid[r0][c0]
            if color==0 or color in banned or (r0,c0) in seen: continue
            q=deque([(r0,c0)]); seen.add((r0,c0)); cells=[]
            while q:
                r,c=q.popleft(); cells.append((r,c))
                for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    nr,nc=r+dr,c+dc
                    if 0<=nr<h and 0<=nc<w and (nr,nc) not in seen and grid[nr][nc]==color:
                        seen.add((nr,nc)); q.append((nr,nc))
            out.append(cells)
    return out

reports=[]
for task in ('1d8a1c70332a','9c69eb63c11a'):
    m,p=load(task); counts=Counter(); failures=[]; unique=set()
    for band in ('easy','medium','hard'):
        for i in range(100):
            idx={'easy':0,'medium':100,'hard':200}[band]+i
            g=m.generate(44617,idx,difficulty=band)
            unique.add(json.dumps(g,separators=(',',':')))
            errs=m.self_check(g,difficulty=band)
            counts[f'{band}_draws']+=1
            counts[f'{band}_invalid']+=bool(errs)
            if errs and len(failures)<8: failures.append({'band':band,'index':idx,'errors':errs})
            if task=='1d8a1c70332a':
                n=len(comps_by_color(g,banned=(1,)))
                counts[f'{band}_non_color_1_components_{n}']+=1
            else:
                n=len(comps_by_nonzero(g))
                counts[f'{band}_nonzero_components_{n}']+=1
                if n==3:
                    sizes=tuple(sorted(map(len,comps_by_nonzero(g))))
                    counts[f'{band}_sizes_{sizes}']+=1
    reports.append({'task_id':task,'generator_sha256':sha(p),'seed':44617,'indices':'0..299 partitioned 100/band','summary':dict(sorted(counts.items())),'unique_inputs':len(unique),'sample_failures':failures})
OUT.write_text(json.dumps({'reports':reports},indent=2,sort_keys=True)+'\n')
print(json.dumps({'reports':reports},indent=2,sort_keys=True))
