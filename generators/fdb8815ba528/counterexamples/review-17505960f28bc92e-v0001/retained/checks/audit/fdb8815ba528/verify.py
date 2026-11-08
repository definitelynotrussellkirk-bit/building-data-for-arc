"""Verify retained current-source audit evidence; no puzzle source execution."""
from pathlib import Path
import hashlib, json
HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'racket.json').read_text());w=json.loads((HERE/'witness.json').read_text());p=json.loads((HERE/'probe.json').read_text())
source=HERE.parents[2]/'repo/generators/fdb8815ba528/generator.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()==p['generator_sha256']==w['generator_sha256']==r['generator_sha256']
assert len(r['results'])==1 and r['results'][0]['error'] is None and r['results'][0]['valid_output']
assert r['results'][0]['input']==w['input']
assert r['results'][0]['output']==w['actual_racket_output']==w['independent_expected_output']
assert r['results'][0]['output']!=w['rival_output']
assert r['executed_rule_hash']==w['rule_hash']==p['rule_hash']
assert r['rule_text_sha256']==w['rule_text_sha256']==p['rule_text_sha256']
assert len(w['difference_coordinates'])==11 and w['validator_errors']==[]
assert p['failures']==[]
assert p['counts']['default_grids']+p['counts']['joint_override_grids']==2880
assert p['counts']['legacy_agrees']==p['counts']['validator_accepted']==p['counts']['mirror_agrees']==2880
assert all(not row['validator_errors'] and row['independent_matches_label'] and row['legacy_matches_label'] and all(row['declared_canonical_shortcuts'].values()) for row in p['canonical'])
print(json.dumps({'status':'verified','generated_draws':2880,'unique_inputs':p['unique_input_hashes'],'canonical_pairs':len(p['canonical']),'actual_racket_witness_differing_cells':11,'generator_sha256':p['generator_sha256'],'rule_text_sha256':r['rule_text_sha256']},sort_keys=True))
