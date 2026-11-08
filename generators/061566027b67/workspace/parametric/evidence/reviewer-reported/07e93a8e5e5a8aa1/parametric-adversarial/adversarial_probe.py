"""Independent task-local rejection probes; run: python adversarial_probe.py REPO_ROOT.
No generated-label success is claimed: these checks do not run real Racket.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

root = Path(sys.argv[1]).resolve()
path = root / 'generators/061566027b67/workspace/parametric/rectangle_modes.py'
spec = importlib.util.spec_from_file_location('adversarial_rectangle_modes', path)
p = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = p
spec.loader.exec_module(p)
passed = []

def rejects(name, fn, kinds=(ValueError, TypeError)):
    try:
        fn()
    except kinds:
        passed.append(name)
    else:
        raise AssertionError('unexpected acceptance: ' + name)

for bad in (True, 1.0, '1', None):
    rejects('invalid_seed_' + repr(bad), lambda: p.build_episode(bad))
rejects('invalid_parameter_object', lambda: p.build_episode(1, {'shape_mode': 'solid'}))
generator = p._source()[0]
grid = generator.generate(1300615, 0, rectangle_profile='3x3_tab', winner_color=4)
other = generator.generate(1300615, 1, rectangle_profile='3x4_tab', winner_color=7)
params = p.Parameters()
train = [{'input': grid, 'output': p.solve_python(grid, params)}]
for bad in (None, [], {}, [None], [{'input': grid}], [{'input': grid, 'output': [[0]]}]):
    rejects('bad_certificate_train_' + str(len(passed)), lambda: p.demo_certificate(bad, [other], params))
for bad in (None, [], {}, [[[0]]]):
    rejects('bad_certificate_query_' + str(len(passed)), lambda: p.demo_certificate(train, bad, params))
wrong = copy.deepcopy(train)
wrong[0]['output'] = [[0] * 16 for _ in range(16)]
rejects('inconsistent_demo_label', lambda: p.demo_certificate(wrong, [other], params))
cert = p.demo_certificate(train, [grid, other], params)
assert len(cert['survivors']) == 2
assert cert['per_query'][0]['identified'] is True
assert cert['per_query'][1]['identified'] is False
passed.append('query_agreement_distinct_from_unique_parameters')

# Retry exhaustion must raise before the bridge is accessed, and must be bounded.
original_source = p._source
calls = []
class RepeatingSource:
    RECTANGLE_PROFILES = generator.RECTANGLE_PROFILES
    self_check = staticmethod(generator.self_check)
    def generate(self, *args, **kwargs):
        calls.append((args, kwargs))
        return grid
try:
    p._source = lambda: (RepeatingSource(), None, None)
    rejects('bounded_distinct_input_exhaustion', lambda: p._build_episode(1, params, 2, 1, None), (RuntimeError,))
    assert len(calls) == 65, len(calls)
finally:
    p._source = original_source

for value in (None, [], [grid, grid], [[[True] * 16 for _ in range(16)]], [[[0]]]):
    bridge = SimpleNamespace(eval_text=lambda expr, value=value: value)
    rejects('malformed_bridge_output_' + str(len(passed)), lambda: p._racket_outputs([grid], p.canonical_program(), bridge), (RuntimeError, ValueError))

with tempfile.TemporaryDirectory() as temporary:
    base = Path(temporary)
    episode = {'train': train, 'test': [{'input': other, 'output': p.solve_python(other, params)}]}
    bad = copy.deepcopy(episode)
    bad['test'][0]['input'][0][0] = True
    private_bad = dict(episode, unserializable=object())
    for index, episodes in enumerate(([bad], [private_bad], [episode, copy.deepcopy(episode)])):
        target = base / str(index)
        rejects('writer_preflight_' + str(index), lambda: p.write_batch(episodes, target))
        assert not target.exists()
    target = base / 'good'
    receipt = p.write_batch([episode], target)
    public = next((target / 'public').glob('*.json'))
    body = public.read_bytes()
    assert public.stem == hashlib.sha256(body).hexdigest()
    assert list(json.loads(body)['test'][0]) == ['input']
    assert receipt['public'][0]['id'] == public.stem
    passed.append('writer_hash_and_query_privacy')
print(json.dumps({'status': 'passed', 'checks': passed, 'real_racket_executed': False,
                  'prototype_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}, sort_keys=True))
