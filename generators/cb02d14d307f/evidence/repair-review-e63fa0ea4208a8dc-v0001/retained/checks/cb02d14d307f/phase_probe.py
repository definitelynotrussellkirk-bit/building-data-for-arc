"""Bounded adversarial episode probe; production files remain unchanged."""
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, load_selected_generator
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

TASK = 'cb02d14d307f'
root = Path.cwd()
module, source, digest = load_selected_generator(TASK, root=root)
rows = [json.loads(line) for line in (root / 'shared/data/canonical/puzzles.jsonl').read_text().splitlines()
        if json.loads(line).get('task_id') == TASK]
assert len(rows) == 1
program = rows[0]['program_solution']
rival = program.replace('(mod (- r start) sc)', '(mod r sc)')
assert rival != program

def signature(g):
    sources = sum(row[0] == 5 for row in g)
    start = 1 + max(r for r, row in enumerate(g) if any(row))
    return sources, start

episode = None
for seed in range(128):
    grids = [module.generate(seed, i) for i in range(4)]
    sigs = [signature(g) for g in grids]
    if all(start % sc == 0 for sc, start in sigs[:3]) and sigs[3][1] % sigs[3][0]:
        episode = (seed, grids, sigs)
        break

report = {'task_id': TASK, 'probe': 'absolute-row phase versus reset-at-blank-band phase',
          'generator_source': str(source.relative_to(root)), 'generator_sha256': digest,
          'canonical_program_sha256': hashlib.sha256(program.encode()).hexdigest(),
          'rival_program': rival, 'seed_search': {'first': 0, 'last': 127, 'demos': 3, 'queries': 1},
          'limits': ['One rival only; no broad battery, parametric qualification, or production edits.',
                     'Candidate seed search screens phase divisibility; one episode receives live Racket labels.',
                     'This is an existence witness, not an estimated ambiguity frequency.']}
if episode is None:
    report['outcome'] = 'bounded_no_finding'
else:
    seed, grids, sigs = episode
    report['seed_search']['last_checked'] = seed
    report['seed'] = seed
    report['signatures'] = [{'source_rows': sc, 'repeat_start': start} for sc, start in sigs]
    report['self_checks'] = [module.self_check(g) for g in grids]
    assert all(not errors for errors in report['self_checks'])
    with _local_imports(root / 'shared/runtime', source.parent):
        apply, identity, bridge = _real_evaluator(root / 'shared/runtime')
        try:
            canonical = [apply(program, g) for g in grids]
            alternative = [apply(rival, g) for g in grids]
            pairs = canonical_pairs(TASK, root=root)
            canonical_checks = [apply(program, p['input']) == p['output'] for p in pairs]
            rival_canonical_checks = [apply(rival, p['input']) == p['output'] for p in pairs]
        finally:
            bridge.close()
    fits = [a == b for a, b in zip(canonical, alternative)]
    report.update({'outcome': 'concrete_generated_episode_ambiguity' if fits == [True, True, True, False] else 'candidate_rejected',
                   'racket': identity, 'racket_evaluations': 8 + 2 * len(pairs),
                   'rival_matches': fits, 'canonical_pair_checks': canonical_checks,
                   'rival_canonical_pair_checks': rival_canonical_checks,
                   'train': [{'sample_index': i, 'input': grids[i], 'output': canonical[i], 'rival_output': alternative[i]} for i in range(3)],
                   'test': [{'sample_index': 3, 'input': grids[3], 'output': canonical[3], 'rival_output': alternative[3]}]})
    assert all(canonical_checks)
    assert fits == [True, True, True, False]

out = Path(__file__).with_name('phase_probe_report.json')
out.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k not in {'train', 'test', 'rival_program'}}, indent=2))
