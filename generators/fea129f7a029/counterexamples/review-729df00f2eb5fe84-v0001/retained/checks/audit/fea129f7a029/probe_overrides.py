from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / 'repo'
GEN = ROOT / 'generators' / 'fea129f7a029' / 'generator.py'
sys.path.insert(0, str(ROOT / 'shared' / 'runtime'))
spec = importlib.util.spec_from_file_location('audit_fea129f7a029', GEN)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

def digest(g):
    return hashlib.sha256(json.dumps(g, separators=(',', ':')).encode()).hexdigest()

def facts(g):
    h, w = len(g), len(g[0])
    divs = [r for r in range(h) if all(v == 5 for v in g[r])]
    div = divs[0]
    keys = mod._components_where(g, lambda v, r, c: r < div and v not in (0,3,5))
    targets = mod._components_where(g, lambda v, r, c: r > div and v == 3)
    sigs = {mod._sig(cells) for _, cells in keys}
    matched = sum(mod._sig(cells) in sigs for _, cells in targets)
    unmatched = len(targets) - matched
    return {'height':h,'width':w,'keys':len(keys),'targets':len(targets),'matched_targets':matched,'unmatched_targets':unmatched,'self_check':mod.self_check(g,difficulty='medium')}

seed=17
sample_index=4
cases={
    'n_pairs_1': {'n_pairs':1},
    'n_pairs_6': {'n_pairs':6},
    'n_unmatched_0': {'n_unmatched':0},
    'n_unmatched_7': {'n_unmatched':7},
    'shape_size_2': {'shape_size':2},
    'shape_size_6': {'shape_size':6},
}
rows={}
for name, overrides in cases.items():
    g=mod.generate(seed,sample_index,difficulty='medium',**overrides)
    rows[name]={'overrides':overrides,'sha256':digest(g),'facts':facts(g),'grid':g}
comparisons={
    'n_pairs_extremes_identical': rows['n_pairs_1']['grid']==rows['n_pairs_6']['grid'],
    'n_unmatched_extremes_identical': rows['n_unmatched_0']['grid']==rows['n_unmatched_7']['grid'],
    'shape_size_extremes_identical': rows['shape_size_2']['grid']==rows['shape_size_6']['grid'],
}
out={
    'task_id':mod.TASK_ID,
    'generator_sha256':hashlib.sha256(GEN.read_bytes()).hexdigest(),
    'seed':seed,'sample_index':sample_index,'difficulty':'medium',
    'comparisons':comparisons,
    'cases':rows,
    'finding':'Declared exact overrides n_pairs, n_unmatched, and shape_size are ignored when their extreme values produce byte-identical grids.'
}
Path(__file__).with_name('override-reproducer.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'comparisons':comparisons,'hashes':{k:v['sha256'] for k,v in rows.items()},'facts':{k:v['facts'] for k,v in rows.items()}},indent=2))
