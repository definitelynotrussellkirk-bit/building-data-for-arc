"""Focused source-bound ordered-lesson ambiguity probe; never edits sources."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

TASK = 'a85b9271a0ee'
REPO = Path.cwd()
OUT = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + '\n')

def generator():
    spec = importlib.util.spec_from_file_location('audit_generator', REPO / 'generators' / TASK / 'generator.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def wrap(grid):
    h, w = len(grid), len(grid[0])
    result = [[0] * w for _ in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                result[(r + 1) % h][(c + 1) % w] = value
    return result

def diff(left, right):
    return [{'row': r, 'column': c, 'reference': left[r][c], 'rival': right[r][c]}
            for r in range(len(left)) for c in range(len(left[0])) if left[r][c] != right[r][c]]

def prepare():
    mod = generator()
    canonical_line = next(line for line in (REPO / 'shared/data/canonical/puzzles.jsonl').read_bytes().splitlines()
                          if json.loads(line).get('task_id') == TASK)
    canonical = json.loads(canonical_line)
    hashes = {'generator_sha256': sha(REPO / 'generators' / TASK / 'generator.py'),
              'generator_version': mod.VERSION, 'declared_rule_hash': mod.RULE_HASH,
              'canonical_row_sha256': hashlib.sha256(canonical_line).hexdigest(),
              'canonical_program_text_sha256': hashlib.sha256(canonical['program_solution'].encode()).hexdigest(),
              'normalized_rule_hash': hashlib.sha256(' '.join(canonical['program_solution'].split()).encode()).hexdigest()[:12],
              'base_rule_sha256': sha(REPO / 'shared/data/base/solutions/banks/276b5e4c56a1/easy_b05__a85b9271a0ee.json')}
    cases = []
    for i, pair in enumerate(canonical['train'] + canonical['test']):
        cases.append({'origin': 'canonical', 'canonical_pair_index': i, 'input': pair['input'], 'stored_output': pair['output']})
    screening = []
    selected = []
    for band in ('easy', 'medium', 'hard'):
        for seed in range(32):
            grids = [mod.generate(seed, i, difficulty=band) for i in range(4)]
            observed = [mod.observe_overrides(g) for g in grids]
            validators = [mod.self_check(g, difficulty=band) for g in grids]
            edge_modes = [o['edge_mode'] for o in observed]
            ambiguous = edge_modes == ['in_bounds', 'in_bounds', 'in_bounds', 'mixed']
            screening.append({'seed': seed, 'sample_indices': [0, 1, 2, 3], 'difficulty': band,
                              'overrides': {}, 'edge_modes': edge_modes, 'validator_results': validators,
                              'wrap_ambiguity_candidate': ambiguous})
            if ambiguous and not any(s['difficulty'] == band for s in selected):
                selection = {'seed': seed, 'sample_index': 0, 'sample_indices': [0, 1, 2, 3],
                             'difficulty': band, 'overrides': {}, 'n_train': 3, 'n_test': 1,
                             'input_indices': list(range(len(cases), len(cases) + 4))}
                selected.append(selection)
                for i, grid in enumerate(grids):
                    cases.append({'origin': 'generated', 'seed': seed, 'sample_index': i,
                                  'difficulty': band, 'overrides': {}, 'role': 'demo' if i < 3 else 'query',
                                  'observed': observed[i], 'validator_result': validators[i], 'input': grid})
    assert selected, 'No witness in finite screen'
    write('source_hashes.json', hashes)
    write('screening.json', {'scope': '32 seeds per band; sample indices 0..3; no overrides; no reference claims',
                             'lessons': screening, 'selected': selected})
    write('cases.json', cases)
    write('input.json', [case['input'] for case in cases])
    print(json.dumps({'screened_lessons': len(screening), 'selected': selected,
                      'ambiguity_candidates': sum(s['wrap_ambiguity_candidate'] for s in screening)}))

def materialize():
    from arcpuzzles import Catalog
    catalog = Catalog()
    selections = json.loads((OUT / 'screening.json').read_text())['selected']
    cases = json.loads((OUT / 'cases.json').read_text())
    episodes = []
    for selection in selections:
        episode = catalog.generate(TASK, count=1, seed=selection['seed'], sample_index=0,
                                   difficulty=selection['difficulty'], n_train=3, n_test=1, allow_unapproved=True)[0]
        assert episode['sample_indices'] == [0, 1, 2, 3]
        assert not episode['rejections']
        assert [p['input'] for p in episode['train'] + episode['test']] == [cases[i]['input'] for i in selection['input_indices']]
        episodes.append(episode)
    write('production.json', episodes)
    print(json.dumps({'production_episodes': len(episodes), 'sample_indices': [e['sample_indices'] for e in episodes],
                      'rejections': [e['rejections'] for e in episodes]}))

def analyze():
    receipt = json.loads((OUT / 'racket.json').read_text())
    print(json.dumps({'receipt_keys': list(receipt)}))
    cases = json.loads((OUT / 'cases.json').read_text())
    rows = receipt['results']
    assert len(rows) == len(cases)
    for i, (case, row) in enumerate(zip(cases, rows)):
        assert row.get('error') is None, row
        assert row['input'] == case['input']
        output = row['output']
        if 'stored_output' in case:
            assert output == case['stored_output']
        case['racket_output'] = output
        case['rival_output'] = wrap(case['input'])
        case['rival_diff'] = diff(output, case['rival_output'])
    productions = json.loads((OUT / 'production.json').read_text())
    selections = json.loads((OUT / 'screening.json').read_text())['selected']
    verdicts = []
    for selection, production in zip(selections, productions):
        lesson_cases = [cases[i] for i in selection['input_indices']]
        for case, pair in zip(lesson_cases, production['train'] + production['test']):
            assert case['racket_output'] == pair['output']
        demo_matches = [not c['rival_diff'] for c in lesson_cases[:3]]
        query_wrong = bool(lesson_cases[3]['rival_diff'])
        assert all(demo_matches) and query_wrong
        rotations = []
        for query in range(4):
            fits = all(not lesson_cases[i]['rival_diff'] for i in range(4) if i != query)
            rotations.append({'query_pair_index': query, 'rival_fits_remaining_three': fits,
                              'rival_wrong_on_query': bool(lesson_cases[query]['rival_diff']),
                              'ambiguity': fits and bool(lesson_cases[query]['rival_diff'])})
        verdicts.append({**selection, 'rival_matches_demos': demo_matches, 'query_wrong': query_wrong,
                         'query_diff': lesson_cases[3]['rival_diff'], 'query_rotations': rotations})
    hashes = json.loads((OUT / 'source_hashes.json').read_text())
    assert sha(REPO / 'generators' / TASK / 'generator.py') == hashes['generator_sha256']
    assert receipt['executed_rule_hash'] == hashes['declared_rule_hash'] == hashes['normalized_rule_hash']
    assert receipt['rule_hash_matches_catalog'] is True
    canonical_line = next(line for line in (REPO / 'shared/data/canonical/puzzles.jsonl').read_bytes().splitlines()
                          if json.loads(line).get('task_id') == TASK)
    assert hashlib.sha256(canonical_line).hexdigest() == hashes['canonical_row_sha256']
    assert sha(REPO / 'shared/data/base/solutions/banks/276b5e4c56a1/easy_b05__a85b9271a0ee.json') == hashes['base_rule_sha256']
    write('cases.json', cases)
    write('summary.json', {'task_id': TASK, 'source_hashes': hashes, 'racket_inputs': len(cases),
                           'canonical_wrap_matches': sum(not c['rival_diff'] for c in cases if c['origin'] == 'canonical'),
                           'ordered_production_ambiguous_lessons': len(verdicts), 'ordered_production_checked_lessons': len(verdicts),
                           'rotated_ambiguous_queries': sum(r['ambiguity'] for v in verdicts for r in v['query_rotations']),
                           'rotated_checked_queries': 4 * len(verdicts), 'lessons': verdicts,
                           'production_executed_rule_hashes': [e['executed_rule_hash'] for e in productions],
                           'source_integrity_after': 'unchanged generator; canonical exact outputs verified'})
    print(json.dumps({'verified_lessons': len(verdicts), 'racket_inputs': len(cases)}))

if __name__ == '__main__':
    {'prepare': prepare, 'materialize': materialize, 'analyze': analyze}[sys.argv[1]]()
