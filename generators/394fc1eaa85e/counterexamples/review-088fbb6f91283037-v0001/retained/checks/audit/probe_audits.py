"""Findings-only checks for the two immutable audit assignments."""
from collections import Counter, deque
import hashlib, importlib.util, json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'repo/shared/runtime'))

def load(tid):
 p=ROOT/'repo/generators'/tid/'generator.py'
 s=importlib.util.spec_from_file_location('audit_'+tid,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def comps(grid):
 seen=set(); result=[]
 for r,row in enumerate(grid):
  for c,v in enumerate(row):
   if not v or (r,c) in seen:continue
   todo=[(r,c)];seen.add((r,c));cells=[]
   while todo:
    a,b=todo.pop();cells.append((a,b))
    for da,db in ((1,0),(-1,0),(0,1),(0,-1)):
     x,y=a+da,b+db
     if 0<=x<len(grid) and 0<=y<len(grid[0]) and (x,y) not in seen and grid[x][y]==v:
      seen.add((x,y));todo.append((x,y))
   mr=min(a for a,b in cells);mc=min(b for a,b in cells)
   result.append(tuple(sorted((a-mr,b-mc) for a,b in cells)))
 return result

def crop(shape):
 h=1+max(r for r,c in shape);w=1+max(c for r,c in shape)
 out=[[0]*w for _ in range(h)]
 for r,c in shape:out[r][c]=6
 return out

if __name__=='__main__':
 tid='bf097cbccabe'; m=load(tid); dest=ROOT/'checks/audit'/tid;dest.mkdir(exist_ok=True)
 report={'task_id':tid,'generator_sha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),'findings':[]}
 inputs=[]
 for texture in ('all_same_shape','two_uniques'):
  grid=m.generate(7,0,texture=texture);counts=Counter(comps(grid))
  inputs.append(grid)
  report['findings'].append({'kind':'validator_accepts_documented_degenerate','texture':texture,'seed':7,'sample_index':0,'self_check':m.self_check(grid),'shape_multiplicities':list(counts.values()),'singleton_classes':sum(v==1 for v in counts.values()),'input_index':len(inputs)-1,'rival_output':[[0]]})
 overrides={'grid_h':11,'grid_w':11,'n_dup_shapes':3,'copies':3}
 grid=m.generate(7,0,difficulty='easy',**overrides); inputs.append(grid);counts=Counter(comps(grid))
 report['findings'].append({'kind':'exact_overrides_ignored','seed':7,'sample_index':0,'difficulty':'easy','overrides':overrides,'observed':{'grid_h':len(grid),'grid_w':len(grid[0]),'shape_multiplicities':sorted(counts.values()),'n_dup_shapes':sum(v>1 for v in counts.values())},'input_index':len(inputs)-1})
 unknown=m.generate(7,0,difficulty='easy',typo_axis=42)
 report['unknown_override_accepted']=True
 report['unknown_override_same_as_default']=unknown==m.generate(7,0,difficulty='easy')
 census=[]
 for band in ('easy','medium','hard'):
  failures=[]
  for seed in range(10):
   g=m.generate(seed,seed,difficulty=band);mult=Counter(comps(g))
   if sum(v==1 for v in mult.values())!=1 or m.self_check(g):failures.append(seed)
  census.append({'band':band,'seed_and_index_range':[0,9],'samples':10,'unique_shape_failures':failures})
 report['ordinary_draw_census']=census
 (dest/'inputs.json').write_text(json.dumps(inputs)+'\n');(dest/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
 print(tid,json.dumps(report))

 tid='394fc1eaa85e';m=load(tid);dest=ROOT/'checks/audit'/tid;dest.mkdir(exist_ok=True)
 inputs=[];meta=[];perband={}; all_failures=[]
 for band in ('easy','medium','hard'):
  grids=[m.generate(7,i,difficulty=band) for i in range(12)]
  for i,g in enumerate(grids):inputs.append(g);meta.append({'band':band,'seed':7,'sample_index':i})
  rejected=[]
  for start in range(8):
   demos=[{'input':g,'output':m.rule_mirror(g)} for g in grids[start:start+3]]
   q={'input':grids[start+3],'output':m.rule_mirror(grids[start+3])}
   reasons=m.lesson_identifiable(demos,q)
   if reasons:rejected.append({'start':start,'reasons':reasons})
  perband[band]={'draws':len(grids),'selfcheck_failures':sum(bool(m.self_check(g)) for g in grids),'strict_failures':sum(bool(m.strict_canonical_like(g)) for g in grids),'lessons':8,'lesson_rejections':rejected,'wall_profiles':dict(Counter(m.semantic_observables(g)['wall_profile'] for g in grids)),'unreachable_open_counts':[m.semantic_observables(g)['unreachable_open_count'] for g in grids]}
 # Lawful hand-made island: both seeds remain in the main connected region,
 # but an enclosed open cell is unreachable from either. Default draws above
 # may never teach the finite-distance qualification.
 island=[[0]*11 for _ in range(9)];island[7][2]=2;island[7][8]=3
 for r in range(1,4):
  for c in range(4,7):
   if r in (1,3) or c in (4,6):island[r][c]=5
 analysis=m._analysis(island)
 output=m.rule_mirror(island)
 rival=[list(row) for row in output]
 # Tempting bug: absent distances are both infinity, and infinity==infinity.
 for r,c in analysis['unreachable_open']:rival[r][c]=8
 island_i=len(inputs);inputs.append(island);meta.append({'kind':'handmade_unreachable_island'})
 pairs=[]
 for line in (ROOT/'repo/shared/data/canonical/puzzles.jsonl').open():
  row=json.loads(line)
  if row.get('task_id')==tid:
   pairs=row['train']+([row['test']] if isinstance(row['test'],dict) else row['test']);break
 report={'task_id':tid,'generator_sha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),'rule_hash':m.RULE_HASH,'per_band':perband,'input_metadata':meta,'expected_outputs':[m.rule_mirror(g) for g in inputs],
 'canonical_shortcut_matches':{n:sum(fn(p['input'])==p['output'] for p in pairs) for n,fn in m.CANONICAL_SHORTCUTS.items()},'canonical_pairs':len(pairs),
 'island':{'input_index':island_i,'input':island,'self_check':m.self_check(island),'strict_canonical_like':m.strict_canonical_like(island),'unreachable_open':analysis['unreachable_open'],'rival_output':rival,'rival_differs':rival!=output,'domain':'Accepted input grammar; not one of the four generated wall templates'}}
 (dest/'inputs.json').write_text(json.dumps(inputs)+'\n');(dest/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
 print(tid,json.dumps({k:v for k,v in report.items() if k not in ('expected_outputs','island','input_metadata')}))
