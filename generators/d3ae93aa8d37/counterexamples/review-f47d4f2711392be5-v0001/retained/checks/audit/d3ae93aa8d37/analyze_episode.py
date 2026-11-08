"""Score one exact production lesson against the obstacle-blind row rival."""
import hashlib,json
from pathlib import Path
from reviewer_support import find_root,load_selected_generator,canonical_pairs

root=find_root(__file__)
g,source,sha=load_selected_generator('d3ae93aa8d37',root=root)
base=Path(__file__).resolve().parent
episode=json.loads((base/'wrong-query-episode.jsonl').read_text().strip())

def straight(grid):
    starts=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==2]
    goals=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==3]
    if len(starts)!=1 or len(goals)!=1 or starts[0][0]!=goals[0][0]:
        raise ValueError('rival requires one same-row start and goal')
    out=[row[:] for row in grid]
    r,c1=starts[0];_,c2=goals[0]
    for c in range(min(c1,c2)+1,max(c1,c2)):
        out[r][c]=8
    return out

comparisons=[]
for split in ('train','test'):
    for index,p in enumerate(episode[split]):
        rival=straight(p['input'])
        comparisons.append({'split':split,'pair_index':index,'input':p['input'],
          'racket_output':p['output'],'rival_output':rival,'self_check':g.self_check(p['input']),
          'rival_agrees':rival==p['output'],
          'differences':[[r,c,p['output'][r][c],rival[r][c]] for r,row in enumerate(rival) for c,v in enumerate(row) if v!=p['output'][r][c]]})
can=[]
for p in canonical_pairs('d3ae93aa8d37',root=root):
    try:
        fit=straight(p['input'])==p['output']
    except ValueError:
        fit=False
    can.append({'split':p['split'],'pair_index':p['pair_index'],'rival_fits':fit})
out={'task_id':g.TASK_ID,'generator_sha256':sha,'version':g.VERSION,
 'episode_metadata':{k:v for k,v in episode.items() if k not in ('train','test','program')},
 'canonical_rival_checks':can,'pairs':comparisons,
 'demo_rival_agreements':[p['rival_agrees'] for p in comparisons if p['split']=='train'],
 'query_rival_agreements':[p['rival_agrees'] for p in comparisons if p['split']=='test']}
(base/'wrong-query-evidence.json').write_text(json.dumps(out,indent=2)+'\n')
(base/'query-input.json').write_text(json.dumps({'input':episode['test'][0]['input']})+'\n')
assert out['demo_rival_agreements']==[True]*4,out['demo_rival_agreements']
assert out['query_rival_agreements']==[False],out['query_rival_agreements']
assert all(not p['self_check'] for p in comparisons)
print(json.dumps({k:v for k,v in out.items() if k not in ('pairs','episode_metadata')},indent=2))
print(json.dumps(out['episode_metadata'],indent=2))
