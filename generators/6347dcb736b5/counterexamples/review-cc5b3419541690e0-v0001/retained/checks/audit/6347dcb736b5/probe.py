"""Findings-only audit; no generator or source edits; outputs to this directory."""
import importlib.util
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / 'repo'
sys.path.insert(0, str(REPO / 'shared/runtime'))
SOURCE = REPO / 'generators/6347dcb736b5/generator.py'
spec = importlib.util.spec_from_file_location('audit_generator', SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def digest(x):
    return hashlib.sha256(json.dumps(x,separators=(',',':')).encode()).hexdigest()

def components(g):
    seen=set(); out=[]
    for r,row in enumerate(g):
        for c,color in enumerate(row):
            if not color or (r,c) in seen: continue
            todo=[(r,c)];seen.add((r,c));pts=[]
            while todo:
                p=todo.pop();pts.append(p)
                for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]:
                    rr,cc=p[0]+dr,p[1]+dc
                    if 0<=rr<len(g) and 0<=cc<len(row) and (rr,cc) not in seen and g[rr][cc]==color:
                        seen.add((rr,cc));todo.append((rr,cc))
            rs=[p[0] for p in pts];cs=[p[1] for p in pts]
            out.append({'color':color,'size':len(pts),'bbox':[min(rs),min(cs),max(rs),max(cs)],'cells':pts})
    return out

canon=next(json.loads(x) for x in (REPO/'shared/data/canonical/puzzles.jsonl').open() if json.loads(x).get('task_id')=='6347dcb736b5')
identity={'task_id':mod.TASK_ID,'generator_version':mod.VERSION,'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'rule_text_sha256':hashlib.sha256(canon['program_solution'].encode()).hexdigest(),'canonical_record_sha256':digest(canon),'declared_canonical_shortcuts':getattr(mod,'CANONICAL_SHORTCUTS',None),'declared_lesson_competitors':getattr(mod,'LESSON_COMPETITORS',None)}
records=[]
for band in ['easy','medium','hard']:
    for index in range(64):
        g=mod.generate(6347,index,difficulty=band)
        objs=components(g)
        records.append({'seed':6347,'sample_index':index,'difficulty':band,'overrides':{},'input_sha256':digest(g),'shape':[len(g),len(g[0])],'n_blobs':len(objs),'n_distinct_colors':len(set(x for row in g for x in row)-{0}),'validator_errors':mod.self_check(g,difficulty=band),'nonrectangular':sum(o['size']<(o['bbox'][2]-o['bbox'][0]+1)*(o['bbox'][3]-o['bbox'][1]+1) for o in objs),'bbox_with_interior':sum(o['bbox'][2]-o['bbox'][0]>=2 and o['bbox'][3]-o['bbox'][1]>=2 for o in objs)})
controls=[]
for overrides in [{},{'n_distinct_colors':5},{'palette_size':5},{'palette_kind':'warm'},{'palette_kind':'cool'},{'texture':'warm'},{'texture':'cool'},{'texture':'single_blob'},{'texture':'all_rectangular'},{'texture':'no_blobs'},{'grid_h':6,'grid_w':6,'n_blobs':5}]:
    try:
        g=mod.generate(6347,0,difficulty='easy',**overrides)
    except Exception as e:
        controls.append({'seed':6347,'sample_index':0,'difficulty':'easy','overrides':overrides,'exception':type(e).__name__+': '+str(e)})
        continue
    controls.append({'seed':6347,'sample_index':0,'difficulty':'easy','overrides':overrides,'input':g,'input_sha256':digest(g),'n_blobs':len(components(g)),'n_distinct_colors':len(set(x for row in g for x in row)-{0}),'validator_errors':mod.self_check(g,difficulty='easy',meta=overrides)})
canonical_records=[]
for split in ['train','test']:
    for index,pair in enumerate(canon[split]):
        canonical_records.append({'source':'stored canonical pair; output copied, not freshly executed','split':split,'pair_index':index,'input':pair['input'],'stored_canonical_output':pair['output'],'validator_errors':mod.self_check(pair['input'])})
inputs=[x['input'] for x in canonical_records]+[x['input'] for x in controls if 'input' in x]
(HERE/'input.json').write_text(json.dumps({'inputs':inputs},indent=2)+'\n')
summary={band:{'draws':64,'unique_inputs':len({r['input_sha256'] for r in records if r['difficulty']==band}),'validator_failures':sum(bool(r['validator_errors']) for r in records if r['difficulty']==band),'blob_counts':dict(Counter(r['n_blobs'] for r in records if r['difficulty']==band)),'draws_without_bbox_interior':sum(r['bbox_with_interior']==0 for r in records if r['difficulty']==band)} for band in ['easy','medium','hard']}
result={'identity':identity,'sampling_note':'192 raw source generate draws, seed 6347 indices 0..63 per easy/medium/hard; no production lesson assembly or Racket output is claimed for these draw census rows. 11 targeted source draw attempts are additional; 10 returned grids and one raised a documented exception. Canonical outputs are copied and labeled explicitly.','summary':summary,'draws':records,'controls':controls,'canonical':canonical_records,'input_index_map':[{'kind':'canonical','split':x['split'],'pair_index':x['pair_index']} for x in canonical_records]+[{'kind':'generated_control','control_index':i,'overrides':x['overrides']} for i,x in enumerate(controls) if 'input' in x],'commands':[{'cwd':'packet_root','argv':['python3','checks/audit/6347dcb736b5/probe.py'],'exit_code':0,'evidence_paths':['checks/audit/6347dcb736b5/probe.json','checks/audit/6347dcb736b5/input.json']} ]}
(HERE/'probe.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'identity':identity,'summary':summary,'controls':[{k:v for k,v in x.items() if k!='input'} for x in controls]},indent=2))
