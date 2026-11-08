import hashlib,json
from pathlib import Path
from arcpuzzles.parametric_worker import _real_evaluator
out=Path('../checks/38200022d1b7'); c=json.loads((out/'candidate.json').read_text())
for line in Path('shared/data/canonical/puzzles.jsonl').open():
 row=json.loads(line)
 if row.get('task_id')==c['task_id']:
  original=row['program_solution'];break
needle='(not (= v 5))'
assert original.count(needle)==1
rival=original.replace(needle,needle+' (> (length (find-color g v)) 1)')
(out/'frequency_rival.rkt').write_text(rival+'\n')
apply,identity,bridge=_real_evaluator(Path('shared/runtime').resolve())
try:
 outputs=[apply(rival,p['input']) for p in c['pairs']]
finally: bridge.close()
assert outputs==c['rival_predictions']
qi=c['query_index'];assert all(outputs[i]==c['pairs'][i]['output'] for i in range(5) if i!=qi)
assert outputs[qi]!=c['pairs'][qi]['output']
r={'schema':'arc-protected-rival-replay-v1','generator_sha256':c['generator_sha256'],'original_rule_hash':c['rule_hash'],'rival_program':rival,'rival_sha256':hashlib.sha256(rival.encode()).hexdigest(),'racket':identity,'outputs':outputs,'all_rival_predictions_match_protected_racket':True,'demonstrations_fit':True,'query_disagrees':True}
(out/'rival_racket.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if k not in ('outputs','rival_program')},indent=2))
