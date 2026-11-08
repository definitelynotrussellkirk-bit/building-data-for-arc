"""Findings-only probes; neither audit generator is modified.
Run from the packet root: python3 checks/reproduce_audits.py
"""
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'repo'
sys.path.insert(0, str(REPO / 'shared/runtime'))
sys.path.insert(0, str(ROOT))
from setup_racket import ensure_racket
os.environ['RACKET_PATH'] = str(ensure_racket())
os.environ['TERM'] = 'dumb'
scripts = types.ModuleType('scripts'); scripts.__path__ = [str(REPO / 'shared/tools')]
sys.modules['scripts'] = scripts
from puzzle_generators import runner


def load(tid):
    path = REPO / 'generators' / tid / 'generator.py'
    spec = importlib.util.spec_from_file_location('audit_'+tid,path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module, hashlib.sha256(path.read_bytes()).hexdigest()


canonical = {}
with (REPO / 'shared/data/canonical/puzzles.jsonl').open() as f:
    for line in f:
        row=json.loads(line)
        if row['task_id'] in ('c1a1716e05ab','93ca517eac25'):
            canonical[row['task_id']]=row

a, digest = load('c1a1716e05ab')
base = a.generate(0, 0, difficulty='medium')
overridden = a.generate(0, 0, difficulty='medium', palette_size=1, n_distinct_colors=1)
try:
    a.generate(0,0,difficulty='medium',grid_h=4)
    boundary = {'raised': False}
except Exception as exc:
    boundary = {'raised': True, 'error': type(exc).__name__, 'message': str(exc)}
record = {'task_id': a.TASK_ID, 'generator_sha256': digest,
          'replay': {'seed':0, 'sample_index':0, 'difficulty':'medium',
                     'overrides': {'palette_size':1, 'n_distinct_colors':1}},
          'input': overridden, 'override_equals_default': overridden == base,
          'actual_nonzero_colors': sorted({v for row in overridden for v in row if v}),
          'self_check': a.self_check(overridden),
          'declared_grid_h_4': boundary,
          'unknown_override_ignored': a.generate(0,0,difficulty='medium',typo_axis=99)==base,
          'malformed_input': [[True,0],[0,0]],
          'malformed_self_check': a.self_check([[True,0],[0,0]])}
bridge, fn=runner._open_bridge_with_rule(runner.wrap_rule(canonical[a.TASK_ID]['program_solution']))
try:
    record['racket_output'] = runner._apply_rule(bridge,fn,overridden)
    record['canonical_exact'] = [runner._apply_rule(bridge,fn,p['input'])==p['output']
          for split in ('train','test') for p in canonical[a.TASK_ID][split]]
finally: bridge.shutdown()
(ROOT / 'checks/audit-c1a1716e05ab.json').write_text(json.dumps(record,indent=2)+'\n')
print('c1a1716e05ab', record['actual_nonzero_colors'], boundary,flush=True)

b, digest = load('93ca517eac25')
def key(cells): return tuple(sorted(b._normalize(cells)))
# Learn the lookup ONLY from the shipped shape inventories and canonical inputs.
lookup={}
for masks in (b._SYMMETRIC_MASKS,b._ASYMMETRIC_MASKS):
    for mask in masks:
        cells=b._mask_cells(mask)
        lookup[key(cells)]=b._vertically_symmetric(cells)
for grid in b._PUBLIC_INPUTS.values():
    for cells in b._components(grid,1):
        lookup[key(cells)]=b._vertically_symmetric(cells)

def lookup_rival(grid):
    cells=b._components(grid,1)
    flags=[lookup.get(key(c),False) for c in cells]
    n=sum(flags)
    out=[row[:] for row in grid]
    if 0<n<len(flags) and min(n,len(flags)-n)==1:
        selected=cells[flags.index(n==1)]
        for r,c in selected: out[r][c]=2
    return out

bridge,fn=runner._open_bridge_with_rule(runner.wrap_rule(canonical[b.TASK_ID]['program_solution']))
try:
    samples=0; mismatches=[]; unique_inputs=set()
    for profile in b.SCENE_PROFILES:
        for seed in range(8):
            grid=b.generate(seed,0,difficulty='medium',scene_profile=profile)
            reference=runner._apply_rule(bridge,fn,grid)
            if b.self_check(grid) or lookup_rival(grid)!=reference:
                mismatches.append({'profile':profile,'seed':seed,'input':grid,'output':reference})
            samples+=1; unique_inputs.add(json.dumps(grid))
    # A connected five-wide symmetric cross absent from the finite inventory.
    novel=[[0]*13 for _ in range(13)]
    def place(mask,r0,c0,color):
        for r,row in enumerate(mask):
            for c,value in enumerate(row):
                if value=='1': novel[r0+r][c0+c]=color
    place(('00100','11111','00100'),1,1,1)
    place(('10','10','11'),7,1,1)
    place(('01','01','11'),7,8,1)
    novel[11][6]=3
    target=b._analysis(novel)
    reference=runner._apply_rule(bridge,fn,novel)
    record={'task_id':b.TASK_ID,'generator_sha256':digest,'lookup_shape_count':len(lookup),
            'sampled_profiles':list(b.SCENE_PROFILES),'seeds':list(range(8)),
            'sample_count':samples,'unique_inputs':len(unique_inputs),'lookup_mismatches':mismatches,
            'novel_input':novel,'novel_self_check':b.self_check(novel),
            'novel_profile':target['scene_profile'],'racket_output':reference,
            'lookup_output':lookup_rival(novel),
            'lookup_fails_on_novel':lookup_rival(novel)!=reference,
            'changed_cells':[[r,c] for r in range(13) for c in range(13) if novel[r][c]!=reference[r][c]],
            'canonical_exact':[runner._apply_rule(bridge,fn,p['input'])==p['output']
                    for split in ('train','test') for p in canonical[b.TASK_ID][split]]}
finally: bridge.shutdown()
(ROOT / 'checks/audit-93ca517eac25.json').write_text(json.dumps(record,indent=2)+'\n')
print('93ca517eac25',samples,'lookup mismatches',len(mismatches),'novel fails',record['lookup_fails_on_novel'],flush=True)
