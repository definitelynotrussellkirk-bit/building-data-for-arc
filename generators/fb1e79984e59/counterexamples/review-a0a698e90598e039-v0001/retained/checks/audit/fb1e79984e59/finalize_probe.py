from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
GEN_PATH = PACKET / 'repo/generators/fb1e79984e59/generator.py'


def ring_colors(grid):
    h, w = len(grid), len(grid[0])
    return [grid[d][d] for d in range((min(h, w) + 1) // 2)]


def repaint(grid, mapping):
    return [[mapping.get(value, value) for value in row] for row in grid]


def unique_predecessor(grid):
    unique = list(dict.fromkeys(ring_colors(grid)))
    return repaint(grid, {v: unique[(i - 1) % len(unique)] for i, v in enumerate(unique)})


def sorted_predecessor(grid):
    unique = sorted(set(ring_colors(grid)))
    return repaint(grid, {v: unique[(i - 1) % len(unique)] for i, v in enumerate(unique)})

pre = json.loads((OUT / 'probe_pre_apply.json').read_text())
generated = json.loads((OUT / 'generated_racket.json').read_text())
generated_authority_matches = [
    unique_predecessor(item['input']) == item['output'] for item in generated['results']
]
lesson = json.loads((OUT / 'lesson_racket.json').read_text())
lesson_meta = json.loads((OUT / 'lesson_meta.json').read_text())
rival_outputs = [sorted_predecessor(item['input']) for item in lesson['results']]
fits_demo = [rival_outputs[i] == lesson['results'][i]['output'] for i in range(3)]
query_diff = rival_outputs[3] != lesson['results'][3]['output']
(OUT / 'lesson_rival.json').write_text(json.dumps({
    'rival_name': 'numeric-sorted unique-color predecessor cycle',
    'definition': 'Sort the distinct ring colors numerically, then map each color to its cyclic predecessor in that sorted list.',
    'outputs': rival_outputs,
}, indent=2) + '\n')

diffs = [
    [r, c, lesson['results'][3]['output'][r][c], rival_outputs[3][r][c]]
    for r in range(len(rival_outputs[3]))
    for c in range(len(rival_outputs[3][0]))
    if lesson['results'][3]['output'][r][c] != rival_outputs[3][r][c]
]

final = {
    'schema': 'arcpuzzles-audit-probe-v1',
    'task_id': 'fb1e79984e59',
    'finding': 'lesson_level_color_order_shortcut',
    'generator_sha256': hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    'executed_rule_hash': lesson['executed_rule_hash'],
    'python_authority_checked_against_racket': {
        'matches': sum(generated_authority_matches),
        'denominator': len(generated_authority_matches),
        'seed': 20261004,
        'samples_per_band': 20,
    },
    'source_probe': {
        'census': pre['census'],
        'lesson_probe': pre['lesson_probe'],
        'overrides': {k: v for k, v in pre['overrides'].items() if k != 'results'},
    },
    'counterexample_lesson': {
        'difficulty': 'easy',
        'seed': 1,
        'start_sample_index': 2,
        'roles': ['demo', 'demo', 'demo', 'query'],
        'metadata_path': 'checks/audit/fb1e79984e59/lesson_meta.json',
        'input_path': 'checks/audit/fb1e79984e59/lesson_inputs.json',
        'authority_path': 'checks/audit/fb1e79984e59/lesson_racket.json',
        'rival_path': 'checks/audit/fb1e79984e59/lesson_rival.json',
        'all_inputs_pass_target_self_check': all(not item['self_check'] for item in lesson_meta),
        'all_inputs_belong_default_generated_distribution': True,
        'rival_fits_demo_vector': fits_demo,
        'rival_fits_all_three_demos': all(fits_demo),
        'rival_differs_on_query': query_diff,
        'query_differing_cell_count': len(diffs),
        'query_differing_cells': diffs,
    },
    'interpretation': (
        'The structural six-step schedule defeats direction and positional-depth rivals, '
        'but it does not schedule color-order permutations. On this ordinary generated '
        'lesson, numeric color order is accidentally a cyclic rotation of outer-to-inner '
        'order in all three demonstrations and ceases to be so on the query.'
    ),
}
(OUT / 'analysis.json').write_text(json.dumps(final, indent=2) + '\n')
print(json.dumps({
    'finding': final['finding'],
    'generator_sha256': final['generator_sha256'],
    'python_authority_checked_against_racket': final['python_authority_checked_against_racket'],
    'lesson_probe_ambiguous_case_count': pre['lesson_probe']['ambiguous_case_count'],
    'counterexample_lesson': final['counterexample_lesson'],
}, indent=2))
