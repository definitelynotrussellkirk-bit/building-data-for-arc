from __future__ import annotations
import json
from collections import deque
from itertools import product
from pathlib import Path

SETTINGS=('split_both','clockwise_only','counterclockwise_only')

def cw(d):
    dr,dc=d; return dc,-dr

def ccw(d):
    dr,dc=d; return -dc,dr

def launches(grid,launch):
    s=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==3]
    if len(s)!=2: raise ValueError
    s=sorted(s); (r1,c1),(r2,c2)=s
    if r1==r2 and abs(c1-c2)==1:
        lo,hi=sorted((c1,c2)); out=[(r1,lo-1,0,-1),(r1,hi+1,0,1)]
        four=out+[(r1,lo+1,0,1),(r1,hi-1,0,-1)]
    elif c1==c2 and abs(r1-r2)==1:
        lo,hi=sorted((r1,r2)); out=[(lo-1,c1,-1,0),(hi+1,c1,1,0)]
        four=out+[(lo+1,c1,1,0),(hi-1,c1,-1,0)]
    else: raise ValueError
    return out if launch=='outward' else four

def solve(grid,setting,cfg):
    if not grid:return []
    h,w=len(grid),len(grid[0]); out=[row[:] for row in grid]
    q=deque(launches(grid,cfg['launch_mode'])); seen=set()
    while q:
        r,c,dr,dc=q.popleft()
        if not (0<=r<h and 0<=c<w): continue
        st=(r,c,dr,dc)
        if st in seen: continue
        seen.add(st); cell=grid[r][c]
        if cell==8:
            aligned=cfg['cyan_along_pass'] and (
                (dr!=0 and ((0<=r-dr<h and grid[r-dr][c]==8) or (0<=r+dr<h and grid[r+dr][c]==8))) or
                (dc!=0 and ((0<=c-dc<w and grid[r][c-dc]==8) or (0<=c+dc<w and grid[r][c+dc]==8))))
            if aligned:
                q.append((r+dr,c+dc,dr,dc)); continue
            ds=[]
            if setting in ('split_both','clockwise_only'): ds.append(cw((dr,dc)))
            if setting in ('split_both','counterclockwise_only'): ds.append(ccw((dr,dc)))
            if cfg['straight_at_wall']: ds.append((dr,dc))
            for nr,nc in ds:q.append((r+nr,c+nc,nr,nc))
        elif cell==7:
            out[r][c]=3
            if not cfg['orange_stops']: q.append((r+dr,c+dc,dr,dc))
        elif cell in (0,3):
            q.append((r+dr,c+dc,dr,dc))
        elif not cfg['other_stops']:
            q.append((r+dr,c+dc,dr,dc))
    return out

def candidates():
    for setting in SETTINGS:
      for launch,straight,ostop,calong,otherstop in product(
          ('outward','four'),(False,True),(False,True),(False,True),(True,False)):
        yield setting,dict(launch_mode=launch,straight_at_wall=straight,orange_stops=ostop,
                           cyan_along_pass=calong,other_stops=otherstop)

challenge=json.loads(Path(__file__).with_name('challenge.json').read_text())
train=challenge['train']
valid=[]
for setting,cfg in candidates():
    try:
        if all(solve(p['input'],setting,cfg)==p['output'] for p in train):
            valid.append((setting,cfg))
    except Exception:
        pass
if not valid:
    raise SystemExit('No candidate matched all visible demonstrations')
# Prefer the minimal/canonical interpretation among observationally equivalent candidates.
def rank(item):
    setting,c=item
    return (setting!='split_both',c['launch_mode']!='outward',c['straight_at_wall'],c['orange_stops'],not c['cyan_along_pass'],not c['other_stops'])
setting,cfg=min(valid,key=rank)
Path(__file__).with_name('visible-calibration.json').write_text(json.dumps({
    'matching_candidates':len(valid),'selected_setting':setting,'selected_config':cfg
},indent=2)+'\n')

solution=f'''"""Visible-demonstration solution for the post-repair solve."""
from collections import deque
SETTING={setting!r}
CONFIG={cfg!r}

def _cw(d):
    dr,dc=d; return dc,-dr

def _ccw(d):
    dr,dc=d; return -dc,dr

def _launches(grid):
    s=sorted((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==3)
    if len(s)!=2: raise ValueError("expected two green seed cells")
    (r1,c1),(r2,c2)=s
    if r1==r2 and abs(c1-c2)==1:
        lo,hi=sorted((c1,c2)); out=[(r1,lo-1,0,-1),(r1,hi+1,0,1)]
        four=out+[(r1,lo+1,0,1),(r1,hi-1,0,-1)]
    elif c1==c2 and abs(r1-r2)==1:
        lo,hi=sorted((r1,r2)); out=[(lo-1,c1,-1,0),(hi+1,c1,1,0)]
        four=out+[(lo+1,c1,1,0),(hi-1,c1,-1,0)]
    else: raise ValueError("seed cells must be adjacent")
    return out if CONFIG["launch_mode"]=="outward" else four

def solve(grid):
    if not grid:return []
    h,w=len(grid),len(grid[0]); out=[row[:] for row in grid]
    q=deque(_launches(grid)); seen=set()
    while q:
        r,c,dr,dc=q.popleft()
        if not (0<=r<h and 0<=c<w): continue
        state=(r,c,dr,dc)
        if state in seen: continue
        seen.add(state); cell=grid[r][c]
        if cell==8:
            aligned=CONFIG["cyan_along_pass"] and (
                (dr!=0 and ((0<=r-dr<h and grid[r-dr][c]==8) or (0<=r+dr<h and grid[r+dr][c]==8))) or
                (dc!=0 and ((0<=c-dc<w and grid[r][c-dc]==8) or (0<=c+dc<w and grid[r][c+dc]==8))))
            if aligned:
                q.append((r+dr,c+dc,dr,dc)); continue
            dirs=[]
            if SETTING in ("split_both","clockwise_only"): dirs.append(_cw((dr,dc)))
            if SETTING in ("split_both","counterclockwise_only"): dirs.append(_ccw((dr,dc)))
            if CONFIG["straight_at_wall"]: dirs.append((dr,dc))
            for nr,nc in dirs:q.append((r+nr,c+nc,nr,nc))
        elif cell==7:
            out[r][c]=3
            if not CONFIG["orange_stops"]: q.append((r+dr,c+dc,dr,dc))
        elif cell in (0,3):
            q.append((r+dr,c+dc,dr,dc))
        elif not CONFIG["other_stops"]:
            q.append((r+dr,c+dc,dr,dc))
    return out
'''
Path(__file__).with_name('solution.py').write_text(solution)
