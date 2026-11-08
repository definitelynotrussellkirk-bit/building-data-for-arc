"""One bounded, source-bound allocation inspection; no corpus/model job."""
from pathlib import Path
import collections, hashlib, importlib.util, json, os, signal, tempfile, time
from datetime import datetime, timezone
from arcpuzzles import Catalog

START = time.monotonic()
ROOT = Path.cwd()
WORK = ROOT.parent
OUT = WORK / 'checks/tickets/ticket-813a3bbb2f4572b2'
SEED = '5b8271e35324230b77c7398e068ff133fd0279afc7b6a2217cfd21548317a4ae'
ANCHOR = '2a43e4f3a796'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
tempfile.tempdir = str(OUT)
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('110-second total probe cap')))
signal.alarm(110)

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def content_hash(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(name, value): (OUT / name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
m = json.loads((WORK/'PACKET-MANIFEST.json').read_text())
rank = lambda tid: hashlib.sha256((SEED+':'+tid).encode()).hexdigest()
selected = [ANCHOR] + sorted((x for x in m['main_draw_policy']['ids'] if x != ANCHOR),key=rank)[:2]
cat = Catalog(ROOT)
raw_rows = [json.loads(line) for line in (ROOT/'catalog/puzzles.jsonl').read_text().splitlines()]
derived = {r['task_id']:r for r in map(json.loads,(ROOT/'shared/data/derived/generator_catalog.jsonl').read_text().splitlines())}
files = []
def record(path):
 p=WORK/path
 row={'path':path,'sha256':digest(p),'packet_sha256':m['files'].get(path)}
 row['matches_packet']=row['sha256']==row['packet_sha256'] if row['packet_sha256'] else None
 files.append(row); return row
for path in ['PACKET-MANIFEST.json','TICKETS.md','TRAINING-CONTEXT.md','repo/catalog/puzzles.jsonl','repo/shared/data/canonical/puzzles.jsonl','repo/shared/data/derived/generator_catalog.jsonl','repo/src/arcpuzzles/runtime.py','repo/shared/runtime/puzzle_generators/runner.py']:
 record(path)
inspect={'schema':'bounded-allocation-inspection-v1','observed_utc':datetime.now(timezone.utc).isoformat(),'seed':SEED,
 'sampling':{'method':'Pinned anchor plus the two lowest lexical SHA256(seed + colon + task_id) ranks among actual main_draw_policy.ids excluding anchor; no replacement. Anchor is purposive, other two are seeded. No claim of population prevalence.','population_size':len(m['main_draw_policy']['ids']),'selected_ids':selected,'ranks':{tid:rank(tid) for tid in selected}},
 'packet':{'main_distribution':m['main_draw_policy']['distribution'],'main_ids':len(m['main_draw_policy']['ids']),'manifest_approved_in_main':sum(m['generators'][x]['approved'] for x in m['main_draw_policy']['ids']),
 'priority_scope':m['main_draw_policy']['priority_scope'],'selection_policy':m['selection']['policy'],'quotas':m['selection']['quotas'],'owner_generator_count':m['selection']['owner_generator_count'],'reviewable_roots':m['selection']['reviewable_root_count'],
 'focus_probability':m['authoring_focus_policy']['probability'],'focus_anchors':len(m['authoring_focus_policy']['anchors']),'focus_tiers':dict(collections.Counter(a['selected_tier'] for a in m['authoring_focus_policy']['anchors'])),'focus_scope':m['authoring_focus_policy']['scope'],
 'parameter_priority_counts':m['parametric_priority']['counts'],'supplementary_weights':m['supplementary_ticket_policy']['weights'],'weight_basis':m['supplementary_ticket_policy']['weight_basis']},
 'catalog':{'rows':len(raw_rows),'mix_weight_counts':dict(collections.Counter(str(r['mix_weight']) for r in raw_rows)),'train_safety_counts':dict(collections.Counter(r['train_safety'] for r in raw_rows)),
 'source_family_memberships':dict(collections.Counter(s for r in raw_rows for s in set(x.split(':')[0] for x in r['sources']))),'weight_is_not_approval':True},
 'external_evidence':{'arc_gen_or_re_arc_path_matches':[x for x in m['files'] if any(s in x.lower() for s in ('arc-gen','arcgen','re-arc','rearc'))],'interpretation':'No named ARC-GEN/RE-ARC source-specific receipts in packet inventory: coverage gap, not a source quality ranking. Dated training snapshot is not a fresh source comparison.'},'records':[]}
mods={}
for tid in selected:
 row=cat.describe(tid)
 source=record('repo/'+row['generator'])
 spec=importlib.util.spec_from_file_location('allocation_'+tid,ROOT/row['generator']); mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mods[tid]=mod
 indexpath=f'repo/generators/{tid}/evidence/review_index.json';record(indexpath);idx=json.loads((WORK/indexpath).read_text())
 for n in ['notes.md','evidence/associated_notes.jsonl']:
  record(f'repo/generators/{tid}/{n}')
 d=derived.get(tid,{})
 inspect['records'].append({'task_id':tid,'selection_reason':m['selection']['reasons'].get(tid),
 'current':{k:row.get(k) for k in ['generator_sha256','rule_hash','rule_task_id','version','sources','summary','mix_weight','approved','approval_reasons','train_safety','approval_verification_status']},
 'matches_pinned_generator':source['sha256']==m['generators'][tid]['generator_sha256'],'matches_pinned_rule':row['rule_hash']==m['generators'][tid]['rule_hash'],
 'generator_declared_examples_needed':getattr(mod,'EXAMPLES_NEEDED',None),'declared_axes':getattr(mod,'AXES',{}),
 'derived_catalog_dated':{k:d.get(k) for k in ['cataloged_at','version','lint_status','diversity_score','combinatorial_reach','notes']},
 'derived_version_matches_current':d.get('version')==row['version'],
 'existing_audits':[{'source_sha256':a.get('source_sha256'),'matches_current':a.get('source_sha256')==source['sha256'],'resolution':a.get('resolution'),'verification_status':a.get('verification_status'),'text':a.get('text'),'assets_manifest':a.get('assets_manifest')} for a in idx.get('audits',[])]})
# Retain only aggregates of existing relevant evidence, with exact file hashes.
evidence = {}
paths = {
 'anchor_battery':'repo/shared/tools/proposals/d6e040dd30df29bf/checks/after-v31/checks/2a43e4f3a796_after_battery_summary.json',
 'anchor_lesson_census':'repo/generators/2a43e4f3a796/counterexamples/current-shortcut/checks/lesson-census-v31.json',
 'template_corner_probe':'repo/generators/1ea2cf5a712b/counterexamples/review-8f64e58294fb638f-v0001/retained/checks/audit/1ea2cf5a712b/corner_shortcut_probe.json',
 'template_semantic_gate':'repo/generators/1ea2cf5a712b/counterexamples/review-8f64e58294fb638f-v0001/retained/checks/audit/1ea2cf5a712b/semantic_gate/result.json',
 'template_distribution_gate':'repo/generators/1ea2cf5a712b/counterexamples/review-8f64e58294fb638f-v0001/retained/checks/audit/1ea2cf5a712b/dist_gate/result.json',
 'majority_witness':'repo/generators/1d14de95c43e/counterexamples/review-463a8c78e1056098-v0001/retained/checks/audit/1d14de95c43e/counterexample.json'}
for key,path in paths.items():
 record(path);v=json.loads((WORK/path).read_text())
 allowed=['schema','status','verdict','counts','generator_file_sha256','generator_sha256','source_sha256','rule_hash','summary','sampler','generated_utc','green_stages','failed_stages','source_hashes','results','conclusion','stage']
 evidence[key]={'path':path,'fields':{k:v[k] for k in allowed if k in v},'top_level_keys':list(v)}
 if key=='anchor_battery':evidence[key]['stage_duration_seconds']={k:s.get('duration_seconds') for k,s in v['stages'].items()}
inspect['retained_evidence']=evidence
inspect['files']=files
save('inspection.json',inspect)

report={'schema':'bounded-four-query-probe-v1','seed':SEED,'command':'PYTHONDONTWRITEBYTECODE=1 python3 review.py run --receipt checks/tickets/ticket-813a3bbb2f4572b2/command.json python3 -B ../checks/tickets/ticket-813a3bbb2f4572b2/probe.py',
 'limits':{'targeted_probes':1,'total_seconds_cap':110,'per_generation_seconds_cap':20,'default_records':3,'additional_anchor_size_episode':1,'model_jobs':0,'corpus_reruns':0},'episodes':[]}
try:
 for tid,setting,overrides in [(x,'default',{}) for x in selected]+[(ANCHOR,'research-size-24x18',{'grid_h':24,'grid_w':18})]:
  seed=int(hashlib.sha256((SEED+':episode:'+tid).encode()).hexdigest()[:8],16)
  t=time.monotonic();r={'task_id':tid,'setting':setting,'seed':seed,'sample_index':0,'difficulty':None,'requested_demos':4,'requested_queries':4,'overrides':overrides,'research_only':bool(overrides) or not cat.describe(tid)['approved']}
  try:
   ep=cat.generate(tid,count=1,seed=seed,sample_index=0,difficulty=None,n_train=4,n_test=4,overrides=overrides,allow_unapproved=True,timeout=20)[0]
   pairs=ep['train']+ep['test']; hashes=[content_hash(x['input']) for x in pairs]
   r.update(status='materialized',n_demos=len(ep['train']),n_queries=len(ep['test']),unique_inputs=len(set(hashes)),query_input_sha256=hashes[len(ep['train']):],query_output_sha256=[content_hash(x['output']) for x in ep['test']],episode_sha256=content_hash(ep),sampling=ep.get('sampling'),input_shapes=[[len(p['input']),len(p['input'][0])] for p in pairs],output_shapes=[[len(p['output']),len(p['output'][0])] for p in pairs],large_query_outputs=sum(max(len(p['output']),len(p['output'][0]))>=20 for p in ep['test']),label_authority='Catalog.generate canonical Racket',generator_sha256=cat.describe(tid)['generator_sha256'],rule_hash=cat.describe(tid)['rule_hash'])
   rivals=dict(getattr(mods[tid],'LESSON_COMPETITORS',{}))
   if tid=='1d14de95c43e':rivals['first_nonzero'] = lambda g:[[next((row[c] for row in g if row[c]),0) for c in range(len(g[0]))]]
   r['declared_rival_demo_refutations']={name:sum(fn(p['input'])!=p['output'] for p in ep['train']) for name,fn in rivals.items()}
   r['limits']='One exact episode only; named rival diagnostics are incomplete and materialization is not admission or universal teachability.'
  except Exception as exc:r.update(status='unknown',error=type(exc).__name__+': '+str(exc)[:900])
  r['elapsed_seconds']=round(time.monotonic()-t,6);report['episodes'].append(r);save('probe.json',report)
finally:
 report['elapsed_seconds']=round(time.monotonic()-START,6);save('probe.json',report);signal.alarm(0)
print(json.dumps({'selected_ids':selected,'elapsed_seconds':report['elapsed_seconds'],'episodes':[{k:r.get(k) for k in ['task_id','setting','status','n_demos','n_queries','unique_inputs','large_query_outputs','elapsed_seconds','error']} for r in report['episodes']]},indent=2))
