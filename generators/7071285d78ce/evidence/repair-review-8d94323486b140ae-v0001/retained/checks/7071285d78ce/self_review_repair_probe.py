"""Narrow protected replay of the preserved 7071285d78ce teaching gaps.

Run from the packet root through review.py; inputs and labels remain private.
This probe does not alter generator source or the preserved original finding.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _real_evaluator


ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
RELATIVE_HOME = Path('generators/7071285d78ce/workspace/parametric')
HOME = ROOT / RELATIVE_HOME
ORIGINAL = HERE / 'self-review-nonsquare-v1'


def sha(value):
    return hashlib.sha256(value).hexdigest()


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bindings():
    paths = sorted(p for p in HOME.glob('*') if p.suffix in ('.py', '.rkt', '.json'))
    paths += sorted((HOME.parents[1] / 'tests').glob('test_native_*.py'))
    return {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in paths}


def compare(execute, program, rival, episode):
    records = []
    for split in ('train', 'test'):
        for index, pair in enumerate(episode[split]):
            intended = execute(program, pair['input'])
            predicted = execute(rival, pair['input'])
            assert intended == pair['output'], ('intended_label', split, index)
            changes = [[r, c] for r, row in enumerate(intended) for c, value in enumerate(row)
                       if value != predicted[r][c]]
            records.append({'split': split, 'index': index, 'different': bool(changes),
                            'input_sha256': sha(raw(pair['input'])),
                            'intended_output': intended, 'intended_output_sha256': sha(raw(intended)),
                            'rival_output': predicted, 'rival_output_sha256': sha(raw(predicted)),
                            'changed_positions': changes})
    return records


original_bytes = (ORIGINAL / 'finding.json').read_bytes()
original = json.loads(original_bytes)
for path, digest in original['source_sha256'].items():
    assert sha((ORIGINAL / 'source' / path).read_bytes()) == digest, path
family = load(HOME / 'native_family.py', 'repaired707_family')
adapter = load(HOME / 'adapter.py', 'repaired707_adapter')
old_family = load(ORIGINAL / 'source' / RELATIVE_HOME / 'native_family.py', 'preserved707_family')
current_binding = bindings()
settings = {'selection': 'smallest'}
repaired_episode = adapter.generate(0, settings, 3, 4)
program = adapter.program(settings)
assert program == original['intended_program'] == old_family.program(settings)
assert repaired_episode['test'] == original['episode']['test']
nonsquare = family.rivals(settings)['nonsquare_objects_only']
assert nonsquare == original['rival_program']
size_five = family.rivals(settings)['source_size_at_most_five']
old_size_five = '(rule! (lambda (g) ' + old_family.selection_body(
    old_family.local_body(condition='(<= (obj-size obj) 5)'), 'smallest') + '))'
assert size_five == old_size_five

apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
assert identity['backend'] == 'racket' and identity['protected'] is True
executions = 0


def execute(source, grid):
    global executions
    executions += 1
    return apply(source, grid)


try:
    repaired_records = compare(execute, program, nonsquare, repaired_episode)
    original_size_records = compare(execute, program, size_five, original['episode'])
    size_five_repair_prediction = execute(size_five, repaired_episode['train'][1]['input'])
finally:
    bridge.close()

repaired_demo_refutations = [row['index'] for row in repaired_records
                            if row['split'] == 'train' and row['different']]
original_size_conflicts = [row['index'] for row in original_size_records
                          if row['split'] == 'test' and row['different']]
assert repaired_demo_refutations == [1]
assert not any(row['different'] for row in original_size_records if row['split'] == 'train')
assert original_size_conflicts == original['conflicting_queries']
assert size_five_repair_prediction != repaired_episode['train'][1]['output']
assert current_binding == bindings()
result = {
    'task_id': '7071285d78ce', 'status': 'confirmed_original_gaps_repaired',
    'scope': 'Seed zero, smallest selection, preserved original and repaired three-demo/four-query lesson only.',
    'racket': identity, 'protected_executions': executions,
    'original_finding_path': str((ORIGINAL / 'finding.json').relative_to(ROOT.parent)),
    'original_finding_sha256': sha(original_bytes),
    'original_source_sha256': original['source_sha256'],
    'current_source_sha256': current_binding, 'current_source_unchanged': True,
    'rival_builder_identity': {
        'path': str(RELATIVE_HOME / 'native_family.py'),
        'original_sha256': original['source_sha256'][str(RELATIVE_HOME / 'native_family.py')],
        'current_sha256': current_binding[str(RELATIVE_HOME / 'native_family.py')],
        'original_and_current_size_five_program_identical': True,
    },
    'probe_sha256': sha(Path(__file__).read_bytes()),
    'seed': 0, 'settings': settings, 'intended_program': program,
    'intended_program_sha256': sha(program.encode()), 'intended_program_unchanged': True,
    'all_four_query_inputs_and_labels_unchanged': True,
    'original_episode': original['episode'], 'repaired_episode': repaired_episode,
    'repaired_nonsquare': {
        'rival_program': nonsquare, 'rival_program_sha256': sha(nonsquare.encode()),
        'demo_refutations': repaired_demo_refutations, 'records': repaired_records,
    },
    'original_source_size_at_most_five': {
        'rival_program': size_five, 'rival_program_sha256': sha(size_five.encode()),
        'all_three_demonstrations_fit': True, 'conflicting_queries': original_size_conflicts,
        'records': original_size_records,
    },
    'repaired_source_size_at_most_five': {
        'refuting_demo_index': 1, 'rival_output': size_five_repair_prediction,
        'rival_output_sha256': sha(raw(size_five_repair_prediction)),
        'intended_output_sha256': sha(raw(repaired_episode['train'][1]['output'])),
    },
    'interpretation': 'Private diagnostic counterexamples; rivals are not official extra answers. '
                      'The repaired second demonstration refutes both rivals without changing any query.',
}
output = HERE / 'self-review-repair-proof.json'
assert not output.exists()
output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'status': result['status'], 'protected_executions': executions,
                  'nonsquare_refuting_demo_index': repaired_demo_refutations,
                  'old_size_five_conflicting_queries': original_size_conflicts,
                  'new_size_five_refuting_demo_index': 1,
                  'all_four_queries_unchanged': True, 'path': str(output)}))
