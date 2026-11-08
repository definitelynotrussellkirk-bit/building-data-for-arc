import hashlib
import json
from pathlib import Path
root=Path(__file__).resolve().parent
repo=root.parents[2]/'repo'
p=json.loads((root/'probe.json').read_text())
r=json.loads((root/'racket.json').read_text())
assert p['generator_sha256']==r['generator_sha256']==hashlib.sha256((repo/'generators/e9cd770abc01/generator.py').read_bytes()).hexdigest()
assert p['catalog_rule_hash']==r['executed_rule_hash']==r['catalog_rule_hash']
assert r['rule_hash_matches_catalog']
rows=[]
for case,result in zip(p['cases'],r['results'],strict=True):
    assert result['valid_output'] and result['error'] is None
    assert result['output']==case['intended_output']
    rows.append({'source':case['source'],'seed':case.get('seed'),
                 'index':case.get('sample_index',case.get('index')),
                 'validator_result':case['validator_result'],'racket_valid_output':result['valid_output'],
                 'racket_error':result['error'],'racket_matches_intended':True,
                 'racket_matches_euclidean_rival':result['output']==case['euclidean_rival_output']})
assert all(x['racket_matches_euclidean_rival'] for x in rows[:4])
assert not rows[-1]['racket_matches_euclidean_rival']
out={'status':'domain_question_metric_ambiguity','generator_sha256':p['generator_sha256'],
     'normalized_rule_sha256':p['normalized_rule_sha256'],'catalog_rule_hash':p['catalog_rule_hash'],
     'racket_execution_rule_text_sha256':r['rule_text_sha256'],'checks':rows,
     'scope':'Bounded 15 raw generator draws to select three retained witnesses, plus two canonical demonstrations. No full battery or production lesson census.'}
(root/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
