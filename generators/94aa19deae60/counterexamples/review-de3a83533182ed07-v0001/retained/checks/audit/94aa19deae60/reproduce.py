"""Reproduce the assigned audit counterexample without changing audited files."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'checks/audit/94aa19deae60'
SOURCE = ROOT / 'repo/generators/94aa19deae60/generator.py'
sys.path.insert(0, str(ROOT / 'repo/shared/runtime'))
spec = importlib.util.spec_from_file_location('audit_target_94aa19deae60', SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
row = next(json.loads(line) for line in (ROOT / 'repo/shared/data/canonical/puzzles.jsonl').read_text().splitlines() if json.loads(line).get('task_id') == '94aa19deae60')
seed, sample_index, difficulty = 0, 0, 'medium'
overrides = {'texture': 'no_legend'}
grid = module.generate(seed, sample_index, difficulty=difficulty, **overrides)
errors = module.self_check(grid, difficulty=difficulty, meta=overrides)
(OUT / 'input.json').write_text(json.dumps(grid, indent=2) + '\n')
report = {
    'task_id': module.TASK_ID,
    'status': 'awaiting_public_racket_verification',
    'generator_path': str(SOURCE.relative_to(ROOT)),
    'generator_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'rule_source_path': 'repo/shared/data/canonical/puzzles.jsonl',
    'rule_hash_method': 'sha256 of UTF-8 program_solution, without added newline',
    'rule_sha256': hashlib.sha256(row['program_solution'].encode()).hexdigest(),
    'canonical_row_sha256_method': 'sha256 of JSON sorted keys, separators comma-colon, ensure_ascii=True',
    'canonical_row_sha256': hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
    'generation': {'seed': seed, 'sample_index': sample_index, 'difficulty': difficulty, 'overrides': overrides},
    'input_sha256': hashlib.sha256((OUT / 'input.json').read_bytes()).hexdigest(),
    'validator_result': {'method': 'self_check(grid, difficulty="medium", meta={"texture":"no_legend"})', 'errors': errors, 'accepted': not errors},
    'documented_domain_membership': {
        'advertised_override': 'AXES["texture"]["valid"] explicitly includes no_legend; DEGENERATE_TEXTURES also includes it.',
        'generated_by_advertised_api': True,
        'satisfies_normal_legend_invariant': False,
        'qualification': 'This is explicitly advertised degenerate support, not a counterexample inside the ordinary positive-legend domain. generate returns this grid and self_check explicitly accepts its declared texture.'
    },
    'expected_issue': 'The no_legend branch returns a grid with an empty top row. The canonical rule constructs no crops then evaluates (apply max ...), which has no arguments.',
    'commands': [{'argv': ['python3', 'checks/audit/94aa19deae60/reproduce.py'], 'cwd': str(ROOT), 'exit_code': 0}],
}
(OUT / 'generation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'shape': [len(grid), len(grid[0])], 'legend': [x for x in grid[0] if x], 'validator_errors': errors, 'generator_sha256': report['generator_sha256'], 'rule_sha256': report['rule_sha256']}))
