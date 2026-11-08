"""Read-only, source-bound frame-content generator audit."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for ancestor in HERE.parents:
    candidates = (ancestor / 'repo/shared/runtime', ancestor / 'shared/runtime', ancestor)
    found = next((p for p in candidates if (p / 'reviewer_support.py').is_file()), None)
    if found:
        sys.path.insert(0, str(found))
        break
else:
    raise ImportError('No local reviewer_support runtime')
from reviewer_support import find_root, load_selected_generator, canonical_path

ROOT = find_root(__file__)
g, source, source_hash = load_selected_generator('92074aefc590', root=ROOT)
expected = '0bcd802c52cd5a30940cc0ee214f37d1804e6b4b8699a9ccd05f9d30c5f13755'
assert source_hash == expected
programs = {r['program_solution'] for r in map(json.loads, canonical_path(ROOT).read_text().splitlines())
            if r.get('task_id') == g.TASK_ID}
assert len(programs) == 1
program = programs.pop()
input_grid = [[2, 5, 0], [0, 0, 0], [0, 0, 0]]
assert g.self_check(input_grid) == []
(HERE / 'input.json').write_text(json.dumps(input_grid) + '\n')
failures = []
checked = 0
for seed in range(5000):
    checked += 1
    try:
        grid = g.generate(seed, 0, difficulty='easy')
    except Exception as exc:
        failures.append({'seed': seed, 'sample_index': 0, 'difficulty': 'easy',
                         'overrides': {}, 'exception_type': type(exc).__name__, 'message': str(exc)})
    if len(failures) >= 2:
        break
axis_probe = []
for n in (2, 5):
    grid = g.generate(0, 0, difficulty='medium', n=n)
    axis_probe.append({'n': n, 'input_sha256': hashlib.sha256(json.dumps(grid).encode()).hexdigest(),
                       'self_check_errors': g.self_check(grid)})
assert axis_probe[0]['input_sha256'] == axis_probe[1]['input_sha256']
receipt = {'schema': 'frame-content-audit-v1', 'task_id': g.TASK_ID,
           'generator_version': g.VERSION, 'generator_sha256': source_hash,
           'generator_source': str(source), 'canonical_rule_sha256': hashlib.sha256(program.encode()).hexdigest(),
           'canonical_rule_normalized_sha256': hashlib.sha256(' '.join(program.split()).encode()).hexdigest(),
           'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'command_argv': [sys.executable, str(Path(__file__).resolve())], 'cwd': str(Path.cwd()),
           'validator_counterexample': {'input': input_grid, 'self_check_errors': g.self_check(input_grid),
               'nonzero_color_count': 2, 'frame_count': 0,
               'rival_name': 'empty_canvas', 'rival_output': [[0] * 3 for _ in range(3)],
               'domain': 'Accepted by validator; outside documented generated frame/content domain'},
           'default_easy_census': {'seed_range_inclusive': [0, checked-1], 'sample_index': 0,
               'checked': checked, 'failure_count': len(failures), 'failures': failures,
               'unique_generated_successes_counted': False,
               'stopping_policy': 'Stop after two exceptions or 5000 sequential seeds'},
           'ignored_n_override': axis_probe,
           'limits': ['No broad lesson census or arbitrary-rival identification claim.',
                      'Racket labels are obtained separately with the supported arcpuzzles apply command.',
                      'No generator, reference-rule, shared-tool, or blind-solve data changes.']}
if (HERE / 'racket.json').is_file():
    racket_bytes = (HERE / 'racket.json').read_bytes()
    racket = json.loads(racket_bytes)
    assert racket['generator_sha256'] == source_hash
    # Public apply hashes the materialized callable text separately from the
    # raw ledger program; bind the source through its normalized rule hash.
    assert racket['executed_rule_hash'] == receipt['canonical_rule_normalized_sha256'][:12]
    assert racket['results'][0]['input'] == input_grid
    assert racket['results'][0]['error'] is None
    actual = racket['results'][0]['output']
    assert actual == receipt['validator_counterexample']['rival_output']
    receipt['validator_counterexample']['actual_racket_output'] = actual
    receipt['racket_evidence'] = {'path': 'racket.json',
        'sha256': hashlib.sha256(racket_bytes).hexdigest(),
        'materialized_callable_sha256': racket['rule_text_sha256'],
        'rule_hash': racket['executed_rule_hash'], 'command': racket['command'], 'cwd': racket['cwd']}
(HERE / 'probe.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'checked': checked, 'failures': failures, 'validator_errors': g.self_check(input_grid)}))
