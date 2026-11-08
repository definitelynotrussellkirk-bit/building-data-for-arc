from __future__ import annotations
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path('/mnt/data/arc_review_20261002_153658/repo')
sys.path.insert(0, str(ROOT / 'shared/runtime'))


def load(tid):
    path=ROOT/f'generators/{tid}/generator.py'
    spec=importlib.util.spec_from_file_location('audit_'+tid,path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

rows={}
for line in (ROOT/'shared/data/canonical/puzzles.jsonl').open():
    row=json.loads(line)
    if row.get('task_id') in {'641f580d5310','bb75d495c809'}:
        rows[row['task_id']]=row

# 641f: independent official and a shortcut that overwrites the center source.
def mirror_official(g):
    h,w=len(g),len(g[0]); out=[row[:] for row in g]
    for r in range(h):
        for c in range(w):
            if g[r][c]==0 and g[r][w-1-c]==1:
                out[r][c]=4
    return out

def overwrite_mirror_rival(g):
    h,w=len(g),len(g[0]); out=[row[:] for row in g]
    for r in range(h):
        for c in range(w):
            if g[r][c]==1:
                out[r][w-1-c]=4
    return out

m=load('641f580d5310')
canon=[]
for i,pair in enumerate(rows['641f580d5310']['train']+rows['641f580d5310'].get('test',[])):
    g=pair['input']; w=len(g[0]);
    canon.append({
        'index':i,
        'dims':[len(g),w],
        'center_axis_ones':sum(v==1 and c==w//2 for row in g for c,v in enumerate(row)),
        'self_check_errors':m.self_check(g),
        'official_matches_public_output': ('output' not in pair or mirror_official(g)==pair['output']),
        'overwrite_rival_differs':overwrite_mirror_rival(g)!=mirror_official(g),
    })
ordinary={'samples':0,'center_axis_ones':0,'rival_disagreements':0,'self_check_failures':0}
for band in ('easy','medium','hard'):
    for seed in range(256):
        g=m.generate(seed,0,difficulty=band)
        ordinary['samples']+=1; w=len(g[0])
        ordinary['center_axis_ones'] += sum(v==1 and c==w//2 for row in g for c,v in enumerate(row))
        ordinary['rival_disagreements'] += overwrite_mirror_rival(g)!=mirror_official(g)
        ordinary['self_check_failures'] += bool(m.self_check(g))
overrides={}
for key,val in [('bogus',1),('palette_kind','warm'),('palette_size',2),('n_distinct_colors',2),('grid_h',12),('grid_w',14),('n_ones',15)]:
    try:
        g=m.generate(1,0,**{key:val})
        overrides[key]={'status':'accepted','realized_dims':[len(g),len(g[0])],
                        'ones':sum(v==1 for row in g for v in row)}
    except Exception as e:
        overrides[key]={'status':'error','type':type(e).__name__,'message':str(e)}
report641={'canonical':canon,'ordinary':ordinary,'override_probes':overrides}

# bb75: distribution and contract probes.
def comps0(g):
    h,w=len(g),len(g[0]); seen=set(); comps=[]
    for r in range(h):
        for c in range(w):
            if g[r][c]!=0 or (r,c) in seen: continue
            stack=[(r,c)];seen.add((r,c)); cells=[]
            while stack:
                x=stack.pop();cells.append(x)
                for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    y=(x[0]+dr,x[1]+dc)
                    if 0<=y[0]<h and 0<=y[1]<w and g[y[0]][y[1]]==0 and y not in seen:
                        seen.add(y);stack.append(y)
            comps.append(cells)
    return comps

def diag_contact(comps):
    return any(any(abs(a[0]-b[0])==1 and abs(a[1]-b[1])==1 for a in A for b in B)
               for i,A in enumerate(comps) for B in comps[i+1:])

b=load('bb75d495c809')
canon_b=[]
for i,pair in enumerate(rows['bb75d495c809']['train']+rows['bb75d495c809'].get('test',[])):
    g=pair['input']; sizes=Counter(map(len,comps0(g)))
    canon_b.append({'index':i,'self_check_errors':b.self_check(g),'histogram':dict(sorted(sizes.items())),
                    'diagonal_contact':diag_contact(comps0(g))})
ordinary_b={'samples':0,'self_check_failures':0,'missing_size_1_2_3':0,'big_samples':0,
            'diagonal_true':0,'dims':Counter(),'walls':Counter(),'pocket_counts':Counter()}
for band in ('easy','medium','hard'):
    for seed in range(128):
        g=b.generate(seed,0,difficulty=band); cs=comps0(g); sizes=[len(x) for x in cs]
        ordinary_b['samples']+=1
        ordinary_b['self_check_failures']+=bool(b.self_check(g))
        ordinary_b['missing_size_1_2_3']+=not all(s in sizes for s in (1,2,3))
        ordinary_b['big_samples']+=any(s>=4 for s in sizes)
        ordinary_b['diagonal_true']+=diag_contact(cs)
        ordinary_b['dims'][f'{len(g)}x{len(g[0])}']+=1
        ordinary_b['walls'][str(next(v for row in g for v in row if v))]+=1
        ordinary_b['pocket_counts'][str(len(cs))]+=1
for k in ('dims','walls','pocket_counts'): ordinary_b[k]=dict(sorted(ordinary_b[k].items()))
exact={'big_true':{'ok':0,'fail':[]},'diag_false':{'ok':0,'fail':[]},'diag_true':{'ok':0,'fail':[]}}
for seed in range(32):
    for label,kwargs in [('big_true',{'big_pockets':True,'n_pockets':10}),
                         ('diag_false',{'diagonal_contact':False,'n_pockets':8}),
                         ('diag_true',{'diagonal_contact':True,'n_pockets':8})]:
        try:
            g=b.generate(seed,0,difficulty='medium',**kwargs); obs=b.observe_overrides(g)
            good=(obs['big_pockets'] is True and obs['n_pockets']==10) if label=='big_true' else \
                 (obs['diagonal_contact'] is (label=='diag_true') and obs['n_pockets']==8)
            if good: exact[label]['ok']+=1
            else: exact[label]['fail'].append({'seed':seed,'observed':obs})
        except Exception as e:
            exact[label]['fail'].append({'seed':seed,'error':f'{type(e).__name__}: {e}'})
api={}
for kwargs in ({'bogus':1},{'difficulty':'extreme'}):
    label='unknown_override' if 'bogus' in kwargs else 'unknown_difficulty'
    try:
        g=b.generate(1,0,**kwargs); api[label]={'status':'accepted','dims':[len(g),len(g[0])]}
    except Exception as e: api[label]={'status':'error','type':type(e).__name__,'message':str(e)}
reportb={'canonical':canon_b,'ordinary':ordinary_b,'exact_override_probes':exact,'api_probes':api}

out={'641f580d5310':report641,'bb75d495c809':reportb}
Path('/mnt/data/arc_review_20261002_153658/checks/audit-probes.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
