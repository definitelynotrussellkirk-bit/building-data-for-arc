from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'repo' / 'shared' / 'runtime'))
PATH = ROOT / 'repo' / 'generators' / 'ce40117f40f9' / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_ce40117f40f9', PATH)
mod = importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod)

def nonmarker_cells(g):
    return [(r,c,v) for r,row in enumerate(g) for c,v in enumerate(row) if v not in (0,9)]

def marker_cells(g):
    return [(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v == 9]

cases = {
    'blank': [[0]*8 for _ in range(8)],
    'no_marker': [[0]*9 for _ in range(8)],
    'marker_only': [[0]*9 for _ in range(8)],
    'bool_cell': [[0]*8 for _ in range(8)],
}
for r,c in [(1,1),(1,2),(2,1)]: cases['no_marker'][r][c]=4
cases['marker_only'][5][6]=9
cases['bool_cell'][0][0]=True

ignored = mod.generate(0,0,blob_size=6)
unknown = mod.generate(0,0,not_an_axis=123)
rows=[]
for band in ('easy','medium','hard'):
    down_right=0
    valid=0
    for seed in range(100):
        g=mod.generate(seed,seed,difficulty=band)
        blob=nonmarker_cells(g); marker=marker_cells(g)
        if mod.self_check(g)==[] and blob and len(marker)==1: valid += 1
        if blob and len(marker)==1:
            mr,mc=marker[0]
            if mr > max(r for r,_,_ in blob) and mc > max(c for _,c,_ in blob):
                down_right += 1
    rows.append({'band':band,'draws':100,'self_check_clean_with_entities':valid,'marker_strictly_down_right':down_right})

out={
 'task_id':mod.TASK_ID,
 'generator_sha256':hashlib.sha256(PATH.read_bytes()).hexdigest(),
 'prior_return_used_as_lead':'review-222f5dfc78c493dd:v0001',
 'self_check_cases':{name:mod.self_check(grid) for name,grid in cases.items()},
 'ignored_blob_size':{
   'call':{'seed':0,'sample_index':0,'overrides':{'blob_size':6}},
   'nonmarker_cell_count':len(nonmarker_cells(ignored)),
   'self_check':mod.self_check(ignored),
   'grid':ignored,
 },
 'unknown_override':{
   'call':{'seed':0,'sample_index':0,'overrides':{'not_an_axis':123}},
   'accepted':True,
   'grid_equal_to_default':unknown==mod.generate(0,0),
 },
 'default_census':rows,
 'racket_inputs':cases,
}
(Path(__file__).with_name('probe.json')).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
(Path(__file__).with_name('input.json')).write_text(json.dumps(list(cases.values()),indent=2)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
