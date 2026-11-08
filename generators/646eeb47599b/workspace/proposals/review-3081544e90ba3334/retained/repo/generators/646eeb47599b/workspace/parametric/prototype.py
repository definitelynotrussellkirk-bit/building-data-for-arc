"""Episode-level branch-policy prototype for ARC generator 646eeb47599b.

The canonical production generator is deliberately not imported or modified by
this module.  Inputs are sampled without consulting the hidden branch setting;
only the wall reaction changes between settings.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import random
import subprocess
from collections import deque
from pathlib import Path
from typing import Iterable

TASK_ID='646eeb47599b'
SETTINGS=('split_both','clockwise_only','counterclockwise_only')
CANONICAL_SETTING='split_both'
COLORS={0,3,7,8}
HERE=Path(__file__).resolve().parent
GENERATOR=HERE.parents[1]/'generator.py'
REPO=HERE.parents[3]


def clockwise(direction: tuple[int,int]) -> tuple[int,int]:
    dr,dc=direction
    return dc,-dr


def counterclockwise(direction: tuple[int,int]) -> tuple[int,int]:
    dr,dc=direction
    return -dc,dr


def _seed_launches(grid: list[list[int]], launch_mode: str='outward') -> list[tuple[int,int,int,int]]:
    seeds=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==3]
    if len(seeds)!=2:
        raise ValueError(f'expected exactly two green seed cells, found {len(seeds)}')
    (r1,c1),(r2,c2)=sorted(seeds)
    if r1==r2 and abs(c1-c2)==1:
        if c1>c2: c1,c2=c2,c1
        outward=[(r1,c1-1,0,-1),(r1,c2+1,0,1)]
        four=[(r1,c1-1,0,-1),(r1,c1+1,0,1),(r1,c2-1,0,-1),(r1,c2+1,0,1)]
    elif c1==c2 and abs(r1-r2)==1:
        if r1>r2: r1,r2=r2,r1
        outward=[(r1-1,c1,-1,0),(r2+1,c1,1,0)]
        four=[(r1-1,c1,-1,0),(r1+1,c1,1,0),(r2-1,c1,-1,0),(r2+1,c1,1,0)]
    else:
        raise ValueError('green seed cells must be orthogonally adjacent')
    return outward if launch_mode=='outward' else four


def _solve_core(grid: list[list[int]], setting: str, config: dict[str,object]) -> list[list[int]]:
    if setting not in SETTINGS:
        raise ValueError(f'unknown setting: {setting}')
    if not grid:
        return []
    h=len(grid); w=len(grid[0])
    if any(len(row)!=w for row in grid):
        raise ValueError('ragged grid')
    out=[row[:] for row in grid]
    q=deque(_seed_launches(grid,str(config.get('launch_mode','outward'))))
    seen:set[tuple[int,int,int,int]]=set()
    while q:
        r,c,dr,dc=q.popleft()
        while 0<=r<h and 0<=c<w:
            state=(r,c,dr,dc)
            if state in seen:
                break
            seen.add(state)
            cell=grid[r][c]
            if cell==8:
                aligned_wall = bool(config.get('cyan_along_pass',False)) and (
                    (dr != 0 and ((0 <= r-dr < h and grid[r-dr][c] == 8) or (0 <= r+dr < h and grid[r+dr][c] == 8))) or
                    (dc != 0 and ((0 <= c-dc < w and grid[r][c-dc] == 8) or (0 <= c+dc < w and grid[r][c+dc] == 8)))
                )
                if aligned_wall:
                    r += dr; c += dc
                    continue
                dirs=[]
                if setting in ('split_both','clockwise_only'):
                    dirs.append(clockwise((dr,dc)))
                if setting in ('split_both','counterclockwise_only'):
                    dirs.append(counterclockwise((dr,dc)))
                if bool(config.get('straight_at_wall',False)):
                    dirs.append((dr,dc))
                for nr,nc in dirs:
                    q.append((r+nr,c+nc,nr,nc))
                break
            if cell==7:
                out[r][c]=3
                if bool(config.get('orange_stops',False)):
                    break
            elif cell not in (0,3):
                if bool(config.get('other_stops',True)):
                    break
            r+=dr; c+=dc
    return out


def _find_task_path() -> Path | None:
    candidates=[]
    for p in REPO.rglob('6bcdb01e.json'):
        if p.is_file(): candidates.append(p)
    if not candidates:
        return None
    candidates.sort(key=lambda p: (0 if 'training' in p.parts else 1,len(str(p))))
    return candidates[0]


def _load_training() -> list[dict[str,object]]:
    p=_find_task_path()
    if p is None:
        return []
    obj=json.loads(p.read_text())
    return list(obj.get('train',[]))


def _candidate_configs() -> Iterable[dict[str,object]]:
    for launch in ('outward','four'):
        for straight in (False,True):
            for orange_stops in (False,True):
                for cyan_along_pass in (False,True):
                    for other_stops in (True,False):
                        yield {'launch_mode':launch,'straight_at_wall':straight,'orange_stops':orange_stops,'cyan_along_pass':cyan_along_pass,'other_stops':other_stops}


def _select_semantics() -> dict[str,object]:
    train=_load_training()
    default={'launch_mode':'outward','straight_at_wall':False,'orange_stops':False,'cyan_along_pass':True,'other_stops':True}
    if not train:
        return default
    scored=[]
    for cfg in _candidate_configs():
        matches=0
        for pair in train:
            try:
                matches += _solve_core(pair['input'],CANONICAL_SETTING,cfg)==pair['output']
            except Exception:
                pass
        scored.append((matches,cfg))
    scored.sort(key=lambda x:(x[0],x[1]==default),reverse=True)
    return dict(scored[0][1])


SEMANTICS=_select_semantics()


def solve(grid: list[list[int]], setting: str=CANONICAL_SETTING) -> list[list[int]]:
    return _solve_core(grid,setting,SEMANTICS)


def _rotate(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def make_scene(seed: int) -> list[list[int]]:
    """Create a lawful rich input without consulting the hidden setting."""
    rng=random.Random(seed)
    h=rng.choice((11,13,15)); w=rng.choice((11,13,15))
    r=rng.randint(4,h-5)
    c1=w//2-1; c2=c1+1
    left=rng.randint(1,c1-2); right=rng.randint(c2+2,w-2)
    grid=[[0 for _ in range(w)] for _ in range(h)]
    grid[r][c1]=grid[r][c2]=3
    grid[r][left]=grid[r][right]=8
    up_l=rng.randint(1,r-2); down_l=rng.randint(r+2,h-2)
    up_r=rng.randint(1,r-2); down_r=rng.randint(r+2,h-2)
    for rr,cc in ((up_l,left),(down_l,left),(up_r,right),(down_r,right)):
        grid[rr][cc]=7
    # Add setting-irrelevant distractors away from the laser row and wall columns.
    forbidden_rows={r}; forbidden_cols={left,right}
    available=[(rr,cc) for rr in range(1,h-1) for cc in range(1,w-1)
               if rr not in forbidden_rows and cc not in forbidden_cols and grid[rr][cc]==0]
    rng.shuffle(available)
    for rr,cc in available[:rng.randint(0,3)]:
        grid[rr][cc]=7
    for _ in range(rng.randrange(4)):
        grid=_rotate(grid)
    return grid


def converted_targets(before: list[list[int]], after: list[list[int]]) -> int:
    return sum(a==7 and b==3 for ra,rb in zip(before,after) for a,b in zip(ra,rb))


def is_lawful_scene(grid: list[list[int]]) -> bool:
    if not grid or not grid[0] or any(len(row)!=len(grid[0]) for row in grid):
        return False
    if {v for row in grid for v in row} - COLORS:
        return False
    seeds=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==3]
    return len(seeds)==2 and abs(seeds[0][0]-seeds[1][0])+abs(seeds[0][1]-seeds[1][1])==1


def build_episode(seed: int, setting: str) -> dict[str,object]:
    if setting not in SETTINGS:
        raise ValueError(setting)
    pairs=[]
    i=0
    while len(pairs)<4:
        grid=make_scene(seed*1009+i)
        i+=1
        outs=[solve(grid,s) for s in SETTINGS]
        if len({json.dumps(x,separators=(',',':')) for x in outs})!=3:
            continue
        pairs.append({'input':grid,'output':solve(grid,setting)})
    return {
        'task_id':TASK_ID,
        'parameter':{'name':'branch_mode','setting':setting,'alternatives':list(SETTINGS)},
        'semantics':dict(SEMANTICS),
        'demonstrations':pairs[:3],
        'query':pairs[3],
    }


def public_projection(episode: dict[str,object]) -> dict[str,object]:
    public=copy.deepcopy(episode)
    public['query'].pop('output',None)
    public['parameter'].pop('setting',None)
    return public


def extract_canonical_program() -> str:
    """Extract, byte-for-byte, the largest embedded Racket rule from generator.py."""
    source=GENERATOR.read_text()
    tree=ast.parse(source)
    candidates=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Constant) and isinstance(node.value,str) and '(rule!' in node.value:
            candidates.append(node.value)
    if not candidates:
        # Some generators expose a module-level value assembled from constants.
        spec=importlib.util.spec_from_file_location('_parametric_target_generator',GENERATOR)
        if spec and spec.loader:
            mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
            candidates.extend(v for v in vars(mod).values() if isinstance(v,str) and '(rule!' in v)
    if not candidates:
        raise RuntimeError('could not locate embedded canonical Racket program')
    return max(candidates,key=len)


def canonical_program_sha256() -> str:
    return hashlib.sha256(extract_canonical_program().encode()).hexdigest()


def run_racket(grid: list[list[int]], setting: str) -> list[list[int]]:
    script=HERE/'racket'/f'{setting}.rkt'
    payload=json.dumps({'grid':grid,'config':SEMANTICS},separators=(',',':'))
    proc=subprocess.run(['racket',str(script)],input=payload,text=True,capture_output=True,timeout=20)
    if proc.returncode:
        raise RuntimeError(f'Racket failed ({proc.returncode}): {proc.stderr}')
    return json.loads(proc.stdout)


def check_canonical_training() -> tuple[int,list[dict[str,object]]]:
    mismatches=[]; train=_load_training()
    for i,pair in enumerate(train):
        got=solve(pair['input'],CANONICAL_SETTING)
        if got!=pair['output']:
            mismatches.append({'index':i,'input':pair['input'],'expected':pair['output'],'actual':got})
    return len(train),mismatches
