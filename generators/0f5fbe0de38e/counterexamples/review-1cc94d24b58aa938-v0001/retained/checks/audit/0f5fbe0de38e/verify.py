import hashlib
import json
from pathlib import Path
p=Path(__file__).resolve().parent
r=json.loads((p/'racket.json').read_text())
mirror=json.loads((p/'mirror.json').read_text())
rival=json.loads((p/'rival.json').read_text())
rows=r['results']
summary={
    'input_count':len(rows),
    'valid_output_count':sum(row['valid_output'] is True for row in rows),
    'error_count':sum(row['error'] is not None for row in rows),
    'mirror_mismatch_indices':[i for i,row in enumerate(rows) if row['output'] != mirror[i]],
    'full_footprint_rival_difference_indices':[i for i,row in enumerate(rows) if row['output'] != rival[i]],
    'executed_rule_hash':r['executed_rule_hash'],
    'rule_text_sha256':r['rule_text_sha256'],
    'generator_sha256':r['generator_sha256'],
    'rule_hash_matches_catalog':r['rule_hash_matches_catalog'],
    'evidence_sha256':{name:hashlib.sha256((p/name).read_bytes()).hexdigest() for name in ('input.json','mirror.json','rival.json','racket.json','probe.json')},
}
assert summary['valid_output_count']==36 and summary['error_count']==0
assert summary['mirror_mismatch_indices']==[]
assert len(summary['full_footprint_rival_difference_indices'])==36
(p/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
