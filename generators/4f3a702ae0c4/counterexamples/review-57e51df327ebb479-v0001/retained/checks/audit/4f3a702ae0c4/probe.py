from pathlib import Path
import importlib.util,sys,json,hashlib
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
REPO=WORK/'repo'
sys.path.insert(0,str(REPO/'shared/runtime'))
from reviewer_support import canonical_pairs
TASK='4f3a702ae0c4'
SOURCE=REPO/'generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audit_gen',SOURCE);gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
pairs=canonical_pairs(TASK,root=REPO,labeled_only=True)
anti=[[0]*8 for _ in range(8)];anti[0][7]=2
for r,c in [(3,2),(3,3),(4,4),(4,5)]:anti[r][c]=7
inputs=[pairs[0]['input'],anti,pairs[2]['input'],pairs[1]['input']]
lesson=[{'input':g,'output':gen.rule_mirror(g)} for g in inputs]
verdict=gen.lesson_identifiable(lesson[:3],lesson[3])
def always_main(g):return gen._apply_transform(g,1)
assert verdict==[]
assert all(always_main(p['input'])==p['output'] for p in lesson[:3])
assert always_main(lesson[3]['input'])!=lesson[3]['output']
record={'task_id':TASK,'classification':'reproduced_defect','defect':'lesson_identifiable accepts demonstrations that do not distinguish always-main reflection from command-selected reflection','construction':'handmade lawful anti-command pattern plus canonical train 0 and 2 demonstrations; canonical train 1 query','generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'input_validators':[gen.self_check(g) for g in inputs],'strict_validators':[gen.strict_canonical_like(g) for g in inputs],'actual_lesson_validator_verdict':verdict,'lesson':lesson,'rival_name':'always_main_diagonal','rival_outputs':[always_main(g) for g in inputs],'rival_fits_all_demos':True,'rival_disagrees_on_query':True,'commands':[{'command':'python3 run_with_racket.py python3 ../checks/audit/4f3a702ae0c4/probe.py','cwd':str(WORK),'exit_code':0}]}
(HERE/'input.json').write_text(json.dumps({'inputs':inputs},indent=2)+'\n')
(HERE/'diagnosis.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k not in ('lesson','rival_outputs')},indent=2))
