from __future__ import annotations
import json
from pathlib import Path
from collections import Counter
from reviewer_support import find_root, load_selected_generator

TASK='74e83caa0660'
root=find_root(__file__)
gen,path,sha=load_selected_generator(TASK, root=root)
seed=17
sample_index=9
difficulty='medium'
variants={
    'default': gen.generate(seed,sample_index,difficulty=difficulty),
    'n_pairs_1': gen.generate(seed,sample_index,difficulty=difficulty,n_pairs=1),
    'n_pairs_8': gen.generate(seed,sample_index,difficulty=difficulty,n_pairs=8),
}
counts={name:dict(sorted(Counter(v for row in grid for v in row if v).items())) for name,grid in variants.items()}
report={
    'task_id':TASK,
    'generator_path':str(path),
    'generator_sha256':sha,
    'seed':seed,
    'sample_index':sample_index,
    'difficulty':difficulty,
    'byte_identical': variants['default']==variants['n_pairs_1']==variants['n_pairs_8'],
    'active_color_counts':counts,
    'self_check':{name:gen.self_check(grid) for name,grid in variants.items()},
    'variants':variants,
    'finding':'AXES advertises n_pairs but generate draws key pairs, so explicit n_pairs values are inert.',
}
out=Path('../checks/audit/74e83caa0660/inert-n-pairs.json')
out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
Path('../checks/audit/74e83caa0660/input.json').write_text(json.dumps(variants['n_pairs_1'],indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='variants'},indent=2,sort_keys=True))
