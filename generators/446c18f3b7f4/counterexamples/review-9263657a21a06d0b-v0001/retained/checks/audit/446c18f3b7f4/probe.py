"""Small exact-control audit; selected sources remain unchanged."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / 'repo'
sys.path.insert(0, str(ROOT / 'shared/runtime'))
from reviewer_support import canonical_pairs, canonical_path, find_root

source = ROOT / 'generators/446c18f3b7f4/generator.py'
spec = importlib.util.spec_from_file_location('audited_generator', source)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
root = find_root(source)
records = [json.loads(line) for line in canonical_path(root).open()
           if json.loads(line).get('task_id') == gen.TASK_ID]
rule = records[0]['program_solution']
pairs = canonical_pairs(gen.TASK_ID, root=root)
rows = []
witness = None
for seed in range(4):
    overrides = {'grid_h': 11, 'grid_w': 11, 'n_frames': 3}
    grid = gen.generate(seed, 0, difficulty='medium', **overrides)
    count = len(gen._green_components(grid))
    row = {'seed': seed, 'sample_index': 0, 'difficulty': 'medium',
           'overrides': overrides, 'actual_frames': count,
           'validator_errors': gen.self_check(grid, difficulty='medium')}
    rows.append(row)
    if witness is None and count != 3:
        witness = {**row, 'input': grid}
        (HERE / 'input.json').write_text(json.dumps(grid) + '\n')
controls = []
for difficulty, overrides in [('medium', {'n_frames': 6}),
                              ('medium', {'grid_h': 5}),
                              ('easy', {'n_frames': 2})]:
    try:
        grid = gen.generate(0, 0, difficulty=difficulty, **overrides)
        outcome = {'returned': True, 'actual_frames': len(gen._green_components(grid))}
    except Exception as exc:
        outcome = {'returned': False, 'exception': type(exc).__name__, 'message': str(exc)}
    controls.append({'seed': 0, 'sample_index': 0, 'difficulty': difficulty,
                     'overrides': overrides, **outcome})
report = {'task_id': gen.TASK_ID,
          'generator_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'rule_sha256': hashlib.sha256(rule.encode()).hexdigest(),
          'rule_hash_basis': 'UTF-8 canonical program_solution, exact selected variant 0',
          'review_index_exists': (source.parent / 'evidence/review_index.json').exists(),
          'measured_draws': rows, 'count_witness': witness, 'rejected_controls': controls,
          'canonical_pairs': [{'variant': p['variant'], 'split': p['split'],
              'pair_index': p['pair_index'], 'shape': [len(p['input']), len(p['input'][0])],
              'frames': len(gen._green_components(p['input'])),
              'validator_errors': gen.self_check(p['input'])} for p in pairs],
          'semantic_labels': 'Obtain witness Racket output separately with public apply.'}
(HERE / 'probe.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('task_id', 'generator_sha256', 'rule_sha256', 'measured_draws', 'rejected_controls')}, indent=2))
assert witness is not None, 'No count discrepancy in selected small probe'
