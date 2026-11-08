#!/usr/bin/env python3
"""Bounded findings-only audit; no task/shared source writes."""
import hashlib
import json
from pathlib import Path
import sys
from arcpuzzles.catalog import Catalog
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = '75ba893e1e36'
root = find_root(__file__)
module, source_path, source_sha = load_selected_generator(TASK, root=root)
command = {'cwd': 'repo', 'argv': [sys.executable, *sys.argv], 'exit_code': 0}
observations = []
for seed in (0, 1):
    overrides = {'left_edge_kind': 'matching', 'lr_asymmetric': True}
    grid = module.generate(seed, 0, **overrides)
    observations.append({'generate_call': {'seed': seed, 'sample_index': 0,
                                           'difficulty': None, 'overrides': overrides},
                         'input': grid, 'self_check_errors': module.self_check(grid),
                         'lr_symmetric': all(row == row[::-1] for row in grid)})
witness = observations[1]
assert witness['lr_symmetric'] and witness['self_check_errors']
assert not observations[0]['self_check_errors']
# The documented palette_size lower endpoint also fails before even an explicitly
# supported monochrome texture can be considered.
palette_cases = []
for overrides in ({'palette_size': 1}, {'palette_size': 1, 'texture': 'monochrome'}):
    try:
        module.generate(0, 0, **overrides)
    except ValueError as exc:
        palette_cases.append({'generate_call': {'seed': 0, 'sample_index': 0,
                                                'difficulty': None, 'overrides': overrides},
                              'error': repr(exc)})
    else:
        raise AssertionError('Expected current documented palette endpoint failure')
reference = Catalog(root).apply(TASK, [witness['input']], timeout=300, check_generator_domain=True)
result = reference['results'][0]
assert result['output'] is not None, result
rival = [row * 4 for row in witness['input']]
assert result['output'] == rival
assert result['generator_domain']['status'] == 'invalid'
canonical = canonical_pairs(TASK, root=root, labeled_only=True)
canonical_rival_fits = sum([row * 4 for row in pair['input']] == pair['output'] for pair in canonical)
rules = [json.loads(line)['program_solution'] for line in canonical_path(root).read_text().splitlines()
         if json.loads(line).get('task_id') == TASK]
report = {
    'task_id': TASK, 'status': 'findings only; target unchanged',
    'generator_sha256': source_sha,
    'canonical_rule': rules[0],
    'canonical_rule_exact_text_sha256': hashlib.sha256(rules[0].encode()).hexdigest(),
    'source_identity_verified': reference['generator_sha256'] == source_sha,
    'command': command,
    'wrapper_recipe_from_WORK': ['python3', 'run_with_racket.py', '../.venv/bin/python',
                                 '../checks/audit/75ba893e1e36/reproducer.py'],
    'observations': observations,
    'palette_endpoint_cases': palette_cases,
    'racket_reference': reference,
    'rival': {'name': 'four unchanged horizontal copies', 'output': rival,
              'fits_witness': True, 'canonical_pairs_fit': canonical_rival_fits,
              'canonical_pair_denominator': len(canonical)},
    'counts': {'matching_calls': 2, 'matching_self_check_failures': 1,
               'palette_size_one_calls': 2, 'palette_size_one_rejections': 2,
               'racket_witness_inputs': 1, 'canonical_labeled_pairs_compared_to_rival': len(canonical)},
    'limits': ['Two matching calls only: seeds0..1, sample_index0; no population-frequency estimate.',
               'This is generator/control and validation inconsistency, not a false Racket label.',
               'The symmetric witness is rejected by self_check; no successful export of it is claimed.',
               'The unchanged-copy rival is a witness ambiguity, not a canonical shortcut claim.',
               'No full battery, random lesson census, or production distribution certification.']}
assert report['source_identity_verified']
Path(__file__).with_name('report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'task_id': TASK, 'generator_sha256': source_sha,
                  'rule_hash': reference['executed_rule_hash'], 'counts': report['counts'],
                  'canonical_rival_fits': canonical_rival_fits}))
