#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK='27c1546d634f'
EXPECTED='d6868189578e51934ca8ba9ff8546d38a3bf506d778602fdd7184b9133b30e93'
root=find_root(__file__)
gen, source, sha=load_selected_generator(TASK, root=root)
if sha != EXPECTED: raise RuntimeError(f'source drift: {sha}')
base=Path(__file__).resolve().parent
receipt=json.loads((base/'racket.json').read_text())
row=receipt['results'][0]
report={
 'schema':'arcpuzzles-audit-counterexample-v1',
 'task_id':TASK,
 'generator_path':str(source.relative_to(root)),
 'generator_source_sha256':sha,
 'executed_rule_hash':receipt['executed_rule_hash'],
 'rule_text_sha256':receipt['rule_text_sha256'],
 'input':row['input'],
 'input_sha256':row['input_sha256'],
 'self_check_errors':list(gen.self_check(row['input'])),
 'actual_racket_output':row['output'],
 'actual_output_sha256':row['output_sha256'],
 'rival':'crop only a perfect hollow rectangular border; otherwise return [[0]]',
 'rival_output':[[0]],
 'disagreement':row['output'] != [[0]],
 'domain_note':'The current self_check accepts this nonempty irregular one-hole object, and the protected canonical Racket rule crops it. It is outside the current production sampler, which emits only perfect frames.',
 'authority_receipt':'checks/audit/27c1546d634f/racket.json',
 'command':['python3','review.py','run','python3','-m','arcpuzzles','apply',TASK,'--input','../checks/audit/27c1546d634f/input.json','--out','../checks/audit/27c1546d634f/racket.json'],
 'working_directory':'packet_root',
 'payload_working_directory':'repo',
}
(base/'counterexample.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'disagreement':report['disagreement'],'self_check_errors':report['self_check_errors'],'source_sha256':sha},indent=2))
