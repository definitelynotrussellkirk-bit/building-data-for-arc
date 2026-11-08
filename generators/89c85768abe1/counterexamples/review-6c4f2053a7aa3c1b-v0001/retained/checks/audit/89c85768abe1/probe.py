"""Bounded audit of the assigned target only; Python diagnostics, no private runner."""
from pathlib import Path
import hashlib, importlib.util, json, sys
ROOT=Path(__file__).resolve().parents[3]
REPO=ROOT/'repo'
sys.path.insert(0,str(REPO/'shared/runtime'))
TARGET='89c85768abe1'
source=REPO/'generators'/TARGET/'generator.py'
spec=importlib.util.spec_from_file_location('audited_generator',source)
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
canonical=None
for line in (REPO/'shared/data/canonical/puzzles.jsonl').open():
    item=json.loads(line)
    if item.get('task_id')==TARGET:
        canonical=item; break
assert canonical is not None
sha=lambda b: hashlib.sha256(b).hexdigest()
identity={'task_id':TARGET,'generator_sha256':sha(source.read_bytes()),'canonical_rule_sha256':sha(canonical['program_solution'].encode()),'canonical_record_sha256':sha(json.dumps(canonical,sort_keys=True,separators=(',',':')).encode()),'phase':'unchanged audit target'}
def properties(g):
    colors=sorted({v for row in g for v in row if v})
    return {'height':len(g),'width':len(g[0]),'nonzero_colors':colors,'nonzero_color_count':len(colors),'validator_errors':gen.self_check(g)}
cases=[]
base=gen.generate(0,0,difficulty='easy')
for overrides in ({'palette_size':1},{'n_distinct_colors':1},{'palette_kind':'warm'},{'palette_kind':'cool'},{'texture':'warm'},{'texture':'cool'},{'grid_h':4},{'grid_w':18},{'rectangles':8},{'texture':'single_corner'},{'texture':'collinear_pair','grid_h':8,'grid_w':9}):
    entry={'seed':0,'sample_index':0,'difficulty':'easy','overrides':overrides}
    try:
        grid=gen.generate(0,0,difficulty='easy',**overrides)
        entry.update(input=grid,observed=properties(grid),same_as_baseline=grid==base)
    except Exception as exc:
        entry['exception']=f'{type(exc).__name__}: {exc}'
    cases.append(entry)
# A validator-boundary input with two genuine corner pairs, but intersecting boxes.
overlap=[[0]*5 for _ in range(5)]
overlap[0][0]=2; overlap[3][3]=2; overlap[1][1]=4; overlap[4][4]=4
single=gen.generate(0,0,difficulty='easy',texture='single_corner')
collinear=gen.generate(0,0,difficulty='easy',texture='collinear_pair',grid_h=8,grid_w=9)
actuals=[base,single,collinear,overlap]
(ROOT/'checks/audit'/TARGET/'input.json').write_text(json.dumps(actuals)+'\n')
report={'identity':identity,'measurement_kind':'Python generator/validator diagnostic; Racket authority is recorded separately in racket.json','baseline':{'seed':0,'sample_index':0,'difficulty':'easy','overrides':{},'input':base,'observed':properties(base)},'cases':cases,'racket_input_manifest':[{'index':0,'name':'baseline','domain':'Ordinary generated lawful corner-pair input'}, {'index':1,'name':'single_corner','seed':0,'sample_index':0,'difficulty':'easy','overrides':{'texture':'single_corner'},'observed':properties(single),'domain':'Advertised degenerate texture, rejected by own validator; outside ordinary exactly-two-corners invariant'}, {'index':2,'name':'collinear_pair','seed':0,'sample_index':0,'difficulty':'easy','overrides':{'texture':'collinear_pair','grid_h':8,'grid_w':9},'observed':properties(collinear),'domain':'Advertised degenerate texture; outside nondegenerate two-dimensional rectangle interpretation'}, {'index':3,'name':'overlap','seed':None,'sample_index':None,'overrides':None,'observed':properties(overlap),'domain':'Hand-constructed validator-boundary probe, outside documented disjoint-rectangle domain; not a generator-produced counterexample'}]}
(ROOT/'checks/audit'/TARGET/'diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'identity':identity,'cases':[{k:v for k,v in c.items() if k!='input'} for c in cases],'input_count':len(actuals)},indent=2))
