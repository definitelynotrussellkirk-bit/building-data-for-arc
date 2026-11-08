#!/usr/bin/env python3
"""Read-only source-bound exact-axis reproduction; no private labels or runner."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--repo', required=True)
parser.add_argument('--out', required=True)
args = parser.parse_args()
repo = Path(args.repo).resolve()
out = Path(args.out).resolve()
source = repo / 'generators/76c3f9d7128a/generator.py'
sha = hashlib.sha256(source.read_bytes()).hexdigest()
assert sha == '6ba9ab227d908ffb307ba59fff4ee80a4960838d7a990329096b6a38ef594fec', sha
sys.path.insert(0, str(repo / 'shared/runtime'))
spec = importlib.util.spec_from_file_location('audited_generator', source)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
seed, index, difficulty = 123, 0, 'medium'
base = {'n_pairs':3,'palette_kind':'default','texture':'default'}
grid = gen.generate(seed, index, difficulty=difficulty, **base)
errors = gen.self_check(grid, difficulty=difficulty)
comparisons=[]
for key, choices in [('palette_kind',['warm','cool','varied']),('texture',['warm','cool','varied'])]:
    for value in choices:
        overrides = dict(base);overrides[key] = value
        other = gen.generate(seed,index,difficulty=difficulty,**overrides)
        comparisons.append({'overrides':overrides,'same_as_baseline':other==grid,
            'self_check':gen.self_check(other,difficulty=difficulty),
            'input_sha256':hashlib.sha256(json.dumps(other,separators=(',',':')).encode()).hexdigest()})
rejections=[]
for band, overrides in [('medium',{'grid_h':8}),('medium',{'grid_w':18}),('medium',{'n_pairs':5}),('easy',{'n_pairs':5}),('hard',{'n_pairs':3})]:
    try:
        generated=gen.generate(seed,index,difficulty=band,**overrides)
        rejections.append({'difficulty':band,'overrides':overrides,'accepted':True,'self_check':gen.self_check(generated,difficulty=band)})
    except Exception as exc:
        rejections.append({'difficulty':band,'overrides':overrides,'accepted':False,'exception_type':type(exc).__name__,'message':str(exc)})
(out / 'input.json').write_text(json.dumps(grid,indent=2)+'\n')
report={'schema':'source-bound-exact-axis-audit-v1','task_id':'76c3f9d7128a',
    'generator_sha256':sha,'seed':seed,'sample_index':index,'difficulty':difficulty,
    'overrides':base,'self_check':errors,'passes_self_check':not errors,
    'input':grid,'observed_nonzero_colors':sorted({v for row in grid for v in row if v}),
    'axis_declarations':gen.AXES,'ignored_axis_comparisons':comparisons,
    'declared_valid_override_rejections':rejections,'rival_output':None,
    'rival_output_reason':'These are input-axis contract defects, not competing output semantics.',
    'different_cells':[], 'bounded_checks':'One lawful baseline at seed123/index0/medium; six helpful-axis comparisons and five documented-valid rejection probes. No ordinary scan or identifiability claim.'}
(out / 'probe.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'generator_sha256':sha,'baseline_self_check':errors,'same_input_comparisons':sum(x['same_as_baseline'] for x in comparisons),'comparisons':len(comparisons),'override_rejections':rejections}))
