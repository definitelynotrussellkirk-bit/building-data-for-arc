from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
GEN_PATH=ROOT/'repo/generators/3c01bf0d6576/generator.py'
spec=importlib.util.spec_from_file_location('audit_3c', GEN_PATH); assert spec and spec.loader
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
here=Path(__file__).resolve().parent
grids=json.loads((here/'parity-input.json').read_text())
racket=json.loads((here/'racket.json').read_text())
actual=[item['output'] for item in racket['results']]
expected=[mod._solve_python(g) for g in grids]
mismatches=[i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
record={
 'schema':'arcpuzzles-audit-parity-v1',
 'task_id':mod.TASK_ID,
 'generator_sha256':hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
 'declared_rule_hash':mod.RULE_HASH,
 'executed_rule_hash':racket['executed_rule_hash'],
 'rule_text_sha256':racket['rule_text_sha256'],
 'inputs':len(grids),
 'python_racket_matches':len(grids)-len(mismatches),
 'mismatches':mismatches,
 'all_inputs_pass_self_check':all(mod.self_check(g)==[] for g in grids),
 'apply_command':['python3','run_with_racket.py','python3','-m','arcpuzzles','apply','3c01bf0d6576','--input','../checks/audit/3c01bf0d6576/parity-input.json','--out','../checks/audit/3c01bf0d6576/racket.json'],
 'apply_cwd':'packet_root'
}
(here/'parity.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
assert not mismatches
