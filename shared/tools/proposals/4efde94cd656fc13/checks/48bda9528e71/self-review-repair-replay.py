"""Replay exactly the 8 retained findings against the repaired demo prefix."""
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _real_evaluator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / 'repo'
HOME = ROOT / 'generators/48bda9528e71/workspace/parametric'


def load(name):
    spec = importlib.util.spec_from_file_location('repair_' + name, HOME / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


a, f = load('adapter'), load('native_family')
findings = []
for path in ('self-review-racket.json',):
    report = json.loads((HERE / path).read_text())
    findings += report['confirmed_findings']

apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
cache, rows = {}, []


def execute(program, grid):
    key = (program, json.dumps(grid, separators=(',', ':')))
    if key not in cache: cache[key] = apply(program, grid)
    return cache[key]


try:
    for finding in findings:
        setting, seed, name = finding['settings'], finding['seed'], finding['rival']
        rival = f.retained_rivals(setting)[name]
        assert rival == finding['program'], 'retained rival changed during repair'
        episode = a.generate(seed, setting, 3, 4)
        query = episode['test'][finding['query_index']]
        assert query['input'] == finding['input'], 'repair changed the failing query'
        assert query['output'] == finding['expected'], 'repair changed the reference answer'
        refutations = []
        for index, pair in enumerate(episode['train']):
            gold = execute(a.program(setting), pair['input'])
            prediction = execute(rival, pair['input'])
            assert gold == pair['output']
            if prediction != gold:
                refutations.append({'demo_index': index, 'input': pair['input'],
                                    'output': gold, 'prediction': prediction})
        assert refutations, 'observed shortcut still fits all repaired demonstrations'
        rows.append({'seed': seed, 'settings': setting, 'rival': name,
                     'program_sha256': hashlib.sha256(rival.encode()).hexdigest(),
                     'query_index': finding['query_index'], 'query_unchanged': True,
                     'refutations': refutations})
finally:
    bridge.close()

result = {'status': 'passed', 'scope': 'Only the 8 retained independent findings, with three demos and unchanged queries',
          'racket': identity, 'cases': rows, 'protected_executions': len(cache),
          'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(HOME.glob('*')) if p.suffix in ('.py', '.rkt', '.json')},
          'owner_acceptance': 'pending', 'training_admitted': False}
output = HERE / 'self-review-repair-replay.json'
if output.exists(): raise ValueError('repair replay destination must be new')
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'status': 'passed', 'cases': len(rows), 'protected_executions': len(cache)}))
