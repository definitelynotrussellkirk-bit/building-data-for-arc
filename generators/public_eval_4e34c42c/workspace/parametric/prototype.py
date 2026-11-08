"""Translation-only assembly; no source fixtures or answer tables are imported."""
from collections import Counter


def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or
        type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30 or
        any(type(row) is not list or len(row) != len(grid[0]) or
            any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid)):
        raise ValueError('expected an exact-integer rectangular ARC grid')
    return grid


def background(grid):
    counts = Counter(v for row in grid for v in row)
    return min(counts, key=lambda v: (-counts[v], v))


def normalize(cells):
    r0 = min(r for r, c in cells)
    c0 = min(c for r, c in cells)
    return {(r-r0, c-c0): v for (r,c), v in cells.items()}


def components(grid, bg):
    remaining = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v != bg}
    result = []
    while remaining:
        p = min(remaining); remaining.remove(p); stack = [p]; cells = {}
        while stack:
            r,c = stack.pop(); cells[r,c] = grid[r][c]
            for q in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                if q in remaining:
                    remaining.remove(q); stack.append(q)
        cells = normalize(cells)
        nr = max(r for r,c in cells)+1; nc = max(c for r,c in cells)+1
        result.append({(r,c): cells.get((r,c),bg) for r in range(nr) for c in range(nc)})
    return result


def mono_components(cells, bg):
    remaining = {p for p,v in cells.items() if v != bg}; result = []
    while remaining:
        first = min(remaining); remaining.remove(first); stack = [first]; comp = {}
        while stack:
            p = stack.pop(); comp[p] = cells[p]
            r,c = p
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in remaining and cells[q] == cells[p]:
                    remaining.remove(q); stack.append(q)
        result.append(comp)
    return result


def best_alignment(a, b, bg):
    acs, bcs = mono_components(a,bg), mono_components(b,bg)
    offsets = {(r-s,c-t) for (r,c),v in a.items() if v != bg for (s,t),w in b.items() if v == w}
    best = None
    for dr,dc in sorted(offsets):
        score = sum(v != bg and a.get((r+dr,c+dc)) == v for (r,c),v in b.items())
        if best is not None and score < best[0]:
            continue
        shifted = {(r+dr,c+dc):v for (r,c),v in b.items()}
        if any(p in a and a[p] != v for p,v in shifted.items()):
            continue
        anchor = (any(all(shifted.get(p) == v for p,v in comp.items()) for comp in acs) or
                  any(all(a.get((r+dr,c+dc)) == v for (r,c),v in comp.items()) for comp in bcs))
        if not anchor:
            continue
        merged = a | shifted
        rr = [r for r,c in merged]; cc = [c for r,c in merged]
        area = (max(rr)-min(rr)+1)*(max(cc)-min(cc)+1)
        rank = (score, -area, -abs(dr)-abs(dc), -dr, -dc)
        if best is None or rank > best[1]:
            best = (score, rank, merged, (dr,dc))
    return best


def assemble(grid, trace=False):
    validate_grid(grid)
    bg = background(grid); pieces = components(grid,bg); steps = []
    if not pieces:
        return (grid, steps) if trace else [row[:] for row in grid]
    while len(pieces) > 1:
        choice = None
        for i,a in enumerate(pieces):
            for j in range(i+1, len(pieces)):
                candidate = best_alignment(a,pieces[j],bg)
                if candidate is not None:
                    score, rank, merged, delta = candidate
                    if choice is None or rank > choice[0]:
                        choice = (rank,i,j,merged,delta)
        if choice is None:
            raise ValueError('no consistent nonempty fragment overlap')
        rank,i,j,merged,delta = choice
        steps.append({'piece_count':len(pieces), 'overlap':rank[0], 'translation':list(delta)})
        pieces = [p for k,p in enumerate(pieces) if k not in (i,j)] + [normalize(merged)]
    cells = pieces[0]
    nr = max(r for r,c in cells)+1; nc = max(c for r,c in cells)+1
    out = [[bg]*nc for _ in range(nr)]
    for (r,c),v in cells.items(): out[r][c] = v
    return (out,steps) if trace else out


def bridge_pairs(grid, bg):
    """Join a color's two aligned occurrences only across unoccupied cells."""
    out=[row[:] for row in grid]
    for color in sorted({v for row in grid for v in row}-{bg}):
        points=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==color]
        if len(points)!=2: continue
        (r,c),(s,t)=points
        if r==s: span=[(r,j) for j in range(min(c,t),max(c,t)+1)]
        elif c==t: span=[(i,c) for i in range(min(r,s),max(r,s)+1)]
        else: continue
        if all(grid[i][j] in (bg,color) for i,j in span):
            for i,j in span: out[i][j]=color
    return out


def solve(grid, bridge=False):
    result=assemble(grid)
    return bridge_pairs(result,background(grid)) if bridge else result


def transform(grid, index):
    out=[row[:] for row in grid]
    if index//4: out=[row[::-1] for row in out]
    for _ in range(index%4): out=[list(row) for row in zip(*out[::-1])]
    return out


def scene(seed, index, stress=False, partial=None):
    """Construct overlapping U-shaped mosaics, never copying an original pair.

    Colored 3x3 glyphs are joined by varying-length links. Adjacent fragments
    share a complete glyph; terminal fragments each contain one relay endpoint.
    A redundant glyph fragment sometimes supplies a strict-subset overlap.
    """
    import random
    rng=random.Random((seed+1)*1000003+(index+1)*10007)
    if partial is None: partial = bool(index % 2)
    n=5 if stress else rng.randint(3,5)
    palette=rng.sample(range(10),n+3)
    bg,marker,link=palette[:3]; node_colors=palette[3:]
    gaps=[rng.randint(1,3) for _ in range(n-1)]
    xs=[0]
    for gap in gaps: xs.append(xs[-1]+3+gap)
    width=xs[-1]+3; glyph_h=5 if stress else rng.choice((3,5)); lift=rng.randint(2,4); height=lift+glyph_h
    expected=[[bg]*width for _ in range(height)]
    for x,color in zip(xs,node_colors):
        for r in range(lift,lift+glyph_h):
            for c in range(x,x+3):
                expected[r][c]=link if lift<r<lift+glyph_h-1 and c==x+1 else color
    for i in range(n-1):
        for c in range(xs[i]+3,xs[i+1]): expected[lift+glyph_h//2][c]=link
    for r in range(lift):
        expected[r][0]=node_colors[0];expected[r][-1]=node_colors[-1]
    mr=rng.randint(1,lift-1)
    expected[mr][1]=marker;expected[mr][-2]=marker
    pieces=[]
    for i in range(n-1):
        r0=0 if i in (0,n-2) else lift
        left=xs[i]+(1 if partial and i>0 else 0)
        right=xs[i+1]+(2 if partial and i<n-2 else 3)
        pieces.append([row[left:right] for row in expected[r0:]])
    if not partial and (stress or rng.random()<0.6):
        k=rng.randrange(1,n-1)
        pieces.append([row[xs[k]:xs[k]+3] for row in expected[lift:]])
    orientation=2*rng.randrange(4)+(index%2)
    expected=transform(expected,orientation)
    pieces=[transform(p,orientation) for p in pieces]
    rng.shuffle(pieces)
    canvas_size=30 if stress else rng.randint(25,30)
    h=w=canvas_size
    # Fixed disjoint packing slots, with random assignments and local jitter.
    # Corners are used on stress draws so foreground really touches all edges.
    canvas=[[bg]*w for _ in range(h)]
    slots=[(0,0),(h-10,w-10),(0,w-10),(h-10,0),(h//2-5,w//2-5)]
    # Put the small redundant glyph in the center whenever there are 5 pieces.
    if len(pieces)==5:
        smallest=min(range(len(pieces)),key=lambda i:len(pieces[i])*len(pieces[i][0]))
        pieces[smallest],pieces[-1]=pieces[-1],pieces[smallest]
    placed=[]
    for k,piece in enumerate(pieces):
        ph,pw=len(piece),len(piece[0]); br,bc=slots[k]
        if stress and k<4:
            r=0 if k in (0,2) else h-ph
            c=0 if k in (0,3) else w-pw
        else:
            r=br+rng.randint(0,10-ph);c=bc+rng.randint(0,10-pw)
        if any(not (r+ph<rr or rr+hh<r or c+pw<cc or cc+ww<c) for rr,cc,hh,ww in placed):
            # This can only involve center slot; center the small 3x3 subset.
            r=h//2-ph//2;c=w//2-pw//2
        if any(not (r+ph<rr or rr+hh<r or c+pw<cc or cc+ww<c) for rr,cc,hh,ww in placed):
            raise ValueError('bounded packing slots overlap')
        placed.append((r,c,ph,pw))
        for i,row in enumerate(piece):
            for j,v in enumerate(row):canvas[r+i][c+j]=v
    return canvas,expected
