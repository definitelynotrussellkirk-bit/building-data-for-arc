#!/usr/bin/env python3
"""Create an explicitly intentional post-assembly negative from real labeled episodes."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

p=argparse.ArgumentParser(description=__doc__);p.add_argument('episodes',type=Path);p.add_argument('--out',required=True,type=Path)
a=p.parse_args();home=Path(__file__).resolve().parents[1];sys.path.insert(0,str(home.parents[1]/'shared/runtime'))
spec=importlib.util.spec_from_file_location('stress_subject',home/'generator.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
episodes=[json.loads(line) for line in a.episodes.read_text().splitlines() if line.strip()]
canonical=[];queries=[];seen=set()
for ep in episodes:
    for pair in ep['train']+ep['test']:
        key=json.dumps(pair['input'])
        if key in seen:continue
        seen.add(key)
        (canonical if g.strict_canonical_like(pair['input'])==[] else queries).append(pair)
if len(canonical)<3 or len(queries)<2:raise ValueError('need three distinct interior pairs and two varied pairs')
result={'task_id':g.TASK_ID,'train':copy.deepcopy(canonical[:3]),'test':copy.deepcopy(queries[:2]),
        'provenance':copy.deepcopy(episodes[0]['provenance']),
        'review_stress_test':{'intent':'deliberate post-assembly negative, NOT a failed solve attempt',
            'source_episodes':str(a.episodes),'assembly':'Select only canonical-like interior demonstrations; retain varied queries.',
            'labels':'Unmodified Racket-derived labels from source episodes; seed/index episode lineage not asserted.'}}
with a.out.open('x') as f:f.write(json.dumps(result)+'\n')
print(a.out)
