#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, random, sys, time
from pathlib import Path

ROOT=Path(sys.argv[1]).resolve(); OUT=Path(sys.argv[2]).resolve()
sys.path.insert(0,str(ROOT/'shared/runtime'))
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TICKET_SEED='ab254bb0dbff1a3df623a1535e376da1ce632464c2453d5ab76cf4f95bfb6a13'
TARGET='22ee9e5c3a9a'
PINNED_GENERATOR='191de079ed80d9c2c7727fe6278a94db439713c304bf5f64595127909d580d82'
PINNED_RULE='57d7715bb63d'

def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def load_jsonl(path,key):
    out={}
    for line in path.open():
        if line.strip():
            row=json.loads(line); value=row.get(key)
            if value: out[value]=row
    return out

def weighted_without_replacement(rows,n,rng):
    pool=[(r,float(r.get('recommended_mix_weight') or 0.0)) for r in rows]
    chosen=[]
    for _ in range(min(n,len(pool))):
        total=sum(w for _,w in pool); x=rng.random()*total; acc=0.0
        for i,(row,w) in enumerate(pool):
            acc+=w
            if x <= acc:
                chosen.append(row); pool.pop(i); break
    return chosen

def load_module(tid):
    path=ROOT/'generators'/tid/'generator.py'
    spec=importlib.util.spec_from_file_location(f'_ticket_{tid}',path)
    mod=importlib.util.module_from_spec(spec); assert spec and spec.loader
    sys.modules[spec.name]=mod; spec.loader.exec_module(mod); return mod

def grid_literal(g):
    return "'("+' '.join('('+' '.join(map(str,row))+')' for row in g)+')'
def grid_hash(g):
    return hashlib.sha256(json.dumps(g,separators=(',',':')).encode()).hexdigest()
def palette(g): return sorted({v for row in g for v in row})

def probe_task(tid, canonical, assignment, catalog, weights, bridge, seed_base):
    mod=load_module(tid); rule=canonical[tid]['program_solution']; callable_src=wrap_rule(rule)
    rows=[]; errors=[]
    for i in range(7):
        try:
            g=mod.generate(seed_base+i,i,difficulty=None)
            sc=list(mod.self_check(g,difficulty=None,meta=None)) if callable(getattr(mod,'self_check',None)) else []
            out=bridge.eval_text(f'({callable_src} {grid_literal(g)})')
            rows.append({'index':i,'role':'demo' if i<3 else 'query','input_sha256':grid_hash(g),
                         'output_sha256':grid_hash(out),'shape':[len(g),len(g[0])],
                         'output_shape':[len(out),len(out[0])], 'palette':palette(g),
                         'self_check_errors':sc,'changed_cells':sum(a!=b for ra,rb in zip(g,out) for a,b in zip(ra,rb))})
        except Exception as exc:
            errors.append({'index':i,'error':f'{type(exc).__name__}: {exc}'})
    inputs=[r['input_sha256'] for r in rows]; outputs=[r['output_sha256'] for r in rows]
    a=assignment.get(tid,{}); c=catalog.get(tid,{})
    task_dir=ROOT/'generators'/tid
    return {
      'task_id':tid,'generator_sha256':sha(task_dir/'generator.py'),
      'train_safety':a.get('train_safety',c.get('train_safety')),
      'assignment_status':a.get('status'),'monitor_gate_status':a.get('monitor_gate_status'),
      'findings':a.get('findings',[]),'recommended_mix_weight':a.get('recommended_mix_weight'),
      'catalog_mix_weight':c.get('mix_weight'),'legacy_generator_weight':weights.get(tid),
      'review_status':c.get('review_status'),'reviewed_rule_hash':c.get('reviewed_rule_hash'),
      'tests_count':len(list((task_dir/'tests').glob('test_*.py'))) if (task_dir/'tests').is_dir() else 0,
      'evidence_file_count':len([p for p in (task_dir/'evidence').rglob('*') if p.is_file()]) if (task_dir/'evidence').is_dir() else 0,
      'parametric_manifest_present':(task_dir/'workspace/parametric/evidence/manifest.json').is_file(),
      'materialization':{'requested_pairs':7,'successful_pairs':len(rows),'errors':errors,
          'self_check_clean_pairs':sum(not r['self_check_errors'] for r in rows),
          'unique_inputs':len(set(inputs)),'unique_outputs':len(set(outputs)),
          'exact_pair_duplicates':len(rows)-len(set(zip(inputs,outputs))),
          'queries':sum(r['role']=='query' for r in rows),
          'distinct_queries':len({r['input_sha256'] for r in rows if r['role']=='query'}),
          'max_input_side':max((max(r['shape']) for r in rows),default=None),
          'large_side_at_least_20':sum(max(r['shape'])>=20 for r in rows),
          'changed_pairs':sum(r['changed_cells']>0 for r in rows)},
      'pairs':rows,
    }

started=time.perf_counter()
assignment=load_jsonl(ROOT/'shared/data/derived/kimi_generator_assignment.jsonl','task_id')
catalog=load_jsonl(ROOT/'catalog/puzzles.jsonl','id')
canonical=load_jsonl(ROOT/'shared/data/canonical/puzzles.jsonl','task_id')
weights=json.loads((ROOT/'shared/data/derived/generator_weights.json').read_text())
blacklist={x.strip() for x in (ROOT/'shared/data/derived/generator_blacklist.txt').read_text().splitlines() if x.strip() and not x.startswith('#')}
# Source-layout equivalent of build_safe_pool.py: packet generators/ maps to runtime per_puzzle/.
eligible=[]; drops=[]
for tid,row in sorted(assignment.items()):
    if row.get('train_safety')!='reviewed_safe' or row.get('active_semantic_veto'):
        continue
    w=float(row.get('recommended_mix_weight') or 0.0)
    if w<=0: continue
    if not (ROOT/'generators'/tid/'generator.py').is_file(): drops.append({'task_id':tid,'reason':'no generator'}); continue
    if tid not in canonical or not (canonical[tid].get('program_solution') or '').strip(): drops.append({'task_id':tid,'reason':'no canonical rule'}); continue
    eligible.append(row)
rng=random.Random(int(TICKET_SEED,16))
sampled=weighted_without_replacement(eligible,3,rng)
seed_base=int(TICKET_SEED[:12],16)%1_000_000_000
bridge=RacketBridge(max_calls_before_restart=48)
try:
    focal=probe_task(TARGET,canonical,assignment,catalog,weights,bridge,seed_base)
    controls=[probe_task(r['task_id'],canonical,assignment,catalog,weights,bridge,seed_base+10000*(i+1)) for i,r in enumerate(sampled)]
    # Explicit production-override boundary on the focal task.
    mod=load_module(TARGET)
    override_checks=[]
    for value in (18,20):
        try:
            g=mod.generate(seed_base,99,difficulty='hard',grid_h=value,grid_w=value,n_lines=8)
            override_checks.append({'grid_side':value,'accepted':True,'actual_shape':[len(g),len(g[0])],
                                    'self_check_errors':list(mod.self_check(g,difficulty='hard',meta=None))})
        except Exception as exc:
            override_checks.append({'grid_side':value,'accepted':False,'error':f'{type(exc).__name__}: {exc}'})
finally:
    bridge.shutdown()
base=ROOT/'shared/data/base/solutions/banks/0d41ded5f4cd/E86__22ee9e5c3a9a.json'
base_row=json.loads(base.read_text()); rt=base_row['racket_target']; canon_rule=canonical[TARGET]['program_solution']
report={
 'schema':'allocation-quality-ticket-probe-v1','ticket_id':'ticket-684825f5c790f7f2','task_id':TARGET,
 'ticket_seed':TICKET_SEED,'sample_method':'weighted without replacement from current tier-1 reviewed_safe pool using recommended_mix_weight',
 'identity':{'generator_expected':PINNED_GENERATOR,'generator_actual':sha(ROOT/'generators'/TARGET/'generator.py'),
             'rule_hash_expected':PINNED_RULE,'catalog_rule_hash':catalog[TARGET].get('reviewed_rule_hash'),
             'assignment_rule_hash_expected':assignment[TARGET].get('rule_hash_expected')},
 'pool':{'tier1_eligible_tasks':len(eligible),'total_recommended_weight':sum(float(r.get('recommended_mix_weight') or 0) for r in eligible),
         'dropped_after_safety_filter':drops,'target_in_tier1_pool':any(r['task_id']==TARGET for r in eligible),
         'target_exclusion':{'train_safety':assignment[TARGET].get('train_safety'),'active_semantic_veto':assignment[TARGET].get('active_semantic_veto')},
         'target_legacy_generator_weight':weights.get(TARGET),'target_blacklisted_in_legacy_stream':TARGET in blacklist},
 'authority':{'canonical_equals_base_raw_code':canon_rule==rt.get('raw_code'),
              'canonical_equals_base_target_code':canon_rule==rt.get('target_code'),
              'base_target_diff_is_comment_only':canon_rule.replace('\n',' ').split()==rt.get('target_code','').replace('\n',' ').split(),
              'assignment_findings':assignment[TARGET].get('findings',[])},
 'sampled_control_ids':[r['task_id'] for r in sampled], 'focal':focal,'controls':controls,
 'override_boundary':override_checks,
 'training_context':{'snapshot_date':'2026-10-23T11:10-11:17Z','reported_arc_puzzles_items_share':0.47,
                     'reported_arc_puzzles_tokens_share':0.37,'reported_arc_gen_tokens_share':0.16,
                     'reported_re_arc_tokens_share':0.11,'reported_large_side_arc_puzzles':0.073,
                     'reported_large_side_public_eval':0.47},
 'coverage_gaps':['No source-specific ARC-GEN or RE-ARC linter/rejection/repair/ambiguity/grammar receipts are present in this packet; only aggregate token shares are available.',
                  'Seven-pair materialization checks execution, self-checks, exact duplicates and four distinct query inputs; it is not a semantic-identifiability or model-quality experiment.'],
 'elapsed_seconds':round(time.perf_counter()-started,6),
}
assert report['identity']['generator_actual']==PINNED_GENERATOR
assert report['identity']['catalog_rule_hash']==PINNED_RULE==report['identity']['assignment_rule_hash_expected']
assert not report['pool']['target_in_tier1_pool']
assert focal['materialization']['successful_pairs']==7
OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps({'status':'completed','sampled_control_ids':report['sampled_control_ids'],
                  'tier1_pool':report['pool']['tier1_eligible_tasks'],
                  'target_in_pool':False,'target_pairs':focal['materialization']['successful_pairs'],
                  'override_boundary':override_checks},sort_keys=True))
