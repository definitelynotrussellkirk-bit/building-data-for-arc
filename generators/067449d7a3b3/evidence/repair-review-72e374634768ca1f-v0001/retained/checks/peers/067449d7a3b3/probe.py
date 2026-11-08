#!/usr/bin/env python3
"""Bounded protected-Racket learnability probe; no approvals or source mutations."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import signal
import sys
import time

START = time.monotonic()
signal.alarm(90)
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2] / 'repo'
RUNTIME = ROOT / 'shared/runtime'
sys.path[:0] = [str(ROOT / 'src'), str(RUNTIME)]
from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import load_selected_generator, canonical_pairs

TASK = '067449d7a3b3'
EXPECTED_SOURCE = 'a99b4745c87be0be95a1b46d3098123a962734c5f8552ee1d6560b9e33f28ee7'
EXPECTED_RULE = 'fb156b8e3aee'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
gen, source, source_sha = load_selected_generator(TASK, root=ROOT)
assert source_sha == EXPECTED_SOURCE, source_sha
catalog = Catalog(ROOT)
selected = catalog.describe(TASK)
rule_task_id = selected.get('rule_task_id', TASK)
program, = {v['program_solution'] for v in catalog._variants()[rule_task_id]}
assert sha(' '.join(program.split()).encode())[:12] == EXPECTED_RULE
old = '(!= (at g r c) 9)'
assert program.count(old) == 1
rival = program.replace(old, '(= (at g r c) bg)')

# A valid three-object counterexample: a nearby maroon 2x4 rectangle's halo
# crosses a non-maroon L without joining its 8-connected component.
witness = [[0] * 10 for _ in range(10)]
for r, c in ((1, 1), (1, 2), (2, 1)):
    witness[r][c] = 2
for r in (3, 4):
    for c in range(3, 7):
        witness[r][c] = 9
witness[1][8] = 9
assert gen.self_check(witness) == []
assert gen.strict_canonical_like(witness) == []
seed = 91
indices = [0, 1, 2]
inputs = [gen.generate(seed, i) for i in indices]
assert all(gen.self_check(g) == [] for g in inputs)
apply, identity, bridge = _real_evaluator(RUNTIME)
calls = 0

def run(code, grid):
    global calls
    result = apply(code, grid)
    calls += 1
    return result

try:
    canonical_checks = []
    for i, pair in enumerate(canonical_pairs(rule_task_id, root=ROOT, labeled_only=True)):
        actual = run(program, pair['input'])
        alternate = run(rival, pair['input'])
        assert actual == alternate == pair['output'], ('canonical', i)
        canonical_checks.append({'index': i, 'reference_and_rival_match': True})
    demos = []
    for i, grid in zip(indices, inputs):
        actual, alternate = run(program, grid), run(rival, grid)
        assert actual == alternate, ('demo', i)
        assert actual == gen._mirror(grid)
        demos.append({'input': grid, 'output': actual})
    expected, alternate = run(program, witness), run(rival, witness)
    assert expected == gen._mirror(witness)
    assert expected != alternate
finally:
    bridge.close()
errors = gen.lesson_identifiable(demos, {'input': witness, 'output': expected})
assert errors == [], errors
assert sha(source.read_bytes()) == source_sha
changed = [{'row': r, 'col': c, 'reference': value, 'rival': alternate[r][c]}
           for r, row in enumerate(expected) for c, value in enumerate(row)
           if value != alternate[r][c]]
result = {
    'schema': 'bounded-peer-learnability-v1', 'task_id': TASK,
    'generator_sha256': source_sha, 'normalized_rule_hash': EXPECTED_RULE,
    'reference_program_sha256': sha(program.encode()),
    'rival_program_sha256': sha(rival.encode()),
    'reference_program': program, 'rival_program': rival,
    'runtime_identity': identity, 'status': 'finding',
    'finding': 'preserve_all_foreground_during_halo_painting_survives_demos',
    'rival_description': 'Paint green halo cells only where the original input is background; preserve every original foreground color instead of preserving only maroon 9.',
    'canonical_checks': canonical_checks,
    'generated_demo_calls': {'seed': seed, 'sample_indices': indices, 'difficulty': None, 'overrides': {}},
    'lesson': {'train': demos, 'test': [{'input': witness, 'output': expected}]},
    'query_rival_output': alternate, 'query_differences': changed,
    'query_origin': 'authored accepted-manifold query, not generated',
    'query_self_check': [], 'query_strict_canonical_like': [],
    'query_observed_axes': gen.observe_overrides(witness),
    'lesson_identifiable_errors': errors, 'rival_fits_all_visible_demos': True,
    'rival_changes_query': True, 'source_unchanged_before_after': True,
    'racket_executions': calls,
    'actionable_proposal': 'Add a Racket-checked counterexample where a maroon object halo visibly crosses a separate non-maroon irregular object, and include this preservation rival in demo-only learnability checks while retaining current schedule guarantees.',
    'limits': ['One targeted rival and one three-demo lesson; no census or battery.', 'Query is authored and self-check accepted; no generated-query failure was established.', 'Does not prove this rival agrees on every generated input.', 'No generator or approval changes.'],
    'completed_utc': datetime.now(timezone.utc).isoformat(),
    'elapsed_seconds': time.monotonic() - START,
}
(OUT / 'evidence.json').write_text(json.dumps(result, sort_keys=True, separators=(',', ':')) + '\n')
signal.alarm(0)
print(json.dumps({k: result[k] for k in ('status', 'finding', 'generator_sha256', 'racket_executions', 'query_differences', 'elapsed_seconds')}))
