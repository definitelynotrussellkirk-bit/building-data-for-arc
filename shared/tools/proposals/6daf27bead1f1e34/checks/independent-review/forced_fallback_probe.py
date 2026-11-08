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
assert digest == '2a753a1f8a34096d078ad1b6d55d2cad00fd68427cba582198e33d218380cfab', digest

class ForceFallback:
    def __init__(self): self.calls = 0
    def shuffle(self, values):
        self.calls += 1
        if self.calls <= 80:
            values.clear()  # All randomized first-object attempts fail; permutation pass remains.

phases = [
    ([[(0,0),(1,0),(2,0),(2,1)],[(0,c) for c in range(5)],[(0,0)]], [3,6,9], ('bbox_area',)),
    ([[(0,c) for c in range(4)],[(0,0),(0,1),(1,0),(1,1)],[(0,0),(1,0),(1,1),(1,2)]], [6,9,3], ('ignore_height','ignore_width')),
    ([[(0,0),(0,1),(1,0),(1,1)] for _ in range(4)], [9,6,3,9], ('ignore_color','merge_by_color'))]
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
result={'generator_sha256':digest,'forced_fallback_reflection_cases_by_phase':counts,
        'forced_fallback_cases':sum(counts),'exact_control_cases':control_cases,
        'structured_incompatibility_cases':rejected,'status':'passed','blind_source_inspected':False}
(Path(__file__).with_name('forced_fallback_probe.json')).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
