"""Counted primitive-stencil family. Standard library only; labels are claims until Racket replay."""
from copy import deepcopy
import random

POLICIES=('raster','snake','raw_period','raw_period_snake','partial_period','literal_backing','constant_backing','transpose_backing','transparent_black','swap_counts','distinct_counts','bbox_counts','snake_even')

POLICIES += tuple('snake/'+x for x in POLICIES if x not in ('raster','snake','raw_period_snake','snake_even'))

def grid_check(g):
    if (type(g) is not list or not 2<=len(g)<=30 or len(g)%2 or type(g[0]) is not list or
        not 2<=len(g[0])<=30 or len(g[0])%2 or any(type(row) is not list or len(row)!=len(g[0]) or
        any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('expected even rectangular 2..30 grid of exact integer colors')

def periods(tile,exact=True):
    h,w=len(tile),len(tile[0])
    ph=next(p for p in range(1,h+1) if (not exact or h%p==0) and all(tile[r][c]==tile[r%p][c] for r in range(h) for c in range(w)))
    pw=next(p for p in range(1,w+1) if (not exact or w%p==0) and all(tile[r][c]==tile[r][c%p] for r in range(h) for c in range(w)))
    return ph,pw

def parse(g):
    grid_check(g);h,w=len(g)//2,len(g[0])//2
    controls=[[row[:w] for row in g[:h]],[row[w:] for row in g[:h]]]
    H,W=[sum(v!=0 for row in t for v in row) for t in controls]
    if not 1<=H<=30 or not 1<=W<=30:raise ValueError('control counts must define output dimensions 1..30')
    tile=[row[w:] for row in g[h:]];base=[row[:w] for row in g[h:]]
    ph,pw=periods(tile)
    return {'height':H,'width':W,'qh':h,'qw':w,'tile':tile,'base':base,'period':[ph,pw],'controls':controls}

def predict(g,mode='raster'):
    if mode not in POLICIES:raise ValueError('unknown backing policy')
    snake_mode=mode.startswith('snake/') or mode in ('snake','raw_period_snake')
    mode=mode.removeprefix('snake/')
    p=parse(g);H,W=p['height'],p['width'];h,w=p['qh'],p['qw'];ph,pw=p['period'];tile,base=p['tile'],p['base']
    if mode.startswith('raw_period'):ph,pw=h,w
    if mode=='partial_period':ph,pw=periods(tile,exact=False)
    if mode=='swap_counts':H,W=W,H
    if mode=='distinct_counts':H,W=[len({v for row in a for v in row if v}) for a in p['controls']]
    if mode=='bbox_counts':
        def area(a):
            pts=[(r,c) for r,row in enumerate(a) for c,v in enumerate(row) if v]
            return min(30,(max(r for r,c in pts)-min(r for r,c in pts)+1)*(max(c for r,c in pts)-min(c for r,c in pts)+1))
        H,W=map(area,p['controls'])
    out=[]
    for r in range(H):
        row=[]
        for c in range(W):
            br,bc=(r//ph)%h,(c//pw)%w
            if snake_mode and br%2:bc=w-1-bc
            if mode=='snake_even' and not br%2:bc=w-1-bc
            if mode=='literal_backing':br,bc=r%h,c%w
            if mode=='constant_backing':br,bc=0,0
            if mode=='transpose_backing':br,bc=bc%h,br%w
            v=tile[r%ph][c%pw]
            row.append(v if v or mode=='transparent_black' else base[br][bc])
        out.append(row)
    return out

def _scene(seed,index):
    rng=random.Random(f'f931b4a8:scene:{seed}:{index}')
    if index==0:qh,qw,ph,pw,H,W=6,6,2,2,11,13;kind='checker'
    elif index==1:qh,qw,ph,pw,H,W=3,3,3,3,8,7;kind='frame'
    elif index==6:qh,qw,ph,pw,H,W=2,2,2,2,4,3;kind='checker'
    elif index==7:qh,qw,ph,pw,H,W=8,6,1,1,rng.randint(8,20),rng.randint(8,20);kind='empty'
    elif index==8:qh,qw,ph,pw,H,W=12,12,3,4,rng.randint(15,28),rng.randint(15,28);kind='asymmetric'
    elif index==9:qh,qw,ph,pw,H,W=15,15,3,5,30,30;kind='asymmetric'
    else:
        ph,pw=rng.choice([(1,2),(2,1),(2,3),(3,2),(3,3),(4,2)])
        qh,qw=ph*rng.randint(2,min(4,15//ph)),pw*rng.randint(2,min(4,15//pw))
        H,W=rng.randint(1,min(30,qh*qw)),rng.randint(1,min(30,qh*qw));kind='asymmetric'
    palette=rng.sample(range(1,10),9);a,b=palette[:2]
    if kind=='empty':unit=[[0]]
    elif kind=='checker':unit=[[a,0],[0,b]]
    elif kind=='frame':unit=[[a,a,a],[a,0,a],[a,a,a]]
    else:
        # One unique corner color pins both periods, with transparent and varied cells.
        unit=[[rng.choice([0,0,a]) for _ in range(pw)] for _ in range(ph)]
        unit[0][0]=b;unit[-1][-1]=0
    tile=[[unit[r%ph][c%pw] for c in range(qw)] for r in range(qh)]
    base=[[rng.choice(palette[2:]) for _ in range(qw)] for _ in range(qh)]
    # Every odd backing row visibly distinguishes raster versus snake address order.
    for r in range(1,qh,2):base[r][0]=palette[2];base[r][-1]=palette[3]
    controls=[]
    for count in (H,W):
        board=[[0]*qw for _ in range(qh)]
        for pos in rng.sample(range(qh*qw),count):board[pos//qw][pos%qw]=rng.choice(palette)
        controls.append(board)
    g=[controls[0][r]+controls[1][r] for r in range(qh)]+[base[r]+tile[r] for r in range(qh)]
    cert=parse(g)
    return g,{'profile':kind,'source_index':index,'period':cert['period'],'output_shape':[H,W]}

def bank(seed):return [_scene(seed,i) for i in range(10)]
