from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT=Path.cwd()
GEN_PATH=ROOT/'generators/1238481b674b/generator.py'
spec=importlib.util.spec_from_file_location('audit_123',GEN_PATH)
mod=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod)

bands=('easy','medium','hard')
summary={}
apply_inputs=[]
for band_i,band in enumerate(bands):
    selfcheck_fail=[]; profiles=set(); unique=set(); dims=set(); corners=set(); variants=set()
    for i in range(300):
        seed=91000+band_i*1000+i
        g=mod.generate(seed,i,difficulty=band)
        errs=mod.self_check(g)
        if errs: selfcheck_fail.append({'i':i,'errors':errs})
        obs=mod.observe_overrides(g)
        profiles.add(mod.schedule_profile(seed,i,band))
        dims.add((len(g),len(g[0])))
        corners.add(obs['missing_corner']); variants.add(obs['distractor_variant'])
        unique.add(hashlib.sha256(json.dumps(g,separators=(',',':')).encode()).hexdigest())
        if i < 4: apply_inputs.append(g)
    # Test all cyclic starts in a 4-profile schedule. Query is each possible fifth item.
    windows=100; ambiguous=[]; survivor_counts={name:0 for name in mod.LESSON_COMPETITORS}
    for start in range(windows):
        seed=95000+band_i*1000+start
        pairs=[]
        for off in range(mod.EXAMPLES_NEEDED+1):
            g=mod.generate(seed,start+off,difficulty=band)
            pairs.append({'input':g,'output':mod.rule_mirror(g)})
        demos,query=pairs[:-1],pairs[-1]
        reasons=mod.lesson_identifiable(demos,query)
        if reasons: ambiguous.append({'start':start,'reasons':reasons})
        for name,rival in mod.LESSON_COMPETITORS.items():
            if all(rival(d['input'])==d['output'] for d in demos): survivor_counts[name]+=1
    summary[band]={
      'draws':300,'unique_inputs':len(unique),'selfcheck_failures':selfcheck_fail,
      'profiles':sorted(profiles),'dimensions':sorted([list(x) for x in dims]),
      'missing_corners':sorted(corners),'distractor_variants':sorted(variants),
      'lesson_windows':windows,'ambiguous_windows':ambiguous,
      'competitor_demo_survivor_counts':survivor_counts,
    }

# Confirm declared canonical shortcuts really fit all canonical pairs.
row=None
for line in (ROOT/'shared/data/canonical/puzzles.jsonl').read_text().splitlines():
    obj=json.loads(line)
    if obj.get('task_id')==mod.TASK_ID: row=obj; break
assert row
canonical_pairs=[*row['train'],*row['test']]
canonical_shortcuts={}
for name,rival in mod.CANONICAL_SHORTCUTS.items():
    canonical_shortcuts[name]=[rival(p['input'])==p['output'] for p in canonical_pairs]

result={
 'task_id':mod.TASK_ID,'generator_version':mod.VERSION,
 'generator_sha256':hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
 'rule_hash_declared':mod.RULE_HASH,
 'sample_policy':{'draws_per_band':300,'draw_seed':'91000+band_index*1000+i','draw_sample_index':'i','lesson_windows_per_band':100,'lesson_seed':'95000+band_index*1000+start','lesson_sample_indices':'start..start+4'},
 'bands':summary,
 'canonical_pairs':len(canonical_pairs),
 'canonical_shortcuts_fit_each_pair':canonical_shortcuts,
 'task_test_portability_failure':'task_tests stage cannot collect because test computes generator path under generators/1238481b674b/puzzle_generators/per_puzzle/1238481b674b/generator.py',
 'command':['python3','run_with_racket.py','python3','../checks/audit/1238481b674b/probe.py'],
 'cwd':'packet_root',
}
(Path('..')/'checks/audit/1238481b674b/probe.json').write_text(json.dumps(result,indent=2)+'\n')
(Path('..')/'checks/audit/1238481b674b/apply-inputs.json').write_text(json.dumps(apply_inputs,indent=2)+'\n')
# Save expected mirrors for authoritative comparison.
(Path('..')/'checks/audit/1238481b674b/mirror-outputs.json').write_text(json.dumps([mod.rule_mirror(g) for g in apply_inputs],indent=2)+'\n')
print(json.dumps(result,indent=2))
