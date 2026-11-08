"""Freeze baseline and confirm all observed color shortcuts with protected Racket."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

from arcpuzzles.parametric_worker import _real_evaluator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / 'repo'
HOME = ROOT / 'generators/48bda9528e71/workspace/parametric'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


f = load(HOME / 'native_family.py', 'independent_projection_family')
rivals = load(HERE / 'self-review-rivals.py', 'independent_projection_rivals')
report = json.loads((HERE / 'self-review-report.json').read_text())
assert all(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha
           for path, sha in report['source_sha256'].items())
snapshot = HERE / 'self-review-baseline'
snapshot.mkdir(exist_ok=False)
paths = [ROOT / p for p in report['source_sha256']]
paths += [ROOT / 'generators/48bda9528e71/generator.py']
paths += sorted((ROOT / 'generators/48bda9528e71/tests').glob('test_native_*.py'))
manifest = {}
for source in paths:
    relative = source.relative_to(ROOT)
    dest = snapshot / relative; dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)
    manifest[str(relative)] = hashlib.sha256(source.read_bytes()).hexdigest()
(snapshot / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
rows = []; evaluations = 0
try:
    for finding in report['findings']:
        setting = finding['settings']
        program = rivals.programs(f, setting)[finding['rival']]
        demo_outputs = [apply(program, pair['input']) for pair in finding['demos']]
        intended = apply(f.program(setting), finding['input'])
        prediction = apply(program, finding['input']); evaluations += 5
        assert demo_outputs == [pair['output'] for pair in finding['demos']]
        assert intended == finding['expected'] and prediction == finding['rival_output']
        assert intended != prediction
        rows.append({**finding, 'program': program,
            'program_sha256': hashlib.sha256(program.encode()).hexdigest(),
            'executed_demo_outputs': demo_outputs, 'executed_reference_query': intended,
            'executed_rival_query': prediction, 'confirmed': True})
finally:
    bridge.close()
result = {'schema': 'bounded-independent-projection-racket-review-v1',
          'source_sha256': report['source_sha256'], 'backend_identity': identity,
          'scope': 'Only eight observed seed/setting color-selection findings from the 44-comparison Python review.',
          'confirmed_findings': rows, 'protected_evaluations': evaluations,
          'conclusion': 'The three-demo prefix admits color-selection shortcuts with different query outputs.'}
out = HERE / 'self-review-racket.json'
if out.exists(): raise ValueError('choose a new evidence destination')
out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'confirmed': len(rows), 'protected_evaluations': evaluations,
                  'rivals': sorted({row['rival'] for row in rows})}))
