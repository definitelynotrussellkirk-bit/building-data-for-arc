"""Reproduce a declared-rival ambiguity after rotating an ordinary query."""
from pathlib import Path
import hashlib
import json
import types

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs

ROOT = Path.cwd()
TASK = '77e696585932'
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
OUT = Path(__file__).resolve().parent
SHA = 'be2ae4aed1cf23cb1fa18aa1223202c215df7a8e865277e308ec16b4a6dbc1b9'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SHA
gen = types.ModuleType('audit_full_lines_subject')
gen.__file__ = str(SOURCE)
exec(compile(SOURCE.read_bytes(), str(SOURCE), 'exec'), gen.__dict__)

seed, band = 4107, 'medium'
start = next(i for i in range(3) if gen.schedule_profile(seed, i, band) == 'rows')
indices = list(range(start, start + 4))
grids = [gen.generate(seed, i, difficulty=band) for i in indices]
profiles = [gen.observe_overrides(grid)['scene_profile'] for grid in grids]
assert profiles == ['rows', 'columns', 'cross', 'rows']
canonical = canonical_pairs(TASK, root=ROOT)
reference = Catalog(ROOT).apply(TASK, grids + [pair['input'] for pair in canonical],
                                allow_unapproved=True)
assert reference['executed_rule_hash'] == gen.RULE_HASH == '315cb8671701'
assert reference['rule_hash_matches_catalog']
outputs = [result['output'] for result in reference['results']]
assert all(output is not None for output in outputs)
pairs = [{'input': grid, 'output': output} for grid, output in zip(grids, outputs[:4])]
assert all(gen.self_check(grid) == gen.strict_canonical_like(grid) == [] for grid in grids)
assert all(gen._expected_output(pair['input']) == pair['output'] for pair in pairs)
assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []

query_index = 2
demos = [pair for i, pair in enumerate(pairs) if i != query_index]
query = pairs[query_index]
rival = gen.LESSON_COMPETITORS['tie_to_column']
predictions = [rival(grid) for grid in grids]
assert all(predictions[i] == pairs[i]['output'] for i in (0, 1, 3))
assert predictions[2] != query['output']
differences = [[r, c, query['output'][r][c], predictions[2][r][c]]
               for r in range(len(query['input']))
               for c in range(len(query['input'][0]))
               if query['output'][r][c] != predictions[2][r][c]]
assert differences
rotated_reasons = gen.lesson_identifiable(demos, query)
assert rotated_reasons
canon_evidence = []
for pair, result in zip(canonical, reference['results'][4:]):
    assert pair['output'] == result['output']
    canon_evidence.append({**pair, 'racket_output': result['output'],
                           'rival_prediction': rival(pair['input']),
                           'rival_matches': rival(pair['input']) == result['output']})
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SHA

evidence = {
    'task_id': TASK, 'source_sha256': SHA, 'rule_hash': gen.RULE_HASH,
    'classification': 'reproduced_query_rotation_ambiguity',
    'finding': 'A four-pair ordinary lesson can contain only one cross tie witness. Holding that cross out leaves a declared tie-to-column rival consistent with every demonstration but wrong on the query.',
    'parameters': {'seed': seed, 'difficulty': band, 'sample_indices': indices, 'overrides': {}},
    'production_demo_indices': indices[:3], 'production_query_index': indices[3],
    'production_lesson_identifiable': [],
    'rotated_demo_indices': [indices[i] for i in (0, 1, 3)],
    'rotated_query_index': indices[2], 'rotated_lesson_identifiable': rotated_reasons,
    'rival_name': 'tie_to_column', 'rival_fits_rotated_demos': True,
    'rival_changes_query': True, 'query_cell_differences': differences,
    'samples': [{'sample_index': i, 'input': pair['input'], 'racket_output': pair['output'],
                 'rival_prediction': prediction, 'profile': profile,
                 'self_check': [], 'strict_canonical_like': []}
                for i, pair, prediction, profile in zip(indices, pairs, predictions, profiles)],
    'canonical_pairs': canon_evidence,
    'reference_receipt': {k: v for k, v in reference.items() if k != 'results'},
    'bounded_scope': {'generated_draws': 4, 'canonical_pairs': len(canonical),
                      'racket_inputs': len(grids) + len(canonical)},
    'limits': [
        'The native original orientation is identifiable: three scheduled demos cover all three profiles.',
        'The rotated guard correctly warns about missing cross and tie witnesses; it does not falsely claim acceptance.',
        'This is susceptibility to query rotation, not a wrong official label or failure of the original production lesson.',
        'No repair or source mutation was performed; no full battery or large scan was run.'
    ],
    'command_receipt': 'checks/audit/77e696585932/command/receipt.json',
}
(OUT / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
print(json.dumps({key: evidence[key] for key in (
    'task_id', 'classification', 'source_sha256', 'parameters', 'rotated_demo_indices',
    'rotated_query_index', 'rotated_lesson_identifiable', 'query_cell_differences',
    'bounded_scope')}, indent=2))
