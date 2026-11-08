from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
REPO=ROOT/'repo'
sys.path.insert(0,str(REPO/'shared'/'runtime'))
D=json.load(open(Path(__file__).with_name('lesson-census.json')))
lesson=None; rotation=None
for candidate in D['lessons']:
    for rot in candidate.get('rotations',[]):
        if rot.get('ambiguous'):
            lesson=candidate; rotation=rot; break
    if lesson: break
assert lesson and rotation
inst=lesson['instance']
pairs=list(inst['train'])+list(inst['test'])
qidx=rotation['query_index']
train_indices=rotation['train_indices']
path=REPO/'generators'/'9536d5aef3f6'/'generator.py'
spec=importlib.util.spec_from_file_location('audit_gen_9536d5aef3f6',path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
query=pairs[qidx]
rival=mod._rival_fill_empty_only(query['input'])
assert rival != query['output']
assert all(mod._rival_fill_empty_only(pairs[i]['input']) == pairs[i]['output'] for i in train_indices)
out={
 'schema':'arcpuzzles-audit-counterexample-v1',
 'task_id':'9536d5aef3f6',
 'finding':'A rotated holdout removes the only unequal occupied-pair demonstration, so fill_empty_only fits all three demos but disagrees on the query.',
 'generator_sha256':D['generator_sha256'],
 'declared_rule_hash':D['declared_rule_hash'],
 'rule_source_sha256':D['rule_source_sha256'],
 'band':lesson['band'],'lesson_index':lesson['index'],'seed':lesson['seed'],'sample_index':lesson['sample_index'],
 'instance_sha256':lesson['instance_sha256'],
 'query_index':qidx,'train_indices':train_indices,
 'rotation_warnings':rotation['warnings'],
 'demonstrations':[pairs[i] for i in train_indices],
 'query_input':query['input'],
 'intended_output':query['output'],
 'fill_empty_only_output':rival,
 'source_evidence':'checks/audit/9536d5aef3f6/lesson-census.json',
 'command':{
   'cwd':'packet_root',
   'argv':['python3','run_with_racket.py','python3','-m','arcpuzzles','lesson-census','9536d5aef3f6','--per-band','100','--rotate-query','--timeout','1800','--out','../checks/audit/9536d5aef3f6/lesson-census.json'],
   'exit_code':1,
 }
}
Path(__file__).with_name('rotation-counterexample.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ('band','seed','sample_index','query_index','train_indices','generator_sha256','declared_rule_hash')},indent=2))
