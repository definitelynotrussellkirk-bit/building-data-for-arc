"""One versus exactly two diagonal-midpoint completion passes."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import json, random
from typing import Any
HOME=Path(__file__).resolve().parent
CANONICAL_PROGRAM=(HOME/'canonical.rkt').read_text(encoding='utf-8')
TWO_PASS_PROGRAM=r'''(rule!
  (let ()
    (define (pass scene)
      (for*/fold ([out scene])
                 ([r (in-range (rows scene))]
                  [c (in-range (cols scene))]
                  [d (in-list (list (list 2 2) (list 2 -2)))])
        (let* ([v (at scene r c)]
               [nr (+ r (first d))] [nc (+ c (second d))]
               [mr (+ r (quotient (first d) 2))]
               [mc (+ c (quotient (second d) 2))])
          (if (and (not (= v 0))
                   (in-bounds? nr nc (rows scene) (cols scene))
                   (= (at scene nr nc) v)
                   (= (at out mr mc) 0))
              (set-cell out mr mc v)
              out))))
    (pass (pass g))))'''
PROGRAMS={1:CANONICAL_PROGRAM,2:TWO_PASS_PROGRAM}
SETTINGS=({'passes':1},{'passes':2})
DEMO_SPECS=((11,11),(11,17),(17,17),(17,23),(23,23),(24,30))
QUERY_SPECS=((12,12),(18,18),(24,24),(30,30))
DIRECTIONS=((2,2),(2,-2))

def _settings(value:Any)->int:
    if type(value) is not dict or set(value)!={'passes'}: raise ValueError('settings must contain exactly passes')
    n=value['passes']
    if type(n) is not int or n not in (1,2): raise ValueError('passes must be exact integer 1 or 2')
    return n

def _plain_int(name,value,lo,hi):
    if type(value) is not int: raise TypeError(f'{name} must be a plain integer')
    if not lo<=value<=hi: raise ValueError(f'{name} must be in {lo}..{hi}')

def apply_pass(grid):
    h,w=len(grid),len(grid[0]); out=[row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            v=grid[r][c]
            for dr,dc in DIRECTIONS:
                nr,nc=r+dr,c+dc; mr,mc=r+dr//2,c+dc//2
                if v and 0<=nr<h and 0<=nc<w and grid[nr][nc]==v and out[mr][mc]==0: out[mr][mc]=v
    return out

def label(grid,passes):
    out=[row[:] for row in grid]
    for _ in range(passes): out=apply_pass(out)
    return out

def closure(grid):
    out=[row[:] for row in grid]
    for _ in range(12):
        nxt=apply_pass(out)
        if nxt==out: return out
        out=nxt
    return out

def axis_plus_diagonal(grid,passes):
    out=[row[:] for row in grid]
    directions=((2,2),(2,-2),(2,0),(0,2))
    for _ in range(passes):
        src=[row[:] for row in out]; h,w=len(src),len(src[0])
        for r in range(h):
            for c in range(w):
                v=src[r][c]
                for dr,dc in directions:
                    nr,nc=r+dr,c+dc; mr,mc=r+dr//2,c+dc//2
                    if v and 0<=nr<h and 0<=nc<w and src[nr][nc]==v and out[mr][mc]==0: out[mr][mc]=v
    return out

def _orient(cells,k):
    pts=list(cells)
    if k>=4: pts=[(r,4-c) for r,c in pts]; k-=4
    for _ in range(k): pts=[(c,4-r) for r,c in pts]
    return pts
CASCADE=((0,1),(2,3),(3,0),(4,3))
SIMPLE=((0,0),(2,2))
STABLE=((0,0),(1,1),(2,2))
AXIS=((2,0),(2,2))
DIST4=((0,0),(4,4))

def build_input(seed,index,spec):
    h,w=spec; rng=random.Random((seed+1)*1_000_033+index*65_537+0x69927005)
    grid=[[0]*w for _ in range(h)]
    starts=[(r,c) for r in range(0,h-4,6) for c in range(0,w-4,6)]
    if not starts: raise RuntimeError('grid has no gadget slot')
    order=list(range(len(starts))); rng.shuffle(order)
    cascade_count=max(1,(4*len(starts)+4)//5)
    kinds=[CASCADE]*cascade_count
    decoys=(AXIS,STABLE,DIST4,SIMPLE)
    while len(kinds)<len(starts): kinds.append(decoys[(len(kinds)-cascade_count)%len(decoys)])
    rng.shuffle(kinds)
    # Force both a cascade and an axis rival witness in every scene with room.
    kinds[order[0]]=CASCADE
    if len(starts)>1: kinds[order[1]]=AXIS
    offset=rng.randrange(9)
    for slot,(r0,c0) in enumerate(starts):
        sr,sc=r0//6,c0//6; color=((sr*5+sc*2+offset)%9)+1
        cells=_orient(kinds[slot],rng.randrange(8))
        for r,c in cells:
            if grid[r0+r][c0+c]: raise RuntimeError('gadget collision')
            grid[r0+r][c0+c]=color
    one=apply_pass(grid); two=apply_pass(one); three=apply_pass(two)
    if one==two or two==three: raise RuntimeError('scene lacks exact-pass contrasts')
    if len(starts)>1 and axis_plus_diagonal(grid,1)==one: raise RuntimeError('axis rival not exposed')
    return grid

def teaching_check(episode,settings):
    n=_settings(settings); demos=episode['train']
    survivors=[s for s in SETTINGS if all(label(p['input'],s['passes'])==p['output'] for p in demos)]
    rivals=[]
    if all(closure(p['input'])==p['output'] for p in demos): rivals.append('closure')
    if all(axis_plus_diagonal(p['input'],n)==p['output'] for p in demos): rivals.append('axis_plus_diagonal')
    return {'surviving_settings':survivors,'surviving_rivals':rivals,'scope':'one/two passes plus closure and axis-inclusive rivals; demonstrations only'}

def program(settings): return PROGRAMS[_settings(settings)]
def generate(seed,settings,demos,queries):
    _plain_int('seed',seed,0,2**63-1); _plain_int('demos',demos,2,6)
    if type(queries) is not int or queries!=4: raise ValueError('queries must be exactly 4')
    n=_settings(settings); specs=list(DEMO_SPECS[:demos])+list(QUERY_SPECS)
    inputs=[build_input(seed,i,s) for i,s in enumerate(specs)]
    enc=[json.dumps(x,separators=(',',':')) for x in inputs]
    if len(enc)!=len(set(enc)): raise RuntimeError('episode inputs must be distinct')
    pairs=[{'input':deepcopy(g),'output':label(g,n)} for g in inputs]
    episode={'train':pairs[:demos],'test':pairs[demos:],'program_solution':program(settings)}
    cert=teaching_check(episode,settings); episode['certificate']=cert
    if cert['surviving_settings']!=[settings] or cert['surviving_rivals']: raise RuntimeError(f'teaching failure: {cert}')
    return episode

def counterfactual_skip_first_pass_program(): return CANONICAL_PROGRAM
