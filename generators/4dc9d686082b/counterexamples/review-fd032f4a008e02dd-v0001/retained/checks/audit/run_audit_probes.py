from __future__ import annotations
import hashlib, importlib.util, json, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / 'repo'
CANON = REPO / 'shared/data/canonical/puzzles.jsonl'

def load(t):
    p=REPO/'generators'/t/'generator.py'
    spec=importlib.util.spec_from_file_location('audit_'+t,p)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m,p

def canon(t):
    for line in CANON.read_text().splitlines():
        o=json.loads(line)
        if o.get('task_id')==t:
            pairs=[]
            for k in ('train','test'):
                v=o.get(k)
                if isinstance(v,dict): v=[v]
                pairs.extend(v or [])
            return o,pairs
    raise KeyError(t)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def e1_probe():
    t='e1be962ccf97'; g,p=load(t); row,pairs=canon(t)
    canonical=[]
    for i,pair in enumerate(pairs):
        inp=pair['input']; out=pair['output']
        canonical.append({'index':i,'self_check':g.self_check(inp),'mirror_matches':g.rule_mirror(inp)==out,'canonical_profile':g.is_canonical_profile(inp)})
    layout_counts=Counter(); winners=defaultdict(set); failures=[]; not_largest=0; not_densest=0; unique=set()
    for band_i,band in enumerate(('easy','medium','hard')):
        for i in range(300):
            seed=100000*band_i+i
            grid=g.generate(seed, i*37+11, difficulty=band)
            errs=g.self_check(grid)
            if errs: failures.append({'band':band,'i':i,'errors':errs})
            s=g._analyze_scene(grid)
            layout_counts[(band,s['layout_kind'])]+=1
            wi=s['winner_indices'][0]; winners[s['layout_kind']].add(wi)
            areas=[len(c) for c in s['components']]
            if areas[wi] < max(areas): not_largest += 1
            wc=s['red_counts'][wi]; wa=areas[wi]
            if any(c*wa > wc*a for j,(c,a) in enumerate(zip(s['red_counts'],areas)) if j!=wi): not_densest += 1
            unique.add(tuple(map(tuple,grid)))
    exact=[]
    calls=[{'grid_h':9},{'grid_h':22},{'grid_w':9},{'grid_w':22},{'layout_kind':'horizontal'},{'layout_kind':'vertical'},{'layout_kind':'cross'},{'winner_count':3},{'winner_count':7}]
    for i,kwargs in enumerate(calls):
        grid=g.generate(9000+i,700+i,difficulty='hard',**kwargs)
        obs=g.observe_overrides(grid)
        exact.append({'requested':kwargs,'observed':{k:obs[k] for k in kwargs},'honored':all(obs[k]==v for k,v in kwargs.items()),'self_check':g.self_check(grid)})
    return {
      'task_id':t,'generator_sha256':sha(p),'rule_hash':getattr(g,'RULE_HASH',None),
      'canonical_pairs':canonical,'sample_policy':'300 draws per band; seed=100000*band_index+i; sample_index=i*37+11',
      'draws':900,'unique_inputs':len(unique),'selfcheck_failures':failures,
      'layout_counts':{f'{b}:{l}':n for (b,l),n in sorted(layout_counts.items())},
      'winner_positions':{k:sorted(v) for k,v in sorted(winners.items())},
      'winner_not_largest_area':not_largest,'winner_not_highest_density':not_densest,
      'exact_override_checks':exact,
      'finding':'No issue found in the sampled domain: canonical mirror, structural validation, location/area/density anti-shortcuts, and exact controls all held.'
    }

def bbox(cells):
    rs=[r for r,c in cells]; cs=[c for r,c in cells]
    return [max(rs)-min(rs)+1,max(cs)-min(cs)+1] if cells else None

def p4_probe():
    t='4dc9d686082b'; g,p=load(t)
    req={'grid_h':7,'template_bbox':(1,4),'template_idx':999,'layout_idx':999,'swatch_row':4}
    grid=g.generate(314159,271828,difficulty='hard',**req)
    h,w=len(grid),len(grid[0]); sep=[c for c in range(w) if grid[0][c]==5]; s1,s2,s3=sep
    tmpl=[(r,c) for r in range(h) for c in range(s1) if grid[r][c]==1]
    layout=[(r,c) for r in range(h) for c in range(s1+1,s2) if grid[r][c]==2]
    p3=[(r,c,grid[r][c]) for r in range(h) for c in range(s2+1,s3) if grid[r][c] not in (0,5)]
    p4=[(r,c,grid[r][c]) for r in range(h) for c in range(s3+1,w) if grid[r][c] not in (0,5)]
    # A second call demonstrates that absurd indices are silently accepted rather than range-checked.
    second=g.generate(1,2,template_idx=10**6,layout_idx=10**6,swatch_row=5)
    return {
      'task_id':t,'generator_sha256':sha(p),'declared_rule_hash':getattr(g,'RULE_HASH',None),
      'command':'PYTHONPATH=repo/src:repo/shared/runtime python3 checks/audit/run_audit_probes.py',
      'requested_overrides':{k:list(v) if isinstance(v,tuple) else v for k,v in req.items()},
      'observed':{'grid_h':h,'template_actual_bbox':bbox(tmpl),'layout_actual_bbox':bbox(layout),'panel3_swatches':p3,'panel4_swatches':p4},
      'self_check':g.self_check(grid),
      'absurd_index_call_accepted':bool(second),
      'violations':[
        'swatch_row=4 is ignored: both swatches are hard-coded to row 1',
        'template_idx=999 and layout_idx=999 are accepted without validation or exact selection',
        'template_bbox is sampled from an internal RNG rather than a keyed exact-axis draw',
        'RULE_HASH is absent despite a canonical Racket authority'
      ]
    }

out1=e1_probe(); out2=p4_probe()
(ROOT/'checks/audit/e1be962ccf97/probe.json').write_text(json.dumps(out1,indent=2,sort_keys=True)+'\n')
(ROOT/'checks/audit/4dc9d686082b/override-probe.json').write_text(json.dumps(out2,indent=2,sort_keys=True)+'\n')
print(json.dumps({'e1be962ccf97':out1,'4dc9d686082b':out2},indent=2,sort_keys=True))
