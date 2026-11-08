from pathlib import Path
import importlib.util, sys, json, copy
from collections import deque, Counter
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'repo/shared/runtime'))
def load(t):
    p=root/'repo/generators'/t/'generator.py'
    spec=importlib.util.spec_from_file_location('audit_'+t,p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def path_stats(g):
    reds=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==2]
    greens=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==3]
    if len(reds)!=1 or len(greens)!=1:return None
    start,goal=reds[0],greens[0]; q=deque([start]);ds={start:0};ways={start:1}
    while q:
        p=q.popleft()
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            z=p[0]+dr,p[1]+dc
            if not(0<=z[0]<len(g) and 0<=z[1]<len(g[0])) or g[z[0]][z[1]]==5:continue
            if z not in ds:
                ds[z]=ds[p]+1;ways[z]=ways[p];q.append(z)
            elif ds[z]==ds[p]+1:ways[z]=min(2,ways[z]+ways[p])
    return {'distance':ds.get(goal),'number_of_shortest_paths_capped_at_two':ways.get(goal,0)}

out={}
for t,label in [('8584645d3102','maze'),('8a82ec149798','mirror')]:
    m=load(t); records=[json.loads(s) for s in(root/'checks'/('audit-'+label)/'samples.jsonl').open()]
    base=m.generate(0,0)
    findings={'task_id':t,'tiny_self_check':m.self_check([[9]]), 'tiny_input':[[9]],
              'unknown_override_ignored':base==m.generate(0,0,review_unknown_key=999),
              'canonical_failures':json.loads((root/'checks'/('audit-'+label)/'failures.json').read_text())}
    fixtures=[{'name':name,'parameters':dict(seed=0,sample_index=0,texture=name)} for name in m.DEGENERATE_TEXTURES]
    if label=='maze':
        findings['wall_pct_ignored']=m.generate(0,0,wall_pct=0.0)==m.generate(0,0,wall_pct=0.4)
        stats=[(row,path_stats(row['input'])) for row in records]
        bad=[(r,s) for r,s in stats if s['number_of_shortest_paths_capped_at_two']==2]
        findings['multiple_shortest_paths_samples']=len(bad);findings['total_samples']=len(records)
        findings['multiple_path_witness']={**bad[0][0],**bad[0][1]} if bad else None
    else:
        findings['n_cells_ignored']=m.generate(0,0,n_cells=1)==m.generate(0,0,n_cells=6)
    (root/'checks'/('audit-'+label+'-fixtures.json')).write_text(json.dumps(fixtures,indent=2)+'\n')
    out[t]=findings
(root/'checks/audit-diagnostics.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({t:{k:v for k,v in f.items() if k not in ('multiple_path_witness','canonical_failures')} for t,f in out.items()},indent=2))
