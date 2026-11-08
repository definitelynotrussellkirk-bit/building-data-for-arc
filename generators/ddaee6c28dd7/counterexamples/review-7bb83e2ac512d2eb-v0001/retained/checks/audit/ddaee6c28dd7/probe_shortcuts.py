#!/usr/bin/env python3
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
from reviewer_support import find_root, load_selected_generator, canonical_pairs

TASK='ddaee6c28dd7'
root=find_root(__file__)
gen,path,sha=load_selected_generator(TASK, root=root)

def render(comp):
    r1,c1,r2,c2=comp['bbox']; cells=set(comp['cells'])
    return [[8 if (r,c) in cells else 0 for c in range(c1,c2+1)] for r in range(r1,r2+1)]

def choose(grid,name):
    a=gen._analyze(grid)
    comps=a['components']
    keys={
      'largest_area': lambda x:(len(x['cells']),),
      'largest_bbox_area': lambda x:((x['bbox'][2]-x['bbox'][0]+1)*(x['bbox'][3]-x['bbox'][1]+1),),
      'tallest': lambda x:(x['bbox'][2]-x['bbox'][0]+1,),
      'rightmost': lambda x:(x['bbox'][3],),
      'leftmost': lambda x:(-x['bbox'][1],),
      'bottommost': lambda x:(x['bbox'][2],),
      'topmost': lambda x:(-x['bbox'][0],),
      'highest_color': lambda x:(x['color'],),
      'lowest_color': lambda x:(-x['color'],),
    }
    # deterministic row-major tie break: _analyze component order, first maximum.
    key=keys[name]
    best=max(range(len(comps)), key=lambda i:(key(comps[i]), -i))
    return render(comps[best])

names=['largest_area','largest_bbox_area','tallest','rightmost','leftmost','bottommost','topmost','highest_color','lowest_color']
canonical={n:[] for n in names}
for pair in canonical_pairs(TASK,root=root):
    expected=pair['output']
    for n in names: canonical[n].append(choose(pair['input'],n)==expected)

findings=[]
counts=defaultdict(int)
for band in ('easy','medium','hard'):
  for seed in range(300):
    pairs=[]
    for i in range(4):
      g=gen.generate(seed,i,difficulty=band)
      pairs.append({'input':g,'output':gen.rule_mirror(g),'signature':gen.semantic_signature(g)})
    for n in names:
      match=[choose(p['input'],n)==p['output'] for p in pairs]
      if all(match[:3]) and not match[3]:
        counts[(band,n)]+=1
        if len([f for f in findings if f['band']==band and f['rival']==n])<2:
          findings.append({'band':band,'seed':seed,'rival':n,'match':match,'pairs':pairs})

report={'task_id':TASK,'generator_path':str(path.relative_to(root)),'generator_sha256':sha,
        'seeds':'0..299','indices':[0,1,2,3],'canonical_match_vectors':canonical,
        'ambiguous_episode_counts':{f'{b}:{n}':v for (b,n),v in sorted(counts.items())},
        'first_findings':findings}
Path(__file__).with_name('probe-report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'sha':sha,'canonical':canonical,'counts':report['ambiguous_episode_counts'],
                  'finding_summaries':[(f['band'],f['seed'],f['rival'],f['match']) for f in findings]},indent=2))
