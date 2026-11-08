"""Replay one existing tally-position ambiguity; no repository mutations."""
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / 'repo'
sys.path[:0] = [str(ROOT / 'shared/runtime'), str(ROOT / 'src')]
from reviewer_support import canonical_path, find_root, load_selected_generator
from arcpuzzles import Catalog

TASK = '80b1344c17c8'
EXPECTED_SOURCE = 'bdbf96dcad6ea4ce6bf0ada9e5c745f847af9969df1875495f5634bdd17d5263'
assert find_root(__file__) == ROOT
mod, source, digest = load_selected_generator(TASK, root=ROOT)
assert digest == EXPECTED_SOURCE, (digest, EXPECTED_SOURCE)
rows = [json.loads(line) for line in canonical_path(ROOT).open() if line.strip()]
canonical = [row for row in rows if row.get('task_id') == TASK]
assert len(canonical) == 1
rule = canonical[0]['program_solution']


def prefix(grid):
    k = sum(value != 0 for value in grid[0])
    return grid[0] == [1] * k + [0] * (len(grid[0]) - k)


def rival(grid):
    """Known rival: counted clockwise orbit, but copy body on prefix tallies."""
    body = [row[:] for row in grid[1:]]
    if prefix(grid):
        return body
    k = sum(v != 0 for v in grid[0])
    ar, ac = next((r, c) for r, row in enumerate(body) for c, v in enumerate(row) if v == 9)
    output = [[0] * len(body[0]) for _ in body]
    output[ar][ac] = 9
    for r, row in enumerate(body):
        for c, value in enumerate(row):
            if value in (0, 9):
                continue
            dr, dc = r - ar, c - ac
            for _ in range(k):
                rr, cc = ar + dr, ac + dc
                if 0 <= rr < len(body) and 0 <= cc < len(body[0]):
                    output[rr][cc] = value
                dr, dc = dc, -dr
    return output


inputs = [mod.generate(0, index, difficulty='medium') for index in range(2, 8)]
validation = [mod.self_check(grid, difficulty='medium') for grid in inputs]
assert not any(validation), validation
applied = Catalog(ROOT).apply(TASK, inputs, reference='canonical', allow_unapproved=True,
                             timeout=45, check_generator_domain=True)
(HERE / 'racket.json').write_text(json.dumps(applied, indent=2) + '\n')
assert applied['generator_sha256'] == digest
assert applied['executed_rule_hash'] == 'd19ea091585d'
assert applied['rule_hash_matches_catalog']
assert all(row['valid_output'] and row['error'] is None for row in applied['results'])
outputs = [row['output'] for row in applied['results']]
rivals = [rival(grid) for grid in inputs]
fit = [got == expected for got, expected in zip(rivals, outputs)]
demos = [{'input': inp, 'output': out} for inp, out in zip(inputs[:5], outputs[:5])]
query = {'input': inputs[5], 'output': outputs[5]}
reasons = mod.lesson_identifiable(demos, query)
index_path = ROOT / 'generators' / TASK / 'evidence/review_index.json'
index = json.loads(index_path.read_text())
prior = ROOT / 'generators' / TASK / 'counterexamples/review-e30517dcc08d4f0c-v0001/retained/checks/audit/80b1344c17c8/racket.json'
prior_rows = json.loads(prior.read_text())['results']
prior_same = len(prior_rows) == len(inputs) and all(row['input'] == inp and row['output'] == out for row, inp, out in zip(prior_rows, inputs, outputs))
evidence = {
 'schema': 'bounded-peer-learnability-probe-v1', 'task_id': TASK,
 'source_sha256': digest, 'source_path': source.relative_to(ROOT).as_posix(),
 'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'canonical_rule_text_sha256': hashlib.sha256(rule.encode()).hexdigest(),
 'executed_rule_hash': applied['executed_rule_hash'],
 'command': 'WORK/.venv/bin/python review.py run --receipt checks/80b1344c17c8/command.json python3 ../checks/80b1344c17c8/probe.py',
 'case': {'seed': 0, 'difficulty': 'medium', 'demo_indices': list(range(2, 7)), 'query_index': 7},
 'rival': {'name': 'prefix-tally-copy-body', 'definition': 'Use counted clockwise rotations for non-prefix headers; force k=1 for prefix headers.'},
 'validation_errors': validation,
 'tally_counts': [sum(v != 0 for v in grid[0]) for grid in inputs],
 'prefix_flags': [prefix(grid) for grid in inputs],
 'demo_fit': fit[:5], 'query_fit': fit[5],
 'lesson_identifiable_reasons': reasons,
 'prior_witness_inputs_and_outputs_reproduced': prior_same,
 'query_disagreement_cells': [[r,c] for r,row in enumerate(outputs[5]) for c,value in enumerate(row) if value != rivals[5][r][c]],
 'train': demos, 'query': {**query, 'rival_output': rivals[5]},
 'existing_audit_statuses_preserved': [{k: audit.get(k) for k in ('return_id','source_sha256','resolution','verification_status')} for audit in index['audits']],
 'finding': 'Existing query-changing prefix-tally ambiguity reproduced on unchanged source with protected Racket labels.',
 'limits': ['One previously reported six-input lesson only; no frequency estimate or broad battery.', 'Repository source, notes and audit statuses untouched.'],
}
assert all(fit[:5]) and not fit[5], fit
assert reasons == ['no prefix tally demonstration'], reasons
assert prior_same
(HERE / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
print(json.dumps({key:evidence[key] for key in ['source_sha256','executed_rule_hash','demo_fit','query_fit','prefix_flags','lesson_identifiable_reasons','query_disagreement_cells','prior_witness_inputs_and_outputs_reproduced']}))
