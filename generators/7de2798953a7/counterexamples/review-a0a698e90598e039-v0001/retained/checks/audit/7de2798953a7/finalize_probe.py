from __future__ import annotations

import hashlib
import json
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
PACKET = Path(__file__).resolve().parents[3]
GEN_PATH = PACKET / 'repo/generators/7de2798953a7/generator.py'


def rival_left_endpoint_any_two_nonzero(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        positions = [c for c, value in enumerate(row) if value != 0]
        if len(positions) != 2:
            continue
        left, right = positions
        if not all(value == 0 for value in row[left + 1:right]):
            continue
        color = row[left]
        for k, c in enumerate(range(left + 1, right), start=1):
            if k % 2 == 1:
                out[r][c] = color
    return out

pre = json.loads((OUT_DIR / 'probe_pre_apply.json').read_text())
racket = json.loads((OUT_DIR / 'generated_racket.json').read_text())
comparisons = []
for result in racket['results']:
    rival = rival_left_endpoint_any_two_nonzero(result['input'])
    comparisons.append(rival == result['output'])

counter_input = json.loads((OUT_DIR / 'input.json').read_text())
counter_racket = json.loads((OUT_DIR / 'racket.json').read_text())
counter_authority = counter_racket['results'][0]['output']
counter_rival = rival_left_endpoint_any_two_nonzero(counter_input)
(OUT_DIR / 'rival.json').write_text(json.dumps({
    'rival_name': 'left-endpoint alternating bridge for any row with exactly two nonzero cells',
    'output': counter_rival,
}, indent=2) + '\n')

final = {
    'schema': 'arcpuzzles-audit-probe-v1',
    'task_id': '7de2798953a7',
    'finding': 'teaching_shortcut',
    'generator_sha256': hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    'executed_rule_hash': counter_racket['executed_rule_hash'],
    'rival': 'Fill odd interior positions using the left endpoint whenever a row has exactly two nonzero cells; do not require equal endpoint colors.',
    'canonical_pair_count': pre['canonical_pair_count'],
    'rival_fits_all_canonical_pairs': pre['rival_fits_all_canonical_pairs'],
    'generated_sample': {
        'seed': pre['seed'],
        'samples_per_band': pre['samples_per_band'],
        'total': pre['generated_count'],
        'all_pass_self_check': pre['all_generated_pass_self_check'],
        'rival_matches_authority_count': sum(comparisons),
        'denominator': len(comparisons),
    },
    'counterexample': {
        'input_path': 'checks/audit/7de2798953a7/input.json',
        'passes_target_self_check': True,
        'belongs_default_generated_distribution': False,
        'belongs_reference_task_domain': True,
        'authority_output_path': 'checks/audit/7de2798953a7/racket.json',
        'rival_output_path': 'checks/audit/7de2798953a7/rival.json',
        'outputs_differ': counter_authority != counter_rival,
        'differing_cells': [
            [r, c, counter_authority[r][c], counter_rival[r][c]]
            for r in range(len(counter_authority))
            for c in range(len(counter_authority[0]))
            if counter_authority[r][c] != counter_rival[r][c]
        ],
    },
    'commands': [
        {'cwd': 'packet_root', 'argv': ['PYTHONPATH=repo/shared/runtime', 'python3', 'checks/audit/7de2798953a7/build_probe.py']},
        {'cwd': 'packet_root', 'argv': ['python3', 'run_with_racket.py', 'python3', '-m', 'arcpuzzles', 'apply', '7de2798953a7', '--input', '../checks/audit/7de2798953a7/generated_inputs.json', '--out', '../checks/audit/7de2798953a7/generated_racket.json']},
        {'cwd': 'packet_root', 'argv': ['PYTHONPATH=repo/shared/runtime', 'python3', 'checks/audit/7de2798953a7/finalize_probe.py']},
    ],
}
(OUT_DIR / 'analysis.json').write_text(json.dumps(final, indent=2) + '\n')
print(json.dumps({k: final[k] for k in ('task_id','finding','rival_fits_all_canonical_pairs')}, indent=2))
print(json.dumps(final['generated_sample'], indent=2))
print(json.dumps(final['counterexample'], indent=2))
