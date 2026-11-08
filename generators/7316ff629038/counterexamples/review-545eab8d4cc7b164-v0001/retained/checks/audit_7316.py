"""Findings-only reproducible audit; makes no changes to the audited source."""
import hashlib,importlib.util,json
from pathlib import Path
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs,find_root
ROOT=find_root(Path.cwd())
TASK='7316ff629038'
p=ROOT/'generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audited',p);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)

def components(grid):
    seen=set();objs=[]
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if not v or (r,c) in seen:continue
            seen.add((r,c));cells=[];stack=[(r,c)]
            while stack:
                a,b=stack.pop();cells.append((a,b))
                for x,y in ((a-1,b),(a+1,b),(a,b-1),(a,b+1)):
                    if 0<=x<len(grid) and 0<=y<len(grid[0]) and (x,y) not in seen and grid[x][y]==v:
                        seen.add((x,y));stack.append((x,y))
            objs.append((v,min(y for x,y in cells),max(y for x,y in cells)))
    return sorted(objs)

def rival(grid):
    objs=components(grid)
    return [[int(a[1]<b[1]) for b in objs] for a in objs]

def mirror(grid):
    objs=components(grid);centers=[(a+b)//2 for _,a,b in objs]
    return [[int(a<b) for b in centers] for a in centers]

base=g.generate(77,3,difficulty='medium')
ignored={}
for name,a,b in [('palette_kind','warm','cool'),('palette_size',3,5),('n_distinct_colors',3,5)]:
    ga=g.generate(77,3,difficulty='medium',**{name:a});gb=g.generate(77,3,difficulty='medium',**{name:b})
    ignored[name]={'first_value':a,'second_value':b,'equal_to_default':ga==base and gb==base,'same_pixels':ga==gb}
try:g.generate(77,3,difficulty='easy',n_components=7)
except Exception as exc:boundary={'type':type(exc).__name__,'message':str(exc),'overrides':{'n_components':7},'difficulty':'easy'}
else:boundary={'unexpected':'accepted'}
pairs=canonical_pairs(TASK,root=ROOT)
found=None
for band in ('easy','medium','hard'):
    for i in range(100):
        grid=g.generate(7700+i,i,difficulty=band)
        if rival(grid)!=mirror(grid):
            found={'seed':7700+i,'sample_index':i,'difficulty':band,'overrides':{},'input':grid,
                   'rival_output':rival(grid),'validator_errors':g.self_check(grid)};break
    if found:break
out=ROOT.parent/'checks/audit'/TASK;out.mkdir(parents=True,exist_ok=True)
input_grid=found['input'] if found else base
(out/'input.json').write_text(json.dumps(input_grid)+'\n')
report={'task_id':TASK,'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
        'seed':77,'sample_index':3,'difficulty':'medium','input':base,'validator_errors':g.self_check(base),
        'ignored_axes':ignored,'advertised_boundary_rejection':boundary,
        'unknown_axis_accepted_unchanged':g.generate(77,3,difficulty='medium',typo_axis=1)==base,
        'left_edge_rival_canonical_fit':{'matched':sum(rival(x['input'])==x['output'] for x in pairs),'total':len(pairs)},
        'generated_rival_counterexample':found,
        'interpretation':'Ignored controls and boundary rejection are reproduced defects. A left-edge rival difference is a useful generated witness, not a teaching defect by itself.'}
(out/'findings.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('input','generated_rival_counterexample')}))
