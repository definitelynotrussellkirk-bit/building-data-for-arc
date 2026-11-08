#!/usr/bin/env python3
import hashlib, json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

root=find_root(__file__)
mod, source, digest=load_selected_generator('e93047bc5081', root=root)
grid=mod.generate(57000,0,difficulty='easy')
observed=mod.observe_overrides(grid)
colors=sorted({v for row in grid for v in row})
mutated=[[True if v == 1 else v for v in row] for row in grid]
result={
 'schema':'arcpuzzles-audit-validator-probe-v1',
 'task_id':'e93047bc5081','generator_sha256':digest,'version':mod.VERSION,'rule_hash':mod.RULE_HASH,
 'seed':57000,'sample_index':0,'difficulty':'easy','observed':observed,'colors':colors,
 'normal_self_check':mod.self_check(grid,difficulty='easy'),
 'boolean_self_check':mod.self_check(mutated,difficulty='easy'),
 'metadata_mismatch_self_check':mod.self_check(grid,difficulty='easy',meta={'overrides':{'marker_side':'bottom'}}),
 'boolean_replacements':sum(v is True for row in mutated for v in row),
 'input':grid,'boolean_input':mutated,
 'commands':{
   'build':'python3 run_with_racket.py python3 ../checks/audit/e93047bc5081/build_inputs.py',
   'apply':'python3 run_with_racket.py python3 -m arcpuzzles apply e93047bc5081 --input ../checks/audit/e93047bc5081/boolean-input.json --check-generator-domain --out ../checks/audit/e93047bc5081/racket.json'
 },
 'cwd':str(root.parent),
}
base=Path(__file__).resolve().parent
(base/'boolean-input.json').write_text(json.dumps(mutated,indent=2)+'\n')
(base/'probe.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('generator_sha256','colors','observed','normal_self_check','boolean_self_check','metadata_mismatch_self_check','boolean_replacements')},indent=2))
