from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

TASK='2ff23bbd7de8'
spec=importlib.util.spec_from_file_location(f'audit_generator_{TASK}', Path(f'generators/{TASK}/generator.py'))
assert spec and spec.loader
gen=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
source=Path(f'generators/{TASK}/generator.py')
sha=hashlib.sha256(source.read_bytes()).hexdigest()
results={
  'schema':'arc-audit-probe-v1','task_id':TASK,'generator_sha256':sha,
  'seeds':list(range(9100,9112)),'starts':list(range(8)),
  'lesson_count':0,'example_count':0,'identifiable_failures':[],
  'rival_refutations':{name:0 for name in gen.LESSON_COMPETITORS},
  'canonical_shortcut_fit':{},
}
for si, seed in enumerate(results['seeds']):
    difficulty=('easy','medium','hard')[si%3]
    for start in results['starts']:
        demos=[]
        for idx in range(start,start+gen.EXAMPLES_NEEDED):
            grid=gen.generate(seed,idx,difficulty=difficulty)
            out=gen.rule_mirror(grid)
            demos.append({'input':grid,'output':out})
            results['example_count']+=1
            for name,rival in gen.LESSON_COMPETITORS.items():
                if rival(grid)!=out:
                    results['rival_refutations'][name]+=1
        qgrid=gen.generate(seed,start+gen.EXAMPLES_NEEDED,difficulty=difficulty)
        reasons=gen.lesson_identifiable(demos, {'input':qgrid,'output':gen.rule_mirror(qgrid)})
        if reasons:
            results['identifiable_failures'].append({'seed':seed,'start':start,'difficulty':difficulty,'reasons':reasons})
        results['lesson_count']+=1
# canonical pairs through the repository data exposed for authoring, not solve
row=None
for line in Path('shared/data/canonical/puzzles.jsonl').read_text().splitlines():
    obj=json.loads(line)
    if obj.get('task_id')==TASK:
        row=obj; break
pairs=list(row['train']) + ([row['test']] if isinstance(row['test'],dict) else list(row['test']))
for name,rival in gen.CANONICAL_SHORTCUTS.items():
    results['canonical_shortcut_fit'][name]={
      'fit':sum(rival(p['input'])==p['output'] for p in pairs),
      'total':len(pairs),
    }
results['status']='pass' if not results['identifiable_failures'] and all(v>0 for v in results['rival_refutations'].values()) else 'fail'
Path('../checks/audit/2ff23bbd7de8/probe.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n')
print(json.dumps(results,indent=2,sort_keys=True))
