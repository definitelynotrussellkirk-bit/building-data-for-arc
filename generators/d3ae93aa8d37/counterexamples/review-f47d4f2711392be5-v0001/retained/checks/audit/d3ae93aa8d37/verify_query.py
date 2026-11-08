import hashlib,json
from pathlib import Path
base=Path(__file__).resolve().parent
evidence=json.loads((base/'wrong-query-evidence.json').read_text())
applied=json.loads((base/'query-racket.json').read_text())
query=evidence['pairs'][-1]
assert query['racket_output']==applied['results'][0]['output']
assert evidence['generator_sha256']==applied['generator_sha256']
assert applied['rule_hash_matches_catalog']
assert evidence['demo_rival_agreements']==[True,True,True,True]
assert evidence['query_rival_agreements']==[False]
out={'status':'reproduced_wrong_query_lesson','generator_sha256':applied['generator_sha256'],
 'rule_hash':applied['executed_rule_hash'],'rule_text_sha256':applied['rule_text_sha256'],
 'input_sha256':applied['results'][0]['input_sha256'],
 'output_sha256':applied['results'][0]['output_sha256'],
 'differences':query['differences'],
 'files':{name:hashlib.sha256((base/name).read_bytes()).hexdigest() for name in
          ('wrong-query-episode.jsonl','wrong-query-evidence.json','query-input.json','query-racket.json')}}
(base/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
