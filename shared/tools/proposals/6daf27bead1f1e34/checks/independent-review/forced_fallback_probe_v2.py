"""Independent main-only forced placement fallback review, no blind imports."""
import hashlib
import itertools
import json
from pathlib import Path
import random
import sys

WORK = Path(__file__).resolve().parents[2]
ROOT = WORK / 'repo'
sys.path.insert(0, str(ROOT / 'shared/runtime'))
from reviewer_support import load_selected_generator
G, source, digest = load_selected_generator('15e7e0613c19', root=ROOT)
assert digest == '0c8171c8bf81df45cc1ffd8916213712758a96612552e8c9fc5f353873242a17', digest

class ForceFallback:
    def __init__(self): self.calls = 0
    def shuffle(self, values):
        self.calls += 1
        if self.calls <= 80:
            values.clear()  # All randomized first-object attempts fail; permutation pass remains.

phases = [
    ([[(0,0),(1,0),(2,0),(2,1)],[(r,0) for r in range(5)],[(0,0)]], [3,6,9], ('bbox_area',)),
    ([[(r,0) for r in range(4)],[(0,0),(0,1),(1,0),(1,1)],[(0,0),(1,0),(1,1),(1,2)]], [6,9,3], ('ignore_height','ignore_width')),
    ([[(0,0),(1,0)] for _ in range(4)], [9,6,3,9], ('ignore_color','merge_by_color'))]
counts=[]
for shapes,colors,required in phases:
    count=0
    for flips in itertools.product(range(4), repeat=len(shapes)):
        reflected=[]
        for shape,flip in zip(shapes,flips):
            h=max(r for r,c in shape)+1;w=max(c for r,c in shape)+1
            reflected.append([(h-1-r if flip&1 else r,w-1-c if flip&2 else c) for r,c in shape])
        rng=ForceFallback();grid=G._place(reflected,colors,7,9,rng,required)
        assert rng.calls==81,rng.calls
        assert G.self_check(grid)==[],(flips,G.self_check(grid))
        answer=G.solve_reference(grid)
        assert len(answer)<len(grid) and len(answer[0])<len(grid[0])
        assert all(G.SEMANTIC_RIVALS[name](grid)!=answer for name in required)
        count+=1
    counts.append(count)

# Independent corner/control samples: every accepted (n,colors) count pair,
# both aliases independently, dimensions at both extremes, all three phases.
control_cases=0
for n in range(2,6):
    for colors in range(2,n+2):
        for h,w in [(7,9),(7,16),(14,9),(14,16)]:
            for alias in ['palette_size','n_distinct_colors']:
                for phase in range(3):
                    kwargs={'grid_h':h,'grid_w':w,'n':n,alias:colors}
                    grid=G.generate(88491,phase,**kwargs)
                    assert G.self_check(grid)==[],kwargs
                    observed=G.observe_overrides(grid)
                    assert all(observed[k]==v for k,v in kwargs.items()),(kwargs,observed)
                    control_cases+=1

# Negative combinations must be structured incompatibilities, not silently clamped.
rejected=0
for n in range(2,6):
    for colors in range(n+2,7):
        for alias in ['palette_size','n_distinct_colors']:
            try:G.generate(88491,0,n=n,**{alias:colors})
            except G.IncompatibleOverrides as exc:
                assert 'n' in exc.incompatible_axes and alias in exc.incompatible_axes
                rejected+=1
            else:raise AssertionError((n,colors,alias))
# Default consecutive windows retain strict shrink and leave-one-out rival separation.
default_cases=0
for band in ['easy','medium','hard']:
    for seed in [0,19,2026]:
        for start in range(3):
            pairs=[]
            for index in range(start,start+6):
                grid=G.generate(seed,index,difficulty=band)
                answer=G.solve_reference(grid)
                assert G.self_check(grid)==[]
                assert len(answer)<len(grid) and len(answer[0])<len(grid[0]),(band,seed,index)
                pairs.append({'input':grid,'output':answer})
                default_cases+=1
            for heldout in range(6):
                demos=[p for i,p in enumerate(pairs) if i!=heldout]
                assert G.lesson_identifiable(demos,pairs[heldout])==[]
                for name,rival in G.LESSON_COMPETITORS.items():
                    assert any(rival(p['input'])!=p['output'] for p in demos),(band,seed,start,heldout,name)
result={'generator_sha256':digest,'forced_fallback_reflection_cases_by_phase':counts,
        'forced_fallback_cases':sum(counts),'exact_control_cases':control_cases,
        'structured_incompatibility_cases':rejected,'default_strict_shrink_and_schedule_cases':default_cases,'status':'passed','blind_source_inspected':False}
(Path(__file__).with_name('forced_fallback_probe_v2.json')).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
