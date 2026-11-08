from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator
TASK_ID='f9dd4cf0f344'
root=find_root(__file__)
gen,path,sha=load_selected_generator(TASK_ID,root=root)
challenge=json.loads((Path(__file__).parent/'public_challenge.json').read_text())
rows=[]
for split in ('train','test'):
    for index,pair in enumerate(challenge[split]):
        errors=gen.self_check(pair['input'])
        rows.append({'split':split,'index':index,'errors':errors,'passed':not errors,
                     'shape':[len(pair['input']),len(pair['input'][0])]})
print(json.dumps({'schema':'audit-domain-validation-v1','task_id':TASK_ID,
  'generator_path':path.relative_to(root).as_posix(),'generator_sha256':sha,
  'all_passed':all(row['passed'] for row in rows),'rows':rows},indent=2,sort_keys=True))
