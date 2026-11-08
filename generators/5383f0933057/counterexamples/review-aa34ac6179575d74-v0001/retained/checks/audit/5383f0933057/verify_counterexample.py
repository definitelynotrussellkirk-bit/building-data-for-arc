import json
from pathlib import Path
from reviewer_support import find_root,load_selected_generator
root=find_root(Path.cwd());gen,source,digest=load_selected_generator('5383f0933057',root=root)
f=root.parent/'checks/audit/5383f0933057';c=json.loads((f/'candidate.json').read_text());r=json.loads((f/'racket-output.json').read_text())
assert digest==c['generator_sha256']==r['generator_sha256']
assert r['rule_hash_matches_catalog']
outputs=[p['output'] for p in r['results']]
assert outputs==c['mirror_outputs']
assert all(p['generator_domain']['errors']==[] for p in r['results'])
assert c['rival_outputs'][:3]==outputs[:3]
assert c['rival_outputs'][3]!=outputs[3]
pairs=[{'input':g,'output':o} for g,o in zip(c['inputs'],outputs)]
reasons=gen.lesson_identifiable(pairs[:3],pairs[3]);assert any('chebyshev' in reason for reason in reasons)
g=c['inputs'][3]
differences=[{'row':rr,'column':cc,'racket':outputs[3][rr][cc],'rival':c['rival_outputs'][3][rr][cc]} for rr in range(len(g)) for cc in range(len(g[0])) if outputs[3][rr][cc]!=c['rival_outputs'][3][rr][cc]]
record={**c,'rule_text_sha256':r['rule_text_sha256'],'executed_rule_hash':r['executed_rule_hash'],'racket_outputs':outputs,'query_differences':differences,'lesson_identifiable_reasons':reasons,'finding':'chebyshev rival fits all three ordered production demonstrations and mispredicts query'}
(f/'verified-counterexample.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'verified':True,'query_difference_count':len(differences),'lesson_identifiable':reasons,'generator_sha256':digest}))
