import json, hashlib
from pathlib import Path
from reviewer_support import find_root,load_selected_generator,canonical_pairs
root=find_root(Path.cwd()); gen,path,digest=load_selected_generator('5383f0933057',root=root)
folder=root.parent/'checks/audit/5383f0933057'
canonical=canonical_pairs('5383f0933057',root=root,labeled_only=True)
print('canonical mirror:',all(gen.rule_mirror(p['input'])==p['output'] for p in canonical))
for seed in range(300):
 for band in ('easy','medium','hard'):
  for start in range(4):
   grids=[gen.generate(seed,start+i,difficulty=band) for i in range(4)]
   truth=[gen.rule_mirror(g) for g in grids]
   for query in range(4):
    for name,rival in gen._COMPETING_RULES.items():
     outputs=[rival(g) for g in grids]
     if all(outputs[i]==truth[i] for i in range(4) if i!=query) and outputs[query]!=truth[query]:
      record={'task_id':gen.TASK_ID,'generator_sha256':digest,'seed':seed,'difficulty':band,'start_sample_index':start,'sample_indices':list(range(start,start+4)),'overrides':{},'query_position':query,'production_query_position':3,'rival_name':name,'self_check':[gen.self_check(g) for g in grids],'strict_canonical_like':[gen.strict_canonical_like(g) for g in grids],'inputs':grids,'mirror_outputs':truth,'rival_outputs':outputs}
      (folder/'candidate.json').write_text(json.dumps(record,indent=2)+'\n')
      (folder/'inputs.json').write_text(json.dumps({'inputs':grids})+'\n')
      print(json.dumps({k:v for k,v in record.items() if k not in ('inputs','mirror_outputs','rival_outputs')}));raise SystemExit(0)
print('No ambiguity found in bounded search')
