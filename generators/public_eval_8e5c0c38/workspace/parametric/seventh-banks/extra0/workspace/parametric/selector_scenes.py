"""Constructive two-example teaching for damage-based selective completion.

Demo zero: a middle-sized, middle-color silhouette has the greatest damage, while
an even smaller silhouette has a larger damage fraction. Demo one: two silhouettes
tie for greatest damage. Symmetric holes forbid a filled-box shortcut. The legacy
union constructors are retained separately for complex held-out shapes.
"""
from pathlib import Path
import importlib.util
import hashlib
import random
import sys

p=Path(__file__).resolve().with_name('repair.py')
n='_selector_repair_'+hashlib.sha256(str(p).encode()).hexdigest()
s=importlib.util.spec_from_file_location(n,p)
R=importlib.util.module_from_spec(s);sys.modules[n]=R;s.loader.exec_module(R)

def scene(seed,index,*,query=False):
    if type(seed)is not int or not 0<=seed<2**63 or type(index)is not int or index<0:
        raise ValueError('invalid seed/index')
    rng=random.Random(int.from_bytes(hashlib.sha256(f'selective-v1:{seed}:{index}:{query}'.encode()).digest(),'big'))
    h,w=(30,30) if query else (26,28)
    bg=rng.randrange(10)
    colors=sorted(rng.sample([c for c in range(10) if c!=bg],4))
    damage=(1,3,2) if index%2==0 else (2,1,2)
    dimensions=((8,7),(6,7),(4,3))
    slots=((0,0),(0,w-14),(h-4,w-14))
    for attempt in range(128):
        grid=[[bg]*w for _ in range(h)]
        for j,((hh,ww),(rr,cc)) in enumerate(zip(dimensions,slots)):
            left=6-ww//2
            core={(r,c) for r in range(hh) for c in range(left,left+ww)}
            # Internal holes and asymmetric row structure; every removal is symmetric.
            hole_row=rng.randrange(1,hh-1)
            if ww==3:core.discard((hole_row,6))
            else:
                for c in (4,8):core.discard((hole_row,c))
                core.discard(((hole_row+1)%hh,6))
            side=rng.choice((1,11))
            noise={(r,side) for r in rng.sample(range(hh),damage[j])}
            for r,c in core|noise:grid[rr+r][cc+c]=colors[j]
        # A tied maximum-support axis is present in both minimum demos.
        # The canonical leftmost tie-break must be learnable, not deferred to queries.
        tied={(0,0),(0,2),(0,3),(1,0),(1,1),(1,2),(1,3),(2,1)}
        for r,c in tied:grid[h-5+r][5+c]=colors[3]
        found_bg,records=R.analyze(grid)
        by_color={r['color']:r for r in records}
        if (found_bg==bg and all(by_color[c]['damage']==d and len(by_color[c]['maximizers'])==1
                                 for c,d in zip(colors,damage))):
            return grid
    raise RuntimeError('bounded selective-symmetry construction exhausted')
