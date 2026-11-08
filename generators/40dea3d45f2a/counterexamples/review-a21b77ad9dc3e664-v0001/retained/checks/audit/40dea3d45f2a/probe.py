from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

TASK='40dea3d45f2a'
root=Path(__file__).resolve().parents[3] / 'repo'
path=root/'generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audit_40',path)
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)

def label(grid):
    return gen._relation([gen._key(shape) for shape in gen._panel_cells(grid)])

pairs=[]
for index in range(5):
    grid=gen.generate(123,index,difficulty='medium',n_classes=1,palette_size=1)
    pairs.append({'input':grid,'output':label(grid)})
demos,query=pairs[:4],pairs[4]
hook_reasons=gen.lesson_identifiable(demos,query)
rivals=[]
for name,rival in gen.LESSON_COMPETITORS.items():
    fits=all(rival(pair['input'])==pair['output'] for pair in demos)
    query_agrees=rival(query['input'])==query['output']
    if fits:
        rivals.append({'name':name,'fits_all_demos':True,'agrees_with_query':query_agrees})
query_aware=[row['name'] for row in rivals if not row['agrees_with_query']]
summary={
    'schema':'audit-probe-v1','task_id':TASK,
    'generator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
    'settings':{'seed':123,'difficulty':'medium','n_classes':1,'palette_size':1,'demo_indices':[0,1,2,3],'query_index':4},
    'all_inputs_self_check_clean':all(not gen.self_check(pair['input']) for pair in pairs),
    'distinct_inputs':len({json.dumps(pair['input']) for pair in pairs}),
    'hook_reasons':hook_reasons,
    'surviving_rivals':rivals,
    'query_aware_ambiguity_reasons':query_aware,
    'query_input':query['input'],'query_output':query['output'],
}
print(json.dumps(summary,indent=2))
