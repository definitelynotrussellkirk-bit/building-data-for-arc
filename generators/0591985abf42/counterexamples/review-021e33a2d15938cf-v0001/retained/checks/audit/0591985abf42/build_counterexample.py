from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
ROOT=Path('/mnt/data/arcpuzzles_review_035633')
TASK='0591985abf42'
gen_path=ROOT/'repo/generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audit_'+TASK, gen_path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
inputs=json.loads((ROOT/'checks/audit'/TASK/'input.json').read_text())
racket=json.loads((ROOT/'checks/audit'/TASK/'racket.json').read_text())
expected=[entry['output'] for entry in racket['results']]

def rival(grid):
    original=[row[:] for row in grid]
    output=[row[:] for row in grid]
    background=mod._mode_reading_order(original)
    guide=mod._priority_guide(original, background)
    assert guide is not None
    kind,param,line_color=guide
    selected=next(v for row in original for v in row if v not in (background,line_color))
    for r,row in enumerate(original):
        for c,value in enumerate(row):
            if value != selected:
                continue
            rr,cc=mod._mirror_destination(kind,param,r,c)
            if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                output[rr][cc]=value
    return output
rival_outputs=[rival(g) for g in inputs]
assert all(rival_outputs[i] == expected[i] for i in range(4))
assert rival_outputs[4] != expected[4]
query_diffs=[]
for r,(er,rr) in enumerate(zip(expected[4],rival_outputs[4])):
    for c,(e,v) in enumerate(zip(er,rr)):
        if e != v:
            query_diffs.append({'row':r,'col':c,'reference':e,'rival':v})
sha=lambda obj: hashlib.sha256(json.dumps(obj,separators=(',',':')).encode()).hexdigest()
report={
  'schema':'arcpuzzles-audit-counterexample-v1',
  'task_id':TASK,
  'finding':'Four generated demonstrations can support the shortcut “reflect the first object color encountered in reading order” even though the fifth query requires the uniquely least-frequent color.',
  'status':'reproduced teaching ambiguity',
  'generator_version':mod.VERSION,
  'generator_sha256':hashlib.sha256(gen_path.read_bytes()).hexdigest(),
  'rule_hash':racket['executed_rule_hash'],
  'rule_text_sha256':racket['rule_text_sha256'],
  'seed':1,
  'difficulty':'medium',
  'sample_indices':[0,1,2,3,4],
  'lesson_policy':'sample indices 0..3 are demonstrations; index 4 is query',
  'validator':{'all_inputs_pass_self_check':all(not mod.self_check(g,difficulty='medium') for g in inputs)},
  'rival':'Reflect the first non-background, non-guide color encountered in row-major reading order across the guide.',
  'demo_fit':[rival_outputs[i] == expected[i] for i in range(4)],
  'query_differs':rival_outputs[4] != expected[4],
  'query_differing_cells':query_diffs,
  'pairs':[
     {
       'sample_index':i,
       'role':'demo' if i<4 else 'query',
       'input':inputs[i],
       'racket_output':expected[i],
       'rival_output':rival_outputs[i],
       'input_sha256':sha(inputs[i]),
       'racket_output_sha256':sha(expected[i]),
       'rival_output_sha256':sha(rival_outputs[i]),
     }
     for i in range(5)
  ],
  'supported_apply_command':{
    'cwd':'packet_root',
    'argv':['python3','run_with_racket.py','python3','-m','arcpuzzles','apply',TASK,'--input','../checks/audit/'+TASK+'/input.json','--out','../checks/audit/'+TASK+'/racket.json'],
    'exit_code':0,
  },
}
(ROOT/'checks/audit'/TASK/'counterexample.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('task_id','status','generator_sha256','rule_hash','seed','demo_fit','query_differs','query_differing_cells')},indent=2))
