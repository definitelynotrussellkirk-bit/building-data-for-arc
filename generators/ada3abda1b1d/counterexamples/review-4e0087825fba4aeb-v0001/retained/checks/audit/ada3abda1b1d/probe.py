from pathlib import Path
import json
from reviewer_support import find_root, load_selected_generator, canonical_pairs
ROOT=Path.cwd()
module,source,source_hash=load_selected_generator('ada3abda1b1d',root=ROOT)
pairs=canonical_pairs('ada3abda1b1d',root=find_root(source),labeled_only=True)
g=module.generate(0,0,difficulty='easy')
folder=ROOT.parent/'checks/audit/ada3abda1b1d'
(folder/'input.json').write_text(json.dumps({'inputs':[g]+[p['input'] for p in pairs]},indent=2)+'\n')
fit={name:[fn(p['input']) == p['output'] for p in pairs] for name,fn in module.CANONICAL_SHORTCUTS.items()}
report={'schema':'task-local-audit-probe-v1','task_id':'ada3abda1b1d','generator_sha256':source_hash,'declared_rule_hash':module.RULE_HASH,'seed':0,'sample_index':0,'difficulty':'easy','overrides':{},'generator_domain_errors':module.self_check(g),'observed':module.observe_overrides(g),'canonical_fit':fit,'canonical_origins':[{k:v for k,v in p.items() if k not in ('input','output')} for p in pairs],'input_grid':g,'rivals':{name:fn(g) for name,fn in module.CANONICAL_SHORTCUTS.items()}}
(folder/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'generator_sha256':source_hash,'domain_errors':report['generator_domain_errors'],'canonical_fit':fit},indent=2))
