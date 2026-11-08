from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REPO = ROOT / 'WORK' / 'repo'
TASK = '1ec277b81469'
GEN_PATH = REPO / 'generators' / TASK / 'generator.py'
OLD = REPO / 'generators' / TASK / 'counterexamples' / 'review-b5134cdff2f48c98-v0002' / 'retained' / 'checks' / 'audit' / '1ec277b81469' / 'contract-probes.json'
OUT = Path(__file__).with_name('result.json')
spec=importlib.util.spec_from_file_location('audit_1ec',GEN_PATH)
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
sha=hashlib.sha256(GEN_PATH.read_bytes()).hexdigest()
old=json.loads(OLD.read_text())

def colors(grid): return sorted({v for row in grid for v in row if v})
base={'seed':20261005,'sample_index':0,'difficulty':'medium'}
probes=[]
for kwargs in [
    {'n_distinct_colors':1}, {'palette_size':1},
    {'texture':'no_active_rows'},
    {'texture':'no_active_rows','grid_h':14,'grid_w':18},
    {'texture':'fully_packed_rows'},
]:
    try:
        grid=gen.generate(base['seed'],base['sample_index'],difficulty=base['difficulty'],**kwargs)
        probes.append({'kwargs':kwargs,'accepted':True,'shape':[len(grid),len(grid[0])],'nonzero_colors':colors(grid),'self_check':gen.self_check(grid),'grid':grid})
    except Exception as exc:
        probes.append({'kwargs':kwargs,'accepted':False,'error':f'{type(exc).__name__}: {exc}'})
report={
    'schema':'arcpuzzles-current-audit-probe-v1','task_id':TASK,'generator_sha256':sha,
    'prior_finding_source_sha256':old['generator_sha256'],'prior_source_still_current':sha==old['generator_sha256'],
    **base,'probes':probes,
    'prior_exact_grid_reproduced': probes[0].get('grid')==old['probe_1']['grid'],
    'prior_no_active_rows_reproduced': probes[2].get('grid')==old['probe_2']['grid'],
}
OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'sha':sha,'prior_source_still_current':report['prior_source_still_current'],'summary':[{'kwargs':p['kwargs'],'shape':p.get('shape'),'colors':p.get('nonzero_colors'),'self_check':p.get('self_check')} for p in probes]},indent=2))
