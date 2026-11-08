from __future__ import annotations
import hashlib, importlib.util, json, traceback
from pathlib import Path

PACKET = Path(__file__).resolve().parents[3]
GEN_PATH = PACKET / 'repo/generators/generic_bar_transfer_gen1/generator.py'
spec = importlib.util.spec_from_file_location('audit_generic_bar_transfer_gen1_repro', GEN_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
record = {
    'task_id': 'generic_bar_transfer_gen1',
    'generator_sha256': hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    'seed': 0,
    'difficulty': 'hard',
    'command': ['python3', '../checks/audit/generic_bar_transfer_gen1/reproduce.py'],
    'cwd': 'repo',
}
try:
    module.generate_task(0, difficulty='hard')
    record['status'] = 'unexpected_success'
except Exception as exc:
    record.update({
        'status': 'reproduced_generation_failure',
        'exception_type': type(exc).__name__,
        'exception': str(exc),
        'root_cause': 'hard mode uses 5 towers; icon width 5 gives w_need=1+5*(5+1)=31, then rng.randint(31,30)',
        'traceback': traceback.format_exc(),
    })
out = Path(__file__).resolve().parent / 'counterexample.json'
out.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
raise SystemExit(0 if record['status'] == 'reproduced_generation_failure' else 1)
