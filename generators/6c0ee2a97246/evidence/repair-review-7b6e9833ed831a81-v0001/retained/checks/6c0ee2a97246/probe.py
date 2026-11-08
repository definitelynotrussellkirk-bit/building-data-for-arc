"""Bounded source-bound peer audit; no source/approval mutations."""
import hashlib
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / 'repo'
sys.path.insert(0, str(ROOT / 'shared/runtime'))
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator
from arc_repl.isolated_verifier import Limits, verify_candidate

TASK = '6c0ee2a97246'
assert find_root(__file__) == ROOT
gen, source_path, source_hash = load_selected_generator(TASK, root=ROOT)
rows = [json.loads(line) for line in canonical_path(ROOT).open() if line.strip()]
selected = [row for row in rows if row.get('task_id') == TASK]
assert len(selected) == 1
rule = selected[0]['program_solution']
rule_hash = hashlib.sha256(rule.encode()).hexdigest()
canonical = canonical_pairs(TASK, root=ROOT)

def rival(grid):
    """Fill each bbox, but erase occupied input cells strictly inside it."""
    result = [[0] * len(grid[0]) for _ in grid]
    for color, cells in gen._components(grid):
        rs, cs = zip(*cells)
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1) or grid[r][c] == 0:
                    result[r][c] = color
    return result

RIVAL_RULE = '''(rule! (for/fold ((out (empty-grid (rows g) (cols g) 0))) ((obj (in-list (objects g 0))))
 (let ((r0 (obj-r1 obj)) (r1 (obj-r2 obj)) (c0 (obj-c1 obj)) (c1 (obj-c2 obj)))
  (paint-cells out (for*/list ((r (in-range r0 (+ r1 1))) (c (in-range c0 (+ c1 1)))
    #:when (or (= r r0) (= r r1) (= c c0) (= c c1) (= (at g r c) 0))) (list r c)) (obj-color obj)))))'''

candidate = None
searched = []
for seed in range(64):
    pairs = []
    for index in range(1, 6):
        grid = gen.generate(seed, index, difficulty='medium')
        assert not gen.self_check(grid)
        pairs.append({'input': grid, 'output': gen.rule_mirror(grid)})
    gate = gen.lesson_identifiable(pairs[:4], pairs[4])
    fits = all(rival(p['input']) == p['output'] for p in pairs[:4])
    differs = rival(pairs[4]['input']) != pairs[4]['output']
    searched.append({'seed': seed, 'start_index': 1, 'gate_reasons': gate,
                     'rival_fits_four_demos': fits, 'rival_differs_query': differs})
    if not gate and fits and differs:
        candidate = {'seed': seed, 'difficulty': 'medium', 'sample_indices': [1,2,3,4,5],
                     'train': pairs[:4], 'test': pairs[4:]}
        break

limits = Limits(wall_seconds=35, step_seconds=3, cpu_seconds=20, memory_mb=2048, max_pairs=24)
canonical_task = {'train': [p for p in canonical if p['split'] == 'train'],
                  'test': [p for p in canonical if p['split'] == 'test']}
reports = {}
for label, program in [('canonical_reference', rule), ('canonical_rival', RIVAL_RULE)]:
    reports[label] = verify_candidate(canonical_task, program, racket_path=os.environ['RACKET_PATH'], limits=limits)
if candidate:
    for label, program in [('witness_reference', rule), ('witness_rival', RIVAL_RULE)]:
        reports[label] = verify_candidate(candidate, program, racket_path=os.environ['RACKET_PATH'], limits=limits)
    prediction = rival(candidate['test'][0]['input'])
    candidate['rival_query_output'] = prediction
    expected = candidate['test'][0]['output']
    candidate['query_differences'] = [{'row':r,'col':c,'reference':expected[r][c],'rival':prediction[r][c]}
        for r in range(len(expected)) for c in range(len(expected[0])) if expected[r][c] != prediction[r][c]]
    (HERE / 'witness.json').write_text(json.dumps(candidate, indent=2)+'\n')

report = {'task_id':TASK, 'assignment':'review-7b6e9833ed831a81',
          'generator_path':str(source_path.relative_to(ROOT)), 'generator_sha256':source_hash,
          'rule_sha256':rule_hash, 'canonical_variant':0,
          'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'rival_rule':RIVAL_RULE, 'search':searched, 'protected_reports':reports,
          'scope':'One rival, at most 64 medium lessons starting at index 1; stopped at first witness. No broad battery or parameter duty.',
          'racket_pair_evaluations_planned':18 if candidate else 8,
          'finding':bool(candidate)}
(HERE / 'result.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'generator_sha256':source_hash,'rule_sha256':rule_hash,'searched':len(searched),
                  'witness_seed':candidate['seed'] if candidate else None,
                  'query_differences':candidate['query_differences'] if candidate else [],
                  'native':{k:{'status':v['status'],'hidden_exact':v.get('hidden_exact'),'error':v.get('error')} for k,v in reports.items()}},indent=2))
assert all(r['status']=='pass' for r in reports.values())
if candidate:
    assert reports['witness_reference']['hidden_exact'] is True
    assert reports['witness_rival']['hidden_exact'] is False
    assert reports['witness_rival']['test_outputs'] == [candidate['rival_query_output']]
