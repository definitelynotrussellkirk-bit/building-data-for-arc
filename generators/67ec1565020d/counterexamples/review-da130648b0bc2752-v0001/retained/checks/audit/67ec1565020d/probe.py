from pathlib import Path
import hashlib, importlib.util, json, sys
ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'repo'
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / 'shared/runtime'))
spec = importlib.util.spec_from_file_location('audited_generator', REPO/'generators/67ec1565020d/generator.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
def sha(b): return hashlib.sha256(b).hexdigest()
def components(g):
    seen = set(); out = []
    for r,row in enumerate(g):
        for c,col in enumerate(row):
            if not col or (r,c) in seen: continue
            todo=[(r,c)]; seen.add((r,c)); cells=[]
            while todo:
                rr,cc=todo.pop(); cells.append((rr,cc))
                for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    nr,nc=rr+dr,cc+dc
                    if 0<=nr<len(g) and 0<=nc<len(row) and g[nr][nc]==col and (nr,nc) not in seen:
                        seen.add((nr,nc)); todo.append((nr,nc))
            out.append(cells)
    return out
def bbox(cells):
    rs,cs=zip(*cells)
    return min(rs),min(cs),max(rs),max(cs)
def solid(cells):
    a,b,c,d=bbox(cells)
    return len(cells)==(c-a+1)*(d-b+1)
def rival(g):
    out=[[0]*len(g[0]) for _ in g]
    for cells in components(g):
        r0,c0,r1,c1=bbox(cells); h=r1-r0+1; w=c1-c0+1
        color=4 if h==w else 2 if w>h else 3
        for r in range(r0,r1+1):
            for c in range(c0,c1+1): out[r][c]=color
    return out
canonical = next(json.loads(line) for line in (REPO/'shared/data/canonical/puzzles.jsonl').read_text().splitlines() if json.loads(line)['task_id']=='67ec1565020d')
rule=canonical['program_solution']
hashes={str(path.relative_to(ROOT)):sha(path.read_bytes()) for path in (REPO/'generators/67ec1565020d/generator.py', REPO/'shared/runtime/puzzle_generators/base.py', REPO/'shared/runtime/puzzle_generators/helpers/shape.py', REPO/'shared/runtime/puzzle_generators/helpers/grid.py')}
record={'task_id':mod.TASK_ID,'generator_version':mod.VERSION,'source_sha256':hashes,'rule_text':rule,'rule_text_sha256':sha(rule.encode()),'rule_hash':sha(rule.encode())[:12], 'canonical_pairs':[], 'sampling':{'seed':670004,'sample_index_inclusive':[0,99],'overrides':{},'bands':['easy','medium','hard']},'bands':{}, 'sample_manifest':[]}
for split in ('train','test'):
    for i,pair in enumerate(canonical[split]):
        record['canonical_pairs'].append({'split':split,'index':i,'validator_errors':mod.self_check(pair['input']), 'rival_matches_saved_canonical_output':rival(pair['input'])==pair['output'], 'all_components_solid':all(map(solid,components(pair['input'])))})
for band in record['sampling']['bands']:
    stats={'inputs':0,'unique_inputs':0,'validator_accepted':0,'components':0,'non_solid_components':0,'inputs_with_non_solid_components':0}; unique=set()
    for index in range(100):
        g=mod.generate(670004,index,difficulty=band)
        cs=components(g); errors=mod.self_check(g,difficulty=band)
        ih=sha(json.dumps(g,separators=(',',':')).encode()); unique.add(ih)
        ns=sum(not solid(c) for c in cs)
        stats['inputs']+=1; stats['validator_accepted']+=not errors; stats['components']+=len(cs); stats['non_solid_components']+=ns; stats['inputs_with_non_solid_components']+=bool(ns)
        record['sample_manifest'].append({'difficulty':band,'sample_index':index,'input_sha256':ih,'validator_errors':errors,'components':len(cs),'non_solid_components':ns})
    stats['unique_inputs']=len(unique); record['bands'][band]=stats
# A 6x9 witness respects all three aspect classes, three distinct source colors,
# zero background, and no orthogonal or diagonal touching of separate objects.
g=[[0]*9 for _ in range(6)]
for r,c in ((1,1),(1,2),(2,1)):g[r][c]=5
for c in (5,6,7):g[1][c]=6
for r in (3,4,5):g[r][7]=7
record['witness']={'sampled':False,'seed':None,'sample_index':None,'overrides':None,'origin':'hand-built: replace one square corner with background','generator_validator_errors':mod.self_check(g),'dimensions':[6,9],'components':len(components(g)),'non_solid_components':sum(not solid(c) for c in components(g)), 'rival_definition':'Recolor by bounding-box aspect, painting every bbox cell, including absent object cells.', 'rival_output':rival(g)}
(OUT/'input.json').write_text(json.dumps(g,indent=2)+'\n')
(OUT/'rival.json').write_text(json.dumps(rival(g),indent=2)+'\n')
(OUT/'probe.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'hashes':hashes,'rule_hash':record['rule_hash'],'canonical_fit':[x['rival_matches_saved_canonical_output'] for x in record['canonical_pairs']], 'bands':record['bands'],'witness':record['witness']}))
