"""Reproduce two findings without modifying either audit target."""
import hashlib, importlib.util, json, sys
from pathlib import Path
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root
root = find_root(Path.cwd())
outroot = root.parent/'checks'
cat = Catalog(root=root)
def load(tid):
    path=root/'generators'/tid/'generator.py'
    spec=importlib.util.spec_from_file_location('audit_'+tid,path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module,path

def crop(grid):
    cells=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v]
    r0,r1=min(r for r,c in cells),max(r for r,c in cells)
    c0,c1=min(c for r,c in cells),max(c for r,c in cells)
    return [row[c0:c1+1] for row in grid[r0:r1+1]]
def clockwise(g): return [list(row) for row in zip(*g[::-1])]
def summary_rival(grid):
    state=crop([row[:] for row in grid[1:]])
    states=[]
    for code in [v for v in grid[0] if v]:
        if code == 2:state=clockwise(state)
        elif code == 3:state=clockwise(clockwise(state))
        elif code == 4:state=clockwise(clockwise(clockwise(state)))
        states.append(state)
    result=[[0]*(sum(len(g[0]) for g in states)+len(states)-1) for _ in range(max(map(len,states)))]
    col=0
    for g in states:
        for r,row in enumerate(g): result[r][col:col+len(row)]=row
        col+=len(g[0])+1
    return result

def gravity(g, ignore_bottom=False):
    h,w=len(g),len(g[0]); out=[[0]*w for _ in range(h)]
    for c in range(w):
        vals=[g[r][c] for r in range(h-int(ignore_bottom)) if g[r][c]]
        for r,v in enumerate(vals, h-len(vals)):out[r][c]=v
    return out

tid='ce3c0854174d';gen,path=load(tid)
seed=0
while True:
    grid=gen.generate(seed,0,difficulty='easy')
    if grid[0][0]==1:break
    seed+=1
folder=outroot/'audit'/tid
(folder/'input.json').write_text(json.dumps(grid)+'\n')
(folder/'rival.json').write_text(json.dumps(summary_rival(grid))+'\n')
errors=[]
for axis,value in [('height',7),('width',10),('script_len',2)]:
    try: gen.generate(0,0,**{axis:value}); errors.append({'axis':axis,'value':value,'accepted':True})
    except Exception as exc: errors.append({'axis':axis,'value':value,'error':str(exc)})
(folder/'metadata.json').write_text(json.dumps({'task_id':tid,'generator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'rule_hash':cat.describe(tid)['rule_hash'],'seed':seed,'sample_index':0,'difficulty':'easy','overrides':{},
 'validator_errors':gen.self_check(grid),'within_documented_generator_domain':True,
 'rival':'mapping stated in SUMMARY: 1 identity, 2 clockwise, 3 half-turn, 4 counterclockwise',
 'boundary_rejections':errors,'command':sys.argv,'cwd':str(Path.cwd())},indent=2)+'\n')

tid='2a43e4f3a796';gen,path=load(tid);folder=outroot/'audit'/tid
pairs=canonical_pairs(tid,root=root)
grid=pairs[0]['input']
counts={'generated':0,'generated_nonzero_bottom_row':0,'ignore_bottom_rival_matches_diagnostic':0,
        'canonical_pairs':len(pairs),'canonical_rival_matches':0}
for band in ['easy','medium','hard']:
    for seed in range(100):
        g=gen.generate(seed,0,difficulty=band);counts['generated']+=1
        counts['generated_nonzero_bottom_row']+=int(any(g[-1]))
        counts['ignore_bottom_rival_matches_diagnostic']+=int(gravity(g)==gravity(g,True))
for pair in pairs:counts['canonical_rival_matches']+=int(gravity(pair['input'],True)==pair['output'])
(folder/'input.json').write_text(json.dumps(grid)+'\n')
(folder/'rival.json').write_text(json.dumps(gravity(grid,True))+'\n')
(folder/'metadata.json').write_text(json.dumps({'task_id':tid,'generator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'rule_hash':cat.describe(tid)['rule_hash'],'source':'canonical variant 0 train pair 0',
 'validator_errors':gen.self_check(grid),'within_documented_rule_domain':True,
 'within_actual_ordinary_sampler_support':False,'counts':counts,'seed_range':[0,99],'sample_index':0,
 'rival':'drop the original bottom input row, then compact each column',
 'command':sys.argv,'cwd':str(Path.cwd())},indent=2)+'\n')

baseline=json.loads((outroot/'coverage-baseline.json').read_text())
case=baseline['first_counterexamples']['CANONICAL_SHORTCUTS.bbox_area']
assert case['query_index']==case['input_indices'][-1]
folder=outroot/'baseline-ambiguity'
(folder/'inputs.json').write_text(json.dumps(case['inputs'])+'\n')
(folder/'case.json').write_text(json.dumps({'source_generator_sha256':baseline['source_sha256'],
 'rival_generator_sha256':baseline['rival_source_sha256'],'rule_hash':baseline['rule_hash'],
 'rival':'bbox_area','case':case,'command':sys.argv,'cwd':str(Path.cwd())},indent=2)+'\n')
print('Built two audit counterexamples and one baseline production-lesson ambiguity.')
print('audit script seed:', json.loads((outroot/'audit/ce3c0854174d/metadata.json').read_text())['seed'])
