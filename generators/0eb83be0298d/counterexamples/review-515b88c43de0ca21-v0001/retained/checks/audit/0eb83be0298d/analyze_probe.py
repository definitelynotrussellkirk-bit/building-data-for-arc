#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent
prep=json.load(open(D/'probe_preparation.json'))
rivals=json.load(open(D/'generated_rivals.json'))['outputs']
racket=json.load(open(D/'generated_racket.json'))
results=racket['results']
matches=[]
for case,rival,result in zip(prep['cases'],rivals,results,strict=True):
    matches.append({**case,'matches_racket':rival==result['output'],'racket_output_sha256':result['output_sha256']})
canon_rival=json.load(open(D/'canonical_rival.json'))['output']
canon=json.load(open(D/'canonical_racket.json'))
canon_out=canon['results'][0]['output']
report={
 'schema':'arcpuzzles-template-free-shortcut-audit-v1','status':'shortcut_reproduced' if all(x['matches_racket'] for x in matches) and canon_rival!=canon_out else 'not_reproduced',
 'task_id':prep['task_id'],'generator_sha256':prep['generator_sha256'],'executed_rule_hash':racket['executed_rule_hash'],'rule_hash_matches_catalog':racket['rule_hash_matches_catalog'],
 'shortcut':prep['rival'],'generated':{'draws':len(matches),'matches':sum(x['matches_racket'] for x in matches),'mismatches':sum(not x['matches_racket'] for x in matches),'cases':matches},
 'canonical_counterexample':{'input_sha256':prep['canonical_input_sha256'],'rival_matches_racket':canon_rival==canon_out,'racket_output_sha256':canon['results'][0]['output_sha256'],'rival_output_sha256':prep['canonical_rival_sha256']},
 'evidence':{'generated_apply':'generated_racket.json','canonical_apply':'canonical_racket.json','inputs':'generated_inputs.json','rivals':'generated_rivals.json'},
 'limits':['Finite 60-draw generated census; structural source inspection explains why ordinary draws all share this shortcut.']}
(D/'template_free_shortcut.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(f"status={report['status']} generated={report['generated']['matches']}/{report['generated']['draws']} canonical_match={report['canonical_counterexample']['rival_matches_racket']}")
raise SystemExit(0 if report['status']=='shortcut_reproduced' else 1)
