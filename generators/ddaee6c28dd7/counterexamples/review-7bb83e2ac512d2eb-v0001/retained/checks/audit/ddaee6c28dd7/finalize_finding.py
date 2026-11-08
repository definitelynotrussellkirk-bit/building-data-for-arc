#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator, canonical_pairs

TASK='ddaee6c28dd7'; BAND='easy'; SEED=145; INDICES=(0,1,2,3)
root=find_root(__file__)
gen,path,sha=load_selected_generator(TASK,root=root)

def render(comp):
 r1,c1,r2,c2=comp['bbox']; cells=set(comp['cells'])
 return [[8 if (r,c) in cells else 0 for c in range(c1,c2+1)] for r in range(r1,r2+1)]
def lowest_color(grid):
 a=gen._analyze(grid); comp=min(a['components'],key=lambda c:c['color'])
 return render(comp)

def grid_hash(grid):
 return hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest()

pairs=[]
for i in INDICES:
 grid=gen.generate(SEED,i,difficulty=BAND)
 intended=gen.rule_mirror(grid); rival=lowest_color(grid)
 pairs.append({'sample_index':i,'difficulty':BAND,'input':grid,'input_sha256':grid_hash(grid),
               'self_check':gen.self_check(grid),'signature':gen.semantic_signature(grid),
               'intended_output':intended,'rival_output':rival,'rival_matches':rival==intended})
canonical=[]
for pair in canonical_pairs(TASK,root=root):
 rival=lowest_color(pair['input'])
 canonical.append({'input_sha256':grid_hash(pair['input']),
                   'rival_matches':rival==pair['output']})
report={
 'task_id':TASK,'generator_path':str(path.relative_to(root)),'generator_sha256':sha,
 'generator_version':gen.VERSION,'rule_hash':gen.RULE_HASH,
 'rival':'select the component with the numerically lowest input color, crop its exact mask, recolor to 8',
 'canonical_match_vector':[row['rival_matches'] for row in canonical],
 'episode':{'seed':SEED,'difficulty':BAND,'sample_indices':list(INDICES),
            'demo_indices':[0,1,2],'query_index':3,
            'match_vector':[p['rival_matches'] for p in pairs], 'pairs':pairs},
 'measured_probe':{'script':'probe_shortcuts.py','seeds':'0..299','sample_indices':[0,1,2,3],
                   'lesson_policy':'indices 0..2 demonstrations; index 3 query',
                   'ambiguous_episodes':{'easy':6,'medium':8,'hard':4},
                   'denominator_per_band':300,
                   'total_ambiguous':18,'total_episodes':900},
 'limitations':['Finite rival and seed scan only.','Probe labels used the source-bound Python mirror; retained four-grid Racket execution is stored separately.'],
}
here=Path(__file__).resolve().parent
(here/'input.json').write_text(json.dumps([p['input'] for p in pairs],indent=2)+'\n')
(here/'finding.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'generator_sha256':sha,'canonical_match_vector':report['canonical_match_vector'],
                  'episode_match_vector':report['episode']['match_vector'],
                  'winner_colors':[p['signature']['winner_color'] for p in pairs]},indent=2))
