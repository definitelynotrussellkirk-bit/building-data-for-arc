#!/usr/bin/env python3
import hashlib, json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
episode_path = Path(__file__).with_name('episode.jsonl')
episode = json.loads(episode_path.read_text().splitlines()[0])

def straight_row(grid):
    out = [row[:] for row in grid]
    red = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 2]
    green = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 3]
    if len(red) != 1 or len(green) != 1 or red[0][0] != green[0][0]:
        return out
    r = red[0][0]
    a,b = sorted((red[0][1], green[0][1]))
    for c in range(a+1,b):
        out[r][c] = 8
    return out

pairs=[]
for split in ('train','test'):
    for i,pair in enumerate(episode[split]):
        rival=straight_row(pair['input'])
        pairs.append({
            'split':split,'pair_index':i,
            'sample_index': episode['sample_indices'][i if split=='train' else len(episode['train'])+i],
            'self_check_recorded': None,
            'rival_matches_authority': rival == pair['output'],
            'input':pair['input'],'authority_output':pair['output'],'rival_output':rival,
        })
source=(root/'repo/generators/d3ae93aa8d37/generator.py').read_bytes()
result={
 'schema':'arcpuzzles-audit-counterexample-v1',
 'task_id':'d3ae93aa8d37',
 'finding':'four-demo lesson and held-out query fail to distinguish straight-row painting from BFS obstacle avoidance',
 'generator_sha256':hashlib.sha256(source).hexdigest(),
 'executed_rule_hash':episode['executed_rule_hash'],
 'command':'python3 run_with_racket.py python3 -m arcpuzzles generate d3ae93aa8d37 --count 1 --seed 8 --sample-index 0 --difficulty easy --train 4 --test 1 --allow-unapproved --out ../checks/audit/d3ae93aa8d37/episode.jsonl',
 'cwd':str(root),
 'seed':8,'sample_index':0,'difficulty':'easy','train_count':4,'test_count':1,
 'all_train_match':all(x['rival_matches_authority'] for x in pairs if x['split']=='train'),
 'query_matches':all(x['rival_matches_authority'] for x in pairs if x['split']=='test'),
 'pairs':pairs,
 'limitation':'This single deterministic lesson reproduces an ambiguity; it is not a frequency estimate.'
}
Path(__file__).with_name('evidence.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('generator_sha256','executed_rule_hash','all_train_match','query_matches')},indent=2))
