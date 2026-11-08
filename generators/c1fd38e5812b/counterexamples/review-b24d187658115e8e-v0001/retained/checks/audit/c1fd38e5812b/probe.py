from __future__ import annotations
import hashlib, importlib.util, json, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT/'repo'
OUT = Path(__file__).resolve().parent
source = REPO/'generators/c1fd38e5812b/generator.py'
spec = importlib.util.spec_from_file_location('audited_c1fd38e5812b', source)
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
sha = hashlib.sha256(source.read_bytes()).hexdigest()
rows = [json.loads(s) for s in (REPO/'shared/data/canonical/puzzles.jsonl').read_text().splitlines()]
canonical = next(r for r in rows if r['task_id']==g.TASK_ID and r['source']=='training')
# Independent reference candidate: retain consecutive distinct whole rows and
# columns. On exact Cartesian block expansions this should coincide with sampling.
def consecutive_unique(grid):
    kept = [grid[0][:]]
    kept.extend(row[:] for i,row in enumerate(grid[1:],1) if row != grid[i-1])
    columns = [tuple(row[c] for row in kept) for c in range(len(kept[0]))]
    starts = [0]+[c for c in range(1,len(columns)) if columns[c]!=columns[c-1]]
    return [[row[c] for c in starts] for row in kept]
def globally_unique(grid):
    kept = []
    for row in grid:
        if row not in kept: kept.append(row[:])
    columns = [tuple(row[c] for row in kept) for c in range(len(kept[0]))]
    starts = [c for c in range(len(columns)) if columns[c] not in columns[:c]]
    return [[row[c] for c in starts] for row in kept]
def equal_stride(grid):
    # Guess one common block size from the two initial edge runs.
    hr = next((i for i in range(1,len(grid)) if grid[i][0]!=grid[0][0]),len(grid))
    wc = next((i for i in range(1,len(grid[0])) if grid[0][i]!=grid[0][0]),len(grid[0]))
    return [row[::wc] for row in grid[::hr]]
def expand(logical,rs,cs):
    return [list(v for v,n in zip(row,cs) for _ in range(n)) for row,n in zip(logical,rs) for _ in range(n)]
cases=[]
for i,pair in enumerate(canonical['train']+canonical['test']):
    cases.append(dict(kind='canonical',pair_index=i,input=pair['input'],expected=pair['output'],seed=None,sample_index=None,overrides={}))
for pidx,profile in enumerate(g.SCENE_PROFILES):
    for bidx,band in enumerate(('easy','medium','hard')):
        for index in range(2):
            seed=4_240_000+100*pidx+10*bidx+index
            grid=g.generate(seed,index,difficulty=band,scene_profile=profile)
            cases.append(dict(kind='generated',seed=seed,sample_index=index,difficulty=band,overrides={'scene_profile':profile},input=grid,expected=consecutive_unique(grid)))
handmade=[
    ([[0,1],[2,3]],[2,12],[12,2]),
    ([[0,1],[2,3]],[4,4],[4,4]),
    ([[0,1,2,3],[4,4,4,4],[0,1,2,3],[5,5,5,5]],[2,3,4,5],[2,3,4,5]),
    ([[0,1,0,1],[2,3,2,3],[0,1,0,1],[2,3,2,3]],[2,2,2,2],[2,2,2,2]),
]
for size in (3,4,5,6):
    logical=[[(r+c)%4 for c in range(size)] for r in range(size)]
    span=3 if size==3 else 4
    handmade.append((logical,[span]*size,[span]*size))
handmade.extend([
    ([[0,1,2],[3,3,3],[0,3,3]],[2,6,4],[2,4,6]),
    ([[0,1],[2,2],[3,3],[0,1],[2,2],[3,3]],[2]*6,[4,8]),
    ([[0,1,2,0,1,2],[3,3,3,3,3,3]],[12,12],[2]*6),
])
for i,(logical,rs,cs) in enumerate(handmade):
    cases.append(dict(kind='handcrafted',case_index=i,seed=None,sample_index=None,overrides={},logical=logical,row_spans=rs,col_spans=cs,input=expand(logical,rs,cs),expected=logical))
assert len(cases)==64
for i,case in enumerate(cases):
    case['batch_index']=i
    case['self_check']=g.self_check(case['input'])
    assert case['self_check']==[],case
    case['observed_overrides']=g.observe_overrides(case['input'])
    case['rivals']={'global_row_column_dedup':globally_unique(case['input']),'equal_stride':equal_stride(case['input'])}
    case['documented_domain_judgment']='Accepted exact Cartesian expansion: 2..6 logical rows/columns, edge boundaries visible, spans 2..12, dimensions 8..24, at least four colors.'
# Rejections exercise validator boundaries separately from the public apply batch.
base=cases[6]['input']
invalid=[]
def add(label,grid): invalid.append({'label':label,'self_check':g.self_check(grid),'input':grid})
add('empty',[])
add('ragged',[[1,2],[3]])
add('bool',[[True,2],[3,4]])
add('small_total',expand([[0,1],[2,3]],[2,2],[2,2]))
add('three_color',expand([[0,1],[2,0]],[4,4],[4,4]))
add('one_pixel_run',expand([[0,1],[2,3]],[1,7],[4,4]))
add('oversized_run',expand([[0,1],[2,3]],[13,2],[4,4]))
broken=[row[:] for row in base]; broken[1][1]=(broken[1][1]+1)%10
add('broken_solid_block',broken)
assert all(c['self_check'] for c in invalid)
record={'task_id':g.TASK_ID,'generator_sha256':sha,'rule_hash':g.RULE_HASH,'canonical_program':canonical['program_solution'],'canonical_program_sha256':hashlib.sha256(canonical['program_solution'].encode()).hexdigest(),'cases':cases,'validator_rejections':invalid,'counts':{'canonical':5,'generated':48,'handcrafted':11,'accepted':64,'negative_validator_checks':8,'unique_inputs':len({json.dumps(c['input']) for c in cases})},'small_review_index':'No evidence/review_index.json exists for this target; focused test file inspected.'}
(OUT/'input.json').write_text(json.dumps([c['input'] for c in cases])+'\n')
(OUT/'probe.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'generator_sha256':sha,'rule_hash':g.RULE_HASH,'counts':record['counts'],'global_dedup_expected_divergences':sum(c['rivals']['global_row_column_dedup']!=c['expected'] for c in cases),'equal_stride_expected_divergences':sum(c['rivals']['equal_stride']!=c['expected'] for c in cases)}))
