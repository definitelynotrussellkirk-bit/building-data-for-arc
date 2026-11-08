"""Cumulative transform gallery with an input-derived final-cue projection variant."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import json, random
from typing import Any

HOME=Path(__file__).resolve().parent
CANONICAL_PROGRAM=(HOME/'canonical.rkt').read_text(encoding='utf-8')
FINAL_CUE_PROGRAM=r'''(rule!
  (let ()
    (define (paste-crop grid crop r0 c0)
      (for*/fold ([out grid]) ([r (in-range (rows crop))] [c (in-range (cols crop))])
        (let ([v (at crop r c)])
          (if (= v 0) out (set-cell out (+ r0 r) (+ c0 c) v)))))
    (define (gallery crops)
      (let* ([h (apply max (map rows crops))]
             [w (+ (apply + (map cols crops)) (sub1 (length crops)))])
        (let loop ([xs crops] [left 0] [out (empty-grid h w 0)])
          (if (empty? xs) out
              (let ([crop (first xs)])
                (loop (rest xs) (+ left (cols crop) 1)
                      (paste-crop out crop 0 left)))))))
    (define (transform-by-key scene key)
      (cond [(= key 1) (rotate-cw scene)]
            [(= key 2) (rotate-180 scene)]
            [(= key 3) (flip-lr scene)]
            [(= key 4) (flip-ud scene)]
            [else scene]))
    (define (states crop keys)
      (let loop ([remaining keys] [cur crop] [acc (list crop)])
        (if (empty? remaining) (reverse acc)
            (let ([next (transform-by-key cur (first remaining))])
              (loop (rest remaining) next (cons next acc))))))
    (let* ([keys (filter (lambda (v) (not (= v 0))) (first g))]
           [crop (crop-to-content (rest g) 0)]
           [full-states (states crop keys)]
           [final (first (reverse full-states))]
           [cue (first (for*/list ([r (in-range (rows final))]
                                   [c (in-range (cols final))]
                                   #:when (not (= (at final r c) 0)))
                         (at final r c)))]
           [masked (cellmap crop (r c v) (if (= v cue) v 0))])
      (gallery (states masked keys)))))'''
PROGRAMS={'cumulative':CANONICAL_PROGRAM,'final_cue_projection':FINAL_CUE_PROGRAM}
SETTINGS=tuple({'gallery_mode':x} for x in PROGRAMS)
DEMO_SPECS=((8,12,3,4,2),(10,15,4,4,3),(12,18,3,5,4),(14,20,5,5,2),(16,22,4,5,3),(18,24,5,5,4))
QUERY_SPECS=((9,14,4,3,3),(13,19,5,4,4),(20,27,5,5,4),(30,30,5,5,4))
SEQUENCES=((1,3),(2,4,1),(3,1,1,4),(4,2),(1,4,3),(2,1,3,4),(3,2,1),(4,1,2,3))

def _settings(value:Any)->str:
    if type(value) is not dict or set(value)!={'gallery_mode'}: raise ValueError('settings must contain exactly gallery_mode')
    mode=value['gallery_mode']
    if type(mode) is not str or mode not in PROGRAMS: raise ValueError('gallery_mode must be cumulative or final_cue_projection')
    return mode

def _plain_int(name,value,lo,hi):
    if type(value) is not int: raise TypeError(f'{name} must be a plain integer')
    if not lo<=value<=hi: raise ValueError(f'{name} must be in {lo}..{hi}')
    return value

def rotate_cw(g): return [list(row) for row in zip(*g[::-1])]
def rotate_180(g): return [row[::-1] for row in g[::-1]]
def flip_lr(g): return [row[::-1] for row in g]
def flip_ud(g): return [row[:] for row in g[::-1]]
def transform(g,key):
    return {1:rotate_cw,2:rotate_180,3:flip_lr,4:flip_ud}[key](g)
def script_states(crop,keys):
    states=[deepcopy(crop)]; cur=deepcopy(crop)
    for key in keys:
        cur=transform(cur,key); states.append(cur)
    return states

def gallery(crops):
    h=max(map(len,crops)); w=sum(len(x[0]) for x in crops)+len(crops)-1
    out=[[0]*w for _ in range(h)]; left=0
    for crop in crops:
        for r,row in enumerate(crop):
            for c,v in enumerate(row):
                if v: out[r][left+c]=v
        left+=len(crop[0])+1
    return out

def final_cue_color(crop,keys):
    final=script_states(crop,keys)[-1]
    return next(v for row in final for v in row if v)
def project_color(crop,color): return [[v if v==color else 0 for v in row] for row in crop]

def _parse(grid):
    keys=[v for v in grid[0] if v]
    cells=[(r,c) for r in range(1,len(grid)) for c,v in enumerate(grid[r]) if v]
    if not keys or not cells: raise ValueError('input needs keys and motif')
    r0=min(r for r,c in cells); r1=max(r for r,c in cells); c0=min(c for r,c in cells); c1=max(c for r,c in cells)
    return keys,[row[c0:c1+1] for row in grid[r0:r1+1]]

def label(grid,mode):
    keys,crop=_parse(grid)
    if mode=='cumulative': return gallery(script_states(crop,keys))
    if mode=='final_cue_projection':
        cue=final_cue_color(crop,keys)
        return gallery(script_states(project_color(crop,cue),keys))
    raise ValueError('unknown mode')

def _rival(grid,name):
    keys,crop=_parse(grid)
    if name=='independent_transforms': return gallery([crop]+[transform(crop,k) for k in keys])
    if name=='original_first_projection': return gallery(script_states(project_color(crop,next(v for row in crop for v in row if v)),keys))
    if name=='fixed_min_projection': return gallery(script_states(project_color(crop,min(v for row in crop for v in row if v)),keys))
    raise ValueError(name)

def _motif(rng,h,w):
    palette=[5,6,7,8,9]; rng.shuffle(palette); corners=palette[:4]
    g=[[palette[(r*w+c+r+c)%len(palette)] for c in range(w)] for r in range(h)]
    g[0][0],g[0][-1],g[-1][0],g[-1][-1]=corners
    # Repeat each directional cue away from its corner so projection is substantive.
    spots=[(h//2,0),(0,w//2),(h-1,w//2),(h//2,w-1)]
    for p,color in zip(spots,corners): g[p[0]][p[1]]=color
    return g

def build_input(seed,index,spec):
    h,w,mh,mw,nkeys=spec; rng=random.Random((seed+1)*1_000_003+index*97_409+0x6F6C567E)
    crop=_motif(rng,mh,mw)
    candidates=list(SEQUENCES); rng.shuffle(candidates)
    keys=None
    for seq in candidates:
        seq=seq[:nkeys]
        if (len(seq)==nkeys and final_cue_color(crop,seq)!=crop[0][0]
                and final_cue_color(crop,seq)!=min(v for row in crop for v in row if v)):
            keys=list(seq); break
    if keys is None: raise RuntimeError('no distinguishing key script')
    grid=[[0]*w for _ in range(h)]
    if (h,w)==(30,30):
        cols=[0,w-1,w//3,2*w//3][:nkeys]; r0=h-mh; c0=w-mw
    else:
        cols=sorted(rng.sample(range(w),nkeys)); r0=rng.randint(2,h-mh); c0=rng.randint(0,w-mw)
    for c,k in zip(cols,keys): grid[0][c]=k
    for r,row in enumerate(crop): grid[r0+r][c0:c0+mw]=row
    if label(grid,'cumulative')==label(grid,'final_cue_projection'): raise RuntimeError('settings collapsed')
    return grid

def teaching_check(episode,settings):
    demos=episode['train']
    survivors=[s for s in SETTINGS if all(label(p['input'],s['gallery_mode'])==p['output'] for p in demos)]
    rivals=[name for name in ('independent_transforms','original_first_projection','fixed_min_projection') if all(_rival(p['input'],name)==p['output'] for p in demos)]
    return {'surviving_settings':survivors,'surviving_rivals':rivals,'scope':'two settings and three named shortcut families; demonstrations only'}

def program(settings): return PROGRAMS[_settings(settings)]
def generate(seed,settings,demos,queries):
    _plain_int('seed',seed,0,2**63-1); _plain_int('demos',demos,2,6)
    if type(queries) is not int or queries!=4: raise ValueError('queries must be exactly 4')
    mode=_settings(settings); specs=list(DEMO_SPECS[:demos])+list(QUERY_SPECS)
    inputs=[build_input(seed,i,s) for i,s in enumerate(specs)]
    enc=[json.dumps(x,separators=(',',':')) for x in inputs]
    if len(enc)!=len(set(enc)): raise RuntimeError('episode inputs must be distinct')
    pairs=[{'input':deepcopy(g),'output':label(g,mode)} for g in inputs]
    episode={'train':pairs[:demos],'test':pairs[demos:],'program_solution':program(settings)}
    cert=teaching_check(episode,settings); episode['certificate']=cert
    if cert['surviving_settings']!=[settings] or cert['surviving_rivals']: raise RuntimeError(f'teaching failure: {cert}')
    return episode

def counterfactual_program(color:int)->str:
    if type(color) is not int or not 1<=color<=9: raise ValueError('color must be 1..9')
    return FINAL_CUE_PROGRAM.replace('[cue (first (for*/list ([r (in-range (rows final))]\n                                   [c (in-range (cols final))]\n                                   #:when (not (= (at final r c) 0)))\n                         (at final r c)))]',f'[cue {color}]')
