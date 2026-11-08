"""Findings-only audit; no reference evaluator imports or source changes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'repo/shared/runtime'))
GENERATOR_PATH = ROOT / 'repo/generators/1bc09b475319/generator.py'
PIN = '3d9835756a2a0d9d692df242abd2cff7aa5928eacb08e008829faeb1c1ac2445'
sha = lambda data: hashlib.sha256(data).hexdigest()
assert sha(GENERATOR_PATH.read_bytes()) == PIN
spec = importlib.util.spec_from_file_location('audit_generator', GENERATOR_PATH)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def rival(grid):
    # Same palette and horizontal axis, but no >=2 consecutive-6 condition.
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == 0 and ((c > 0 and row[c-1] == 6) or
                           (c+1 < len(row) and row[c+1] == 6)):
                out[r][c] = 8
    return out

def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + '\n')

if sys.argv[1] == 'prepare':
    cases = []
    seed = 'audit-1bc09b475319-horizontal-single-neighbor'
    for band in ('easy', 'medium', 'hard'):
        for i in range(20):
            g = gen.generate(seed, i, difficulty=band)
            cases.append({'source': 'generated-default', 'seed': seed,
                          'sample_index': i, 'difficulty': band, 'overrides': {},
                          'self_check_errors': gen.self_check(g, difficulty=band),
                          'documented_generator_domain': True, 'input': g})
    g = gen.generate(seed, 0, difficulty='medium', texture='length_one_bars')
    cases.append({'source': 'generated-explicit-degenerate', 'seed': seed,
                  'sample_index': 0, 'difficulty': 'medium',
                  'overrides': {'texture': 'length_one_bars'},
                  'self_check_errors': gen.self_check(g, difficulty='medium', meta={'texture': 'length_one_bars'}),
                  'self_check_errors_without_meta': gen.self_check(g, difficulty='medium'),
                  'documented_generator_domain': True, 'default_generation_domain': False, 'input': g})
    matching = []
    for line in (ROOT / 'repo/shared/data/canonical/puzzles.jsonl').read_text().splitlines():
        d = json.loads(line)
        if d.get('task_id') == '1bc09b475319':
            matching.append(d)
    assert len(matching) == 1
    d = matching[0]
    for split in ('train', 'test'):
        for i, pair in enumerate(d.get(split, [])):
            cases.append({'source': 'canonical', 'split': split, 'pair_index': i,
                          'self_check_errors': gen.self_check(pair['input']),
                          'input': pair['input'], 'canonical_output': pair['output']})
    assert len(cases) == 64
    save('input.json', {'inputs': [c['input'] for c in cases]})
    save('cases.json', {'task_id': '1bc09b475319', 'generator_sha256': PIN,
                        'canonical_rule_sha256': sha(d['program_solution'].encode()),
                        'cases': cases})
    print('Prepared 60 default draws, one generated singleton degenerate, three canonical pairs.')
elif sys.argv[1] == 'compare':
    report = json.loads((HERE/'racket.json').read_text())
    print('Reference report top-level fields:', list(report))
    # Supported apply reports list per-input actual results under results.
    records = report['results']
    cases_report = json.loads((HERE/'cases.json').read_text())
    cases = cases_report['cases']
    assert len(records) == len(cases) == 64
    differences = []
    agreements = []
    for i, (case, record) in enumerate(zip(cases, records)):
        actual = record['output']
        prediction = rival(case['input'])
        if 'canonical_output' in case:
            assert actual == case['canonical_output']
        changed = [[r,c] for r,row in enumerate(actual) for c,v in enumerate(row) if prediction[r][c] != v]
        result = {'case_index': i, 'source': case['source'], 'rival_output': prediction,
                  'actual_racket_output': actual, 'differing_cells': changed}
        (differences if changed else agreements).append(result)
    assert len(differences) == 1 and differences[0]['case_index'] == 60
    assert len(agreements) == 63
    witness = dict(cases[60])
    witness.update(differences[0])
    witness.update({'task_id': '1bc09b475319', 'generator_sha256': PIN,
                    'canonical_rule_sha256': cases_report['canonical_rule_sha256'],
                    'reference_metadata': {k:v for k,v in report.items() if k != 'results'},
                    'reference_command': ['python3','run_with_racket.py','python3','-m','arcpuzzles','apply','1bc09b475319','--input','../checks/audit/1bc09b475319/input.json','--out','../checks/audit/1bc09b475319/racket.json'],
                    'reference_command_cwd': 'packet_root', 'reference_payload_cwd': 'repo'})
    save('witness.json', witness)
    save('summary.json', {'task_id': '1bc09b475319', 'generator_sha256': PIN,
                         'canonical_rule_sha256': cases_report['canonical_rule_sha256'],
                         'generated_default_agreements': 60, 'canonical_agreements': 3,
                         'generated_degenerate_disagreements': 1,
                         'all_self_check_accept': all(not c['self_check_errors'] for c in cases),
                         'unique_inputs': len({json.dumps(c['input']) for c in cases}),
                         'differences': differences})
    print('Rival matches 60/60 default draws and 3/3 canonical pairs; differs on generated singleton degenerate.')
else:
    raise ValueError(sys.argv[1])
