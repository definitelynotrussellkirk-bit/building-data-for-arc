
from pathlib import Path
import hashlib,json
from reviewer_support import public_challenge_bytes, public_challenge_id
from arcpuzzles.parametric_priority import _prototype
root=Path.cwd().resolve();work=root.parent
c=json.loads((work/'ASSIGNMENT.json').read_text())
home=root/'generators'/c['task_id']; batch=home/'workspace/parametric/evidence/paired-batch-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
unchanged={}
for rel in ['repo/generators/ad4e576b99c4/generator.py','repo/shared/data/canonical/puzzles.jsonl','repo/shared/data/base/solutions/training/9f41bd9c__ad4e576b99c4.json']:
 unchanged[rel]=sha(work/rel)==c['baseline_sha256'][rel]
assert all(unchanged.values())
manifest=json.loads((batch/'private/manifest.json').read_text())
ids=manifest['public_ids']
assert len(ids)==3 and ids==sorted(ids) and len(set(ids))==3
episodes={}
for key in ids:
 public=(batch/'public'/f'{key}.json').read_bytes()
 private=json.loads((batch/'private/episodes'/f'{key}.json').read_text())
 assert hashlib.sha256(public).hexdigest()==key==public_challenge_id(private)
 assert public==public_challenge_bytes(private)
 visible=json.loads(public)
 assert set(visible)=={'train','test'}
 assert all(set(x)=={'input','output'} for x in visible['train'])
 assert all(set(x)=={'input'} for x in visible['test'])
 assert len(private['train'])==2 and len(private['test'])==4
 assert private['prototype_sha256']==sha(home/'workspace/parametric/prototype.py')
 assert private['generator_sha256']==c['generator']['generator_sha256']
 assert len(private['certificate']['candidates'])==14
 assert not any(private['certificate']['per_query_disagreements'])
 assert private['training_admitted'] is False
 setting=private['parameters']['shear_start_rows']
 assert manifest['setting_map'][key]==setting
 episodes[setting]=private
assert set(episodes)=={2,3,4}
inputs=[[pair['input'] for pair in episodes[k]['train']+episodes[k]['test']] for k in (2,3,4)]
assert inputs[0]==inputs[1]==inputs[2]
assert len({json.dumps(x) for x in inputs[0]})==6
distinct_queries=sum(len({json.dumps(episodes[k]['test'][i]['output']) for k in (2,3,4)})==3 for i in range(4))
assert distinct_queries==4
inventory=_prototype(root,{'id':c['task_id'],**c['generator']})
assert inventory['status']=='current' and inventory['variant_approved'] is False
result=dict(status='pass',unchanged_authorities=unchanged,prototype_inventory=inventory,
 public_payloads_verified=3,accepted_racket_labelled_pairs_retained=18,
 distinct_inputs_within_each_episode=6,paired_inputs_across_settings=True,
 queries_with_three_distinct_setting_outputs=distinct_queries,
 candidate_survivors={str(k):v['certificate']['survivors'] for k,v in episodes.items()},
 source_sha256=sha(home/'workspace/parametric/prototype.py'),
 scope='Read-only inspection of final retained export, exact byte identity, source hashes and inventory; no new Racket execution')
(work/'checks/parametric/final-export-inspection.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))

