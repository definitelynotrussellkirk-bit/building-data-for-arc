"""Recheck the retained production witness and count distinct sampled inputs."""
import hashlib, importlib.util, json
from pathlib import Path
from rivals import rival

root=Path.cwd()
out=root.parent/'checks/audit/0a444f80387e'
source=root/'generators/0a444f80387e/generator.py'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash=='9df826e90d3b82f23b1c1062500eb9db7e1c53bfa2afb92f6a7201b2c24e724c'
spec=importlib.util.spec_from_file_location('audit_target',source)
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
lesson=json.loads((out/'ambiguous_lesson.json').read_text())
actual=json.loads((out/'query_racket.json').read_text())
assert lesson['seed']==30 and lesson['sample_indices']==[0,1,2,3]
checks=[]
for i,pair in enumerate(lesson['train']+lesson['test']):
    reproduced=g.generate(30,i,difficulty='medium')
    checks.append({'sample_index':i,'reproduced':reproduced==pair['input'],'self_check':g.self_check(reproduced),'rival_matches':rival(reproduced)==pair['output']})
assert all(row['reproduced'] and not row['self_check'] for row in checks)
assert [row['rival_matches'] for row in checks]==[True,True,True,False]
assert actual['results'][0]['input']==lesson['test'][0]['input']
assert actual['results'][0]['output']==lesson['test'][0]['output']
summary=json.loads((out/'probe_summary.json').read_text())
hashes=set()
for episode in summary['episode_results']:
    for index in episode['sample_indices']:
        grid=g.generate(episode['seed'],index,difficulty='medium')
        hashes.add(hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest())
report={'generator_sha256':source_hash,'rule_text_sha256':actual['rule_text_sha256'],'executed_rule_hash':actual['executed_rule_hash'],'witness_checks':checks,'public_apply_agrees_with_episode':True,'counting_scope':'Recreated the 400 accepted seed/sample tuples from seeds 1..100, indices 0..3, medium, no overrides','sampled_inputs':400,'unique_inputs':len(hashes),'ambiguous_lessons':len(summary['ambiguous']),'lessons':100,'query_reference_output':actual['results'][0]['output'],'query_rival_output':rival(lesson['test'][0]['input'])}
(out/'witness_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
