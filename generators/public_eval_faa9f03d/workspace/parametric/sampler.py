"""Construct damaged networks from known paths, not stored puzzle grids.

A bounded construction check refuses ambiguous damage. It checks the recovered
geometry against independently built vertex paths, not against output labels.
"""
from pathlib import Path
import hashlib
import importlib.util
import random
import sys
BASE=Path(__file__).resolve().parent
p=BASE/'model.py';key='_path_model_'+hashlib.sha256(str(p).encode()).hexdigest()
if key not in sys.modules:
    spec=importlib.util.spec_from_file_location(key,p);m=importlib.util.module_from_spec(spec);sys.modules[key]=m;spec.loader.exec_module(m)
model=sys.modules[key]


def polyline(vertices):
    cells=set()
    for (r,c),(rr,cc) in zip(vertices,vertices[1:]):
        if r!=rr and c!=cc:raise ValueError('orthogonal vertices required')
        cells.update((y,x) for y in range(min(r,rr),max(r,rr)+1) for x in range(min(c,cc),max(c,cc)+1))
    return cells


def symmetries(grid,rotations,mirror):
    out=[row[::-1]for row in grid] if mirror else [row[:]for row in grid]
    for _ in range(rotations):out=[list(row)for row in zip(*out[::-1])]
    return out


def transform_cells(cells,h,w,rotations,mirror):
    out={(r,w-1-c if mirror else c)for r,c in cells}
    for _ in range(rotations):
        out={(c,h-1-r)for r,c in out};h,w=w,h
    return out


def scene(seed,index):
    if type(seed) is not int or not 0<=seed<2**63 or type(index) is not int or index<0:
        raise ValueError('seed and index must be nonnegative exact integers; seed < 2**63')
    for attempt in range(64):
        rng=random.Random(f'faa9f03d-v1:{seed}:{index}:{attempt}')
        stress=index==103;h=30 if stress else rng.randrange(23,31);w=30 if stress else rng.randrange(23,31)
        a=rng.randrange(3,6);b=h-rng.randrange(8,10);end=h-rng.randrange(2,4)
        x1=rng.randrange(5,7);x2=w-rng.randrange(6,8)
        bx=rng.randrange(x1+4,x2-2);br=h-5;low=1 if stress else rng.randrange(1,3)
        cr=rng.randrange(a+4,b-3);cx=w-rng.randrange(2,4)
        vertices=[[(a,0),(a,x1),(b,x1),(b,x2),(end,x2),(end,w-1)],
                  [(0,bx),(br,bx),(br,low),(h-1,low)],
                  [(cr,0),(cr,cx),(0,cx)]]
        palette=[1,3,5,6,7,8,9];rng.shuffle(palette);colors=palette[:3]
        if index==0:
            # Both source and reversed orders must be non-monotone in color ID.
            low_color,middle,high_color=sorted(colors)
            colors=[middle,low_color,high_color] if rng.randrange(2) else [middle,high_color,low_color]
        elif index==1:
            # The red owner is not permanently identified by its median color.
            choices=sorted(colors);colors=[choices[0],choices[2],choices[1]] if rng.randrange(2) else [choices[2],choices[0],choices[1]]
        masks=[polyline(v)for v in vertices]
        order=[1,2,0] if index%2==0 else [0,1,2]
        g=[[0]*w for _ in range(h)]
        for role in order:
            for r,c in masks[role]:g[r][c]=colors[role]
        crosses=set().union(*(masks[i]&masks[j]for i in range(3)for j in range(i+1,3)))
        if any(not masks[i]&masks[j]for i in range(3)for j in range(i+1,3)):continue
        corners=set(vertices[0][1:-1])
        for r,c in corners:g[r][c]=2
        changed=vertices[0][:]
        yellow=[]
        if index%4 in (0,3):
            yellow.append((a,x1+1));changed[0]=(a,w-1)
        if index%4==1:
            # Reverse at an earlier pivot: the old terminal arm contains two
            # later bends, not merely the adjacent straight segment.
            yellow.append((b,x1-1));changed=vertices[0][:3]+[(b,0)]
        if index%4 in (2,3):
            yellow.append((end,x2-1));changed[-1]=(end,0)
        if any(g[r][c] for r,c in yellow):continue
        for r,c in yellow:g[r][c]=4
        # Damage avoids turns/crossings; recoverability is independently checked.
        forbidden=set(crosses)|set(yellow)|set().union(*(set(v)for v in vertices))
        for role in range(3):
            choices=sorted(p for p in masks[role] if p not in forbidden and 0<p[0]<h-1 and 0<p[1]<w-1)
            rng.shuffle(choices);deleted=[]
            for p in choices:
                if any(abs(p[0]-q[0])+abs(p[1]-q[1])<=2 for q in deleted):continue
                if any(abs(p[0]-q[0])+abs(p[1]-q[1])<=1 for q in forbidden):continue
                g[p[0]][p[1]]=0;deleted.append(p)
                if len(deleted)==(5 if stress else 2+index%3):break
        if index in (0,1,103):
            for c in range(1,4):g[cr][c]=0
        rotated=rng.randrange(4);mirror=bool(rng.randrange(2))
        truth={colors[i]:transform_cells(masks[i],h,w,rotated,mirror)for i in range(3)}
        public_input=symmetries(g,rotated,mirror)
        recovered={p['color']:p['cells']for p in model.recover_paths(public_input)}
        if recovered!=truth:continue
        routed=[polyline(changed),masks[1],masks[2]]
        outputs={}
        for mode in model.MODES:
            paint=([0,1,2] if index%2==0 else [1,2,0]) if mode=='reverse_marked' else order
            out=[[0]*w for _ in range(h)]
            for role in paint:
                for r,c in routed[role]:out[r][c]=colors[role]
            outputs[mode]=symmetries(out,rotated,mirror)
        # The pure construction owns these expected outputs. This check rejects
        # inputs with ambiguous crossing observations or yellow associations.
        if any(model.solve(public_input,mode)!=out for mode,out in outputs.items()):continue
        return {'input':public_input,'paths':truth,'outputs':outputs,
                'marked_color':colors[0],'original_paint_order':[colors[i]for i in order],
                'construction_attempt':attempt,'yellow_count':len(yellow)}
    raise ValueError(f'No unambiguous damaged network for seed={seed}, index={index}')
