"""Independent bounding-box-contact rival. No generator-private or runtime-private imports."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path.cwd()
OUT = Path(__file__).resolve().parent
TASK = '1f9fef86a482'
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_subject', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def objects(grid):
    seen = set()
    result = []
    for r in range(1, len(grid)):
        for c in range(len(grid[0])):
            if (r,c) in seen or not grid[r][c]: continue
            todo = [(r,c)]; seen.add((r,c)); cells = []
            while todo:
                p = todo.pop(); cells.append(p)
                for dr,dc in ((0,1),(0,-1),(1,0),(-1,0)):
                    q = (p[0]+dr,p[1]+dc)
                    if 1 <= q[0] < len(grid) and 0 <= q[1] < len(grid[0]) and q not in seen and grid[q[0]][q[1]] == grid[r][c]:
                        seen.add(q);todo.append(q)
            result.append(set(cells))
    return result

def box(cells):
    return min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells)

def box_contact(a,b):
    ar,ac,az,ax=box(a);br,bc,bz,bx=box(b)
    return (((ax+1==bc or bx+1==ac) and max(ar,br)<=min(az,bz)) or
            ((az+1==br or bz+1==ar) and max(ac,bc)<=min(ax,bx)))

def cell_contact(a,b):
    return any((r+dr,c+dc) in b for r,c in a for dr,dc in ((0,1),(0,-1),(1,0),(-1,0)))

def predict(grid,contact):
    obs=objects(grid);ds=[sum(j!=i and contact(a,b) for j,b in enumerate(obs)) for i,a in enumerate(obs)]
    k=grid[0].count(1);out=[[0]*len(grid[0]) for _ in grid]
    for a,d in zip(obs,ds):
        if d==k:
            for r,c in a:out[r][c]=8
    return out,ds

row=next(json.loads(line) for line in (ROOT/'shared/data/canonical/puzzles.jsonl').open() if json.loads(line).get('task_id')==TASK)
tests=row['test'] if isinstance(row['test'],list) else [row['test']]
pairs=[p for p in row['train']+tests if p.get('output')]
canonical=[{'pair':i,'rival_matches':predict(p['input'],box_contact)[0]==p['output'],
            'independent_matches':predict(p['input'],cell_contact)[0]==p['output'],
            'self_check_errors':gen.self_check(p['input'])} for i,p in enumerate(pairs)]
census=[]
for band in ('easy','medium','hard'):
    errors=[];mismatches=[]
    for index in range(80):
        seed=1200+index
        grid=gen.generate(seed,index,difficulty=band)
        if gen.self_check(grid): errors.append(index)
        if predict(grid,box_contact)[0]!=predict(grid,cell_contact)[0]: mismatches.append(index)
    census.append({'band':band,'draws':80,'seed_rule':'1200 + sample_index','sample_indices':'0..79','overrides':{},'validator_error_indices':errors,'rival_disagreement_indices':mismatches})
grid=[[0]*12 for _ in range(9)];grid[0][:2]=[1,1]
groups=[(2,[(3,1),(3,2),(4,1),(4,2)]),(3,[(3,3),(4,3),(5,3),(5,4)]),
        (4,[(6,3),(6,4),(7,4)]),(7,[(2,5),(2,6),(3,5),(3,6)])]
for color,cells in groups:
    for r,c in cells:grid[r][c]=color
expected,degrees=predict(grid,cell_contact);rival,bd=predict(grid,box_contact)
(OUT/'input.json').write_text(json.dumps(grid)+'\n')
(OUT/'rival.json').write_text(json.dumps(rival)+'\n')
report={'task_id':TASK,'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'canonical_program_text_sha256':hashlib.sha256(row['program_solution'].encode()).hexdigest(),
        'canonical_pairs':canonical,'default_census':census,
        'finding':'bounding-box edge contact substitutes for exact cell contact',
        'counterexample':{'origin':'authored in-grammar chain scene; not claimed emitted','seed':None,'sample_index':None,'overrides':None,
        'self_check_errors':gen.self_check(grid),'observable_controls':gen.observe_overrides(grid),
        'component_sizes':sorted(map(len,objects(grid))),'exact_degrees':degrees,'bbox_degrees':bd,
        'independent_expected':expected,'rival':rival}}
(OUT/'finding.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='counterexample'}))
print('counterexample validator',report['counterexample']['self_check_errors'],'exact',degrees,'box',bd)
