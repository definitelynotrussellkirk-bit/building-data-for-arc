"""Confirm the retained lesson against public Racket apply and generation receipts."""
from pathlib import Path
import hashlib
import json

from probe_lesson import audit_fill_any_span

BASE = Path(__file__).resolve().parent
search = json.loads((BASE / 'python-search.json').read_text())
apply = json.loads((BASE / 'racket-seed3.json').read_text())
episode = json.loads((BASE / 'production-seed3.jsonl').read_text().splitlines()[0])
witness = search['first_witness']
assert witness['seed'] == episode['seed'] == 3
assert episode['sample_indices'] == [0, 1, 2, 3]
assert episode['rejections'] == []
assert apply['generator_sha256'] == episode['provenance']['generator_sha256'] == search['generator_sha256']
assert apply['executed_rule_hash'] == episode['executed_rule_hash'] == search['rule_hash']
materialized = episode['train'] + episode['test']
assert len(materialized) == len(apply['results']) == len(witness['pairs']) == 4
pairs = []
for i, (pair, actual, predicted) in enumerate(zip(materialized, apply['results'], witness['pairs'])):
    assert pair['input'] == actual['input'] == predicted['input']
    assert actual['valid_output'] and actual['error'] is None
    assert actual['generator_domain']['status'] == 'valid'
    assert pair['output'] == actual['output'] == predicted['python_mirror_output']
    rival = audit_fill_any_span(pair['input'])
    assert rival == predicted['audit_rival_output']
    mismatches = [{'row': r, 'column': c, 'actual_racket': actual['output'][r][c],
                   'audit_rival': rival[r][c]}
                  for r in range(len(rival)) for c in range(len(rival[0]))
                  if rival[r][c] != actual['output'][r][c]]
    pairs.append({'pair_index': i, 'split': 'train' if i < 3 else 'test',
                  'sample_index': i, 'input': pair['input'],
                  'input_shape': [len(pair['input']), len(pair['input'][0])],
                  'actual_racket_output': actual['output'], 'rival_output': rival,
                  'rival_matches': not mismatches, 'mismatches': mismatches,
                  'generator_domain': actual['generator_domain'],
                  'input_sha256': actual['input_sha256'], 'output_sha256': actual['output_sha256']})
assert all(p['rival_matches'] for p in pairs[:3]) and not pairs[3]['rival_matches']
rotations = []
for query in range(4):
    demos = [i for i in range(4) if i != query]
    fits = all(pairs[i]['rival_matches'] for i in demos)
    disagrees = not pairs[query]['rival_matches']
    rotations.append({'query_pair_index': query, 'demo_pair_indices': demos,
                      'rival_fits_demos': fits, 'rival_disagrees_query': disagrees,
                      'unsupported_under_audit_rival': fits and disagrees})
result = {'schema': 'arcpuzzles-audit-lesson-counterexample-v1',
          'finding_id': 'A-2b3472c73d30-1', 'task_id': search['task_id'],
          'generator_sha256': search['generator_sha256'],
          'rule_hash': apply['executed_rule_hash'], 'rule_text_sha256': apply['rule_text_sha256'],
          'seed': 3, 'sample_index': 0, 'sample_indices': [0,1,2,3],
          'difficulty': 'medium', 'overrides': {}, 'demonstration_count': 3,
          'production_policy': 'first 3 accepted pairs are demonstrations; fourth is query',
          'production_unsupported_queries': 1, 'production_queries_checked': 1,
          'rotation_policy': 'audit diagnostic: each of these same 4 pairs held out once',
          'rotation_unsupported_queries': sum(p['unsupported_under_audit_rival'] for p in rotations),
          'rotation_queries_checked': len(rotations), 'rotations': rotations,
          'audit_rival': 'audit_fill_any_span: fill only zero gaps between extrema of any row-local repeated color',
          'rival_origin': 'audit-added plausible canonical-fitting shortcut; generator declares no rivals',
          'retained_generation_lesson_check': episode['lesson_check'],
          'racket_pairs_checked': 4, 'racket_valid_domain_pairs': 4,
          'python_mirror_matches_racket': 4, 'pairs': pairs,
          'apply_command': apply['command'], 'apply_cwd': apply['cwd'],
          'artifacts': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in [BASE/'production-seed3.jsonl', BASE/'racket-seed3.json', BASE/'python-search.json']}}
(BASE / 'counterexample.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('pairs','rotations','artifacts')},sort_keys=True))
print(json.dumps({'query_mismatch_cells': len(pairs[3]['mismatches']), 'query_mismatches': pairs[3]['mismatches']}))
