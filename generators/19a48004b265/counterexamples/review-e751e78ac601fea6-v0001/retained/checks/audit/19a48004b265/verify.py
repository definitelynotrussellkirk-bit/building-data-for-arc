import hashlib
import json
from pathlib import Path

out = Path(__file__).resolve().parent
work = out.parents[2]
p = json.loads((out/'probe_results.json').read_text())
r = json.loads((out/'racket.json').read_text())
c = json.loads((out/'combined/result.json').read_text())
assert hashlib.sha256((work/'repo/generators/19a48004b265/generator.py').read_bytes()).hexdigest() == p['generator_sha256'] == r['generator_sha256']
assert r['rule_hash_matches_catalog'] and r['results'][0]['valid_output']
assert r['results'][0]['error'] is None
assert r['results'][0]['output'] == json.loads((out/'expected_transpose.json').read_text())
assert p['generated']['count'] == 573 and not p['generated']['self_check_failures']
assert len(p['declared_axis_boundary_probes']) == 4
assert all(row['status'] == 'rejected' for row in p['declared_axis_boundary_probes'])
assert p['oversized_validator_probe']['self_check'] == []
assert c['exit_code'] == 1 and not c['timed_out']
print('Verified source binding, 573-probe counts, four boundary rejections, validator witness, actual Racket output, and recorded combined-audit failure.')
