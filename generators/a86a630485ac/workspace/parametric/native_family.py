"""Symmetry eligibility followed by occupied-cell ranking, with all ties kept.

The exact LR/all authority is preserved. Alternative labels are deterministic
Python claims independently executed by native protected-Racket qualification.
Ten constructive inputs are fixed before count slicing; query order has its own
seed stream, independent of settings and requested demonstration/query counts.
"""
from __future__ import annotations

from collections import deque
import hashlib
import itertools
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
AXES=("lr","ud")
POLICIES=("all","largest_eligible")
DEFAULT={"axis":"lr","keep_policy":"all"}
SETTINGS=tuple({"axis":a,"keep_policy":p} for a,p in itertools.product(AXES,POLICIES))


def _integer(value,name,lo,hi):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _settings(settings):
    if type(settings) is not dict or set(settings)!={"axis","keep_policy"}:
        raise ValueError("settings must name exactly axis and keep_policy")
    if type(settings["axis"]) is not str or settings["axis"] not in AXES:
        raise ValueError("axis must be lr or ud")
    if type(settings["keep_policy"]) is not str or settings["keep_policy"] not in POLICIES:
        raise ValueError("keep_policy must be all or largest_eligible")
    return settings["axis"],settings["keep_policy"]


def validate_grid(grid):
    if (type(grid) is not list or not 6 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 6 <= len(grid[0]) <= 30):
        raise ValueError("native grids must have dimensions 6..30")
    w=len(grid[0])
    if any(type(row) is not list or len(row)!=w
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("expected rectangular exact-integer color grids")


def components(grid):
    """Monochrome four-connected components, ordered by first row-major cell."""
    validate_grid(grid)
    h,w=len(grid),len(grid[0])
    seen=set()
    result=[]
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r,c) in seen:
                continue
            color=grid[r][c]
            cells=[]
            queue=deque([(r,c)])
            seen.add((r,c))
            while queue:
                rr,cc=queue.popleft()
                cells.append((rr,cc))
                for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    nr,nc=rr+dr,cc+dc
                    if (0 <= nr < h and 0 <= nc < w and (nr,nc) not in seen
                            and grid[nr][nc]==color):
                        seen.add((nr,nc))
                        queue.append((nr,nc))
            cells=tuple(sorted(cells))
            result.append({"color":color,"cells":cells,"size":len(cells),
                           "bbox":(min(x for x,y in cells),min(y for x,y in cells),
                                   max(x for x,y in cells),max(y for x,y in cells))})
    return result


def is_symmetric(cells,axis):
    if axis not in AXES:
        raise ValueError("axis must be lr or ud")
    cells=set(cells)
    if not cells:
        return False
    minr,maxr=min(r for r,c in cells),max(r for r,c in cells)
    minc,maxc=min(c for r,c in cells),max(c for r,c in cells)
    reflected={(r,minc+maxc-c) if axis=="lr" else (minr+maxr-r,c) for r,c in cells}
    return cells==reflected


def apply_python(grid,settings):
    axis,policy=_settings(settings)
    objects=components(grid)
    eligible=[o for o in objects if is_symmetric(o["cells"],axis)]
    if policy=="largest_eligible" and eligible:
        best=max(o["size"] for o in eligible)
        eligible=[o for o in eligible if o["size"]==best]
    out=[[0]*len(grid[0]) for _ in grid]
    for obj in eligible:
        for r,c in obj["cells"]:
            out[r][c]=obj["color"]
    return out


def program(settings):
    axis,policy=_settings(settings)
    if settings==DEFAULT:
        return (HERE/"canonical.rkt").read_text()
    reflected="(list (first p) (- mc (second p)))" if axis=="lr" else "(list (- mr (first p)) (second p))"
    selection="(selected eligible)" if policy=="all" else """(ranked eligible)
             (best (if (empty? ranked) 0 (apply max (map obj-size ranked))))
             (selected (filter (lambda (o) (= (obj-size o) best)) eligible))"""
    return f"""(rule! (lambda (g)
      (let* ((objs (objects g 0))
             (symmetric? (lambda (o)
               (let* ((cells (normalize-cells (obj-cells o)))
                      (mr (apply max (map first cells)))
                      (mc (apply max (map second cells))))
                 (all? (lambda (p) (member? {reflected} cells)) cells))))
             (eligible (filter symmetric? objs))
             {selection})
        (reduce (lambda (out obj) (paint-cells out (obj-cells obj) (obj-color obj)))
                (empty-grid (rows g) (cols g) 0) selected))))"""


def _solid(h,w=None):
    w=h if w is None else w
    return tuple((r,c) for r in range(h) for c in range(w))


def _near_square(n):
    return tuple((r,c) for r,c in _solid(n) if (r,c)!=(n-1,n-1))


def _ring(n):
    return tuple((r,c) for r in range(n) for c in range(n) if r in (0,n-1) or c in (0,n-1))


def _lr_t(h,w):
    return tuple(sorted({(0,c) for c in range(w)}|{(r,w//2) for r in range(h)}))


def _transpose(shape):
    return tuple(sorted((c,r) for r,c in shape))


def _ud_t(h,w):
    return _transpose(_lr_t(w,h))


def _plus(n):
    return tuple(sorted({(r,n//2) for r in range(n)}|{(n//2,c) for c in range(n)}))


def _dense_lr(lengths):
    width=max(lengths)
    return tuple((r,c) for r,length in enumerate(lengths)
                 for c in range((width-length)//2,(width+length)//2))


def _rng(seed,purpose):
    value=hashlib.sha256(f"a86a630485ac/native-v1/{purpose}/{seed}".encode()).digest()
    return random.Random(int.from_bytes(value,"big"))


def _paint(grid,shape,top,left,color):
    for r,c in shape:
        if grid[top+r][left+c]:
            raise RuntimeError("constructive placement overlapped")
        grid[top+r][left+c]=color


def _finish(grid,rng):
    if rng.getrandbits(1):
        grid=grid[::-1]
    if rng.getrandbits(1):
        grid=[row[::-1] for row in grid]
    validate_grid(grid)
    return grid


def _core_one(rng,palette):
    # Main-axis rank is 7, other-axis rank is 5; both have two tied winners.
    # Plus/asymmetric/LR-T share a color but are separate four-components.
    # Plus and asymmetric object touch only diagonally. LR/UD Ts touch with
    # different colors, preserving their separate monochrome object roles.
    grid=[[0]*23 for _ in range(11)]
    # Both axis projections have symmetric counts, but this connected bitmap
    # is asymmetric. Row/column marginals cannot replace cellwise reflection.
    balanced_asym=((0,0),(0,1),(1,1),(1,2),(2,1),(2,2),(3,2),(3,3))
    up_t=tuple((2-r,c) for r,c in _lr_t(3,5))
    objects=[(_plus(3),0,0,palette[0]),(balanced_asym,3,2,palette[0]),
             (_lr_t(5,3),0,7,palette[0]),(_ud_t(3,3),3,9,palette[1]),
             (up_t,7,1,palette[0]),(_lr_t(3,3),7,20,palette[3]),
             (_solid(2,1),9,14,palette[4])]
    for shape,r,c,color in objects:
        _paint(grid,shape,r,c,color)
    return _finish(grid,rng)


def _tiled(h,w,shapes,rng,palette,rows,cols,gap=1):
    slot_h=(h-gap*(rows-1))//rows
    slot_w=(w-gap*(cols-1))//cols
    positions=[(r*(slot_h+gap),c*(slot_w+gap)) for r in range(rows) for c in range(cols)]
    rng.shuffle(positions)
    grid=[[0]*w for _ in range(h)]
    for i,(shape,(top,left)) in enumerate(zip(shapes,positions,strict=False)):
        sh=max(r for r,c in shape)+1
        sw=max(c for r,c in shape)+1
        if sh>slot_h or sw>slot_w:
            raise RuntimeError("profile shape does not fit its constructive slot")
        if rng.getrandbits(1):
            shape=tuple((sh-1-r,c) for r,c in shape)
        if rng.getrandbits(1):
            shape=tuple((r,sw-1-c) for r,c in shape)
        _paint(grid,shape,top+rng.randint(0,slot_h-sh),left+rng.randint(0,slot_w-sw),palette[i%len(palette)])
    return _finish(grid,rng)


def _large(rng,palette,winner_size):
    grid=[[0]*30 for _ in range(30)]
    for i,(r,c) in enumerate(((0,0),(0,30-winner_size),(30-winner_size,0),(30-winner_size,30-winner_size))):
        _paint(grid,_solid(winner_size),r,c,palette[i%3])
    others=[(_ring(9),0,10),(_lr_t(9,9),10,0),(_near_square(9),10,10),
            (_ud_t(9,9),10,21),(_plus(9),21,10)]
    for i,(shape,r,c) in enumerate(others):
        _paint(grid,shape,r,c,palette[i+3])
    return _finish(grid,rng)


def _scene(seed,index):
    rng=_rng(seed,f"input/{index}")
    palette=list(range(1,10))
    rng.shuffle(palette)
    dense15=_dense_lr((5,5,3,1,1))
    dense17=_dense_lr((5,5,3,3,1))
    dense19=_dense_lr((5,5,3,3,1,1,1))
    dense21=_dense_lr((5,5,5,3,1,1,1))
    if index==0:
        return _core_one(rng,palette)
    if index==1:
        # LR maximum16, UD maximum17 reverses the axis rank order from core1.
        return _tiled(15,23,[dense15,_transpose(dense17),_lr_t(7,7),_ud_t(7,7),_solid(4),_near_square(6)],rng,palette,2,3)
    if index in (2,6):
        small=_solid(2) if index==2 else _solid(2,1)
        # All four colors are distinct, so neighboring slots may touch while
        # remaining separate monochrome components on this minimum canvas.
        return _tiled(6,8,[_lr_t(3,3),_ud_t(3,3),_plus(3),small],rng,palette,2,2,gap=0)
    if index==3:
        return _tiled(18,24,[dense19,_transpose(dense21),_lr_t(7,7),_ud_t(7,7),_ring(5),_near_square(6)],rng,palette,2,3)
    if index==4:
        return _tiled(26,27,[_solid(6),_solid(6),_ring(7),_lr_t(7,7),_ud_t(7,7),_near_square(8),_plus(7),dense17,_near_square(5)],rng,palette,3,3)
    if index in (5,9):
        return _large(rng,palette,8 if index==5 else 7)
    if index==7:
        wide_lr=tuple([(0,c) for c in range(4)]+[(r,c) for r in (1,2) for c in (1,2)])
        wide_ud=((0,0),(0,1),(1,0),(1,1),(1,2),(1,3),(2,0),(2,1))
        return _tiled(14,20,[wide_lr,wide_ud,_solid(3),_ring(5),_near_square(6),_transpose(dense17)],rng,palette,2,3)
    if index==8:
        return _tiled(23,29,[dense19,_transpose(dense21),_lr_t(9,9),_ud_t(9,9),_solid(6),_near_square(9)],rng,palette,2,3)
    raise ValueError("unknown profile")


def generate(seed,settings=None,demos=3,queries=4):
    _integer(seed,"seed",0,2**63-1)
    _integer(demos,"demos",2,6)
    _integer(queries,"queries",1,4)
    if settings is None:
        settings=dict(_rng(seed,"setting").choice(SETTINGS))
    _settings(settings)
    bank=[_scene(seed,i) for i in range(10)]
    tests=bank[6:]
    _rng(seed,"query-order").shuffle(tests)
    def labeled(inputs):
        return [{"input":g,"output":apply_python(g,settings)} for g in inputs]
    return {"train":labeled(bank[:demos]),"test":labeled(tests[:queries]),
            "program_solution":program(settings)}
