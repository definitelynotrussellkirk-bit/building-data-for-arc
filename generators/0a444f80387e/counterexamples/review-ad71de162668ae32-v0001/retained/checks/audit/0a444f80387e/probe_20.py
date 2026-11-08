"""Find production lessons that fail to distinguish component-only cropping."""
import hashlib
import importlib.util
import json
from pathlib import Path
from arcpuzzles.catalog import Catalog
from reviewer_support import canonical_pairs

TASK='0a444f80387e'
ROOT=Path.cwd()
OUT=ROOT.parent/'checks/audit'/TASK
SOURCE=ROOT/'generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audit_target', SOURCE)
generator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

def rival(grid):
    h,w=len(grid),len(grid[0])
    by={};seen=set()
    for r in range(h):
        for c in range(w):
            color=grid[r][c]
            if not color or (r,c) in seen: continue
            todo=[(r,c)];seen.add((r,c));cells=[]
            while todo:
                a,b=todo.pop();cells.append((a,b))
                for nr,nc in ((a-1,b),(a+1,b),(a,b-1),(a,b+1)):
                    if 0<=nr<h and 0<=nc<w and (nr,nc) not in seen and grid[nr][nc]==color:
                        seen.add((nr,nc));todo.append((nr,nc))
            by.setdefault(color,[]).append(cells)
    for color,components in by.items():
        big=[component for component in components if len(component)>1]
        if sum(len(component)==1 for component in components)==1 and len(big)==1:
            cells=big[0]
            r0=min(r for r,c in cells);r1=max(r for r,c in cells)
            c0=min(c for r,c in cells);c1=max(c for r,c in cells)
            result=[[0]*(c1-c0+1) for _ in range(r1-r0+1)]
            for r,c in cells: result[r-r0][c-c0]=color
            return result
    return [[0]]

pairs=canonical_pairs(TASK,root=ROOT,labeled_only=True)
canonical=[{'index':i,'matches':rival(p['input'])==p['output']} for i,p in enumerate(pairs)]
catalog=Catalog(ROOT)
episodes=catalog.generate(TASK,count=20,seed=0,difficulty='medium',n_train=3,n_test=1,allow_unapproved=True,timeout=300)
(OUT/'episode_schema.json').write_text(json.dumps({'keys':list(episodes[0]),'episode':episodes[0]},indent=2)+'\n')
summary={'task_id':TASK,'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'canonical':canonical,'generated_episode_count':len(episodes),'generation_options':{'count':20,'seed':0,'difficulty':'medium','n_train':3,'n_test':1,'sample_index':0,'overrides':{},'allow_unapproved':True},'ambiguous':[]}
for i,episode in enumerate(episodes):
    challenge=episode.get('challenge',episode)
    train=challenge.get('train',[]);test=challenge.get('test',[])
    if not train or not test: raise ValueError('Inspect retained public episode schema: missing train/test')
    if all(rival(p['input'])==p['output'] for p in train) and any(rival(p['input'])!=p['output'] for p in test):
        summary['ambiguous'].append(i)
        if len(summary['ambiguous'])==1:
            (OUT/'ambiguous_lesson.json').write_text(json.dumps(episode,indent=2)+'\n')
            (OUT/'query_input.json').write_text(json.dumps(test[0]['input'])+'\n')
            (OUT/'query_rival.json').write_text(json.dumps({'output':rival(test[0]['input']),'self_check':generator.self_check(test[0]['input'])},indent=2)+'\n')
(OUT/'probe_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
