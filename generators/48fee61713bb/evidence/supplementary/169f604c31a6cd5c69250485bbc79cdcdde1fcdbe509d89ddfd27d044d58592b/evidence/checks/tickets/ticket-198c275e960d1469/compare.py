#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
repo=Path.cwd().resolve()
assets=repo/'generators/48fee61713bb/counterexamples/review-6364b207c4fc11dc-v0001/audit_assets.json'
index=repo/'generators/48fee61713bb/evidence/review_index.json'
assert hashlib.sha256(assets.read_bytes()).hexdigest()=='63581af6654dcfb4634af123b28d91e39c486463ca2c0844ebd5d9a87dc0dcdc'
assert hashlib.sha256(index.read_bytes()).hexdigest()=='69bb9ddfff338c0f16f7501c320a00b47fc2af0d474e09b9cf8542e404e81955'
manifest=json.loads(assets.read_text())
for row in manifest['files']:
 p=repo/row['path']; data=p.read_bytes()
 assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
current_source=repo/'generators/48fee61713bb/generator.py'
current_sha=hashlib.sha256(current_source.read_bytes()).hexdigest()
assert current_sha=='7a43eacd6626e8c595ea24c4a7c75874d6e40993598f3cc75dfc3b58ffdb3a3b'
retained_root=repo/'generators/48fee61713bb/counterexamples/review-6364b207c4fc11dc-v0001/retained/checks/audit/48fee61713bb'
retained=json.loads((retained_root/'racket.json').read_text())
replay=json.loads((repo.parent/'checks/tickets/ticket-198c275e960d1469/replay.json').read_text())
retained_outputs=[r['output_sha256'] for r in retained['results']]
replay_outputs=[r['output_sha256'] for r in replay['results']]
assert retained['executed_rule_hash']==replay['executed_rule_hash']=='88f9214cd87f'
assert retained_outputs==replay_outputs
assert len(set(replay_outputs))==1
assert all(r['error'] is None and r['valid_output'] for r in replay['results'])
metadata=json.loads((retained_root/'marker-blind-metadata.json').read_text())
assert metadata['racket_outputs_equal'] is True
result={
 'schema':'supplementary-audit-replay-v1',
 'ticket_id':'ticket-198c275e960d1469',
 'status':'completed',
 'assets_manifest_sha256':hashlib.sha256(assets.read_bytes()).hexdigest(),
 'audit_index_sha256':hashlib.sha256(index.read_bytes()).hexdigest(),
 'audited_generator_sha256':manifest['audited_generator_sha256'],
 'current_generator_sha256':current_sha,
 'source_drift_since_audit':current_sha!=manifest['audited_generator_sha256'],
 'executed_rule_hash':replay['executed_rule_hash'],
 'retained_output_sha256':retained_outputs,
 'replayed_output_sha256':replay_outputs,
 'marker_relocation_outputs_equal':True,
 'assessment':'The exact retained valid/counterfactual inputs still produce byte-identical canonical Racket outputs under unchanged rule hash 88f9214cd87f. The generator source has since changed and now documents the blue edge as correlated rather than causal, so this replay reproduces the historical bounded witness but does not clear or reopen the existing audit automatically.',
}
out=Path(__file__).with_name('result.json'); out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
