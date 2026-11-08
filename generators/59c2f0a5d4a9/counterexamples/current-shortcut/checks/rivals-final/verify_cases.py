import hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent
cases=json.loads((p/'cases.json').read_text())
receipt=json.loads((p/'racket.json').read_text())
assert cases['generator_sha256']==receipt['generator_sha256']
assert cases['rule_hash']==receipt['executed_rule_hash']
verified=[]
for case,result in zip(cases['cases'],receipt['results'],strict=True):
 assert result['output'] is not None and result['input']==case['input']
 diffs=[{'cell':[r,c],'racket':v,'rival':case['rival_output'][r][c]}
        for r,row in enumerate(result['output']) for c,v in enumerate(row)
        if v!=case['rival_output'][r][c]]
 assert diffs and not case['validation_errors']
 verified.append({**case,'actual_racket_output':result['output'],'differing_cells':diffs})
out={k:cases[k] for k in ('task_id','generator_sha256','rule_hash')}
out.update({'status':'pass','cases':verified,'racket_receipt_sha256':hashlib.sha256((p/'racket.json').read_bytes()).hexdigest()})
(p/'verified.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({case['rival']:len(case['differing_cells']) for case in verified}))
