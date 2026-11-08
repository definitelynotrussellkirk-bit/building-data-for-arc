import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
WORK = ROOT / 'WORK'
REPO = WORK / 'repo'
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / 'shared/runtime'))
from puzzle_generators.base import set_ctx_observer

generator_path = REPO / 'generators/81897d424b35/generator.py'
authority_path = REPO / 'shared/data/base/solutions/banks/ecfb302aa617/easy_p06__81897d424b35.json'
spec = importlib.util.spec_from_file_location('audit_generator', generator_path)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
authority = json.loads(authority_path.read_text())

def sha(data):
    return hashlib.sha256(data).hexdigest()

def gravity(grid):
    out = [[0] * len(grid[0]) for _ in grid]
    for c in range(len(grid[0])):
        values = [row[c] for row in grid if row[c]]
        for r, value in enumerate(values, len(grid) - len(values)):
            out[r][c] = value
    return out

contexts = []
set_ctx_observer(contexts.append)
cases = []
for overrides in ({}, {'palette_size': 1}, {'n_distinct_colors': 1},
                  {'palette_kind': 'warm'}, {'palette_kind': 'cool'},
                  {'texture': 'warm'}, {'texture': 'cool'},
                  {'active_cols': 1}, {'texture': 'single_active_col'}):
    try:
        grid = generator.generate(1, 0, **overrides)
    except Exception as error:
        cases.append({'seed': 1, 'sample_index': 0, 'difficulty': None,
                      'overrides': overrides, 'exception': repr(error)})
        continue
    ctx = contexts[-1]
    cases.append({'seed': 1, 'sample_index': 0, 'difficulty': None,
                  'overrides': overrides, 'grid': grid,
                  'colors': sorted({x for row in grid for x in row if x}),
                  'self_check_errors': generator.self_check(grid),
                  'recorded_draws': ctx.recorded_draws(),
                  'overrides_used': ctx.overrides_used(),
                  'python_mirror_output': gravity(grid)})

samples = json.loads(authority['samples']['samples_text']) if 'samples' in authority else None
if samples is None:
    for value in authority.values():
        if isinstance(value, dict) and 'samples_text' in value:
            samples = json.loads(value['samples_text'])
            break
assert samples is not None
train_checks = [gravity(pair['input']) == pair['output'] for pair in samples['train']]
binding = {'generator_path': str(generator_path.relative_to(WORK)),
           'generator_sha256': sha(generator_path.read_bytes()),
           'authority_path': str(authority_path.relative_to(WORK)),
           'authority_file_sha256': sha(authority_path.read_bytes()),
           'rule_text_sha256': {key: sha(value.encode()) for obj in authority.values()
                               if isinstance(obj, dict) for key, value in obj.items()
                               if key in ('raw_code', 'target_code') and isinstance(value, str)},
           'review_index': 'absent', 'generator_version': generator.VERSION}
result = {'source_binding': binding, 'cases': cases,
          'canonical_train_python_mirror_matches': {'passed': sum(train_checks), 'total': len(train_checks)},
          'canonical_test_inputs_inspected': len(samples['test']),
          'python_mirror_is_not_authoritative': True}
(OUT / 'probe.json').write_text(json.dumps(result, indent=2) + '\n')
(OUT / 'input.json').write_text(json.dumps(cases[1]['grid']) + '\n')
print(json.dumps({'source_binding': binding, 'case_count': len(cases),
                  'palette_size_1_colors': cases[1]['colors'],
                  'palette_size_1_selfcheck': cases[1]['self_check_errors'],
                  'canonical_train_matches': result['canonical_train_python_mirror_matches']}))
