import json,importlib.util,hashlib
from pathlib import Path
for line in Path('repo/shared/data/canonical/puzzles.jsonl').read_text().splitlines():
 row=json.loads(line)
 if row.get('task_id')=='f273ee8b09ee':print(row['program_solution']);break
path=Path('repo/generators/f273ee8b09ee/generator.py');spec=importlib.util.spec_from_file_location('audit_target',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
g=m.generate(17,9,difficulty='medium',n_blobs=4)
print('palette',sorted({x for row in g for x in row}-{0}),'selfcheck',m.self_check(g,difficulty='medium'),'identical_to_default',g==m.generate(17,9,difficulty='medium'))
print('hash',hashlib.sha256(path.read_bytes()).hexdigest())
out=Path('checks/audit/f273ee8b09ee');out.mkdir(parents=True,exist_ok=True)
(out/'counterexample-input.json').write_text(json.dumps({'input':g},indent=2)+'\n')
(out/'structural-evidence.json').write_text(json.dumps({'generator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'seed':17,'sample_index':9,'difficulty':'medium','overrides':{'n_blobs':4},'observed_distinct_nonzero_colors':len({x for row in g for x in row}-{0}),'self_check':m.self_check(g,difficulty='medium'),'same_as_default':g==m.generate(17,9,difficulty='medium')},indent=2)+'\n')
