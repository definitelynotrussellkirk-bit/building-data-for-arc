"""Source-bound, Python-only audit reproducer for e562f7bff9ee."""
import hashlib
import json
from pathlib import Path
import sys

WORK=Path(__file__).resolve().parents[3]
ROOT=WORK/'repo'
TARGET='e562f7bff9ee'
EXPECTED='79bb46f2d69418848f390d77199ad6449905ab7b0d73fe19ed54b68a9fabb4b3'
audit=json.loads((WORK/'AUDIT_ASSIGNMENT.json').read_bytes())
row=next(r for r in audit['targets'] if r['task_id']==TARGET)
assert row['generator_sha256']==EXPECTED
sys.path.insert(0,str(ROOT/'shared/runtime'))
from reviewer_support import load_selected_generator
G,source,source_hash=load_selected_generator(TARGET,root=ROOT)
assert source_hash==EXPECTED

def observe(grid):
    return {'grid_h':len(grid),'grid_w':len(grid[0]),
            'n_satellites':sum(v in (8,9) for r in grid for v in r),
            'n_distinct_colors':len({v for r in grid for v in r}),
            'satellite_color_count':len({v for r in grid for v in r if v in (8,9)}),
            'grid_sha256':hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest(),
            'self_check':G.self_check(grid)}

rows=[];fallback=None
for h,w,n in [(10,10,3),(10,11,3),(11,10,2)]:
    for seed in [0,17,2026]:
        args={'grid_h':h,'grid_w':w,'n_satellites':n}
        grid=G.generate(seed,0,difficulty='easy',**args)
        actual=observe(grid)
        assert (actual['grid_h'],actual['grid_w'],actual['n_satellites'])==(12,12,1),actual
        assert actual['self_check']==[]
        if fallback is None:fallback=grid
        assert grid==fallback
        rows.append({'seed':seed,'sample_index':0,'difficulty':'easy','overrides':args,'observed':actual})

# Dimension limits alone prove this cannot be a low-probability random failure:
# with origins in [3,h-4]x[3,w-4], max L1 separation is h+w-14 <8.
geometry=[{'h':h,'w':w,'max_possible_origin_L1_distance':h+w-14,'required':8}
          for h,w in [(10,10),(10,11),(11,10)]]

# Finite observed default collapse; not a claim about the whole distribution.
defaults=[]
for seed in range(24):
    grid=G.generate(seed,0,difficulty='easy')
    defaults.append({'seed':seed,'sample_index':0,'observed':observe(grid),'equals_fixed_fallback':grid==fallback})
assert any(r['equals_fixed_fallback'] for r in defaults)

# The documented all-colors count cannot equal5: 0 plus2..7 plus at least8/9 =>>=8.
colors=[]
for seed in [0,17,2026]:
    args={'grid_h':16,'grid_w':16,'n_satellites':4,'palette_size':2,'n_distinct_colors':5}
    grid=G.generate(seed,0,**args);actual=observe(grid)
    assert actual['n_distinct_colors']>=8 and actual['n_distinct_colors']!=5,actual
    assert actual['self_check']==[]
    colors.append({'seed':seed,'sample_index':0,'overrides':args,'observed':actual})

# Detect thinning even when a large requested sample count is accepted.
thinned=[]
for seed in range(24):
    grid=G.generate(seed,0,grid_h=12,grid_w=12,n_satellites=4)
    actual=observe(grid)
    if actual['n_satellites']!=4:thinned.append({'seed':seed,'sample_index':0,'observed':actual})

unreachable_counts=[]
for difficulty in [None,'easy','medium','hard']:
    for n in [1,7]:
        try:G.generate(0,0,difficulty=difficulty,grid_h=(12 if difficulty=='easy' else 16),grid_w=(12 if difficulty=='easy' else 16),n_satellites=n)
        except ValueError as error:unreachable_counts.append({'difficulty':difficulty,'n_satellites':n,'error':str(error)})
        else:raise AssertionError(('unexpected count support',difficulty,n))
assert hashlib.sha256(source.read_bytes()).hexdigest()==EXPECTED
result={'schema':'arcpuzzles-findings-audit-python-v1','task_id':TARGET,'source_sha256':EXPECTED,
        'assignment_source_hash_matched':True,'status':'reproduced','public_racket_run':False,
        'checked_scope':'Python generation, exact advertised controls, geometric feasibility, self_check; selected canonical public rule inspected separately',
        'impossible_origin_geometry':geometry,'fixed_fallback_cases':rows,
        'default_easy_probe':{'sample_count':len(defaults),'fixed_fallback_count':sum(r['equals_fixed_fallback'] for r in defaults),'cases':defaults},
        'unrealizable_declared_color_count_cases':colors,'unreachable_advertised_satellite_count_cases':unreachable_counts,'thinned_n_satellites_cases':thinned,
        'blind_source_inspected':False}
out=Path(__file__).with_name('evidence.json')
out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'source_sha256':EXPECTED,'fixed_fallback_cases':len(rows),
                 'default_fallbacks':result['default_easy_probe']['fixed_fallback_count'],
                 'default_probes':len(defaults),'bad_color_count_cases':len(colors),
                 'thinned_satellite_count_cases':len(thinned),'status':'reproduced'},sort_keys=True))
