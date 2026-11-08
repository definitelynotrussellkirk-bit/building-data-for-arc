"""Source-bound findings-only audit: minimum color-concentration shortcut."""
import copy
import itertools
import json
from collections import Counter
from pathlib import Path
from reviewer_support import load_selected_generator, canonical_pairs, canonical_path

TASK='47be86674731'
EXPECTED_SHA='dd6702444e5c653bc197cdd194a9bdd6bf56058c51754284aaf4e4ce2380cec6'
OUT=Path(__file__).resolve().parent
ROOT=Path.cwd()
g,source,digest=load_selected_generator(TASK,root=ROOT)
assert digest == EXPECTED_SHA, digest

def rival(grid):
    """Crop the block with minimum concentration, without counting its colors."""
    h,w=len(grid),len(grid[0]); seen=set(); blocks=[]
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r,c) in seen: continue
            todo=[(r,c)]; seen.add((r,c)); cells=[]
            while todo:
                a,b=todo.pop(); cells.append((a,b))
                for x,y in ((a-1,b),(a+1,b),(a,b-1),(a,b+1)):
                    if 0<=x<h and 0<=y<w and grid[x][y] and (x,y) not in seen:
                        seen.add((x,y)); todo.append((x,y))
            counts=Counter(grid[a][b] for a,b in cells)
            concentration=sum(n*n for n in counts.values())
            r0=min(a for a,b in cells); r1=max(a for a,b in cells)
            c0=min(b for a,b in cells); c1=max(b for a,b in cells)
            crop=[row[c0:c1+1] for row in grid[r0:r1+1]]
            blocks.append((concentration,r0,c0,crop))
    return min(blocks,key=lambda x:x[:3])[3]

counts={'generated':0,'generated_valid':0,'generated_rival_matches':0,'overrides':0,'overrides_valid':0,'overrides_observed_exact':0,'overrides_rival_matches':0,'canonical':0,'canonical_valid':0,'canonical_rival_matches':0}
for seed in range(100):
    for band in ('easy','medium','hard'):
        for index in range(4):
            grid=g.generate(seed,index,difficulty=band)
            counts['generated']+=1
            counts['generated_valid']+=not g.self_check(grid)
            counts['generated_rival_matches']+=rival(grid)==g.rule_mirror(grid)
for band,h,w,rank,mode,dist in itertools.product(('easy','medium','hard'),(12,18),(12,18),range(4),('nine_nonzero','eight_nonzero'),('balanced','mixed','skewed')):
    kw=dict(grid_h=h,grid_w=w,target_rank=rank,palette_mode=mode,target_distribution=dist)
    grid=g.generate(20261023,7,difficulty=band,**kw)
    counts['overrides']+=1
    counts['overrides_valid']+=not g.self_check(grid)
    counts['overrides_observed_exact']+=g.observe_overrides(grid)==kw
    counts['overrides_rival_matches']+=rival(grid)==g.rule_mirror(grid)
for pair in canonical_pairs(TASK,root=ROOT):
    counts['canonical']+=1
    counts['canonical_valid']+=not g.self_check(pair['input'])
    counts['canonical_rival_matches']+=rival(pair['input'])==pair['output']
kw=dict(grid_h=12,grid_w=12,target_rank=0,palette_mode='nine_nonzero',target_distribution='skewed')
original=g.generate(0,0,difficulty='medium',**kw)
f=g._analysis(original); b=f['blocks'][f['target_rank']]; r,c,_,_=b['bbox']; colors=b['colors']
witness=copy.deepcopy(original)
for k,value in enumerate([colors[0]]*7+[colors[1],colors[2]]): witness[r+k//3][c+k%3]=value
errors=g.self_check(witness)
official_mirror=g.rule_mirror(witness)
rival_output=rival(witness)
assert errors==[]
assert rival_output != official_mirror
facts=g._analysis(witness)
record={'task_id':TASK,'generator_sha256':digest,'kind':'supported-domain mutation of an emitted draw, not an emitted override combination','base_seed':0,'sample_index':0,'difficulty':'medium','overrides':kw,'mutation':'replace target row-major cells with seven of its first sorted color and one each of its other two colors','validator_errors':errors,'observables':g.semantic_observables(witness),'blocks':[{'bbox':x['bbox'],'color_counts':dict(x['counts']),'concentration':sum(v*v for v in x['counts'].values())} for x in facts['blocks']],'input':witness,'python_rule_mirror_output':official_mirror,'rival_output':rival_output}
demos=[{'input':(di:=g.generate(0,index,difficulty='medium')),'output':g.rule_mirror(di)} for index in range(3)]
lesson={'demo_seed':0,'demo_sample_indices':[0,1,2],'demo_difficulty':'medium','demo_overrides':{},'validator_reasons':g.lesson_identifiable(demos,{'input':witness,'output':official_mirror}),'rival_fits_all_demos':all(rival(d['input'])==d['output'] for d in demos),'rival_changes_query':rival_output!=official_mirror}
assert lesson['validator_reasons']==[] and lesson['rival_fits_all_demos'] and lesson['rival_changes_query']
record['lesson_witness']=lesson
(OUT/'input.json').write_text(json.dumps(witness)+'\n')
if (OUT/'racket.json').exists():
    receipt=json.loads((OUT/'racket.json').read_text())
    result=receipt['results'][0]
    assert receipt['generator_sha256']==digest
    assert receipt['rule_hash_matches_catalog'] and receipt['executed_rule_hash']==g.RULE_HASH
    assert result['input']==witness and result['output']==official_mirror
    assert result['valid_output'] and result['error'] is None
    assert result['output']!=rival_output
    record['racket_authority']={key:receipt[key] for key in ('executed_rule_hash','catalog_rule_hash','rule_text_sha256','generator_sha256')}
    record['racket_authority'].update({key:result[key] for key in ('input_sha256','output_sha256','output','valid_output','error')})
    record['racket_authority']['receipt']='racket.json'
(OUT/'witness.json').write_text(json.dumps(record,indent=2)+'\n')
(OUT/'original_generated_input.json').write_text(json.dumps(original)+'\n')
summary={'task_id':TASK,'generator_sha256':digest,'counts':counts,'default_census':{'seed_range_inclusive':[0,99],'sample_indices':[0,1,2,3],'difficulty':['easy','medium','hard'],'overrides':{}},'override_census':{'seed':20261023,'sample_index':7,'difficulty':['easy','medium','hard'],'grid_h':[12,18],'grid_w':[12,18],'target_rank':[0,1,2,3],'palette_mode':['nine_nonzero','eight_nonzero'],'target_distribution':['balanced','mixed','skewed']},'limit':'Census labels use the Python mirror; supported-domain witness additionally verified against exact Racket apply in racket.json.'}
(OUT/'census.json').write_text(json.dumps(summary,indent=2)+'\n')
for line in canonical_path(ROOT).read_text().splitlines():
    row=json.loads(line)
    if row.get('task_id')==TASK:
        (OUT/'selected_program.rkt').write_text(row['program_solution']+'\n')
print(json.dumps(summary,indent=2))
print('WITNESS',json.dumps(record,indent=2))
