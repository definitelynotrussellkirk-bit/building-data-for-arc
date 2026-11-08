"""Bounded findings-only audit: an admitted lesson can hide color-8 semantics."""
from pathlib import Path
import hashlib
import importlib.util
import json

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs

TASK = 'cbe60e2c4b18'
ROOT = Path.cwd()
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_cbe_generator', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def ignore_input_azure(grid):
    """Aligned intersection, treating input color 8 as background."""
    width = (len(grid[0]) - 1) // 2
    return [[8 if grid[r][c] not in (0, 8, 9)
             and grid[r][c + width + 1] not in (0, 8, 9) else 0
             for c in range(width)] for r in range(len(grid))]

seed, band, indices = 703, 'medium', list(range(3, 8))
grids = [gen.generate(seed, i, difficulty=band) for i in indices]
canonical = canonical_pairs(TASK, root=ROOT)
catalog = Catalog(ROOT)
applied = catalog.apply(TASK, grids + [p['input'] for p in canonical])
assert applied['executed_rule_hash'] == gen.RULE_HASH
assert applied['rule_hash_matches_catalog']
results = applied['results']
assert all(r['output'] is not None for r in results), results
labels = [r['output'] for r in results[:5]]
demos = [{'input': g, 'output': y} for g, y in zip(grids[:4], labels[:4])]
query = {'input': grids[4], 'output': labels[4]}
predictions = [ignore_input_azure(g) for g in grids]
assert all(p == y for p, y in zip(predictions[:4], labels[:4]))
assert predictions[4] != labels[4]
assert gen.lesson_identifiable(demos, query) == []
assert all(gen.self_check(g) == [] for g in grids)
assert all(result['output'] == pair['output'] == ignore_input_azure(pair['input'])
           for result, pair in zip(results[5:], canonical))
assert all(gen.rule_mirror(g) == y for g, y in zip(grids, labels))
evidence = {
    'task_id': TASK,
    'classification': 'reproduced_lesson_ambiguity',
    'finding': 'Input color 8 can be treated as transparent throughout an accepted four-demo lesson, but that rival changes its ordinary query answer.',
    'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'rule_hash': gen.RULE_HASH,
    'scope': 'One ordinary sliding lesson, five generated grids plus all three canonical labeled pairs; no overrides or source changes.',
    'parameters': {'seed': seed, 'difficulty': band, 'sample_indices': indices, 'overrides': {}},
    'lesson_identifiable': gen.lesson_identifiable(demos, query),
    'rival_definition': 'Intersect aligned supports after treating input values 0, 8, and 9 as background; render surviving cells in 8.',
    'samples': [{'sample_index': i, 'input': g, 'racket_output': y,
                 'rival_prediction': p, 'rival_matches': p == y,
                 'observed': gen.observe_overrides(g), 'self_check': gen.self_check(g)}
                for i, g, y, p in zip(indices, grids, labels, predictions)],
    'canonical_pairs': [{'variant': p['variant'], 'split': p['split'],
                         'pair_index': p['pair_index'], 'input': p['input'],
                         'recorded_output': p['output'], 'racket_output': r['output'],
                         'rival_prediction': ignore_input_azure(p['input'])}
                        for p, r in zip(canonical, results[5:])],
    'reference_receipt': {k: v for k, v in applied.items() if k != 'results'},
    'limitations': [
        'No wrong official labels found: Python mirror and Racket agree for all five generated inputs.',
        'This rival is not declared in LESSON_COMPETITORS. Notes already limit finite-rival and palette-pair universality claims.',
        'No claim about every production episode or all seeds; this is one exact accepted ordinary lesson.'
    ],
}
(OUT / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
print(json.dumps({'classification': evidence['classification'],
                  'source_sha256': evidence['source_sha256'], 'rule_hash': gen.RULE_HASH,
                  'demos_fit': True, 'query_differs': True,
                  'lesson_identifiable': [], 'evidence': str(OUT / 'evidence.json')}, indent=2))
