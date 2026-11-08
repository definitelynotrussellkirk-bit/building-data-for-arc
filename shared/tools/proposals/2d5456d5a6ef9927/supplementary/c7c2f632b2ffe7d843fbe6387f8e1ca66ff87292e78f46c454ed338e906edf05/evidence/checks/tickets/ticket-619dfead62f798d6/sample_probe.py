from pathlib import Path
import ast,collections,hashlib,json,random,time
w=Path.cwd()
d=w/'checks/tickets/ticket-619dfead62f798d6'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((w/'PACKET-MANIFEST.json').read_text())
seed='d1fda9427a1b327681512803c271e4853d06cd394b2d5a738eb31a7dbf5d0643'
anchor='7e6a7bb1fcfc'
cohort=sorted(set(m['generators'])-{anchor})
ids=[anchor]+random.Random(int(seed,16)).sample(cohort,2)
rows=[json.loads(l) for l in (w/'repo/catalog/puzzles.jsonl').read_text().splitlines() if l.strip()]
lookup={r['id']:r for r in rows}
canonical={i:[] for i in ids}
for line in (w/'repo/shared/data/canonical/puzzles.jsonl').read_text().splitlines():
 if not any(i in line for i in ids): continue
 r=json.loads(line)
 if r.get('task_id') in canonical:canonical[r['task_id']].append(r)
result={'scope':'Static source/receipt probe only; no generation, Racket execution, models, batteries, or census','sampling':{'seed':seed,'method':'fixed pinned anchor then random.Random(int(seed,16)).sample(sorted(manifest.generators IDs excluding anchor),2)','cohort_count':len(cohort)+1,'cohort_sha256':hashlib.sha256(('\n'.join(sorted(m['generators']))+'\n').encode()).hexdigest(),'sampled_ids':ids,'selection_bias':'Anchor fixed; remaining two uniform without replacement from packet generator identities, not representative of training mixtures or normal main draws'},'input_identities':{str(p.relative_to(w)):sha(p) for p in [w/'PACKET-MANIFEST.json',w/'repo/catalog/puzzles.jsonl',w/'repo/shared/data/canonical/puzzles.jsonl',w/'TRAINING-CONTEXT.md']},'pool':{'packet_generator_count':len(m['generators']),'normal_main_count':len(m['main_draw_policy']['normal_ids']),'main_ids_count':len(m['main_ids']),'focus':{k:v for k,v in m['main_draw_policy']['evaluation_focus'].items() if k not in ('anchors','provided_tasks')},'provided_focus_anchor_count':len(m['main_draw_policy']['evaluation_focus']['anchors']),'selection_policy':m['selection']['policy'],'selection_quotas':m['selection']['quotas'],'metadata_weight_histogram':dict(collections.Counter(str(r.get('mix_weight')) for r in rows))},'records':[]}
for i in ids:
 p=w/'repo/generators'/i/'generator.py';s=p.read_text();t=ast.parse(s); assignments={}
 for n in t.body:
  if isinstance(n,ast.Assign):
   for name in n.targets:
    if isinstance(name,ast.Name) and name.id in ('AXES','EXAMPLES_NEEDED','RULE_HASH','VERSION','SCENE_SPECS','EXPECTED_OUTPUT_CODOMAIN','MIN_STRICT_FRAC'):
     try:assignments[name.id]=ast.literal_eval(n.value)
     except (ValueError,TypeError):pass
 canonical_meta=[]
 for r in canonical[i]:
  pairs=r.get('train',[])+r.get('test',[])
  shapes=[{k:[len(pair[k]),len(pair[k][0])] for k in ('input','output') if k in pair} for pair in pairs]
  rule_hash=hashlib.sha256(' '.join(r['program_solution'].split()).encode()).hexdigest()[:12]
  canonical_meta.append({'task_id':i,'source':r.get('source'),'train_count':len(r.get('train',[])),'test_count':len(r.get('test',[])),'rule_hash':rule_hash,'pair_shapes':shapes})
 evidence_files={str(q.relative_to(w)):sha(q) for q in (p.parent/'evidence').rglob('*') if q.is_file()}
 for q in [p.parent/'notes.md',*list((p.parent/'tests').glob('*.py'))]:evidence_files[str(q.relative_to(w))]=sha(q)
 receipt=lookup[i].get('approval_receipt')
 if receipt:
  q=w/'repo'/receipt;evidence_files[str(q.relative_to(w))]=sha(q)
 observed=sha(p);pinned=m['generators'][i]
 result['records'].append({'task_id':i,'source_sha256':observed,'manifest':pinned,'matches_manifest_generator':observed==pinned['generator_sha256'],'matches_reviewed_generator':observed==lookup[i].get('reviewed_generator_sha256'),'matches_manifest_rule':all(r['rule_hash']==pinned['rule_hash'] for r in canonical_meta),'catalog':lookup[i],'in_normal_main_pool':i in m['main_draw_policy']['normal_ids'],'packet_selection_reason':m['selection']['reasons'].get(i),'declarations':assignments,'declares_lesson_identifiable':any(isinstance(n,ast.FunctionDef) and n.name=='lesson_identifiable' for n in t.body),'canonical':canonical_meta,'evidence_file_sha256':evidence_files})
(d/'inspection.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'sampled_ids':ids,'identities_match':all(r['matches_manifest_generator'] and r['matches_manifest_rule'] and r['matches_reviewed_generator'] for r in result['records']),'normal_pool_membership':[r['in_normal_main_pool'] for r in result['records']],'weight_histogram':result['pool']['metadata_weight_histogram'],'output':'checks/tickets/ticket-619dfead62f798d6/inspection.json'}))
