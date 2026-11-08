"""Bounded adversarial metric audit. Uses the target's public generate/self_check."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[3] / 'repo'
sys.path.insert(0, str(REPO / 'shared/runtime'))
OUT = Path(__file__).resolve().parent
TASK = 'e9cd770abc01'
gen_path = REPO / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audited_generator', gen_path)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
canon_path = REPO / 'shared/data/base/solutions/banks/b87bafc16aa7/S4_M1__e9cd770abc01.json'
canonical = json.loads(canon_path.read_text())
rule = canonical['racket_target']['target_code']

def components(grid):
    h,w=len(grid),len(grid[0]); seen=set(); result=[]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 3 or (r,c) in seen: continue
            todo=[(r,c)]; seen.add((r,c))
            for a,b in todo:
                for da,db in [(1,0),(-1,0),(0,1),(0,-1)]:
                    p=(a+da,b+db)
                    if 0<=p[0]<h and 0<=p[1]<w and grid[p[0]][p[1]]==3 and p not in seen:
                        seen.add(p); todo.append(p)
            result.append(sorted(todo))
    return result

def describe(grid):
    h,w=len(grid),len(grid[0]); rows=[]
    for comp in components(grid):
        r1=min(r for r,c in comp); c1=min(c for r,c in comp)
        r2=max(r for r,c in comp); c2=max(c for r,c in comp)
        dr=r1+r2-(h-1); dc=c1+c2-(w-1)
        rows.append({'bbox':[r1,c1,r2,c2], 'cells':comp,
                     'doubled_center_offset':[dr,dc],
                     'manhattan_times_2':abs(dr)+abs(dc),
                     'euclidean_squared_times_4':dr*dr+dc*dc})
    manhattan=min(range(len(rows)),key=lambda i:(rows[i]['manhattan_times_2'],rows[i]['bbox']))
    euclidean=min(range(len(rows)),key=lambda i:(rows[i]['euclidean_squared_times_4'],rows[i]['bbox']))
    intended=[row[:] for row in grid]; rival=[row[:] for row in grid]
    for r,c in rows[manhattan]['cells']: intended[r][c]=7
    for r,c in rows[euclidean]['cells']: rival[r][c]=7
    return {'objects':rows,'manhattan_winner':manhattan,'euclidean_winner':euclidean,
            'manhattan_unique':sum(row['manhattan_times_2']==rows[manhattan]['manhattan_times_2'] for row in rows)==1,
            'rivals_agree':manhattan==euclidean,
            'intended_output':intended,'euclidean_rival_output':rival}

canonical_checks=[]
for i,pair in enumerate(canonical['visible_context']['train']):
    d=describe(pair['input'])
    canonical_checks.append({'source':'canonical_train','index':i,'input':pair['input'],
                             'validator_result':gen.self_check(pair['input'],difficulty='medium'),
                             'intended_matches_canonical':d['intended_output']==pair['output'],
                             'rival_matches_canonical':d['euclidean_rival_output']==pair['output'],**d})
selected=None
for seed in range(100):
    samples=[]
    for i in range(3):
        g=gen.generate(seed,i,difficulty='medium')
        d=describe(g)
        samples.append({'source':'generator','seed':seed,'sample_index':i,'difficulty':'medium',
                        'overrides':{},'input':g,'validator_result':gen.self_check(g,difficulty='medium'),**d})
    if all(s['rivals_agree'] for s in samples[:2]) and not samples[2]['rivals_agree'] and samples[2]['manhattan_unique'] and all(not s['validator_result'] for s in samples):
        selected=samples; break
assert selected is not None
checks=canonical_checks+selected
normalized=' '.join(rule.split())
report={'task_id':TASK,'generator_sha256':hashlib.sha256(gen_path.read_bytes()).hexdigest(),
        'canonical_path':str(canon_path.relative_to(REPO)),
        'canonical_file_sha256':hashlib.sha256(canon_path.read_bytes()).hexdigest(),
        'normalized_rule_sha256':hashlib.sha256(normalized.encode()).hexdigest(),
        'catalog_rule_hash':hashlib.sha256(normalized.encode()).hexdigest()[:12],
        'canonical_written_rule':canonical['description_target']['target_text'],
        'canonical_target_code':rule,
        'selection_search':{'seeds_inclusive':[0,seed],'sample_indices':[0,1,2],
                            'purpose':'find two L1/L2-agreeing samples followed by a unique-L1 disagreement'},
        'cases':checks,
        'scope':'Raw public generator draws. This does not assert these are a production Catalog.generate lesson or estimate a population frequency.'}
(OUT/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'input.json').write_text(json.dumps({'inputs':[c['input'] for c in checks]},indent=2)+'\n')
print(json.dumps({'generator_sha256':report['generator_sha256'],'rule_hash':report['catalog_rule_hash'],
                  'selected_seed':seed,'cases':[{'source':s['source'],'index':s.get('sample_index',s.get('index')),
                  'validator_result':s['validator_result'],'rivals_agree':s['rivals_agree'],
                  'manhattan_winner':s['manhattan_winner'],'euclidean_winner':s['euclidean_winner']} for s in checks]},indent=2))
