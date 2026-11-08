from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK='e84a374b51f2'
root=find_root(__file__)
gen,path,sha=load_selected_generator(TASK, root=root)
cases=[]
for label,args,kwargs in [
    ('seed_bool',(True,0),{}),
    ('seed_float',(1.5,0),{}),
    ('seed_string',('1',0),{}),
    ('seed_negative',(-1,0),{}),
    ('sample_bool',(1,True),{}),
    ('sample_float',(1,1.5),{}),
    ('sample_string',(1,'1'),{}),
    ('sample_negative',(1,-1),{}),
]:
    try:
        grid=gen.generate(*args, **kwargs)
        cases.append({'case':label,'accepted':True,'shape':[len(grid),len(grid[0])],'grid':grid})
    except Exception as exc:
        cases.append({'case':label,'accepted':False,'error_type':type(exc).__name__,'error':str(exc)})

malformed=[]
for label,grid in [
    ('row_as_digit_string',['00200']),
    ('cells_as_digit_strings',[['0','0','2','0','0']]),
]:
    errors=gen.self_check(grid)
    malformed.append({'case':label,'grid':grid,'errors':errors,'accepted':not errors})

out={'task_id':TASK,'generator_path':str(path),'generator_sha256':sha,'api_cases':cases,'malformed_validator_cases':malformed}
Path('../checks/audit/e84a374b51f2/api-probe.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
