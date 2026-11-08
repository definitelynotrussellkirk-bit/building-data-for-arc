#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parents[4]
GENERATOR = PACKET / 'repo/generators/d7b84df5a06a/generator.py'
RECEIPT = Path(__file__).with_name('racket.json')
OUT = Path(__file__).with_name('evidence.json')

spec = importlib.util.spec_from_file_location('audit_d7b84df5a06a', GENERATOR)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
grid = module.generate(1701, 0, difficulty='medium')
receipt = json.loads(RECEIPT.read_text())
output = receipt['results'][0]['output']
pair = {'input': grid, 'output': output}
report = {
    'schema': 'arcpuzzles-audit-domain-question-v1',
    'task_id': 'd7b84df5a06a',
    'generator_sha256': hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
    'rule_hash': receipt['executed_rule_hash'],
    'seed': 1701,
    'sample_index': 0,
    'difficulty': 'medium',
    'self_check': module.self_check(grid),
    'python_rule_matches_racket': module.rule_mirror(grid) == output,
    'witnesses': {name: bool(fn(grid)) for name, fn in module.SEMANTIC_WITNESSES.items()},
    'rival_refuted_by_single_pair': {
        name: rival(grid) != output for name, rival in module.LESSON_COMPETITORS.items()
    },
    'lesson_identifiable_one_demo': module.lesson_identifiable([pair], pair),
    'shared_gate_warning': (
        'EXAMPLES_NEEDED=1 is not an int >= 2 — a lesson that short cannot refute a rival; '
        'this task is a counterexample because one four-chamber demonstration refutes every declared rival.'
    ),
    'input': grid,
    'racket_output': output,
    'reproduction': {
        'cwd': 'packet_root',
        'argv': ['env', 'PYTHONPATH=repo/shared/runtime', 'python3',
                 'checks/audit/d7b84df5a06a/one-demo-proof/reproduce.py'],
    },
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps({
    'all_witnesses_fire': all(report['witnesses'].values()),
    'all_rivals_refuted': all(report['rival_refuted_by_single_pair'].values()),
    'lesson_identifiable': report['lesson_identifiable_one_demo'],
    'out': str(OUT),
}, indent=2))
