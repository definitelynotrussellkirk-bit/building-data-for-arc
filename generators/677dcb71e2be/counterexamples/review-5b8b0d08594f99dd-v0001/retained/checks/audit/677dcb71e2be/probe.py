from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
from reviewer_support import canonical_pairs

TASK='677dcb71e2be'
ROOT=Path(__file__).resolve().parents[3] / 'repo'
GEN=ROOT/'generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audit_677', GEN); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def in_corner_slot(comp,h,w):
    top,left,_,_=comp['bbox']
    return top in {0,1,h-4} and left in {0,1,w-4,w-3}

def rival(grid):
    comps=[c for c in mod._components(grid) if in_corner_slot(c,len(grid),len(grid[0]))]
    comps=sorted(comps,key=lambda c:(-c['size'],c['color']))
    row=[]
    for i,c in enumerate(comps):
        if i: row.append(0)
        row.extend([c['color']]*c['size'])
    return [row]

bands=[None,'easy','medium','hard']
samples=0; generated_noncorner=0; generated_rival_mismatch=0
for band in bands:
    for seed in range(100):
        for index in range(20):
            grid=mod.generate(seed,index,difficulty=band)
            comps=mod._components(grid)
            samples+=1
            generated_noncorner += sum(not in_corner_slot(c,len(grid),len(grid[0])) for c in comps)
            generated_rival_mismatch += rival(grid)!=mod._official_output(grid)

pairs=canonical_pairs(TASK, root=ROOT)
canon=[]; selected=None
for i,pair in enumerate(pairs):
    comps=mod._components(pair['input'])
    noncorner=[{'bbox':list(c['bbox']),'size':c['size'],'color':c['color']} for c in comps if not in_corner_slot(c,len(pair['input']),len(pair['input'][0]))]
    rec={'index':i,'noncorner_components':noncorner,'rival_disagrees':rival(pair['input'])!=pair['output'],'self_check':mod.self_check(pair['input'])}
    canon.append(rec)
    if selected is None and noncorner:
        selected=(i,pair)
assert selected is not None
idx,pair=selected
outdir=ROOT.parent/'checks'/'audit'/TASK
(outdir/'input.json').write_text(json.dumps(pair['input'],indent=2)+'\n')
(outdir/'rival.json').write_text(json.dumps(rival(pair['input']),indent=2)+'\n')
report={
 'schema':'arcpuzzles-audit-probe-v1','task_id':TASK,
 'generator_sha256':hashlib.sha256(GEN.read_bytes()).hexdigest(),
 'domain':{'bands':['default','easy','medium','hard'],'seeds':'0..99','sample_indices':'0..19'},
 'generated':{'samples':samples,'noncorner_components':generated_noncorner,'rival_mismatches':generated_rival_mismatch},
 'canonical':canon,'selected_canonical_index':idx,
 'rival':'find/sort only components whose bounding-box origin is in one of the generator four corner slots',
 'finding':'All generated components start in fixed corner slots. The rival is exact on every sampled generated grid but drops central components accepted by self_check and present in every canonical scene.'
}
(outdir/'probe-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
